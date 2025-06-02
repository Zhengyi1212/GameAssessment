# player.py
import pygame

# Constants from your game (ensure GRID_SIZE is consistent)
GRID_SIZE = 80  # From cube.py
STAGGER_HEIGHT_PER_ROW = int(GRID_SIZE * 0.8) # Visual offset per row in Y

PLAYER_SPRITE_WIDTH = 20  # From inspecting static.png (20x26)
PLAYER_SPRITE_HEIGHT = 26 # From inspecting static.png (20x26)

# Animation settings
ANIMATION_SPEED = 0.1  # Time between frames in seconds
GRID_MOVE_DURATION = 0.15 # Duration for moving one grid cell in seconds

class Player:
    def __init__(self, initial_grid_x, initial_grid_y, maze):
        self.grid_x = initial_grid_x
        self.grid_y = initial_grid_y
        self.maze = maze # For collision detection and offsets

        self.idle_image_orig = None
        self.walk_frames_orig = []
        self.load_sprites()

        self.current_image = self.idle_image_orig
        self.facing_right = True

        self.is_moving_animation = False # For visual animation cycling
        self.is_grid_moving = False      # True if currently executing a single grid move
        
        self.current_screen_x = 0
        self.current_screen_y = 0
        self.target_screen_x = 0
        self.target_screen_y = 0
        
        self.anim_frame_index = 0
        self.anim_timer = 0

        # Set initial screen position
        self._update_screen_pos_from_grid(is_initial_setup=True)

    def load_sprites(self):
        try:
            # Load idle sprite
            self.idle_image_orig = pygame.image.load('./assets/Character/static.png').convert_alpha()
            self.idle_image_orig = pygame.transform.scale(self.idle_image_orig, (PLAYER_SPRITE_WIDTH, PLAYER_SPRITE_HEIGHT))

            # Load walking spritesheet
            walk_sheet = pygame.image.load('./assets/Character/walk.png').convert_alpha()
            num_frames = 6
            frame_width = walk_sheet.get_width() // num_frames
            frame_height = walk_sheet.get_height()

            for i in range(num_frames):
                frame = walk_sheet.subsurface(pygame.Rect(i * frame_width, 0, frame_width, frame_height))
                self.walk_frames_orig.append(pygame.transform.scale(frame, (PLAYER_SPRITE_WIDTH, PLAYER_SPRITE_HEIGHT)))
            
            if not self.walk_frames_orig: # Fallback if loading fails
                self.walk_frames_orig.append(self.idle_image_orig)
        except pygame.error as e:
            print(f"Error loading player sprites: {e}")
            # Create fallback transparent surfaces
            self.idle_image_orig = pygame.Surface((PLAYER_SPRITE_WIDTH, PLAYER_SPRITE_HEIGHT), pygame.SRCALPHA)
            self.walk_frames_orig = [pygame.Surface((PLAYER_SPRITE_WIDTH, PLAYER_SPRITE_HEIGHT), pygame.SRCALPHA)]


    def _calculate_target_screen_pos(self, grid_x, grid_y):
        """Calculates the target screen coordinates (top-left of sprite) for a given grid cell."""
        # This positions the player sprite centered horizontally in the grid cell,
        # and aligns its feet near the bottom of the "top face" of a standard cube in that cell.
        base_x = grid_x * GRID_SIZE
        base_y = grid_y * STAGGER_HEIGHT_PER_ROW 
        
        screen_x = base_x + (GRID_SIZE - PLAYER_SPRITE_WIDTH) / 2
        # Align feet roughly with the "effective floor" of the cell
        # A standard cube's top face bottom is at base_y + GRID_SIZE*0.8
        # A floor cube's top surface starts at base_y + GRID_SIZE*0.4 and ends at base_y + GRID_SIZE*1.2
        # Let's target feet to be on the upper part of the floor face:
        effective_floor_y = base_y + int(GRID_SIZE * 0.5) # Mid-point of top face of a standard cube
        screen_y = effective_floor_y + int(GRID_SIZE * 0.4) - PLAYER_SPRITE_HEIGHT # Adjust so feet are on the visible floor tile
        
        return screen_x, screen_y

    def _update_screen_pos_from_grid(self, is_initial_setup=False):
        """Sets current and target screen positions based on current grid position."""
        self.target_screen_x, self.target_screen_y = self._calculate_target_screen_pos(self.grid_x, self.grid_y)
        if is_initial_setup:
            self.current_screen_x = self.target_screen_x
            self.current_screen_y = self.target_screen_y

    def start_grid_move(self, dx, dy):
        if self.is_grid_moving:
            return False # Already moving

        next_grid_x = self.grid_x + dx
        next_grid_y = self.grid_y + dy

        if self.maze.is_walkable(next_grid_x, next_grid_y):
            self.grid_x = next_grid_x # Update logical grid position immediately
            self.grid_y = next_grid_y
            
            # Old screen position is the current one before this move
            # New target screen position is calculated for the new grid_x, grid_y
            self.target_screen_x, self.target_screen_y = self._calculate_target_screen_pos(self.grid_x, self.grid_y)

            self.is_grid_moving = True
            self.is_moving_animation = True # Start walking animation
            self.anim_frame_index = 0 # Reset animation
            self.anim_timer = 0

            if dx > 0:
                self.facing_right = True
            elif dx < 0:
                self.facing_right = False
            # No change in facing for dy only moves, or keep current.
            
            return True
        return False

    def update_animation(self, dt):
        if self.is_moving_animation:
            self.anim_timer += dt
            if self.anim_timer >= ANIMATION_SPEED:
                self.anim_timer -= ANIMATION_SPEED
                self.anim_frame_index = (self.anim_frame_index + 1) % len(self.walk_frames_orig)
                current_base_image = self.walk_frames_orig[self.anim_frame_index]
        else:
            self.anim_frame_index = 0
            current_base_image = self.idle_image_orig
            self.anim_timer = 0 # Reset timer when idle

        if self.facing_right:
            self.current_image = current_base_image
        else:
            self.current_image = pygame.transform.flip(current_base_image, True, False)


    def update(self, dt):
        if self.is_grid_moving:
            # Interpolate position
            move_step_x = (self.target_screen_x - self.current_screen_x) / GRID_MOVE_DURATION * dt
            move_step_y = (self.target_screen_y - self.current_screen_y) / GRID_MOVE_DURATION * dt

            self.current_screen_x += move_step_x
            self.current_screen_y += move_step_y

            # Check if target reached (with a small tolerance)
            if abs(self.target_screen_x - self.current_screen_x) < abs(move_step_x) * 0.5 + 1 and \
               abs(self.target_screen_y - self.current_screen_y) < abs(move_step_y) * 0.5 + 1:
                self.current_screen_x = self.target_screen_x
                self.current_screen_y = self.target_screen_y
                self.is_grid_moving = False
                # self.is_moving_animation = False # Will be set by input handler if no keys are pressed
        
        # If not grid moving and not told to animate by input, become idle
        # This part will be managed by the main game loop checking key presses

        self.update_animation(dt)


    def draw(self, surface, maze_offset_x, maze_offset_y):
        if self.current_image:
            # The current_screen_x/y are relative to the maze's (0,0) visual point
            draw_x = self.current_screen_x + maze_offset_x
            draw_y = self.current_screen_y + maze_offset_y
            surface.blit(self.current_image, (draw_x, draw_y))