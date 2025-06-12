# main.py
import pygame
import sys
from menu import Menu
from level_page import LevelPage
from level_controller import LevelController
from cube import GRID_SIZE
from player import Player, DEATH_SEQUENCE_DURATION
from npc import NPC

# Game Constants
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 700
FLOOR_BACKGROUND_COLOR = (46, 80, 93)
STAGGER_HEIGHT_PER_ROW = int(GRID_SIZE * 0.8)

def draw_ui(screen, player):
    """Draws the player's health bar."""
    health_bar_bg = pygame.Rect(10, 10, 204, 24)
    pygame.draw.rect(screen, (50, 50, 50), health_bar_bg)
    
    health_ratio = player.health / player.max_health
    health_bar_fg = pygame.Rect(12, 12, 200 * health_ratio, 20)
    pygame.draw.rect(screen, (200, 20, 20), health_bar_fg)
    
    pygame.draw.rect(screen, (255, 255, 255), health_bar_bg, 2) # Border

def game_loop(screen, level_controller, level_number, win_music, lose_music, click_sound):
    """The main game loop for a single level, including pause functionality."""
    # --- Game Setup ---
    maze = level_controller.get_level(level_number)
    if not maze:
        print(f"Error: Could not load level {level_number}.")
        return 'menu'

    player = Player(1, 1, maze)
    clock = pygame.time.Clock()
    
    
    stop_icon = pygame.image.load('./assets/stop2.png').convert_alpha()
    stop_icon = pygame.transform.scale(stop_icon, (40, 40))
    stop_icon_rect = stop_icon.get_rect(topright=(SCREEN_WIDTH - 70, 18))

    font_path = "./assets/font.ttf"
    font = pygame.font.Font(font_path, 72)
    button_color = (60, 95, 110)
    text_color = (255, 255, 255)
    
    resume_text = font.render("Keep Playing", True, text_color)
    menu_text = font.render("Back to Menu", True, text_color)
    
    resume_rect = pygame.Rect(0, 0, 490, 100)
    menu_rect = pygame.Rect(0, 0, 490, 100)
    resume_rect.center = (SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 80)
    menu_rect.center = (SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 80)

    # --- Game State ---
    running = True
    paused = False
    game_over = False
    win = False
    win_sound_played = False
    lose_sound_played = False

    game_over_text = font.render("GAME OVER", True, (255, 255, 255))
    game_over_rect = game_over_text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2))

    win_text = font.render("YOU WIN!", True, (255, 255, 255))
    win_rect = win_text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2))

    while running:
        dt = clock.tick(60) / 1000.0 if not paused else 0

        # --- Event Handling ---
        for event in pygame.event.get():
            yield event 

            if event.type == pygame.QUIT: return 'exit'
            
            # --- Pause Logic with Click Sounds ---
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if not paused and stop_icon_rect.collidepoint(event.pos):
                    if click_sound: click_sound.play()
                    paused = True
                elif paused:
                    if resume_rect.collidepoint(event.pos):
                        if click_sound: click_sound.play()
                        paused = False
                    if menu_rect.collidepoint(event.pos):
                        if click_sound: click_sound.play()
                        return 'menu'

            # --- Gameplay Input (only if not paused) ---
            if not paused:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE: return 'level_select'
                    
                    player.handle_key_down(event.key, maze.npcs)
                    
                    if (game_over or win) and event.key == pygame.K_RETURN:
                        return 'win' if win else 'lose'
                
                if event.type == pygame.KEYUP:
                    player.handle_key_up(event.key)

        # --- Updates (only if not paused) ---
        if not paused:
            player.update(dt, maze.npcs)
            for npc in maze.npcs:
                other_npcs = [other for other in maze.npcs if other != npc]
                npc.update(dt, player, other_npcs)

            maze.npcs = [npc for npc in maze.npcs if not (npc.is_dead and npc.death_timer > npc.config["death_duration"])]

            if not game_over and player.is_dead and player.death_timer > DEATH_SEQUENCE_DURATION:
                game_over = True
            if not win and not maze.npcs:
                win = True

        # --- Drawing & State-Based Sound ---
        screen.fill(FLOOR_BACKGROUND_COLOR)
        maze.draw(screen, player, maze.npcs)
        draw_ui(screen, player)
        screen.blit(stop_icon, stop_icon_rect)
        
        if game_over: 
            if lose_music and not lose_sound_played:
                lose_music.play()
                lose_sound_played = True
            screen.blit(game_over_text, game_over_rect)
        elif win: 
            if win_music and not win_sound_played:
                win_music.play()
                win_sound_played = True
            screen.blit(win_text, win_rect)
            
        if paused:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))

            pygame.draw.rect(screen, button_color, resume_rect, border_radius=10)
            pygame.draw.rect(screen, button_color, menu_rect, border_radius=10)
            screen.blit(resume_text, resume_text.get_rect(center=resume_rect.center))
            screen.blit(menu_text, menu_text.get_rect(center=menu_rect.center))

        yield None

