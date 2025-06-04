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

ANIMATION_SPEED = 0.1
GRID_MOVE_DURATION = 0.3

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

        # Initialize current_image with a default idle pose (e.g., last frame of walk_down_frames_orig)
        # This will be refined by facing_direction_on_stop
        self.current_image = self.walk_down_frames_orig[-1] if self.walk_down_frames_orig else \
                             (self.idle_image_orig if self.idle_image_orig else pygame.Surface((TARGET_PLAYER_WIDTH, TARGET_PLAYER_HEIGHT), pygame.SRCALPHA))
        if not self.idle_image_orig and not self.walk_down_frames_orig: # Ultimate fallback
            self.current_image.fill((0,0,255,128))
            print("CRITICAL WARNING: Player idle_image_orig and walk_down_frames_orig are None. Using fallback for initial current_image.")


        self.facing_right = True # Used for L/R animation frame flipping during movement
        self.current_animation_type = "idle" # General type: "walk_lr", "walk_up", "walk_down", "idle"
        self.facing_direction_on_stop = "down" # Specific direction for idle: "left", "right", "up", "down"
        self.last_animation_type = 'idle'
        self.is_moving_animation = False
        self.is_grid_moving = False

        self.move_start_screen_x = 0.0
        self.move_start_screen_y = 0.0
        self.target_screen_x = 0.0
        self.target_screen_y = 0.0
        self.current_screen_x = 0.0
        self.current_screen_y = 0.0
        self.move_timer = 0.0
        self.visual_offset_updown = 30
        self.anim_frame_index = 0
        self.anim_timer = 0

        initial_target_x, initial_target_y = self._calculate_target_screen_pos(self.grid_x, self.grid_y)
        self.current_screen_x = initial_target_x
        self.current_screen_y = initial_target_y
        self.target_screen_x = initial_target_x
        self.target_screen_y = initial_target_y
        
        # Set initial idle pose based on facing_direction_on_stop
        self.update_animation(0)


    def load_sprites(self):
        try:
            base_idle_image = pygame.image.load('./assets/Guali/static.png').convert_alpha()
            self.idle_image_orig = pygame.transform.scale(base_idle_image, (TARGET_PLAYER_WIDTH, TARGET_PLAYER_HEIGHT))
            
            walk_sheet = pygame.image.load('./assets/Guali/walk.png').convert_alpha()
            walkup_sheet = pygame.image.load('./assets/Guali/upwards.png').convert_alpha()
            walkdown_sheet = pygame.image.load('./assets/Guali/downwards.png').convert_alpha()
            
            num_lr_frames = 6
            orig_num_up_frames_in_sheet = 7 
            num_down_frames = 6

            frame_width_lr = walk_sheet.get_width() // num_lr_frames
            temp_walk_frames = []
            for i in range(num_lr_frames):
                frame = walk_sheet.subsurface(pygame.Rect(i * frame_width_lr, 0, frame_width_lr, walk_sheet.get_height()))
                temp_walk_frames.append(pygame.transform.scale(frame, (TARGET_PLAYER_WIDTH, TARGET_PLAYER_HEIGHT)))
            self.walk_frames_orig = temp_walk_frames if temp_walk_frames else [self.idle_image_orig]

            frame_width_up = walkup_sheet.get_width() // orig_num_up_frames_in_sheet
            temp_up_frames = []
            for i in range(orig_num_up_frames_in_sheet):
                frame = walkup_sheet.subsurface(pygame.Rect(i * frame_width_up, 0, frame_width_up, walkup_sheet.get_height()))
                temp_up_frames.append(pygame.transform.scale(frame, (TARGET_PLAYER_WIDTH*0.8, TARGET_PLAYER_HEIGHT*0.8)))
            self.walk_up_frames_orig = [item for i, item in enumerate(temp_up_frames) if i != 0] 
            if not self.walk_up_frames_orig: self.walk_up_frames_orig = [self.idle_image_orig]

            frame_width_down = walkdown_sheet.get_width() // num_down_frames
            temp_down_frames = []
            for i in range(num_down_frames):
                frame = walkdown_sheet.subsurface(pygame.Rect(i * frame_width_down, 0, frame_width_down, walkdown_sheet.get_height()))
                temp_down_frames.append(pygame.transform.scale(frame, (TARGET_PLAYER_WIDTH*0.8, TARGET_PLAYER_HEIGHT*0.8)))
            self.walk_down_frames_orig = temp_down_frames if temp_down_frames else [self.idle_image_orig]

        except pygame.error as e:
            print(f"ERROR loading player sprites: {e}")
            fallback_surface = pygame.Surface((TARGET_PLAYER_WIDTH, TARGET_PLAYER_HEIGHT), pygame.SRCALPHA)
            fallback_surface.fill((255,0,0,128))
            if self.idle_image_orig is None: self.idle_image_orig = fallback_surface
            if not self.walk_frames_orig: self.walk_frames_orig = [self.idle_image_orig]
            if not self.walk_up_frames_orig: self.walk_up_frames_orig = [self.idle_image_orig]
            if not self.walk_down_frames_orig: self.walk_down_frames_orig = [self.idle_image_orig]

        if self.idle_image_orig is None:
            print("CRITICAL WARNING: self.idle_image_orig is None after load_sprites().")
            self.idle_image_orig = pygame.Surface((TARGET_PLAYER_WIDTH, TARGET_PLAYER_HEIGHT), pygame.SRCALPHA); self.idle_image_orig.fill((255,0,0,128))
        
        # Ensure no animation list is empty; if so, add the idle image as a fallback.
        # This also ensures that list[-1] will always work.
        for anim_list in [self.walk_frames_orig, self.walk_up_frames_orig, self.walk_down_frames_orig]:
            if not anim_list: anim_list.append(self.idle_image_orig if self.idle_image_orig else fallback_surface)


    def _calculate_target_screen_pos(self, grid_x, grid_y):
        base_x = grid_x * GRID_SIZE
        base_y = grid_y * STAGGER_HEIGHT_PER_ROW
        screen_x = base_x + (GRID_SIZE - TARGET_PLAYER_WIDTH) / 2.0
        feet_anchor_y = base_y + int(GRID_SIZE * 1.15)
        screen_y = feet_anchor_y - TARGET_PLAYER_HEIGHT
        return screen_x, screen_y

    def start_grid_move(self, dx, dy, npcs):
        if self.is_grid_moving:
            return False

        next_grid_x = self.grid_x + dx
        next_grid_y = self.grid_y + dy

        if not self.maze.is_walkable(next_grid_x, next_grid_y):
            self.is_moving_animation = False # Stop any current walk animation
            self.current_animation_type = "idle"
            return False

        for npc in npcs:
            if npc.grid_x == next_grid_x and npc.grid_y == next_grid_y:
                self.is_moving_animation = False # Stop any current walk animation
                self.current_animation_type = "idle"
                return False

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
            self.current_animation_type = "walk_lr"
            self.facing_direction_on_stop = "right"
        elif dx < 0:
            self.facing_right = False
            self.current_animation_type = "walk_lr"
            self.facing_direction_on_stop = "left"
        elif dy > 0:
            self.facing_right = True # Default for up/down, doesn't matter for non-lr animations
            self.current_animation_type = "walk_down"
            self.facing_direction_on_stop = "down"
        elif dy < 0:
            self.facing_right = True # Default
            self.current_animation_type = "walk_up"
            self.facing_direction_on_stop = "up"
        return True

    def update_animation(self, dt):
        if not self.is_moving_animation: # Player is idle/stopped
            self.anim_frame_index = 0 # Reset animation frame for idle consistency
            self.anim_timer = 0

            idle_frame_source = None
            if self.facing_direction_on_stop == "right":
                idle_frame_source = self.walk_frames_orig[-1]
                self.current_image = idle_frame_source
            elif self.facing_direction_on_stop == "left":
                idle_frame_source = self.walk_frames_orig[-1]
                self.current_image = pygame.transform.flip(idle_frame_source, True, False)
            elif self.facing_direction_on_stop == "up":
                idle_frame_source = self.walk_up_frames_orig[-1]
                self.current_image = idle_frame_source
            elif self.facing_direction_on_stop == "down":
                idle_frame_source = self.walk_down_frames_orig[-1]
                self.current_image = idle_frame_source
            
            # Fallback if a specific animation list was somehow empty and only contains the generic idle.
            if idle_frame_source is None or idle_frame_source == self.idle_image_orig:
                if self.facing_direction_on_stop == "left":
                     self.current_image = pygame.transform.flip(self.idle_image_orig, True, False)
                else: # For right, up, down if using generic idle, just use it as is.
                     self.current_image = self.idle_image_orig
            return

        # Player is actively moving
        active_frames = []
        if self.current_animation_type == "walk_lr": active_frames = self.walk_frames_orig
        elif self.current_animation_type == "walk_up": active_frames = self.walk_up_frames_orig
        elif self.current_animation_type == "walk_down": active_frames = self.walk_down_frames_orig
        
        if not active_frames: # Should ideally not happen due to load_sprites fallbacks
            self.current_image = self.idle_image_orig
            return

        self.anim_timer += dt
        if self.anim_timer >= ANIMATION_SPEED:
            self.anim_timer -= ANIMATION_SPEED
            self.anim_frame_index = (self.anim_frame_index + 1) % len(active_frames)
        
        current_base_image = active_frames[self.anim_frame_index]

        if self.current_animation_type == "walk_lr" and not self.facing_right:
            self.current_image = pygame.transform.flip(current_base_image, True, False)
        else:
            self.current_image = current_base_image

    def update(self, dt, npcs):
        if self.is_grid_moving:
            self.move_timer += dt
            progress = self.move_timer / GRID_MOVE_DURATION

            if progress >= 1.0:
                progress = 1.0
                self.is_grid_moving = False
                # self.is_moving_animation will be set to False AFTER this block,
                # allowing one last animation update if needed, then idle pose.
            
            self.current_screen_x = self.move_start_screen_x + (self.target_screen_x - self.move_start_screen_x) * progress
            self.current_screen_y = self.move_start_screen_y + (self.target_screen_y - self.move_start_screen_y) * progress
            
            if not self.is_grid_moving: # Movement just completed in this frame
                self.current_screen_x = self.target_screen_x
                self.current_screen_y = self.target_screen_y
                self.is_moving_animation = False # Now set to false, so next update_animation call uses idle logic.
                self.last_animation_type = self.current_animation_type
                self.current_animation_type = "idle" # Set general type to idle

        self.update_animation(dt)

    def draw(self, surface, maze_offset_x, maze_offset_y):
        if self.current_image:
            
            #print(self.current_animation_type)
            #print(self.last_animation_type)
            # offset for visual downwards and upwards sprite
            if ((self.current_animation_type == 'idle') and (self.last_animation_type == "walk_down" or self.last_animation_type =="walk_up"))or (self.current_animation_type == 'walk_down' or self.last_animation_type =='walk_up'):
                print("Offset given")
                draw_y = self.current_screen_y + maze_offset_y +self.visual_offset_updown
            else:
                draw_y = self.current_screen_y + maze_offset_y 
            draw_x = self.current_screen_x + maze_offset_x
            surface.blit(self.current_image, (draw_x, draw_y))
        