# game_manager.py
import pygame
import sys
from menu import Menu
from level_page import LevelPage
from level_controller import LevelController
from player import Player, DEATH_SEQUENCE_DURATION
from npc import NPC
from cube import GRID_SIZE

# --- Constants ---
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 700
FLOOR_BACKGROUND_COLOR = (46, 80, 93)
STAGGER_HEIGHT_PER_ROW = int(GRID_SIZE * 0.8)

# --- Base State Class ---
class BaseState:
    """Abstract base class for all game states."""
    def __init__(self):
        self.next_state = None
        self.done = False

    def handle_events(self, events):
        raise NotImplementedError

    def update(self, dt):
        raise NotImplementedError

    def draw(self, screen):
        raise NotImplementedError

# --- Menu State ---
class MenuState(BaseState):
    def __init__(self, screen, click_sound):
        super().__init__()
        self.screen = screen
        self.menu = Menu(screen)
        self.click_sound = click_sound

    def handle_events(self, events):
        menu_choice = self.menu.run(events)
        if menu_choice == 'start':
            if self.click_sound: self.click_sound.play()
            self.next_state = 'LEVEL_SELECT'
            self.done = True
        elif menu_choice == 'exit':
            self.next_state = 'EXIT'
            self.done = True
            
    def update(self, dt):
        self.menu.update_showcase(dt)

    def draw(self, screen):
        self.menu.draw()

# --- Level Select State ---
class LevelSelectState(BaseState):
    def __init__(self, screen, level_controller, click_sound):
        super().__init__()
        self.screen = screen
        self.level_controller = level_controller
        self.level_page = LevelPage(screen, level_controller)
        self.click_sound = click_sound

    def handle_events(self, events):
        level_choice = self.level_page.run(events)
        if isinstance(level_choice, int):
            if self.click_sound: self.click_sound.play()
            self.next_state = 'GAMEPLAY'
            # Pass the selected level to the next state
            self.done = True
            return {'level_number': level_choice}
        elif level_choice == 'menu':
            if self.click_sound: self.click_sound.play()
            self.next_state = 'MENU'
            self.done = True

    def update(self, dt):
        pass # No dynamic updates needed here

    def draw(self, screen):
        self.level_page.draw()

# --- Gameplay State ---
class GameplayState(BaseState):
    def __init__(self, screen, level_controller, level_number, sounds):
        super().__init__()
        self.screen = screen
        self.level_controller = level_controller
        self.win_music, self.lose_music, self.click_sound = sounds['win'], sounds['lose'], sounds['click']

        self.maze = level_controller.get_level(level_number)
        if not self.maze:
            print(f"Error: Could not load level {level_number}.")
            self.next_state = 'LEVEL_SELECT'
            self.done = True
            return
            
        self.player = Player(1, 1, self.maze)
        self.clock = pygame.time.Clock()

        # --- UI and Pause Setup ---
        self.setup_pause_menu()
        self.setup_ui_elements()
        
        # --- Game State Flags ---
        self.paused = False
        self.game_over = False
        self.win = False
        self.win_sound_played = False
        self.lose_sound_played = False
        self.active_level_number = level_number

    def setup_ui_elements(self):
        self.stop_icon = pygame.transform.scale(pygame.image.load('./assets/stop2.png').convert_alpha(), (40, 40))
        self.stop_icon_rect = self.stop_icon.get_rect(topright=(SCREEN_WIDTH - 70, 18))
        font = pygame.font.Font("./assets/font.ttf", 72)
        self.game_over_text = font.render("GAME OVER", True, (255, 255, 255))
        self.win_text = font.render("YOU WIN!", True, (255, 255, 255))
        self.game_over_rect = self.game_over_text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2))
        self.win_rect = self.win_text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2))

    def setup_pause_menu(self):
        font = pygame.font.Font("./assets/font.ttf", 72)
        button_color = (60, 95, 110)
        text_color = (255, 255, 255)
        self.resume_text = font.render("Keep Playing", True, text_color)
        self.menu_text = font.render("Back to Menu", True, text_color)
        self.resume_rect = pygame.Rect(0, 0, 490, 100)
        self.menu_rect = pygame.Rect(0, 0, 490, 100)
        self.resume_rect.center = (SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 80)
        self.menu_rect.center = (SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 80)

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.handle_mouse_clicks(event.pos)
            if not self.paused:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.done = True
                        self.next_state = 'LEVEL_SELECT'
                    elif (self.game_over or self.win) and event.key == pygame.K_RETURN:
                         if self.win:
                             self.level_controller.unlock_next_level(self.active_level_number)
                         self.done = True
                         self.next_state = 'LEVEL_SELECT'
                    else:
                        self.player.handle_key_down(event.key, self.maze.npcs)
                elif event.type == pygame.KEYUP:
                    self.player.handle_key_up(event.key)

    def handle_mouse_clicks(self, pos):
        if not self.paused and self.stop_icon_rect.collidepoint(pos):
            if self.click_sound: self.click_sound.play()
            self.paused = True
        elif self.paused:
            if self.resume_rect.collidepoint(pos):
                if self.click_sound: self.click_sound.play()
                self.paused = False
            if self.menu_rect.collidepoint(pos):
                if self.click_sound: self.click_sound.play()
                self.done = True
                self.next_state = 'MENU'

    def update(self, dt):
        if self.paused:
            return

        self.player.update(dt, self.maze.npcs)
        for npc in self.maze.npcs:
            other_npcs = [other for other in self.maze.npcs if other != npc]
            npc.update(dt, self.player, other_npcs)

        # Remove dead NPCs
        self.maze.npcs = [npc for npc in self.maze.npcs if not (npc.is_dead and npc.death_timer > npc.config["death_duration"])]

        # Check for game over or win conditions
        if not self.game_over and self.player.is_dead and self.player.death_timer > DEATH_SEQUENCE_DURATION:
            self.game_over = True
        if not self.win and not self.maze.npcs:
            self.win = True

    def draw(self, screen):
        screen.fill(FLOOR_BACKGROUND_COLOR)
        self.maze.draw(screen, self.player, self.maze.npcs)
        self.draw_ui(screen)
        screen.blit(self.stop_icon, self.stop_icon_rect)

        if self.game_over:
            if self.lose_music and not self.lose_sound_played:
                self.lose_music.play()
                self.lose_sound_played = True
            screen.blit(self.game_over_text, self.game_over_rect)
        elif self.win:
            if self.win_music and not self.win_sound_played:
                self.win_music.play()
                self.win_sound_played = True
            screen.blit(self.win_text, self.win_rect)

        if self.paused:
            self.draw_pause_overlay(screen)
            
    def draw_ui(self, screen):
        health_bar_bg = pygame.Rect(10, 10, 204, 24)
        pygame.draw.rect(screen, (50, 50, 50), health_bar_bg)
        health_ratio = self.player.health / self.player.max_health
        health_bar_fg = pygame.Rect(12, 12, 200 * health_ratio, 20)
        pygame.draw.rect(screen, (200, 20, 20), health_bar_fg)
        pygame.draw.rect(screen, (255, 255, 255), health_bar_bg, 2)

    def draw_pause_overlay(self, screen):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))
        pygame.draw.rect(screen, (60, 95, 110), self.resume_rect, border_radius=10)
        pygame.draw.rect(screen, (60, 95, 110), self.menu_rect, border_radius=10)
        screen.blit(self.resume_text, self.resume_text.get_rect(center=self.resume_rect.center))
        screen.blit(self.menu_text, self.menu_text.get_rect(center=self.menu_rect.center))

