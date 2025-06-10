# player.py
import pygame
import os 

# Constants
GRID_SIZE = 80
STAGGER_HEIGHT_PER_ROW = int(GRID_SIZE * 0.8)

# Player sprite visual properties
ORIG_PLAYER_SPRITE_WIDTH = 20
ORIG_PLAYER_SPRITE_HEIGHT = 26
PLAYER_SCALE_FACTOR = 12
TARGET_PLAYER_WIDTH = int(ORIG_PLAYER_SPRITE_WIDTH * PLAYER_SCALE_FACTOR) 
TARGET_PLAYER_HEIGHT = int(ORIG_PLAYER_SPRITE_HEIGHT * PLAYER_SCALE_FACTOR)

# Animation and Movement Speeds
DEFAULT_ANIMATION_SPEED = 0.1 
ATTACK_ANIMATION_SPEED = 0.07 
GRID_MOVE_DURATION = 0.2    

# Attack
ATTACK_DURATION = 8 * ATTACK_ANIMATION_SPEED 

class Player:
    def __init__(self, initial_grid_x, initial_grid_y, maze):
        self.grid_x = initial_grid_x
        self.grid_y = initial_grid_y
        self.maze = maze

        self.current_screen_x = 0.0
        self.current_screen_y = 0.0
        self.move_start_screen_x = 0.0
        self.move_start_screen_y = 0.0
        self.target_screen_x = 0.0
        self.target_screen_y = 0.0
        
        self.animations = {
            "idle": {"up": [], "down": [], "left": [], "right": []},
            "run": {"up": [], "down": [], "left": [], "right": []}, 
            "attack": {"up": [], "down": [], "left": [], "right": []}
        }
        self.current_image = None
        self.anim_frame_index = 0
        self.anim_timer = 0.0
        self.load_sprites() 

        self.facing_direction = "down"  
        self.current_action = "idle"    
        
        self.is_grid_moving = False     
        self.grid_move_timer = 0.0

        self.is_attacking = False
        self.attack_timer = 0.0
        
        self.target_screen_x, self.target_screen_y = self._calculate_target_screen_pos(self.grid_x, self.grid_y)
        self.current_screen_x = self.target_screen_x
        self.current_screen_y = self.target_screen_y
        
        self._update_current_image() 


    def _load_sprite_sheet(self, base_path, action, direction, filename, frame_count, orig_frame_width, orig_frame_height, scale_to_width, scale_to_height, is_single_image=False):
        if action == "attack":
            filepath = os.path.join(base_path, action, filename) 
        else: 
            filepath = os.path.join(base_path, filename)
        
        frames = []
        try:
            sheet = pygame.image.load(filepath).convert_alpha()
            expected_width_for_subsurface = orig_frame_width * frame_count if not is_single_image else orig_frame_width
            expected_height_for_subsurface = orig_frame_height
            # print(f"DEBUG: Loading '{filepath}'. Actual Dims: ({sheet.get_width()}x{sheet.get_height()}). Expected for Subsurface Logic (approx): ({expected_width_for_subsurface}x{expected_height_for_subsurface}) based on {frame_count} frames of ({orig_frame_width}x{orig_frame_height}) each. Scaling to: ({scale_to_width}x{scale_to_height})")

            if is_single_image:
                scaled_frame = pygame.transform.scale(sheet, (scale_to_width, scale_to_height))
                frames.append(scaled_frame)
            else:
                sheet_width_actual = sheet.get_width()
                sheet_height_actual = sheet.get_height()
                
                if frame_count == 0 or orig_frame_width == 0 or orig_frame_height == 0:
                    # print(f"Warning: Invalid frame_count ({frame_count}) or orig_frame_width/height ({orig_frame_width}x{orig_frame_height}) for {filepath}. Treating as single frame.")
                    scaled_frame = pygame.transform.scale(sheet, (scale_to_width, scale_to_height))
                    frames.append(scaled_frame)
                elif orig_frame_width * frame_count > sheet_width_actual + 1 or orig_frame_height > sheet_height_actual + 1: 
                     # print(f"ERROR: Sprite sheet '{filepath}' dimensions mismatch. Sheet is {sheet_width_actual}x{sheet_height_actual}, but trying to extract {frame_count} frames of {orig_frame_width}x{orig_frame_height} (needs {orig_frame_width*frame_count}x{orig_frame_height}). Appending fallback.")
                     raise ValueError(f"Subsurface rectangle outside surface area for {filepath}")
                else:
                    for i in range(frame_count):
                        frame_rect = pygame.Rect(i * orig_frame_width, 0, orig_frame_width, orig_frame_height)
                        frame = sheet.subsurface(frame_rect)
                        scaled_frame = pygame.transform.scale(frame, (scale_to_width, scale_to_height))
                        frames.append(scaled_frame)
        except Exception as e: 
            print(f"ERROR loading sprite: {filepath} - {e}. Appending fallback surface.")
            fallback_surface = pygame.Surface((scale_to_width, scale_to_height), pygame.SRCALPHA)
            fallback_surface.fill((255, 0, 255, 180)) 
            frames.append(fallback_surface)
        
        self.animations[action][direction] = frames

    def load_sprites(self):
        base_asset_path = './assets/Player/' 
        common_frame_count = 8
        common_orig_w = 96 
        common_orig_h = 80

        self._load_sprite_sheet(base_asset_path, "idle", "down", "idle_down.png", common_frame_count, common_orig_w, common_orig_h, TARGET_PLAYER_WIDTH, TARGET_PLAYER_HEIGHT)
        self._load_sprite_sheet(base_asset_path, "idle", "up", "idle_up.png", common_frame_count, common_orig_w, common_orig_h, TARGET_PLAYER_WIDTH, TARGET_PLAYER_HEIGHT) 
        self._load_sprite_sheet(base_asset_path, "idle", "left", "idle_left.png", common_frame_count, common_orig_w, common_orig_h, TARGET_PLAYER_WIDTH, TARGET_PLAYER_HEIGHT) 
        self._load_sprite_sheet(base_asset_path, "idle", "right", "idle_right.png", common_frame_count, common_orig_w, common_orig_h, TARGET_PLAYER_WIDTH, TARGET_PLAYER_HEIGHT)
        self._load_sprite_sheet(base_asset_path, "run", "down", "run_down.png", common_frame_count, common_orig_w, common_orig_h, TARGET_PLAYER_WIDTH, TARGET_PLAYER_HEIGHT)
        self._load_sprite_sheet(base_asset_path, "run", "up", "run_up.png", common_frame_count, common_orig_w, common_orig_h, TARGET_PLAYER_WIDTH, TARGET_PLAYER_HEIGHT)
        self._load_sprite_sheet(base_asset_path, "run", "left", "run_left.png", common_frame_count, common_orig_w, common_orig_h, TARGET_PLAYER_WIDTH, TARGET_PLAYER_HEIGHT)
        self._load_sprite_sheet(base_asset_path, "run", "right", "run_right.png", common_frame_count, common_orig_w, common_orig_h, TARGET_PLAYER_WIDTH, TARGET_PLAYER_HEIGHT)
        self._load_sprite_sheet(base_asset_path, "attack", "left", "attack1_left.png", common_frame_count, common_orig_w, common_orig_h, TARGET_PLAYER_WIDTH, TARGET_PLAYER_HEIGHT)
        self._load_sprite_sheet(base_asset_path, "attack", "right", "attack1_right.png", common_frame_count, common_orig_w, common_orig_h, TARGET_PLAYER_WIDTH, TARGET_PLAYER_HEIGHT) 
        self._load_sprite_sheet(base_asset_path, "attack", "up", "attack1_up.png", common_frame_count, common_orig_w, common_orig_h, TARGET_PLAYER_WIDTH, TARGET_PLAYER_HEIGHT)       
        self._load_sprite_sheet(base_asset_path, "attack", "down", "attack1_down.png", common_frame_count, common_orig_w, common_orig_h, TARGET_PLAYER_WIDTH, TARGET_PLAYER_HEIGHT)  

        for direction in ["up", "down", "left", "right"]:
            if not self.animations["idle"][direction]:
                # print(f"Warning: Idle animation for direction '{direction}' is empty after loading attempts.")
                if self.animations["run"].get(direction) and self.animations["run"][direction]: 
                    #  print(f"Falling back to first frame of 'run_{direction}' for 'idle_{direction}'.")
                     self.animations["idle"][direction] = [self.animations["run"][direction][0]]
                else: 
                    #  print(f"CRITICAL: No run animation for '{direction}' either. Creating ultimate fallback for 'idle_{direction}'.")
                     fb_surface = pygame.Surface((TARGET_PLAYER_WIDTH, TARGET_PLAYER_HEIGHT), pygame.SRCALPHA); fb_surface.fill((0,255,0,100))
                     self.animations["idle"][direction] = [fb_surface]

    def _calculate_target_screen_pos(self, grid_x, grid_y):
        base_x = grid_x * GRID_SIZE
        base_y = grid_y * STAGGER_HEIGHT_PER_ROW # Top-left of the cell's isometric diamond

        screen_x = base_x + (GRID_SIZE - TARGET_PLAYER_WIDTH) / 2.0

        # Feet anchor at the bottom of the cell's top face (surface level)
        feet_anchor_y_on_grid_surface = base_y + STAGGER_HEIGHT_PER_ROW 
        
        screen_y = feet_anchor_y_on_grid_surface - TARGET_PLAYER_HEIGHT # Position sprite so feet are at anchor
        return screen_x, screen_y+110

    def _direction_str_to_dxdy(self, direction_str):
        if direction_str == "up": return 0, -1
        if direction_str == "down": return 0, 1
        if direction_str == "left": return -1, 0
        if direction_str == "right": return 1, 0
        return 0, 0

    def handle_key_down(self, direction_key_str, npcs):
        if self.is_attacking or self.is_grid_moving: 
            return
        dx, dy = self._direction_str_to_dxdy(direction_key_str)
        if dx != 0 or dy != 0:
            self.start_grid_move(dx, dy, npcs) 

    def handle_key_up(self, direction_key_str, npcs):
        pass # Not used for tap-to-move logic

    def start_grid_move(self, dx, dy, npcs): 
        if self.is_grid_moving or self.is_attacking: 
            return False
        next_grid_x = self.grid_x + dx
        next_grid_y = self.grid_y + dy
        if not self.maze.is_walkable(next_grid_x, next_grid_y):
            # print(f"Player blocked: Tried to move to non-walkable tile ({next_grid_x}, {next_grid_y})")
            return False
        for npc in npcs: 
            if npc.grid_x == next_grid_x and npc.grid_y == next_grid_y:
                # print(f"Player blocked: NPC at target tile ({next_grid_x}, {next_grid_y})")
                return False
        self.grid_x = next_grid_x
        self.grid_y = next_grid_y
        if dx > 0: self.facing_direction = "right"
        elif dx < 0: self.facing_direction = "left"
        elif dy > 0: self.facing_direction = "down"
        elif dy < 0: self.facing_direction = "up"
        self.current_action = "run" 
        self.is_grid_moving = True
        self.grid_move_timer = 0.0
        self.anim_frame_index = 0 
        self.anim_timer = 0.0
        self.move_start_screen_x = self.current_screen_x
        self.move_start_screen_y = self.current_screen_y
        self.target_screen_x, self.target_screen_y = self._calculate_target_screen_pos(self.grid_x, self.grid_y)
        # print(f"Player moving to: ({self.grid_x},{self.grid_y}). Screen target: ({self.target_screen_x:.1f},{self.target_screen_y:.1f})")
        return True

    def start_attack(self):
        if self.is_attacking or self.is_grid_moving: 
            return
        self.is_attacking = True
        self.current_action = "attack"
        self.anim_frame_index = 0
        self.anim_timer = 0.0
        self.attack_timer = 0.0

    def _update_grid_move(self, dt): 
        if not self.is_grid_moving:
            return
        self.grid_move_timer += dt
        progress = self.grid_move_timer / GRID_MOVE_DURATION
        if progress >= 1.0:
            progress = 1.0
            self.is_grid_moving = False
            self.current_action = "idle"
            self.current_screen_x = self.target_screen_x
            self.current_screen_y = self.target_screen_y
        else:
            self.current_screen_x = self.move_start_screen_x + (self.target_screen_x - self.move_start_screen_x) * progress
            self.current_screen_y = self.move_start_screen_y + (self.target_screen_y - self.move_start_screen_y) * progress

    def _update_attack_state(self, dt):
        if not self.is_attacking:
            return
        self.attack_timer += dt
        if self.attack_timer >= ATTACK_DURATION:
            self.is_attacking = False
            self.current_action = "idle"
            self.attack_timer = 0.0
            self.anim_frame_index = 0 

    def _update_animation_frames(self, dt):
        if not self.current_action or not self.facing_direction:
            self._update_current_image() 
            return
        frames_list = []
        anim_speed = DEFAULT_ANIMATION_SPEED
        animation_set = self.animations.get(self.current_action)
        if animation_set:
            frames_list = animation_set.get(self.facing_direction, [])
        if self.current_action == "attack":
            anim_speed = ATTACK_ANIMATION_SPEED
        if not frames_list: 
            if self.animations["idle"].get(self.facing_direction) and self.animations["idle"][self.facing_direction]:
                frames_list = self.animations["idle"][self.facing_direction]
            elif self.animations["idle"]["down"] and self.animations["idle"]["down"]: 
                 frames_list = self.animations["idle"]["down"]
            else: 
                if self.current_image is None: 
                    fb_surf = pygame.Surface((TARGET_PLAYER_WIDTH, TARGET_PLAYER_HEIGHT), pygame.SRCALPHA); fb_surf.fill((0,0,255,120))
                    self.current_image = fb_surf
                return
        self.anim_timer += dt
        if self.anim_timer >= anim_speed:
            self.anim_timer -= anim_speed
            if self.current_action == "attack" and self.anim_frame_index == len(frames_list) -1 and self.attack_timer < ATTACK_DURATION:
                pass 
            else:
                self.anim_frame_index = (self.anim_frame_index + 1) % len(frames_list)
        if self.anim_frame_index < len(frames_list):
            self.current_image = frames_list[self.anim_frame_index]
        elif frames_list : 
            self.current_image = frames_list[0]

    def _update_current_image(self):
        active_frames = []
        if self.current_action == "idle" and self.animations["idle"].get(self.facing_direction):
            active_frames = self.animations["idle"][self.facing_direction]
        
        if active_frames and self.anim_frame_index < len(active_frames): # Ensure index is valid
            self.current_image = active_frames[self.anim_frame_index]
        elif active_frames: # Fallback to first frame of active_frames if index is bad
             self.current_image = active_frames[0]
        elif self.animations["idle"]["down"] and self.animations["idle"]["down"]: 
             self.current_image = self.animations["idle"]["down"][0] # Fallback to idle_down's first frame
        
        if self.current_image is None: 
            fb_surf = pygame.Surface((TARGET_PLAYER_WIDTH, TARGET_PLAYER_HEIGHT), pygame.SRCALPHA)
            fb_surf.fill((0,0,255,120)) 
            self.current_image = fb_surf

    def update(self, dt, npcs): 
        if self.is_attacking:
            self._update_attack_state(dt) 
        elif self.is_grid_moving:
            self._update_grid_move(dt) 
        else: 
            if self.current_action != "idle":
                 self.current_action = "idle"
                 # When transitioning to idle, reset animation to the first frame of the current facing direction's idle animation
                 self.anim_frame_index = 0 
                 self.anim_timer = 0.0
                 # Explicitly set the image to the first idle frame
                 if self.animations["idle"].get(self.facing_direction) and self.animations["idle"][self.facing_direction]:
                     self.current_image = self.animations["idle"][self.facing_direction][0]
                 elif self.animations["idle"]["down"] and self.animations["idle"]["down"]: # Fallback
                     self.current_image = self.animations["idle"]["down"][0]

        self._update_animation_frames(dt)
        if self.current_image is None : 
            self._update_current_image()

    def draw(self, surface, maze_offset_x, maze_offset_y):
        if self.current_image:
            draw_x = self.current_screen_x + maze_offset_x
            draw_y = self.current_screen_y + maze_offset_y
            surface.blit(self.current_image, (draw_x, draw_y))
        else: 
            pygame.draw.rect(surface, (255, 0, 0), 
                             (self.current_screen_x + maze_offset_x, 
                              self.current_screen_y + maze_offset_y, 
                              TARGET_PLAYER_WIDTH, TARGET_PLAYER_HEIGHT))
