# player.py
import pygame
import os 
import math

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
ATTACK_FRAME_TO_HIT = 4 # The frame in the attack animation when damage is applied
ATTACK_DURATION = 8 * ATTACK_ANIMATION_SPEED 

class Player:
    def __init__(self, initial_grid_x, initial_grid_y, maze):
        self.grid_x = initial_grid_x
        self.grid_y = initial_grid_y
        self.maze = maze

        self.max_health = 3
        self.health = self.max_health

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
        self.has_dealt_damage_this_attack = False
        
        # --- NEW: State for continuous movement ---
        self.keys_down = {'up': False, 'down': False, 'left': False, 'right': False}
        self.move_intent_direction = None # Stores the next intended move
        
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
        run_frame_count = 4 # NEW: specific frame count for run
        common_orig_w = 96 
        common_orig_h = 80

        # Load Idle Sprites (8 frames)
        self._load_sprite_sheet(base_asset_path, "idle", "down", "idle_down.png", common_frame_count, common_orig_w, common_orig_h, TARGET_PLAYER_WIDTH, TARGET_PLAYER_HEIGHT)
        self._load_sprite_sheet(base_asset_path, "idle", "up", "idle_up.png", common_frame_count, common_orig_w, common_orig_h, TARGET_PLAYER_WIDTH, TARGET_PLAYER_HEIGHT) 
        self._load_sprite_sheet(base_asset_path, "idle", "left", "idle_left.png", common_frame_count, common_orig_w, common_orig_h, TARGET_PLAYER_WIDTH, TARGET_PLAYER_HEIGHT) 
        self._load_sprite_sheet(base_asset_path, "idle", "right", "idle_right.png", common_frame_count, common_orig_w, common_orig_h, TARGET_PLAYER_WIDTH, TARGET_PLAYER_HEIGHT)
        
        # Load Run Sprites (4 frames)
        self._load_sprite_sheet(base_asset_path, "run", "down", "run_down.png", run_frame_count, common_orig_w, common_orig_h, TARGET_PLAYER_WIDTH, TARGET_PLAYER_HEIGHT)
        self._load_sprite_sheet(base_asset_path, "run", "up", "run_up.png", run_frame_count, common_orig_w, common_orig_h, TARGET_PLAYER_WIDTH, TARGET_PLAYER_HEIGHT)
        self._load_sprite_sheet(base_asset_path, "run", "left", "run_left.png", run_frame_count, common_orig_w, common_orig_h, TARGET_PLAYER_WIDTH, TARGET_PLAYER_HEIGHT)
        self._load_sprite_sheet(base_asset_path, "run", "right", "run_right.png", run_frame_count, common_orig_w, common_orig_h, TARGET_PLAYER_WIDTH, TARGET_PLAYER_HEIGHT)

        # Load Attack Sprites (8 frames)
        self._load_sprite_sheet(base_asset_path, "attack", "left", "attack1_left.png", common_frame_count, common_orig_w, common_orig_h, TARGET_PLAYER_WIDTH, TARGET_PLAYER_HEIGHT)
        self._load_sprite_sheet(base_asset_path, "attack", "right", "attack1_right.png", common_frame_count, common_orig_w, common_orig_h, TARGET_PLAYER_WIDTH, TARGET_PLAYER_HEIGHT) 
        self._load_sprite_sheet(base_asset_path, "attack", "up", "attack1_up.png", common_frame_count, common_orig_w, common_orig_h, TARGET_PLAYER_WIDTH, TARGET_PLAYER_HEIGHT)       
        self._load_sprite_sheet(base_asset_path, "attack", "down", "attack1_down.png", common_frame_count, common_orig_w, common_orig_h, TARGET_PLAYER_WIDTH, TARGET_PLAYER_HEIGHT)  

    def _calculate_target_screen_pos(self, grid_x, grid_y):
        base_x = grid_x * GRID_SIZE
        base_y = grid_y * STAGGER_HEIGHT_PER_ROW 
        screen_x = base_x + (GRID_SIZE - TARGET_PLAYER_WIDTH) / 2.0
        feet_anchor_y_on_grid_surface = base_y + STAGGER_HEIGHT_PER_ROW 
        screen_y = feet_anchor_y_on_grid_surface - TARGET_PLAYER_HEIGHT 
        return screen_x, screen_y+110

    def _direction_str_to_dxdy(self, direction_str):
        if direction_str == "up": return 0, -1
        if direction_str == "down": return 0, 1
        if direction_str == "left": return -1, 0
        if direction_str == "right": return 1, 0
        return 0, 0

    def handle_key_down(self, direction_key_str):
        """Sets the state for a pressed key."""
        if direction_key_str in self.keys_down:
            self.keys_down[direction_key_str] = True

    def handle_key_up(self, direction_key_str):
        """Sets the state for a released key."""
        if direction_key_str in self.keys_down:
            self.keys_down[direction_key_str] = False

    def start_grid_move(self, dx, dy, npcs): 
        if self.is_grid_moving or self.is_attacking: 
            return False
        next_grid_x = self.grid_x + dx
        next_grid_y = self.grid_y + dy
        if not self.maze.is_walkable(next_grid_x, next_grid_y):
            return False
        for npc in npcs: 
            if npc.grid_x == next_grid_x and npc.grid_y == next_grid_y and not npc.is_dead:
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
        return True

    def start_attack(self):
        if self.is_attacking or self.is_grid_moving: 
            return
        self.is_attacking = True
        self.current_action = "attack"
        self.anim_frame_index = 0
        self.anim_timer = 0.0
        self.attack_timer = 0.0
        self.has_dealt_damage_this_attack = False

    def take_damage(self, amount):
        self.health -= amount
        if self.health <= 0:
            self.health = 0

    def check_attack_hit(self, npcs):
        if self.has_dealt_damage_this_attack: return

        if self.anim_frame_index == ATTACK_FRAME_TO_HIT:
            dx, dy = self._direction_str_to_dxdy(self.facing_direction)
            target_x, target_y = self.grid_x + dx, self.grid_y + dy

            for npc in npcs:
                if npc.grid_x == target_x and npc.grid_y == target_y and not npc.is_dead:
                    npc.take_damage(1)
                    self.has_dealt_damage_this_attack = True
                    break

    def _update_movement(self, npcs):
        """Checks for held-down keys and initiates movement."""
        if self.is_grid_moving or self.is_attacking:
            return

        # Determine direction from pressed keys
        direction_to_move = None
        if self.keys_down['up']: direction_to_move = 'up'
        elif self.keys_down['down']: direction_to_move = 'down'
        elif self.keys_down['left']: direction_to_move = 'left'
        elif self.keys_down['right']: direction_to_move = 'right'

        if direction_to_move:
            dx, dy = self._direction_str_to_dxdy(direction_to_move)
            self.start_grid_move(dx, dy, npcs)
        else:
            # No keys are pressed, switch to idle
            if self.current_action == 'run':
                self.current_action = 'idle'
                self.anim_frame_index = 0
                self.anim_timer = 0.0

    def _update_grid_move(self, dt): 
        if not self.is_grid_moving: return
        self.grid_move_timer += dt
        progress = self.grid_move_timer / GRID_MOVE_DURATION
        if progress >= 1.0:
            progress = 1.0
            self.is_grid_moving = False
            # Don't set to idle here, let _update_movement decide based on keys
        self.current_screen_x = self.move_start_screen_x + (self.target_screen_x - self.move_start_screen_x) * progress
        self.current_screen_y = self.move_start_screen_y + (self.target_screen_y - self.move_start_screen_y) * progress

    def _update_attack_state(self, dt, npcs):
        if not self.is_attacking: return
        self.attack_timer += dt
        self.check_attack_hit(npcs)
        if self.attack_timer >= ATTACK_DURATION:
            self.is_attacking = False
            self.current_action = "idle"

    def _update_animation_frames(self, dt):
        frames_list = self.animations.get(self.current_action, {}).get(self.facing_direction, [])
        if not frames_list: return
        
        anim_speed = ATTACK_ANIMATION_SPEED if self.current_action == "attack" else DEFAULT_ANIMATION_SPEED
        
        self.anim_timer += dt
        if self.anim_timer >= anim_speed:
            self.anim_timer -= anim_speed
            self.anim_frame_index = (self.anim_frame_index + 1) % len(frames_list)
        
        self.current_image = frames_list[self.anim_frame_index]

    def _update_current_image(self):
        """Ensures a valid image is always set."""
        if self.current_image is None:
            active_frames = self.animations.get(self.current_action, {}).get(self.facing_direction, [])
            if active_frames:
                self.current_image = active_frames[0]
            else: # Fallback
                self.current_image = self.animations['idle']['down'][0]

    def update(self, dt, npcs): 
        self._update_movement(npcs)
        self._update_grid_move(dt)
        self._update_attack_state(dt, npcs)
        self._update_animation_frames(dt)
        self._update_current_image()

    def draw(self, surface, maze_offset_x, maze_offset_y):
        if self.current_image:
            draw_x = self.current_screen_x + maze_offset_x
            draw_y = self.current_screen_y + maze_offset_y
            surface.blit(self.current_image, (draw_x, draw_y))