# --- Game Manager ---
class GameManager:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("THE DUNGEON WARRIOR")
        self.clock = pygame.time.Clock()
        
        self.load_assets()
        self.level_controller = LevelController()

        self.states = {
            'MENU': MenuState(self.screen, self.click_sound),
            'LEVEL_SELECT': LevelSelectState(self.screen, self.level_controller, self.click_sound),
            'GAMEPLAY': None # This will be created on the fly
        }
        self.current_state = self.states['MENU']

    def load_assets(self):
        self.win_music, self.lose_music, self.click_sound = None, None, None
        self.music_on = True
        try:
            pygame.mixer.music.load('./assets/music.mp3')
            pygame.mixer.music.set_volume(0.5)
            self.win_music = pygame.mixer.Sound('./assets/win.mp3')
            self.lose_music = pygame.mixer.Sound('./assets/lose.mp3')
            self.click_sound = pygame.mixer.Sound('./assets/click.mp3')
        except pygame.error as e:
            print(f"Warning: Could not load one or more sounds: {e}")
            self.music_on = False
            
        self.music_on_img = pygame.transform.scale(pygame.image.load('./assets/music.png').convert_alpha(), (50, 50))
        self.music_off_img = pygame.transform.scale(pygame.image.load('./assets/music.png').convert_alpha(), (50, 50))
        self.music_icon_rect = self.music_on_img.get_rect(topright=(SCREEN_WIDTH - 15, 15))

    def transition_state(self, event_info=None):
        next_state_name = self.current_state.next_state
        if next_state_name == 'EXIT':
            self.level_controller._save_progress()
            pygame.quit()
            sys.exit()

        self.current_state.done = False
        
        # When moving from a gameplay state, restart background music
        if isinstance(self.current_state, GameplayState):
            if self.music_on and not pygame.mixer.music.get_busy():
                pygame.mixer.music.play(-1)

        # Create a new gameplay state instance when needed
        if next_state_name == 'GAMEPLAY':
            level_num = event_info.get('level_number', 1)
            sounds = {'win': self.win_music, 'lose': self.lose_music, 'click': self.click_sound}
            self.states['GAMEPLAY'] = GameplayState(self.screen, self.level_controller, level_num, sounds)
        
        self.current_state = self.states[next_state_name]

    def run(self):
        if self.music_on:
            pygame.mixer.music.play(-1)

        while True:
            dt = self.clock.tick(60) / 1000.0
            
            # --- Event Handling ---
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    self.level_controller._save_progress()
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.music_icon_rect.collidepoint(event.pos):
                        self.music_on = not self.music_on
                        if self.music_on: pygame.mixer.music.unpause()
                        else: pygame.mixer.music.pause()
            
            # --- State Machine Logic ---
            event_info = self.current_state.handle_events(events)
            self.current_state.update(dt)
            
            self.screen.fill(FLOOR_BACKGROUND_COLOR)
            self.current_state.draw(self.screen)

            # Draw global UI elements (like music icon)
            self.screen.blit(self.music_on_img if self.music_on else self.music_off_img, self.music_icon_rect)
            
            pygame.display.flip()

            if self.current_state.done:
                self.transition_state(event_info)