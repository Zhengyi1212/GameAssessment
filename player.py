# player.py
import pygame

# Constants
GRID_SIZE = 80
STAGGER_HEIGHT_PER_ROW = int(GRID_SIZE * 0.8)
ORIG_PLAYER_SPRITE_WIDTH = 20
ORIG_PLAYER_SPRITE_HEIGHT = 26
PLAYER_SCALE_FACTOR = 5
TARGET_PLAYER_WIDTH = int(ORIG_PLAYER_SPRITE_WIDTH * PLAYER_SCALE_FACTOR)
TARGET_PLAYER_HEIGHT = int(ORIG_PLAYER_SPRITE_HEIGHT * PLAYER_SCALE_FACTOR)

## up and down need a new size!!!!!
#TODO Fix the bug: foot in the floor
#TODO add 'space' for swallow

ANIMATION_SPEED = 0.1  # Time between frames in seconds
GRID_MOVE_DURATION = 0.3 # Duration for moving one grid cell in seconds (e.g., 0.3 or 0.4)

class Player:
    def __init__(self, initial_grid_x, initial_grid_y, maze):
        self.grid_x = initial_grid_x
        self.grid_y = initial_grid_y
        self.maze = maze

        self.current_move_dx = 0 # <--- left animation
        self.current_move_dy = 0 # <--- 
        
        self.idle_image_orig = None
        self.walk_frames_orig = []
        self.walk_up_frames_orig = []
        self.walk_down_frames_orig = []
        self.load_sprites()

        if self.idle_image_orig:
            self.current_image = self.idle_image_orig
        else:
            self.current_image = pygame.Surface((TARGET_PLAYER_WIDTH, TARGET_PLAYER_HEIGHT), pygame.SRCALPHA)
            self.current_image.fill((0,0,255,128))
            print("CRITICAL WARNING: Player idle_image_orig is None. Using fallback.")

        self.facing_right = True
        self.facing_up = False # True for up, False for down
        self.moving_horizontal = False # True for left/right, False for up/down
        self.is_moving_animation = False
        self.is_grid_moving = False

        self.move_start_screen_x = 0.0
        self.move_start_screen_y = 0.0
        self.target_screen_x = 0.0
        self.target_screen_y = 0.0
        self.current_screen_x = 0.0 # Actual blitting position
        self.current_screen_y = 0.0
        self.move_timer = 0.0

        self.anim_frame_index = 0
        self.anim_timer = 0

        # Initialize screen position
        initial_target_x, initial_target_y = self._calculate_target_screen_pos(self.grid_x, self.grid_y)
        self.current_screen_x = initial_target_x
        self.current_screen_y = initial_target_y
        self.target_screen_x = initial_target_x # Target is initially current
        self.target_screen_y = initial_target_y
        
        self.TARGET_PLAYER_WIDTH = TARGET_PLAYER_WIDTH
        self.TARGET_PLAYER_HEIGHT = TARGET_PLAYER_HEIGHT


        print(f"DEBUG: Player Initialized: grid=({self.grid_x},{self.grid_y}), screen_pos=({self.current_screen_x:.1f},{self.current_screen_y:.1f})")

    def load_sprites(self):
        try:
            base_idle_image = pygame.image.load('./assets/Guali/static.png').convert_alpha()
            self.idle_image_orig = pygame.transform.scale(base_idle_image, (TARGET_PLAYER_WIDTH, TARGET_PLAYER_HEIGHT))
            
            walk_sheet = pygame.image.load('./assets/Guali/walk.png').convert_alpha()
            walkup_sheet = pygame.image.load('./assets/Guali/upwards.png').convert_alpha()
            walkdown_sheet = pygame.image.load('./assets/Guali/downwards.png').convert_alpha()
            
            num_frames = 6
            num_up_frames = 7 
            
            frame_width_orig = walk_sheet.get_width() // num_frames
            frame_height_orig = walk_sheet.get_height()
            
            up_frame_width_orig = walkup_sheet.get_width() // num_up_frames
            up_frame_height_orig = walkup_sheet.get_height()
            down_frame_width_orig = walkdown_sheet.get_width() // num_frames
            down_frame_height_orig = walkdown_sheet.get_height()
            
            temp_walk_frames = []
            for i in range(num_frames):
                frame = walk_sheet.subsurface(pygame.Rect(i * frame_width_orig, 0, frame_width_orig, frame_height_orig))
                temp_walk_frames.append(pygame.transform.scale(frame, (TARGET_PLAYER_WIDTH, TARGET_PLAYER_HEIGHT)))
            
            if temp_walk_frames:
                self.walk_frames_orig = temp_walk_frames
            elif self.idle_image_orig:
                 self.walk_frames_orig.append(self.idle_image_orig)
            else:
                placeholder_walk = pygame.Surface((TARGET_PLAYER_WIDTH, TARGET_PLAYER_HEIGHT), pygame.SRCALPHA)
                placeholder_walk.fill((0,255,0,128))
                self.walk_frames_orig.append(placeholder_walk)
            
            temp_up_frames = []
            for i in range(num_up_frames): 
                up_frame = walkup_sheet.subsurface(pygame.Rect(i * up_frame_width_orig, 0, up_frame_width_orig, up_frame_height_orig))
                temp_up_frames.append(pygame.transform.scale(up_frame, (TARGET_PLAYER_WIDTH, TARGET_PLAYER_HEIGHT*0.8)))
            
            if temp_up_frames:
                self.walk_up_frames_orig = temp_up_frames 
            elif self.idle_image_orig:
                 self.walk_up_frames_orig.append(self.idle_image_orig)
            else:
                placeholder_walk = pygame.Surface((TARGET_PLAYER_WIDTH, TARGET_PLAYER_HEIGHT), pygame.SRCALPHA)
                placeholder_walk.fill((0,255,0,128))
                self.walk_up_frames_orig.append(placeholder_walk)
            
            temp_down_frames = []
            for i in range(num_frames):
                down_frame = walkdown_sheet.subsurface(pygame.Rect(i * down_frame_width_orig, 0, down_frame_width_orig, down_frame_height_orig))
                temp_down_frames.append(pygame.transform.scale(down_frame, (TARGET_PLAYER_WIDTH, TARGET_PLAYER_HEIGHT*0.8)))
            
            if temp_down_frames:
                self.walk_down_frames_orig = temp_down_frames
            elif self.idle_image_orig:
                 self.walk_down_frames_orig.append(self.idle_image_orig)
            else:
                placeholder_walk = pygame.Surface((TARGET_PLAYER_WIDTH, TARGET_PLAYER_HEIGHT), pygame.SRCALPHA)
                placeholder_walk.fill((0,255,0,128))
                self.walk_down_frames_orig.append(placeholder_walk)

        except pygame.error as e:
            print(f"ERROR loading player sprites: {e}")
            if self.idle_image_orig is None:
                self.idle_image_orig = pygame.Surface((TARGET_PLAYER_WIDTH, TARGET_PLAYER_HEIGHT), pygame.SRCALPHA)
                self.idle_image_orig.fill((255,0,0,128))
            if not self.walk_frames_orig:
                self.walk_frames_orig.append(self.idle_image_orig)
            if not self.walk_up_frames_orig:
                self.walk_up_frames_orig.append(self.idle_image_orig)
            if not self.walk_down_frames_orig:
                self.walk_down_frames_orig.append(self.idle_image_orig)
                
        if self.idle_image_orig is None:
            print("CRITICAL WARNING: self.idle_image_orig is None after load_sprites(). Creating emergency fallback.")
            self.idle_image_orig = pygame.Surface((TARGET_PLAYER_WIDTH, TARGET_PLAYER_HEIGHT), pygame.SRCALPHA)
            self.idle_image_orig.fill((255,0,0,128))
        if not self.walk_frames_orig:
            print("CRITICAL WARNING: self.walk_frames_orig is empty after load_sprites(). Using idle_image_orig.")
            self.walk_frames_orig.append(self.idle_image_orig)


    def _calculate_target_screen_pos(self, grid_x, grid_y):
        # Calculate the base screen coordinates for the current grid cell
        base_x = grid_x * GRID_SIZE
        base_y = grid_y * STAGGER_HEIGHT_PER_ROW
        
        # Calculate the horizontal center of the grid cell
        screen_x = base_x + (GRID_SIZE - TARGET_PLAYER_WIDTH) / 2.0
        
        # --- MODIFICATION START ---
        # The 'visual floor' of a cell (where the player stands) should align with the bottom of the cube.
        # From map_generator, the sorting key `cube_bottom_y_for_sort` is `screen_y + GRID_SIZE * 1.2`.
        # This `screen_y` corresponds to `base_y` here.
        # So, the effective 'floor' for the player (bottom of their sprite) should be at `base_y + GRID_SIZE * 1.2`.
        player_feet_y_on_tile = base_y + int(GRID_SIZE*1.2 ) 
        
        # The blit Y coordinate is the top-left of the player sprite.
        # So, subtract the player's height from the desired feet position.
        screen_y = player_feet_y_on_tile - TARGET_PLAYER_HEIGHT
        # --- MODIFICATION END ---
        
        return screen_x, screen_y

   # player.py
    def start_grid_move(self, dx, dy):
        if self.is_grid_moving:
            return False

        next_grid_x = self.grid_x + dx
        next_grid_y = self.grid_y + dy

        print(f"DEBUG: Attempting move from ({self.grid_x},{self.grid_y}) with (dx:{dx}, dy:{dy}) to ({next_grid_x},{next_grid_y})")

        if self.maze.is_walkable(next_grid_x, next_grid_y):
            print(f"  DEBUG: Move to ({next_grid_x},{next_grid_y}) is WALKABLE.")
            self.grid_x = next_grid_x
            self.grid_y = next_grid_y

            self.move_start_screen_x = self.current_screen_x
            self.move_start_screen_y = self.current_screen_y
            self.target_screen_x, self.target_screen_y = self._calculate_target_screen_pos(self.grid_x, self.grid_y)

            self.move_timer = 0.0
            self.is_grid_moving = True
            self.is_moving_animation = True
            self.anim_frame_index = 0
            self.anim_timer = 0

            self.current_move_dx = dx # <--- 新增
            self.current_move_dy = dy # <--- 新增

            if dx != 0: # Horizontal movement
                self.moving_horizontal = True
                self.facing_right = dx > 0
            elif dy != 0: # Vertical movement
                self.moving_horizontal = False
                self.facing_up = dy < 0 

            print(f"  DEBUG: Started move. From screen: ({self.move_start_screen_x:.1f}, {self.move_start_screen_y:.1f}) To screen: ({self.target_screen_x:.1f}, {self.target_screen_y:.1f})")
            return True
        else:
            print(f"  DEBUG: Move to ({next_grid_x},{next_grid_x}) is NOT WALKABLE (blocked).")
            self.is_moving_animation = False
            # Ensure current_move_dx/dy are reset if move fails immediately (optional, but good practice)
            self.current_move_dx = 0 # <--- 新增 (可选)
            self.current_move_dy = 0 # <--- 新增 (可选)
            return False

    def update_animation(self, dt):
        if self.is_moving_animation:
            self.anim_timer += dt
            if self.anim_timer >= ANIMATION_SPEED:
                self.anim_timer -= ANIMATION_SPEED
                
                if self.moving_horizontal:
                    self.anim_frame_index = (self.anim_frame_index + 1) % len(self.walk_frames_orig)
                    current_base_image = self.walk_frames_orig[self.anim_frame_index]
                    if not self.facing_right:
                        self.current_image = pygame.transform.flip(current_base_image, True, False)
                    else:
                        self.current_image = current_base_image
                elif self.facing_up:
                    # Ensure walk_up_frames_orig is not empty before modulo
                    if self.walk_up_frames_orig:
                        self.anim_frame_index = (self.anim_frame_index + 1) % len(self.walk_up_frames_orig)
                        self.current_image = self.walk_up_frames_orig[self.anim_frame_index]
                    else:
                        self.current_image = self.idle_image_orig # Fallback if no specific up frames
                else: # Moving down
                    # Ensure walk_down_frames_orig is not empty before modulo
                    if self.walk_down_frames_orig:
                        self.anim_frame_index = (self.anim_frame_index + 1) % len(self.walk_down_frames_orig)
                        self.current_image = self.walk_down_frames_orig[self.anim_frame_index]
                    else:
                        self.current_image = self.idle_image_orig # Fallback if no specific down frames
        else: # Not moving, reset animation state
            self.anim_frame_index = 0
            self.anim_timer = 0
            if self.moving_horizontal:
                if not self.facing_right:
                    self.current_image = pygame.transform.flip(self.idle_image_orig, True, False)
                else:
                    self.current_image = self.idle_image_orig
            elif self.facing_up:
                if self.walk_up_frames_orig:
                    self.current_image = self.walk_up_frames_orig[0]
                else:
                    self.current_image = self.idle_image_orig 
            else: 
                if self.walk_down_frames_orig:
                    self.current_image = self.walk_down_frames_orig[0]
                else:
                    self.current_image = self.idle_image_orig 


    # player.py
    def update(self, dt):
        if self.is_grid_moving:
            self.move_timer += dt
            progress = self.move_timer / GRID_MOVE_DURATION

            if progress >= 1.0:
                progress = 1.0
                self.is_grid_moving = False
                self.is_moving_animation = False
                self.current_move_dx = 0 # <--- 新增
                self.current_move_dy = 0 # <--- 新增
                print(f"DEBUG: Reached target (timer). Snapped. is_grid_moving=False, is_moving_animation=False.")

            self.current_screen_x = self.move_start_screen_x + (self.target_screen_x - self.move_start_screen_x) * progress
            self.current_screen_y = self.move_start_screen_y + (self.target_screen_y - self.move_start_screen_y) * progress

            if not self.is_grid_moving:
                self.current_screen_x = self.target_screen_x
                self.current_screen_y = self.target_screen_y

        self.update_animation(dt)

    def draw(self, surface, maze_offset_x, maze_offset_y):
        if self.current_image:
            draw_x = self.current_screen_x + maze_offset_x
            draw_y = self.current_screen_y + maze_offset_y
            surface.blit(self.current_image, (draw_x, draw_y))
        else:
            print("CRITICAL WARNING: self.current_image is None in draw(). Drawing red placeholder.")
            fallback_surf = pygame.Surface((TARGET_PLAYER_WIDTH, TARGET_PLAYER_HEIGHT))
            fallback_surf.fill((255,0,0))
            draw_x = self.current_screen_x + maze_offset_x
            draw_y = self.current_screen_y + maze_offset_y
            surface.blit(fallback_surf, (draw_x, draw_y))