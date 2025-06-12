# npc.py
import pygame
import random
import math
from cube import FloorCube, RockCube, WoodCube

# Constants
GRID_SIZE = 80
STAGGER_HEIGHT_PER_ROW = int(GRID_SIZE * 0.8)
ANIMATION_SPEED = 0.1 
GRID_MOVE_DURATION = 0.3

# --- NEW/REVISED NPC CONFIGURATIONS ---
NPC_CONFIGS = {
    "orc": {
        "sprite_sheet_path": "./assets/NPC/Orc/orc3_walk/orc3_walk_full.png",
        "attack_sprite_sheet_path": "./assets/NPC/Orc/orc3_attack/orc3_attack_full.png", # 
        "death_sprite_sheet_path": "./assets/NPC/Orc/orc3_death/orc3_death_full.png", # <
        "orig_frame_width": 63, 
        "orig_frame_height": 64, 
        "attack_frame_width": 63, # <
        "attack_frame_height": 64,# 
        "death_frame_width": 63,
        "death_frame_height": 64, 
        "scale_factor": 2.4,
        "y_draw_offset": 50,
        "animations": { 
            "walk_down": (0, 6), "walk_up": (1, 6), "walk_left": (2, 6), "walk_right": (3, 6)  
        },
        "attack_animations": {
            "attack_down": (0,8), "attack_up": (1,8), "attack_left": (2,8), "attack_right": (3,8)
        },
        "death_animations": {
            "death": (0,8) 
        },
        "idle_frames_source_anim": "walk_down",
        "movement_speed_duration": GRID_MOVE_DURATION,
        "chase_speed_duration": GRID_MOVE_DURATION * 0.8, # Faster when chasing
        "animation_playback_speed": ANIMATION_SPEED,
        "health": 1,
        "detection_range": 3,
        "attack_range": 2,
        "attack_interval": 1.5, # Time between attacks
        "attack_duration": 0.8, # How long the attack animation plays
        "death_duration": 1.5
    },
    "orc2": {
        "sprite_sheet_path": "./assets/NPC/Orc/orc1_walk_full.png",
        "attack_sprite_sheet_path": "./assets/NPC/Orc/orc1_attack_full.png", 
        "death_sprite_sheet_path": "./assets/NPC/Orc/orc1_death_full.png", 
        "orig_frame_width": 63, "orig_frame_height": 64, 
        "attack_frame_width": 63, "attack_frame_height": 64,
        "death_frame_width": 63, "death_frame_height": 64,  
        "scale_factor": 2.4, "y_draw_offset": 50,
        "animations": { "walk_down": (0, 6), "walk_up": (1, 6), "walk_left": (2, 6), "walk_right": (3, 6) },
        "attack_animations": {
            "attack_down": (0,8), "attack_up": (1,8), "attack_left": (2,8), "attack_right": (3,8)
        },
        "death_animations": {
            "death": (0,8) #
        },
        "idle_frames_source_anim": "walk_down",
        "movement_speed_duration": GRID_MOVE_DURATION,
        "chase_speed_duration": GRID_MOVE_DURATION * 0.8,
        "animation_playback_speed": ANIMATION_SPEED,
        "health": 1,
        "detection_range": 2,
        "attack_range": 1,
        "attack_interval": 2.5,
        "attack_duration": 1.0,
        "death_duration": 1.5
    },
    "demon": {
        "sprite_sheet_path": "./assets/NPC/Bird/FLYING.png",
        "attack_sprite_sheet_path": "./assets/NPC/Bird/ATTACK.png", 
        "death_sprite_sheet_path": "./assets/NPC/Bird/DEATH.png",  #
        "orig_frame_width": 78, "orig_frame_height": 64,
        "attack_frame_width":79 , "attack_frame_height": 69, # <<< FILL THIS IN
        "death_frame_width": 340, "death_frame_height": 300,   # <<< FILL THIS IN
        "scale_factor": 1.5, "y_draw_offset": 0,
        "animations": {"fly": (0, 4)},
        "attack_animations": { "attack": (0,8) }, # <<< FILL (row, num_frames)
        "death_animations": { "death": (0,3) },   # <<< FILL (row, num_frames)
        "idle_frames_source_anim": "fly",
        "movement_speed_duration": GRID_MOVE_DURATION * 0.8,
        "chase_speed_duration": GRID_MOVE_DURATION * 0.7, # Very fast when chasing
        "animation_playback_speed": ANIMATION_SPEED * 0.8,
        "fly_over_obstacle_chance": 0.7,
        "fly_height_offset": int(GRID_SIZE * 0.6),
        "health": 1,
        "detection_range": 5,
        "attack_range": 1,
        "attack_interval": 2.0,
        "attack_duration": 0.7,
        "death_duration": 1.0
    }
}

