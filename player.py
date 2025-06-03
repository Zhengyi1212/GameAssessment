import pygame

# Constants
GRID_SIZE = 80
STAGGER_HEIGHT_PER_ROW = int(GRID_SIZE * 0.8)
ORIG_PLAYER_SPRITE_WIDTH = 20
ORIG_PLAYER_SPRITE_HEIGHT = 26
PLAYER_SCALE_FACTOR = 5
TARGET_PLAYER_WIDTH = int(ORIG_PLAYER_SPRITE_WIDTH * PLAYER_SCALE_FACTOR)
TARGET_PLAYER_HEIGHT = int(ORIG_PLAYER_SPRITE_HEIGHT * PLAYER_SCALE_FACTOR)

ANIMATION_SPEED = 0.1  # Time between frames in seconds
# --- Adjusted for slower, more visible gradual movement ---
GRID_MOVE_DURATION = 0.3 # Duration for moving one grid cell in seconds (e.g., 0.3 or 0.4)

# Define the color to be made transparent (e.g., white)
# If your background is a different color, change this tuple.
COLOR_KEY_BACKGROUND = (255, 255, 255)

class Player:
    def __init__(self, initial_grid_x, initial_grid_y, maze):
        self.grid_x = initial_grid_x
        self.grid_y = initial_grid_y
        self.maze = maze

        self.idle_image_orig = None
        self.walk_frames_orig = []
        self.walk_up_frames_orig = []
        self.walk_down_frames_orig = []
        self.load_sprites()

        if self.idle_image_orig:
            self.current_image = self.idle_image_orig
        else:
            # Fallback if idle_image_orig is somehow None after load_sprites
            self.current_image = pygame.Surface((TARGET_PLAYER_WIDTH, TARGET_PLAYER_HEIGHT), pygame.SRCALPHA)
            self.current_image.fill((0,0,255,128)) # Semi-transparent blue
            print("CRITICAL WARNING: Player idle_image_orig is None after load_sprites. Using fallback for current_image.")

        self.facing_right = True
        self.facing_up = False
        self.direction = True # true for left and right false for up and down
        self.is_moving_animation = False
        self.is_grid_moving = False

        # For time-based interpolation
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

        print(f"DEBUG: Player Initialized: grid=({self.grid_x},{self.grid_y}), screen_pos=({self.current_screen_x:.1f},{self.current_screen_y:.1f})")

    def load_sprites(self):
        try:
            base_idle_image_loaded = pygame.image.load('./assets/Guali/static.png')
            # If static.png also might have a background, apply colorkey here too:
            # base_idle_image_loaded.set_colorkey(COLOR_KEY_BACKGROUND)
            base_idle_image = base_idle_image_loaded.convert_alpha()
            self.idle_image_orig = pygame.transform.scale(base_idle_image, (TARGET_PLAYER_WIDTH, TARGET_PLAYER_HEIGHT))

            # Load walk_sheet (left/right - assumed to be clean already)
            walk_sheet_loaded = pygame.image.load('./assets/Guali/walk.png')
            walk_sheet = walk_sheet_loaded.convert_alpha()

            # Load walkup_sheet and apply color key
            walkup_sheet_loaded = pygame.image.load('./assets/Guali/upwards.png')
            walkup_sheet_loaded.set_colorkey(COLOR_KEY_BACKGROUND) # Make white transparent
            walkup_sheet = walkup_sheet_loaded.convert_alpha()

            # Load walkdown_sheet and apply color key
            walkdown_sheet_loaded = pygame.image.load('./assets/Guali/downwards.png')
            walkdown_sheet_loaded.set_colorkey(COLOR_KEY_BACKGROUND) # Make white transparent
            walkdown_sheet = walkdown_sheet_loaded.convert_alpha()

            num_frames = 6 # Assuming all sprite sheets have 6 frames horizontally
            
            # Process walk_sheet (left/right)
            frame_width_orig = walk_sheet.get_width() // num_frames
            frame_height_orig = walk_sheet.get_height()
            temp_walk_frames = []
            for i in range(num_frames):
                frame = walk_sheet.subsurface(pygame.Rect(i * frame_width_orig, 0, frame_width_orig, frame_height_orig))
                temp_walk_frames.append(pygame.transform.scale(frame, (TARGET_PLAYER_WIDTH, TARGET_PLAYER_HEIGHT)))
            
            if temp_walk_frames:
                self.walk_frames_orig = temp_walk_frames
            # Fallbacks for walk_frames_orig (unchanged)

            # Process walkup_sheet
            up_frame_width_orig = walkup_sheet.get_width() // num_frames
            up_frame_height_orig = walkup_sheet.get_height()
            temp_up_frames = []
            for i in range(num_frames):
                up_frame = walkup_sheet.subsurface(pygame.Rect(i * up_frame_width_orig, 0, up_frame_width_orig, up_frame_height_orig))
                temp_up_frames.append(pygame.transform.scale(up_frame, (TARGET_PLAYER_WIDTH, TARGET_PLAYER_HEIGHT)))

            if temp_up_frames:
                self.walk_up_frames_orig = temp_up_frames
            # Fallbacks for walk_up_frames_orig (unchanged)

            # Process walkdown_sheet
            down_frame_width_orig = walkdown_sheet.get_width() // num_frames
            down_frame_height_orig = walkdown_sheet.get_height()
            temp_down_frames = []
            for i in range(num_frames):
                down_frame = walkdown_sheet.subsurface(pygame.Rect(i * down_frame_width_orig, 0, down_frame_width_orig, down_frame_height_orig))
                temp_down_frames.append(pygame.transform.scale(down_frame, (TARGET_PLAYER_WIDTH, TARGET_PLAYER_HEIGHT)))

            if temp_down_frames:
                self.walk_down_frames_orig = temp_down_frames
            # Fallbacks for walk_down_frames_orig (unchanged)

            # Ensure fallbacks if lists are empty (good practice, largely unchanged but check logic)
            if not self.walk_frames_orig and self.idle_image_orig: self.walk_frames_orig.append(self.idle_image_orig)
            if not self.walk_up_frames_orig and self.idle_image_orig: self.walk_up_frames_orig.append(self.idle_image_orig)
            if not self.walk_down_frames_orig and self.idle_image_orig: self.walk_down_frames_orig.append(self.idle_image_orig)


        except pygame.error as e:
            print(f"ERROR loading player sprites: {e}")
            # Ensure essential fallbacks (unchanged)
            if self.idle_image_orig is None:
                self.idle_image_orig = pygame.Surface((TARGET_PLAYER_WIDTH, TARGET_PLAYER_HEIGHT), pygame.SRCALPHA)
                self.idle_image_orig.fill((255,0,0,128)) # Semi-transparent red
            if not self.walk_frames_orig: self.walk_frames_orig.append(self.idle_image_orig)
            if not self.walk_up_frames_orig: self.walk_up_frames_orig.append(self.idle_image_orig)
            if not self.walk_down_frames_orig: self.walk_down_frames_orig.append(self.idle_image_orig)

        # Final safety checks (unchanged)
        if self.idle_image_orig is None:
            print("CRITICAL WARNING: self.idle_image_orig is None after load_sprites(). Creating emergency fallback.")
            self.idle_image_orig = pygame.Surface((TARGET_PLAYER_WIDTH, TARGET_PLAYER_HEIGHT), pygame.SRCALPHA)
            self.idle_image_orig.fill((255,0,0,128)) # Semi-transparent red
            if not self.current_image : self.current_image = self.idle_image_orig # Ensure current_image is also set

        if not self.walk_frames_orig:
            print("CRITICAL WARNING: self.walk_frames_orig is empty. Using idle_image_orig.")
            self.walk_frames_orig.append(self.idle_image_orig)
        if not self.walk_up_frames_orig:
            print("CRITICAL WARNING: self.walk_up_frames_orig is empty. Using idle_image_orig.")
            self.walk_up_frames_orig.append(self.idle_image_orig)
        if not self.walk_down_frames_orig:
            print("CRITICAL WARNING: self.walk_down_frames_orig is empty. Using idle_image_orig.")
            self.walk_down_frames_orig.append(self.idle_image_orig)


    def _calculate_target_screen_pos(self, grid_x, grid_y):
        # (Your existing _calculate_target_screen_pos code - unchanged)
        base_x = grid_x * GRID_SIZE
        base_y = grid_y * STAGGER_HEIGHT_PER_ROW
        screen_x = base_x + (GRID_SIZE - TARGET_PLAYER_WIDTH) / 2.0
        feet_anchor_y = base_y + int(GRID_SIZE * 1.15) # Adjust this for player foot position
        screen_y = feet_anchor_y - TARGET_PLAYER_HEIGHT
        return screen_x, screen_y

    def start_grid_move(self, dx, dy):
        # (Your existing start_grid_move code - unchanged)
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
            
            if dx > 0:  
                self.facing_right = True
                self.direction = True 
            elif dx < 0:  
                self.facing_right = False
                self.direction = True 
            
            if dy > 0:  # Moving Down
                self.facing_up = False # Character is not facing up
                self.direction = False 
            elif dy < 0: # Moving Up
                self.facing_up = True  # Character is facing up
                self.direction = False

            print(f"  DEBUG: Started move. From screen: ({self.move_start_screen_x:.1f}, {self.move_start_screen_y:.1f}) To screen: ({self.target_screen_x:.1f}, {self.target_screen_y:.1f})")
            return True
        else:
            print(f"  DEBUG: Move to ({next_grid_x},{next_grid_y}) is NOT WALKABLE (blocked).")  
            self.is_moving_animation = False 
            return False

    def update_animation(self, dt):
        # Default to idle if not moving, or if somehow animation frames are missing
        current_frames_list = None
        apply_flip = False

        if self.is_moving_animation:
            if self.direction: # Moving left or right
                current_frames_list = self.walk_frames_orig
                if not self.facing_right: # Moving left
                    apply_flip = True
            else: # Moving up or down
                if self.facing_up: # Moving up
                    current_frames_list = self.walk_up_frames_orig
                else: # Moving down
                    current_frames_list = self.walk_down_frames_orig
            
            if current_frames_list: # Ensure the list is not empty/None
                self.anim_timer += dt
                if self.anim_timer >= ANIMATION_SPEED:
                    self.anim_timer -= ANIMATION_SPEED
                    self.anim_frame_index = (self.anim_frame_index + 1) % len(current_frames_list)
                    
                    # Debug prints for specific directions
                    if self.direction and self.facing_right: print("Anim: Move right")
                    elif self.direction and not self.facing_right: print("Anim: Move left")
                    elif not self.direction and self.facing_up: print("Anim: Move up")
                    elif not self.direction and not self.facing_up: print("Anim: Move down")
                        
                    base_image = current_frames_list[self.anim_frame_index]
                    if apply_flip:
                        self.current_image = pygame.transform.flip(base_image, True, False)
                    else:
                        self.current_image = base_image
                # If anim_timer hasn't reached ANIMATION_SPEED, current_image remains from previous frame or initial state
                # Make sure current_image is set even if animation doesn't advance this tick but is_moving_animation is true
                elif self.current_image is self.idle_image_orig and current_frames_list: # e.g. first frame of movement
                     base_image = current_frames_list[self.anim_frame_index] # Show first frame of walk
                     if apply_flip:
                        self.current_image = pygame.transform.flip(base_image, True, False)
                     else:
                        self.current_image = base_image

            else: # Fallback if a frame list is missing (should not happen with good loading)
                self.current_image = self.idle_image_orig
                self.is_moving_animation = False # Stop animation if data is missing
        else:
            self.current_image = self.idle_image_orig
            self.anim_frame_index = 0
            self.anim_timer = 0
            
        # Ensure current_image is never None if idle_image_orig exists
        if self.current_image is None and self.idle_image_orig:
            self.current_image = self.idle_image_orig
            print("WARNING: self.current_image was None in update_animation, reset to idle.")


    def update(self, dt):
        # (Your existing update code for movement interpolation - unchanged)
        if self.is_grid_moving:
            self.move_timer += dt
            progress = self.move_timer / GRID_MOVE_DURATION

            if progress >= 1.0:
                progress = 1.0 
                self.is_grid_moving = False
                self.is_moving_animation = False 
                print(f"DEBUG: Reached target (timer). Snapped. is_grid_moving=False, is_moving_animation=False.")
            
            self.current_screen_x = self.move_start_screen_x + (self.target_screen_x - self.move_start_screen_x) * progress
            self.current_screen_y = self.move_start_screen_y + (self.target_screen_y - self.move_start_screen_y) * progress
            
            if not self.is_grid_moving: 
                self.current_screen_x = self.target_screen_x
                self.current_screen_y = self.target_screen_y

        self.update_animation(dt) # Call animation update regardless of grid movement completion

    def draw(self, surface, maze_offset_x, maze_offset_y):
        # (Your existing draw code - unchanged)
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