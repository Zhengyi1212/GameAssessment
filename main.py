# main.py
import pygame
import sys
from menu import Menu
from level_page import LevelPage
from level_controller import LevelController
from cube import GRID_SIZE
from player import Player
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

def game_loop(screen, level_controller, level_number):
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
    stop_icon_rect = stop_icon.get_rect(topright=(SCREEN_WIDTH - 70, 18)) # Next to music icon

    
    pause_font = pygame.font.SysFont("arial", 50, bold=True)
    button_color = (60, 95, 110)
    text_color = (255, 255, 255)
    
    resume_text = pause_font.render("Keep Playing", True, text_color)
    menu_text = pause_font.render("Back to Menu", True, text_color)
    
    resume_rect = pygame.Rect(0, 0, 320, 70)
    menu_rect = pygame.Rect(0, 0, 320, 70)
    resume_rect.center = (SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 50)
    menu_rect.center = (SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 50)

    # --- Game State ---
    running = True
    paused = False
    game_over = False
    win = False

    game_over_font = pygame.font.SysFont("arial", 80, bold=True)
    game_over_text = game_over_font.render("GAME OVER", True, (255, 0, 0))
    game_over_rect = game_over_text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2))

    win_font = pygame.font.SysFont("arial", 80, bold=True)
    win_text = win_font.render("YOU WIN!\nPlease press enter to continue!", True, (0, 255, 0))
   
    win_rect = win_text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2))


    while running:
        # If the game is paused, dt is 0, so nothing moves.
        dt = clock.tick(60) / 1000.0 if not paused else 0

        # --- Event Handling ---
        for event in pygame.event.get():
            yield event # Yield event to main loop for global handling (music)

            if event.type == pygame.QUIT: return 'exit'
            
            # --- Pause Logic ---
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if not paused and stop_icon_rect.collidepoint(event.pos):
                    paused = True
                elif paused:
                    if resume_rect.collidepoint(event.pos):
                        paused = False
                    if menu_rect.collidepoint(event.pos):
                        return 'menu' # Return to main menu

            # --- Gameplay Input (only if not paused) ---
            if not paused:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE: return 'level_select'
                    if event.key == pygame.K_UP: player.handle_key_down('up')
                    elif event.key == pygame.K_DOWN: player.handle_key_down('down')
                    elif event.key == pygame.K_LEFT: player.handle_key_down('left')
                    elif event.key == pygame.K_RIGHT: player.handle_key_down('right')
                    elif event.key == pygame.K_SPACE: player.start_attack()
                    
                    if (game_over or win) and event.key == pygame.K_RETURN:
                        return 'win' if win else 'lose'

                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_UP: player.handle_key_up('up')
                    elif event.key == pygame.K_DOWN: player.handle_key_up('down')
                    elif event.key == pygame.K_LEFT: player.handle_key_up('left')
                    elif event.key == pygame.K_RIGHT: player.handle_key_up('right')


        # --- Updates (only if not paused) ---
        if not paused:
            player.update(dt, maze.npcs)
            for npc in maze.npcs:
                # A bit of optimization: pass a list of other NPCs
                other_npcs = [other for other in maze.npcs if other != npc]
                npc.update(dt, player, other_npcs)

            maze.npcs = [npc for npc in maze.npcs if not (npc.is_dead and npc.death_timer > npc.config["death_duration"])]

            if player.health <= 0: game_over = True
            if not maze.npcs: win = True

        # --- Drawing ---
        screen.fill(FLOOR_BACKGROUND_COLOR)
        maze.draw(screen, player, maze.npcs)
        draw_ui(screen, player)
        screen.blit(stop_icon, stop_icon_rect) # Always draw stop icon

        if game_over: screen.blit(game_over_text, game_over_rect)
        elif win: screen.blit(win_text, win_rect)

        if paused:
            # Draw overlay and pause menu
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))

            pygame.draw.rect(screen, button_color, resume_rect, border_radius=10)
            pygame.draw.rect(screen, button_color, menu_rect, border_radius=10)
            screen.blit(resume_text, resume_text.get_rect(center=resume_rect.center))
            screen.blit(menu_text, menu_text.get_rect(center=menu_rect.center))

        yield None # Yield for main loop to draw global overlays and flip

def main():
    """Main function to run the game."""
    pygame.init()
    pygame.mixer.init() 
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("A Man With a Sword")

    # --- Music Setup ---
    try:
        pygame.mixer.music.load('./assets/music.mp3')
        pygame.mixer.music.play(-1)
        music_on = True
    except pygame.error as e:
        print(f"Could not load or play music: {e}")
        music_on = False

    # --- Music Icon Setup ---
    music_icon_size = 50
    music_on_img = pygame.image.load('./assets/music.png').convert_alpha()
    music_off_img = pygame.image.load('./assets/music.png').convert_alpha()
    music_on_img = pygame.transform.scale(music_on_img, (music_icon_size, music_icon_size))
    music_off_img = pygame.transform.scale(music_off_img, (music_icon_size, music_icon_size))
    music_icon_rect = music_on_img.get_rect(topright=(SCREEN_WIDTH - 15, 15))


    # Initialize controllers and pages
    menu = Menu(screen)
    level_controller = LevelController()
    level_page = LevelPage(screen, level_controller)
    
    game_state = 'menu'
    active_level_number = None
    game_instance = None

    while True:
        # --- Event Handling ---
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
                    game_instance = game_loop(screen, level_controller, active_level_number)
        
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
