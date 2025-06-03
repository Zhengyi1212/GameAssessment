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

ANIMATION_SPEED = 0.1  # Time between frames in seconds
# --- Adjusted for slower, more visible gradual movement ---
GRID_MOVE_DURATION = 0.3 # Duration for moving one grid cell in seconds (e.g., 0.3 or 0.4)

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
            self.current_image = pygame.Surface((TARGET_PLAYER_WIDTH, TARGET_PLAYER_HEIGHT), pygame.SRCALPHA)
            self.current_image.fill((0,0,255,128))
            print("CRITICAL WARNING: Player idle_image_orig is None. Using fallback.")

        self.facing_right = True
        self.facing_up = False
        self.direction = True # true for left and right false for up and 
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
            base_idle_image = pygame.image.load('./assets/Guali/static.png').convert_alpha()
            self.idle_image_orig = pygame.transform.scale(base_idle_image, (TARGET_PLAYER_WIDTH, TARGET_PLAYER_HEIGHT))
            #
            walk_sheet = pygame.image.load('./assets/Guali/walk.png').convert_alpha()
            walkup_sheet = pygame.image.load('./assets/Guali/upwards.png').convert_alpha()
            walkdown_sheet = pygame.image.load('./assets/Guali/downwards.png').convert_alpha()
            #
            num_frames = 6
            num_frames2 = 7
            frame_width_orig = walk_sheet.get_width() // num_frames
            frame_height_orig = walk_sheet.get_height()
            
            up_frame_width_orig = walkup_sheet.get_width() // num_frames2
            up_frame_height_orig = walkup_sheet.get_height()
            down_frame_width_orig = walkdown_sheet.get_width() // num_frames
            down_frame_height_orig = walkdown_sheet.get_height()
            
            #load temp frame for walking left and right
            temp_walk_frames = []
            for i in range(num_frames):
                frame = walk_sheet.subsurface(pygame.Rect(i * frame_width_orig, 0, frame_width_orig, frame_height_orig))
                temp_walk_frames.append(pygame.transform.scale(frame, (TARGET_PLAYER_WIDTH, TARGET_PLAYER_HEIGHT)))
            
            if temp_walk_frames:
                self.walk_frames_orig = temp_walk_frames
            elif self.idle_image_orig: # Fallback if walk frames fail but idle is ok
                 self.walk_frames_orig.append(self.idle_image_orig)
            else: # Absolute fallback for walk frames
                placeholder_walk = pygame.Surface((TARGET_PLAYER_WIDTH, TARGET_PLAYER_HEIGHT), pygame.SRCALPHA)
                placeholder_walk.fill((0,255,0,128))
                self.walk_frames_orig.append(placeholder_walk)
            
            ####### 
            temp_up_frames = []
            for i in range(num_frames):
                up_frame = walkup_sheet.subsurface(pygame.Rect(i * up_frame_width_orig, 0, up_frame_width_orig, up_frame_height_orig))
                temp_up_frames.append(pygame.transform.scale(up_frame, (TARGET_PLAYER_WIDTH, TARGET_PLAYER_HEIGHT)))
            
            if temp_up_frames:
                self.walk_up_frames_orig  = [item for i, item in enumerate(temp_up_frames) if i != 0]
            elif self.idle_image_orig: # Fallback if walk frames fail but idle is ok
                 self.walk_up_frames_orig .append(self.idle_image_orig)
            else: # Absolute fallback for walk frames
                placeholder_walk = pygame.Surface((TARGET_PLAYER_WIDTH, TARGET_PLAYER_HEIGHT), pygame.SRCALPHA)
                placeholder_walk.fill((0,255,0,128))
                self.walk_up_frames_orig .append(placeholder_walk)
            
            
            
            ##walk_down_frames_orig 
            temp_down_frames = []
            for i in range(num_frames):
                down_frame = walkdown_sheet.subsurface(pygame.Rect(i * down_frame_width_orig, 0, down_frame_width_orig, down_frame_height_orig))
                temp_down_frames.append(pygame.transform.scale(down_frame, (TARGET_PLAYER_WIDTH, TARGET_PLAYER_HEIGHT)))
            
            if temp_down_frames:
                self.walk_down_frames_orig  = temp_down_frames
            elif self.idle_image_orig: # Fallback if walk frames fail but idle is ok
                 self.walk_down_frames_orig .append(self.idle_image_orig)
            else: # Absolute fallback for walk frames
                placeholder_walk = pygame.Surface((TARGET_PLAYER_WIDTH, TARGET_PLAYER_HEIGHT), pygame.SRCALPHA)
                placeholder_walk.fill((0,255,0,128))
                self.walk_down_frames_orig .append(placeholder_walk)




        except pygame.error as e:
            print(f"ERROR loading player sprites: {e}")
            if self.idle_image_orig is None:
                self.idle_image_orig = pygame.Surface((TARGET_PLAYER_WIDTH, TARGET_PLAYER_HEIGHT), pygame.SRCALPHA)
                self.idle_image_orig.fill((255,0,0,128))
            if not self.walk_frames_orig:
                self.walk_frames_orig.append(self.idle_image_orig) # Use idle as fallback
            if not self.walk_up_frames_orig:
                self.walk_up_frames_orig.append(self.idle_image_orig) # Use idle as fallback
                
            if not self.walk_down_frames_orig:
                self.walk_down_frames_orig.append(self.idle_image_orig) # Use idle as fallback
                
        ## no need
        if self.idle_image_orig is None: # Should be caught by above, but final safety
            print("CRITICAL WARNING: self.idle_image_orig is None after load_sprites(). Creating emergency fallback.")
            self.idle_image_orig = pygame.Surface((TARGET_PLAYER_WIDTH, TARGET_PLAYER_HEIGHT), pygame.SRCALPHA)
            self.idle_image_orig.fill((255,0,0,128))
        if not self.walk_frames_orig: # Final safety
            print("CRITICAL WARNING: self.walk_frames_orig is empty after load_sprites(). Using idle_image_orig.")
            self.walk_frames_orig.append(self.idle_image_orig)


    def _calculate_target_screen_pos(self, grid_x, grid_y):
        base_x = grid_x * GRID_SIZE
        base_y = grid_y * STAGGER_HEIGHT_PER_ROW
        screen_x = base_x + (GRID_SIZE - TARGET_PLAYER_WIDTH) / 2.0
        feet_anchor_y = base_y + int(GRID_SIZE * 1.15) # Adjust this for player foot position
        screen_y = feet_anchor_y - TARGET_PLAYER_HEIGHT
        return screen_x, screen_y

    def start_grid_move(self, dx, dy):
        if self.is_grid_moving:
            # print("DEBUG: Already grid moving, cannot start new move yet.") 
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
            
            self.move_timer = 0.0 # Reset timer for the new move
            self.is_grid_moving = True
            self.is_moving_animation = True
            self.anim_frame_index = 0 # Reset animation frame for walk cycle
            self.anim_timer = 0     # Reset animation timer
            ## left right
            if dx > 0: 
                self.facing_right = True
                self.direction = True
            elif dx < 0: 
                self.facing_right = False
                self.direction = True
            ## up down
            if dy > 0: 
                self.facing_up = False
                self.direction = False
            elif dy < 0: 
                self.facing_up = True
                self.direction = False

            print(f"  DEBUG: Started move. From screen: ({self.move_start_screen_x:.1f}, {self.move_start_screen_y:.1f}) To screen: ({self.target_screen_x:.1f}, {self.target_screen_y:.1f})")
            return True
        else:
            print(f"  DEBUG: Move to ({next_grid_x},{next_grid_y}) is NOT WALKABLE (blocked).") 
            self.is_moving_animation = False # Stop animation if blocked immediately
            return False

    def update_animation(self, dt):
        current_base_image = self.idle_image_orig 

        if self.is_moving_animation:
            self.anim_timer += dt
            if self.anim_timer >= ANIMATION_SPEED:
                self.anim_timer -= ANIMATION_SPEED
                if self.facing_right and self.direction:
                    print("Move right")
                    self.anim_frame_index = (self.anim_frame_index + 1) % len(self.walk_frames_orig)
                    current_base_image = self.walk_frames_orig[self.anim_frame_index]
                    self.current_image = current_base_image
                    return
                elif not self.facing_right and self.direction:
                    print('Move left')
                    self.anim_frame_index = (self.anim_frame_index + 1) % len(self.walk_frames_orig)
                    current_base_image = self.walk_frames_orig[self.anim_frame_index]
                    self.current_image = pygame.transform.flip(current_base_image, True, False)
                    return
                # after right/left check so it is fine for either r/l direction
                elif self.facing_up and not self.direction:
                    print('Move up')
                    self.anim_frame_index = (self.anim_frame_index + 1) % len(self.walk_frames_orig)
                    current_base_image = self.walk_up_frames_orig[self.anim_frame_index]
                    self.current_image = current_base_image
                    return
                else:
                    print('Move down')
                    self.anim_frame_index = (self.anim_frame_index + 1) % len(self.walk_frames_orig)
                    current_base_image = self.walk_down_frames_orig[self.anim_frame_index]
                    self.current_image = current_base_image
                    
                
        else: 
            self.anim_frame_index = 0 # Reset to first frame of idle (if idle was animated)
            current_base_image = self.idle_image_orig 
            self.anim_timer = 0 # Reset timer
        '''
        if current_base_image is None: # Should not happen with robust loading
             print("CRITICAL WARNING: current_base_image is None in update_animation. Using emergency fallback.")
             current_base_image = pygame.Surface((TARGET_PLAYER_WIDTH, TARGET_PLAYER_HEIGHT), pygame.SRCALPHA)
             current_base_image.fill((0,0,255,200)) # Bright blue placeholder
        '''
        

    def update(self, dt):
        if self.is_grid_moving:
            self.move_timer += dt
            progress = self.move_timer / GRID_MOVE_DURATION

            if progress >= 1.0:
                progress = 1.0 # Cap progress at 1.0
                self.is_grid_moving = False
                self.is_moving_animation = False # Crucial: stop animation when move completes
                # self.move_timer = 0 # Resetting timer in start_grid_move is better
                print(f"DEBUG: Reached target (timer). Snapped. is_grid_moving=False, is_moving_animation=False.")
            
            # Interpolate current screen position
            self.current_screen_x = self.move_start_screen_x + (self.target_screen_x - self.move_start_screen_x) * progress
            self.current_screen_y = self.move_start_screen_y + (self.target_screen_y - self.move_start_screen_y) * progress
            
            if not self.is_grid_moving: # If move just finished, snap to exact target
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
            # This part should ideally not be reached if __init__ and update_animation are robust
            fallback_surf = pygame.Surface((TARGET_PLAYER_WIDTH, TARGET_PLAYER_HEIGHT))
            fallback_surf.fill((255,0,0)) 
            draw_x = self.current_screen_x + maze_offset_x # Use current_screen_x even for fallback
            draw_y = self.current_screen_y + maze_offset_y
            surface.blit(fallback_surf, (draw_x, draw_y))