class NPC:
    def __init__(self, initial_grid_x, initial_grid_y, maze, npc_type="orc"):
        self.grid_x, self.grid_y = initial_grid_x, initial_grid_y
        self.maze, self.npc_type = maze, npc_type
        self.config = NPC_CONFIGS[npc_type]

        self.target_npc_width = int(self.config["orig_frame_width"] * self.config["scale_factor"])
        self.target_npc_height = int(self.config["orig_frame_height"] * self.config["scale_factor"])

        self.animations = {}
        self.idle_image_base = None
        self.load_sprites()

        self.current_base_image = self.idle_image_base or pygame.Surface((self.target_npc_width, self.target_npc_height), pygame.SRCALPHA)
        if not self.idle_image_base: self.current_base_image.fill((255, 0, 255, 150))

        self.facing_direction = random.choice(['up', 'down', 'left', 'right'])
        self.sprite_flipped = False

        self.is_moving_animation_active, self.is_grid_moving = False, False
        self.move_start_screen_x, self.move_start_screen_y = 0.0, 0.0
        self.target_screen_x, self.target_screen_y = 0.0, 0.0
        self.current_screen_x, self.current_screen_y = 0.0, 0.0
        self.move_timer = 0.0
        self.grid_move_duration = self.config["movement_speed_duration"]

        self.anim_frame_index, self.anim_timer = 0, 0.0
        self.animation_playback_speed = self.config["animation_playback_speed"]

        # --- REVISED FSM ---
        self.fsm_state = 'idle' # idle, choosing_move, moving, chasing, attacking, dead
        self.fsm_timer = random.uniform(1.5, 4.0)
        self.current_planned_dx, self.current_planned_dy = 0, 0
        self.steps_to_take, self.blocked_attempts = 0, 0

        # --- NEW Attributes ---
        self.health = self.config["health"]
        self.is_attacking, self.attack_timer, self.attack_cooldown = False, 0.0, 0.0
        self.is_dead, self.death_timer = False, 0.0
        self.is_flying_high = False

        initial_target_x, initial_target_y = self._calculate_target_screen_pos(self.grid_x, self.grid_y)
        self.current_screen_x, self.current_screen_y = initial_target_x, initial_target_y
        self.target_screen_x, self.target_screen_y = initial_target_x, initial_target_y
        self._update_idle_image_and_flip_status()

    def _load_sprite_logic(self, path, anim_dict, w, h, target_w, target_h):
        if not path: return
        try:
            sheet = pygame.image.load(path).convert_alpha()
            for anim, (row, frames_n) in anim_dict.items():
                if frames_n == 0: continue
                frames = []
                for i in range(frames_n):
                    rect = pygame.Rect(i * w, row * h, w, h)
                    frame = pygame.transform.scale(sheet.subsurface(rect), (target_w, target_h))
                    frames.append(frame)
                self.animations[anim] = frames
        except Exception as e:
            print(f"ERROR loading NPC sprite from '{path}' for '{self.npc_type}': {e}")


    def load_sprites(self):
        # Load walk/fly sprites
        self._load_sprite_logic(self.config["sprite_sheet_path"], self.config["animations"], 
                                self.config["orig_frame_width"], self.config["orig_frame_height"],
                                self.target_npc_width, self.target_npc_height)
        # Load attack sprites
        self._load_sprite_logic(self.config["attack_sprite_sheet_path"], self.config["attack_animations"],
                                self.config["attack_frame_width"], self.config["attack_frame_height"],
                                int(self.config["attack_frame_width"]*self.config["scale_factor"]), 
                                int(self.config["attack_frame_height"]*self.config["scale_factor"]))
        # Load death sprites
        self._load_sprite_logic(self.config["death_sprite_sheet_path"], self.config["death_animations"],
                                self.config["death_frame_width"], self.config["death_frame_height"],
                                int(self.config["death_frame_width"]*self.config["scale_factor"]),
                                int(self.config["death_frame_height"]*self.config["scale_factor"]))

        idle_src = self.config.get("idle_frames_source_anim")
        if idle_src and idle_src in self.animations and self.animations[idle_src]:
            self.idle_image_base = self.animations[idle_src][0]
        elif self.animations:
            self.idle_image_base = next(iter(self.animations.values()))[0]

        if self.idle_image_base is None: self.idle_image_base = pygame.Surface((self.target_npc_width, self.target_npc_height), pygame.SRCALPHA)
        for anim_key in list(self.config["animations"].keys()) + list(self.config["attack_animations"].keys()) + list(self.config["death_animations"].keys()):
            if anim_key not in self.animations: self.animations[anim_key] = [self.idle_image_base]
            
    def take_damage(self, amount):
        if self.is_dead: return
        self.health -= amount
        print(f"{self.npc_type} took damage, health is now {self.health}")
        if self.health <= 0:
            self.health = 0
            self.fsm_state = 'dead'
            self.is_dead = True
            self.death_timer = 0.0
            self.anim_frame_index = 0
            self.is_grid_moving = False
            self.is_attacking = False
            print(f"{self.npc_type} has been slain.")


    def _calculate_target_screen_pos(self, grid_x, grid_y):
        base_x = grid_x * GRID_SIZE 
        base_y = grid_y * STAGGER_HEIGHT_PER_ROW 
        screen_x = base_x + (GRID_SIZE - self.target_npc_width) / 2.0
        feet_anchor_y_on_grid_surface = base_y + STAGGER_HEIGHT_PER_ROW
        screen_y = feet_anchor_y_on_grid_surface - self.target_npc_height 
        screen_y += self.config.get("y_draw_offset", 0) 
        if self.npc_type == "demon" and self.is_flying_high: 
            screen_y -= self.config.get("fly_height_offset", int(GRID_SIZE * 0.6)) 
        return screen_x, screen_y+15

    def _update_idle_image_and_flip_status(self):
        if self.is_attacking or self.is_dead: return
        anim_key = "walk_" + self.facing_direction if self.npc_type != "demon" else "fly"
        if anim_key in self.animations and self.animations[anim_key]:
            self.current_base_image = self.animations[anim_key][0]
        else:
            self.current_base_image = self.idle_image_base 
        
        self.sprite_flipped = (self.npc_type == "demon" and self.facing_direction == "right")

    def start_grid_move(self, dx, dy, player, other_npcs, allow_obstacle_fly=False):
        if self.is_grid_moving or self.is_attacking or self.is_dead: return False
        next_grid_x, next_grid_y = self.grid_x + dx, self.grid_y + dy

        if not (0 <= next_grid_y < self.maze.height and 0 <= next_grid_x < self.maze.width): return False 

        target_tile = self.maze.grid[next_grid_y][next_grid_x]
        can_move = self.maze.is_walkable(next_grid_x, next_grid_y)
        
        if not can_move and self.npc_type == "demon" and allow_obstacle_fly and isinstance(target_tile, (RockCube, WoodCube)):
            can_move = True
            self.is_flying_high = True
        elif can_move and self.is_flying_high:
            self.is_flying_high = False

        if not can_move: return False 
        if player and next_grid_x == player.grid_x and next_grid_y == player.grid_y: return False
        for npc in other_npcs:
            if next_grid_x == npc.grid_x and next_grid_y == npc.grid_y and not npc.is_dead: return False
        
        self.grid_x, self.grid_y = next_grid_x, next_grid_y
        self.move_start_screen_x, self.move_start_screen_y = self.current_screen_x, self.current_screen_y
        self.target_screen_x, self.target_screen_y = self._calculate_target_screen_pos(self.grid_x, self.grid_y) 
        self.move_timer, self.is_grid_moving, self.is_moving_animation_active = 0.0, True, True
        self.anim_frame_index, self.anim_timer = 0, 0.0

        if dx > 0: self.facing_direction = "right"
        elif dx < 0: self.facing_direction = "left"
        elif dy > 0: self.facing_direction = "down"
        elif dy < 0: self.facing_direction = "up"
        
        self.sprite_flipped = (self.npc_type == "demon" and self.facing_direction == "right")
        return True
        
    def check_player_detection(self, player):
        if self.is_dead: return False
        dist_x, dist_y = player.grid_x - self.grid_x, player.grid_y - self.grid_y
        
        dir_map = {"left": (-1, 0), "right": (1, 0), "up": (0, -1), "down": (0, 1)}
        facing_dx, facing_dy = dir_map[self.facing_direction]

        # Check if player is in a line in front of NPC
        if facing_dx != 0 and dist_y == 0 and math.copysign(1, dist_x) == facing_dx:
            return abs(dist_x) <= self.config["detection_range"]
        if facing_dy != 0 and dist_x == 0 and math.copysign(1, dist_y) == facing_dy:
            return abs(dist_y) <= self.config["detection_range"]
            
        return False

    def update_fsm(self, dt, player, other_npcs):
        if self.is_dead or self.is_attacking: return

        # High-priority state changes
        player_detected = self.check_player_detection(player)
        dist_to_player = math.hypot(player.grid_x - self.grid_x, player.grid_y - self.grid_y)

        if player_detected and self.fsm_state != 'chasing':
            print(f"{self.npc_type} detected player! Switching to chase mode.")
            self.fsm_state = 'chasing'
        elif not player_detected and self.fsm_state == 'chasing':
            print(f"{self.npc_type} lost player. Returning to normal behavior.")
            self.fsm_state = 'idle'
            self.fsm_timer = random.uniform(1.0, 2.0)
            self.grid_move_duration = self.config["movement_speed_duration"]

        # Handle states
        self.fsm_timer -= dt
        
        if self.fsm_state == 'chasing':
            self.grid_move_duration = self.config["chase_speed_duration"]
            if dist_to_player <= self.config["attack_range"] and self.attack_cooldown <= 0:
                self.fsm_state = 'attacking'
                self.is_attacking = True
                self.attack_timer = 0.0
                self.anim_frame_index = 0
                print(f"{self.npc_type} is attacking player!")
            elif not self.is_grid_moving:
                # Simple chase logic: move towards player
                dx, dy = player.grid_x - self.grid_x, player.grid_y - self.grid_y
                if abs(dx) > abs(dy):
                    self.start_grid_move(int(math.copysign(1, dx)), 0, player, other_npcs)
                else:
                    self.start_grid_move(0, int(math.copysign(1, dy)), player, other_npcs)

        elif self.fsm_state == 'idle':
            self.grid_move_duration = self.config["movement_speed_duration"]
            if self.fsm_timer <= 0 or self.blocked_attempts > 2:
                self.blocked_attempts = 0
                self.fsm_state = 'choosing_move'
        
        elif self.fsm_state == 'choosing_move':
            directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
            random.shuffle(directions)
            moved = False
            for dx, dy in directions:
                if self.start_grid_move(dx, dy, player, other_npcs):
                    self.fsm_state = 'moving'
                    self.steps_to_take = random.randint(0, 2)
                    moved = True
                    break 
            if not moved:
                self.fsm_state = 'idle'
                self.fsm_timer = random.uniform(0.5, 1.5)
                self.blocked_attempts +=1
        
        elif self.fsm_state == 'moving':
            if not self.is_grid_moving:
                if self.steps_to_take > 0:
                    self.steps_to_take -= 1
                    if not self.start_grid_move(self.current_planned_dx, self.current_planned_dy, player, other_npcs):
                        self.fsm_state = 'idle'
                        self.fsm_timer = random.uniform(1.0, 2.0)
                else:
                    self.fsm_state = 'idle'
                    self.fsm_timer = random.uniform(1.5, 4.0)

    def update_animation(self, dt):
        anim_key = ""
        current_anim_frames = []
        
        if self.is_dead:
            anim_key = "death"
        elif self.is_attacking:
            if self.npc_type == 'demon': anim_key = "attack"
            else: anim_key = "attack_" + self.facing_direction
        elif self.is_moving_animation_active:
            if self.npc_type == 'demon': anim_key = "fly"
            else: anim_key = "walk_" + self.facing_direction
        
        if anim_key and anim_key in self.animations:
            current_anim_frames = self.animations[anim_key]
        
        if not current_anim_frames:
            self._update_idle_image_and_flip_status()
            return
        
        self.anim_timer += dt
        if self.anim_timer >= self.animation_playback_speed:
            self.anim_timer -= self.animation_playback_speed
            # Don't loop death/attack animations
            if not (self.is_dead or self.is_attacking) or self.anim_frame_index < len(current_anim_frames) - 1:
                self.anim_frame_index = (self.anim_frame_index + 1) % len(current_anim_frames)
        
        self.current_base_image = current_anim_frames[self.anim_frame_index]

    def update(self, dt, player, other_npcs):
        if self.attack_cooldown > 0: self.attack_cooldown -= dt
        
        if self.is_dead:
            self.death_timer += dt
            self.update_animation(dt)
            # When death is finished, it will be removed by the main loop
            return

        if self.is_attacking:
            self.attack_timer += dt
            # Simple logic: damage applied halfway through attack animation
            if self.attack_timer >= self.config["attack_duration"] / 2 and self.attack_timer - dt < self.config["attack_duration"] / 2:
                 dist_to_player = math.hypot(player.grid_x - self.grid_x, player.grid_y - self.grid_y)
                 if dist_to_player <= self.config["attack_range"]:
                     player.take_damage(1) # Deal 1 damage
            
            if self.attack_timer >= self.config["attack_duration"]:
                self.is_attacking = False
                self.fsm_state = 'chasing' # Go back to chasing after attack
                self.attack_cooldown = self.config["attack_interval"]
                self.anim_frame_index = 0
            self.update_animation(dt)
            return

        if not self.is_grid_moving:
            self.update_fsm(dt, player, other_npcs)

        if self.is_grid_moving:
            self.move_timer += dt
            progress = self.move_timer / self.grid_move_duration
            if progress >= 1.0:
                progress = 1.0
                self.is_grid_moving = False
                if not (self.fsm_state == 'moving' and self.steps_to_take > 0):
                    self.is_moving_animation_active = False
            
            self.current_screen_x = self.move_start_screen_x + (self.target_screen_x - self.move_start_screen_x) * progress
            self.current_screen_y = self.move_start_screen_y + (self.target_screen_y - self.move_start_screen_y) * progress
            
            if not self.is_grid_moving:
                self.current_screen_x, self.current_screen_y = self.target_screen_x, self.target_screen_y
                if self.npc_type == "demon":
                    self.target_screen_x, self.target_screen_y = self._calculate_target_screen_pos(self.grid_x, self.grid_y)
                    self.current_screen_x, self.current_screen_y = self.target_screen_x, self.target_screen_y

        self.update_animation(dt)

    def draw(self, surface, maze_offset_x, maze_offset_y):
        image_to_blit = self.current_base_image
        if not image_to_blit: return

        if self.sprite_flipped:
            image_to_blit = pygame.transform.flip(image_to_blit, True, False)
            
        w, h = image_to_blit.get_size()
        draw_x = self.current_screen_x + maze_offset_x - (w - self.target_npc_width)/2
        draw_y = self.current_screen_y + maze_offset_y - (h - self.target_npc_height)

        surface.blit(image_to_blit, (draw_x, draw_y))
