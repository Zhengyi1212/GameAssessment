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

# Attack and Death Durations
ATTACK_FRAME_TO_HIT = 4 # The frame in the attack animation when damage is applied
ATTACK_DURATION = 8 * ATTACK_ANIMATION_SPEED 
DEATH_SEQUENCE_DURATION = 2.0 # Time from death until Game Over screen appears

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
        
        self.is_dead = False
        self.death_timer = 0.0
        
        self.run_key_held = None
        self.run_timer = 0.0
        self.RUN_TRIGGER_TIME = 0.15 

        # --- Load player sound effects ---
        self.hurt_sound = None
        self.attack_sound = None
        try:
            self.hurt_sound = pygame.mixer.Sound('./assets/hurt.mp3')
            self.attack_sound = pygame.mixer.Sound('./assets/swing_sword.mp3')
        except pygame.error as e:
            print(f"Warning: Could not load one or more player sounds: {e}")

        self.target_screen_x, self.target_screen_y = self._calculate_target_screen_pos(self.grid_x, self.grid_y)
        self.current_screen_x = self.target_screen_x
        self.current_screen_y = self.target_screen_y
        
        self._update_current_image() 


    def _load_sprite_sheet(self, base_path, action, filename, frame_count, orig_frame_width, orig_frame_height, scale_to_width, scale_to_height, direction=None):
        filepath = os.path.join(base_path, action, filename)
        if not os.path.exists(filepath):
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
        
        if direction:
            self.animations[action][direction] = frames
        else:
            self.animations[action] = frames

    def load_sprites(self):
        base_asset_path = './assets/Player/' 
        common_frame_count = 8
        run_frame_count = 4 
        common_orig_w = 96 
        common_orig_h = 80

        # Load Idle Sprites
        self._load_sprite_sheet(base_asset_path, "idle", "idle_down.png", common_frame_count, common_orig_w, common_orig_h, TARGET_PLAYER_WIDTH, TARGET_PLAYER_HEIGHT, direction="down")
        self._load_sprite_sheet(base_asset_path, "idle", "idle_up.png", common_frame_count, common_orig_w, common_orig_h, TARGET_PLAYER_WIDTH, TARGET_PLAYER_HEIGHT, direction="up") 
        self._load_sprite_sheet(base_asset_path, "idle", "idle_left.png", common_frame_count, common_orig_w, common_orig_h, TARGET_PLAYER_WIDTH, TARGET_PLAYER_HEIGHT, direction="left") 
        self._load_sprite_sheet(base_asset_path, "idle", "idle_right.png", common_frame_count, common_orig_w, common_orig_h, TARGET_PLAYER_WIDTH, TARGET_PLAYER_HEIGHT, direction="right")
        
        # Load Run Sprites
        self._load_sprite_sheet(base_asset_path, "run", "run_down.png", run_frame_count, common_orig_w, common_orig_h, TARGET_PLAYER_WIDTH, TARGET_PLAYER_HEIGHT, direction="down")
        self._load_sprite_sheet(base_asset_path, "run", "run_up.png", run_frame_count, common_orig_w, common_orig_h, TARGET_PLAYER_WIDTH, TARGET_PLAYER_HEIGHT, direction="up")
        self._load_sprite_sheet(base_asset_path, "run", "run_left.png", run_frame_count, common_orig_w, common_orig_h, TARGET_PLAYER_WIDTH, TARGET_PLAYER_HEIGHT, direction="left")
        self._load_sprite_sheet(base_asset_path, "run", "run_right.png", run_frame_count, common_orig_w, common_orig_h, TARGET_PLAYER_WIDTH, TARGET_PLAYER_HEIGHT, direction="right")

        # Load Attack Sprites
        self._load_sprite_sheet(base_asset_path, "attack", "attack1_left.png", common_frame_count, common_orig_w, common_orig_h, TARGET_PLAYER_WIDTH, TARGET_PLAYER_HEIGHT, direction="left")
        self._load_sprite_sheet(base_asset_path, "attack", "attack1_right.png", common_frame_count, common_orig_w, common_orig_h, TARGET_PLAYER_WIDTH, TARGET_PLAYER_HEIGHT, direction="right") 
        self._load_sprite_sheet(base_asset_path, "attack", "attack1_up.png", common_frame_count, common_orig_w, common_orig_h, TARGET_PLAYER_WIDTH, TARGET_PLAYER_HEIGHT, direction="up")       
        self._load_sprite_sheet(base_asset_path, "attack", "attack1_down.png", common_frame_count, common_orig_w, common_orig_h, TARGET_PLAYER_WIDTH, TARGET_PLAYER_HEIGHT, direction="down")  

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

    def handle_key_down(self, key, npcs):
        """Handles a single key press for turning, single steps, or attacking."""
        if self.is_grid_moving or self.is_attacking or self.is_dead:
            return

        direction = None
        if key == pygame.K_UP: direction = 'up'
        elif key == pygame.K_DOWN: direction = 'down'
        elif key == pygame.K_LEFT: direction = 'left'
        elif key == pygame.K_RIGHT: direction = 'right'

        if direction:
            if self.facing_direction == direction:
                dx, dy = self._direction_str_to_dxdy(direction)
                self.start_grid_move(dx, dy, npcs)
            else:
                self.facing_direction = direction
                self.current_action = 'idle'
                self.anim_frame_index = 0
                self.anim_timer = 0.0

            self.run_key_held = key
            self.run_timer = 0.0
        
        elif key == pygame.K_SPACE:
            self.start_attack()
            
    def handle_key_up(self, key):
        """Handles a key release to stop tracking it for a run."""
        if self.run_key_held == key:
            self.run_key_held = None
            self.run_timer = 0.0

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
        
        # --- NEW: Play the attack sound ---
        if self.attack_sound:
            self.attack_sound.play()

        self.is_attacking = True
        self.current_action = "attack"
        self.anim_frame_index = 0
        self.anim_timer = 0.0
        self.attack_timer = 0.0
        self.has_dealt_damage_this_attack = False

    def take_damage(self, amount):
        if self.is_dead: return
        self.health -= amount

        if self.hurt_sound:
            self.hurt_sound.play()

        if self.health <= 0:
            self.health = 0
            if not self.is_dead:
                self.is_dead = True
                self.death_timer = 0.0
                self.is_attacking = False
                self.is_grid_moving = False

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

    def _update_grid_move(self, dt): 
        if not self.is_grid_moving: return
        self.grid_move_timer += dt
        progress = self.grid_move_timer / GRID_MOVE_DURATION
        if progress >= 1.0:
            progress = 1.0
            self.is_grid_moving = False
            self.current_action = 'idle' 
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
        
        anim_speed = DEFAULT_ANIMATION_SPEED
        if self.current_action == "attack":
            anim_speed = ATTACK_ANIMATION_SPEED
        
        self.anim_timer += dt
        if self.anim_timer >= anim_speed:
            self.anim_timer -= anim_speed
            if self.current_action == "attack":
                if self.anim_frame_index < len(frames_list) - 1:
                    self.anim_frame_index += 1
            else: 
                self.anim_frame_index = (self.anim_frame_index + 1) % len(frames_list)
        
        if self.anim_frame_index < len(frames_list):
            self.current_image = frames_list[self.anim_frame_index]

    def _update_current_image(self):
        if self.current_image is None:
            active_frames = self.animations.get(self.current_action, {}).get(self.facing_direction, [])
            if active_frames:
                self.current_image = active_frames[0]
            else: 
                self.current_image = self.animations['idle']['down'][0]

    def update(self, dt, npcs): 
        if self.run_key_held and not self.is_grid_moving and not self.is_attacking and not self.is_dead:
            self.run_timer += dt
            if self.run_timer > self.RUN_TRIGGER_TIME:
                direction = None
                if self.run_key_held == pygame.K_UP: direction = 'up'
                elif self.run_key_held == pygame.K_DOWN: direction = 'down'
                elif self.run_key_held == pygame.K_LEFT: direction = 'left'
                elif self.run_key_held == pygame.K_RIGHT: direction = 'right'
                
                if direction and self.facing_direction == direction:
                    dx, dy = self._direction_str_to_dxdy(direction)
                    self.start_grid_move(dx, dy, npcs)

        if self.is_dead:
            self.death_timer += dt
            return

        self._update_grid_move(dt)
        self._update_attack_state(dt, npcs)
        self._update_animation_frames(dt)
        self._update_current_image()

    def draw(self, surface, maze_offset_x, maze_offset_y):
        if self.is_dead:
            return
            
        if self.current_image:
            draw_x = self.current_screen_x + maze_offset_x
            draw_y = self.current_screen_y + maze_offset_y
            surface.blit(self.current_image, (draw_x, draw_y))