def main():
    """Main function to run the game."""
    pygame.init()
    pygame.mixer.init() 
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("THE DUNGEON WARRIOR")

    # --- Centralized Sound Loading ---
    win_music = None
    lose_music = None
    click_sound = None
    music_on = True
    
    try:
        # Load background music to the dedicated music channel
        pygame.mixer.music.load('./assets/music.mp3')
        pygame.mixer.music.set_volume(0.5)
        
        # Load sound effects to be played on regular channels
        win_music = pygame.mixer.Sound('./assets/win.mp3')
        lose_music = pygame.mixer.Sound('./assets/lose.mp3')
        click_sound = pygame.mixer.Sound('./assets/click.mp3')

    except pygame.error as e:
        print(f"Warning: Could not load one or more sounds: {e}")
        music_on = False

    # --- Music Icon Setup ---
    music_icon_size = 50
    music_on_img = pygame.image.load('./assets/music.png').convert_alpha()
    music_off_img = pygame.image.load('./assets/music.png').convert_alpha()
    music_on_img = pygame.transform.scale(music_on_img, (music_icon_size, music_icon_size))
    music_off_img = pygame.transform.scale(music_off_img, (music_icon_size, music_icon_size))
    music_icon_rect = music_on_img.get_rect(topright=(SCREEN_WIDTH - 15, 15))

    # Initialize controllers and pages
    if music_on:
        pygame.mixer.music.play(-1) # Play background music on loop
    
    menu = Menu(screen)
    level_controller = LevelController()
    level_page = LevelPage(screen, level_controller)
    
    game_state = 'menu'
    active_level_number = None
    game_instance = None

    while True:
        events_to_process = []
        if game_instance is None:
            events_to_process = pygame.event.get()
        else:
            try:
                event = next(game_instance)
                if event:
                    events_to_process.append(event)
            except StopIteration as e:
                game_result = e.value
                # After a level ends, restart the background music for the menu/level select screen
                if music_on and not pygame.mixer.music.get_busy():
                    pygame.mixer.music.play(-1)
                
                if game_result == 'win':
                    level_controller.unlock_next_level(active_level_number)
                    game_state = 'level_select'
                elif game_result in ('lose', 'level_select'):
                    game_state = 'level_select'
                elif game_result == 'menu':
                    game_state = 'menu'
                elif game_result == 'exit':
                    break
                game_instance = None

        for event in events_to_process:
            if event.type == pygame.QUIT:
                level_controller._save_progress()
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if music_icon_rect.collidepoint(event.pos):
                    music_on = not music_on
                    # Use pause/unpause on the music channel, which doesn't affect sound effects
                    if music_on:
                        pygame.mixer.music.unpause()
                    else:
                        pygame.mixer.music.pause()

        # --- Game State Machine ---
        if game_instance is None:
            if game_state == 'menu':
                screen.fill(FLOOR_BACKGROUND_COLOR)
                menu_choice = menu.run(events_to_process)
                if menu_choice == 'start':
                    game_state = 'level_select'
                elif menu_choice == 'exit':
                    break
            
            elif game_state == 'level_select':
                screen.fill(FLOOR_BACKGROUND_COLOR)
                level_choice = level_page.run(events_to_process)
                if level_choice == 'menu':
                    game_state = 'menu'
                elif isinstance(level_choice, int):
                    active_level_number = level_choice
                    game_state = 'game'
                    # FIXED: Removed the line below that was stopping the music
                    # pygame.mixer.music.stop() 
                    game_instance = game_loop(screen, level_controller, active_level_number, win_music, lose_music, click_sound)
        
        # --- Final Drawing (Overlays) ---
        if music_on:
            screen.blit(music_on_img, music_icon_rect)
        else:
            screen.blit(music_off_img, music_icon_rect)

        pygame.display.flip()

    level_controller._save_progress()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()