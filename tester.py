import pygame
import sys

# --- Configuration ---
# Change these values to inspect different NPCs and animations
NPC_TO_DEBUG = "demon"  # e.g., "orc" or "demon"
ANIMATION_TO_DEBUG = "fly" # e.g., "walk_left", "walk_right", "fly"


# --- Data from your game ---
# Copied directly from your npc.py for accuracy
NPC_CONFIGS = {
    "orc": {
        "sprite_sheet_path": "./assets/NPC/Bird/Death.png",
        "orig_frame_width": 240,
        "orig_frame_height": 240,
        "scale_factor": 2,
        "animations": {
            "walk_down": (0,6), # row_index, num_frames
            "walk_up": (1, 6),
            "walk_left": (2, 6),
            "walk_right": (3, 6)
        },
    },
    "demon": {
        "sprite_sheet_path": "./assets/NPC/Bird/Death.png",
        "orig_frame_width": 160,
        "orig_frame_height": 140,
        "scale_factor": 1.5,
        "animations": {"fly": (0, 8)}, # Assumes a single row for flying
    }
}

# --- Debugger Setup ---
pygame.init()

# Window and Colors
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 600
WHITE = (255, 255, 255)
BLACK = (30, 30, 30)
RED = (255, 0, 0)
FONT_COLOR = (240, 240, 240)
BACKGROUND_COLOR = (40, 50, 60)

# Create the display
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Sprite Sheet Frame Debugger")
font = pygame.font.SysFont("consolas", 20)

# --- Main Script ---
def main():
    """Main function to load assets and run the debugger loop."""
    try:
        config = NPC_CONFIGS[NPC_TO_DEBUG]
        animation_data = config["animations"][ANIMATION_TO_DEBUG]
    except KeyError:
        print(f"--- ERROR ---")
        print(f"Could not find NPC '{NPC_TO_DEBUG}' or Animation '{ANIMATION_TO_DEBUG}'.")
        print(f"Please check your spelling in the script and in the NPC_CONFIGS dictionary.")
        return

    # Load the sprite sheet
    try:
        sprite_sheet = pygame.image.load(config["sprite_sheet_path"]).convert_alpha()
    except pygame.error as e:
        print(f"--- ERROR ---")
        print(f"Could not load image file: {config['sprite_sheet_path']}")
        print(f"Pygame Error: {e}")
        return

    # Get animation parameters from config
    orig_w = config["orig_frame_width"]
    orig_h = config["orig_frame_height"]
    row_idx, num_frames = animation_data
    scale = 3  # Use a fixed, large scale for better visibility

    current_frame_idx = 0
    running = True
    while running:
        # --- Event Handling ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                if event.key == pygame.K_RIGHT:
                    current_frame_idx = (current_frame_idx + 1) % num_frames
                if event.key == pygame.K_LEFT:
                    current_frame_idx = (current_frame_idx - 1 + num_frames) % num_frames

        # --- Drawing Logic ---
        screen.fill(BACKGROUND_COLOR)

        # 1. Draw the full sprite sheet for context
        sheet_pos = (50, 50)
        screen.blit(sprite_sheet, sheet_pos)
        
        # 2. Calculate the rectangle for the current frame
        row_start_y = row_idx * orig_h
        frame_x = current_frame_idx * orig_w
        frame_rect = pygame.Rect(frame_x, row_start_y, orig_w, orig_h)
        
        # 3. Draw a highlight box on the sprite sheet
        highlight_pos_on_sheet = (sheet_pos[0] + frame_rect.x, sheet_pos[1] + frame_rect.y)
        pygame.draw.rect(screen, RED, (*highlight_pos_on_sheet, *frame_rect.size), 3)

        # 4. Extract and display the single frame
        extracted_frame_surface = None
        error_message = ""
        try:
             # Check bounds before trying to get subsurface
            if (frame_rect.x + frame_rect.width > sprite_sheet.get_width() or
                frame_rect.y + frame_rect.height > sprite_sheet.get_height()):
                raise pygame.error("subsurface rectangle outside surface area")

            extracted_frame_surface = sprite_sheet.subsurface(frame_rect)
            scaled_frame = pygame.transform.scale(
                extracted_frame_surface,
                (int(orig_w * scale), int(orig_h * scale))
            )
            # Center the scaled frame vertically
            frame_display_y = (WINDOW_HEIGHT - scaled_frame.get_height()) // 2
            screen.blit(scaled_frame, (sprite_sheet.get_width() + 150, frame_display_y))

        except pygame.error as e:
            error_message = f"ERROR: {e}"

        # 5. Draw debug text
        info_y = WINDOW_HEIGHT - 120
        def draw_text(text, x, y, color=FONT_COLOR):
            img = font.render(text, True, color)
            screen.blit(img, (x, y))

        title = f"Debugging NPC: '{NPC_TO_DEBUG}' | Animation: '{ANIMATION_TO_DEBUG}'"
        draw_text(title, 50, info_y - 30)
        
        draw_text(f"Sprite Sheet: '{config['sprite_sheet_path']}' ({sprite_sheet.get_width()}x{sprite_sheet.get_height()} px)", 50, info_y)
        draw_text(f"Config Frame Size (w x h): {orig_w} x {orig_h}", 50, info_y + 25)
        draw_text(f"Current Frame: {current_frame_idx + 1} / {num_frames}", 50, info_y + 50)
        draw_text(f"Slicing at Rect(x={frame_rect.x}, y={frame_rect.y}, w={frame_rect.w}, h={frame_rect.h})", 50, info_y + 75)

        if error_message:
            draw_text(error_message, 50, info_y + 100, RED)

        # Update the display
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == '__main__':
    main()