# npc.py
import pygame
import random
import os # For path joining if needed, though current config uses direct paths
from cube import FloorCube, RockCube, WoodCube # For checking tile types

# Constants
GRID_SIZE = 80
STAGGER_HEIGHT_PER_ROW = int(GRID_SIZE * 0.8)
ANIMATION_SPEED = 0.1 # Default animation speed for NPCs
GRID_MOVE_DURATION = 0.3 # Default move duration for NPCs

NPC_CONFIGS = {
    "orc": {
        "sprite_sheet_path": "./assets/NPC/Orc/orc3_walk/orc3_walk_full.png",
        "orig_frame_width": 63, 
        "orig_frame_height": 64, 
        "scale_factor": 2.4,
        "y_draw_offset": 50, # Visual offset, pushes sprite down
        "animations": { 
            "walk_down": (0, 6), # row_index, num_frames
            "walk_up": (1, 6), 
            "walk_left": (2, 6),
            "walk_right": (3, 6)  
        },
        "idle_frames_source_anim": "walk_down", # Which animation to take the first frame from for idle
        "movement_speed_duration": GRID_MOVE_DURATION, # Time to move one grid cell
        "animation_playback_speed": ANIMATION_SPEED # Speed of frame changes
    },
    # --- FIX: Added new configuration for Orc2 ---
    "orc2": {
        # NOTE: You will need to create this asset path and place your new sprite sheet here.
        "sprite_sheet_path": "./assets/NPC/Orc/orc1_walk_full.png",
        "orig_frame_width": 63, 
        "orig_frame_height": 64, 
        "scale_factor": 2.4,
        "y_draw_offset": 50,
        "animations": { 
            "walk_down": (0, 6),
            "walk_up": (1, 6), 
            "walk_left": (2, 6),
            "walk_right": (3, 6)  
        },
        "idle_frames_source_anim": "walk_down",
        "movement_speed_duration": GRID_MOVE_DURATION,
        "animation_playback_speed": ANIMATION_SPEED
    },
    "demon": {
        "sprite_sheet_path": "./assets/NPC/Bird/FLYING.png",
        "orig_frame_width": 78, 
        "orig_frame_height": 64, 
        "scale_factor": 1.5,
        "y_draw_offset": 0, # No additional Y offset unless specified
        "animations": {"fly": (0, 4)}, # Assumes a single row for flying, all directions use this
        "idle_frames_source_anim": "fly",
        "movement_speed_duration": GRID_MOVE_DURATION * 0.8, 
        "animation_playback_speed": ANIMATION_SPEED * 0.8,
        "fly_over_obstacle_chance": 0.7,
        "fly_height_offset": int(GRID_SIZE * 0.6) # Visual offset when flying high, pulls sprite up
    }
}

class NPC:
    def __init__(self, initial_grid_x, initial_grid_y, maze, npc_type="orc"):
        self.grid_x = initial_grid_x
        self.grid_y = initial_grid_y
        self.maze = maze
        self.npc_type = npc_type
        self.config = NPC_CONFIGS[npc_type]

        self.target_npc_width = int(self.config["orig_frame_width"] * self.config["scale_factor"])
        self.target_npc_height = int(self.config["orig_frame_height"] * self.config["scale_factor"])

        self.animations = {} # Stores lists of Surface objects for each animation
        self.idle_image_base = None # The base image for idle state (usually first frame of an animation)
        self.load_sprites()

        self.current_base_image = self.idle_image_base # Image before potential flipping
        if self.current_base_image is None: 
            self.current_base_image = pygame.Surface((self.target_npc_width, self.target_npc_height), pygame.SRCALPHA)
            self.current_base_image.fill((255, 0, 255, 150)) # Magenta fallback

        self.facing_direction = "down" # 'up', 'down', 'left', 'right'
        self.sprite_flipped = False # True if current_base_image should be flipped horizontally

        self.is_moving_animation_active = False # True when walk/fly animation should play
        self.is_grid_moving = False # True when interpolating screen position

        self.move_start_screen_x = 0.0
        self.move_start_screen_y = 0.0
        self.target_screen_x = 0.0
        self.target_screen_y = 0.0
        self.current_screen_x = 0.0
        self.current_screen_y = 0.0
        self.move_timer = 0.0
        self.grid_move_duration = self.config["movement_speed_duration"]

        self.anim_frame_index = 0
        self.anim_timer = 0.0
        self.animation_playback_speed = self.config["animation_playback_speed"]

        # FSM for basic AI
        self.fsm_state = 'idle'
        self.fsm_timer = random.uniform(1.5, 4.0) # Time in current state
        self.current_planned_dx = 0 # For multi-step moves
        self.current_planned_dy = 0
        self.steps_to_take = 0 # How many more steps in current planned move
        self.blocked_attempts = 0 # To prevent getting stuck choosing same blocked move

        self.is_flying_high = False # Specific to demon

        # Initialize screen position
        initial_target_x, initial_target_y = self._calculate_target_screen_pos(self.grid_x, self.grid_y)
        self.current_screen_x = initial_target_x
        self.current_screen_y = initial_target_y
        self.target_screen_x = initial_target_x
        self.target_screen_y = initial_target_y
        self._update_idle_image_and_flip_status() # Set initial idle image and flip

    def load_sprites(self):
        try:
            sprite_sheet_path = self.config["sprite_sheet_path"]
            sprite_sheet = pygame.image.load(sprite_sheet_path).convert_alpha()
            
            for anim_name, (row_idx, num_frames) in self.config["animations"].items():
                frames = []
                for i in range(num_frames):
                    frame_rect = pygame.Rect(
                        i * self.config["orig_frame_width"], 
                        row_idx * self.config["orig_frame_height"], 
                        self.config["orig_frame_width"], 
                        self.config["orig_frame_height"]
                    )
                    frame_surface = sprite_sheet.subsurface(frame_rect)
                    scaled_frame = pygame.transform.scale(frame_surface, (self.target_npc_width, self.target_npc_height))
                    frames.append(scaled_frame)
                self.animations[anim_name] = frames
            
            idle_source_anim_key = self.config.get("idle_frames_source_anim")
            if idle_source_anim_key and idle_source_anim_key in self.animations and self.animations[idle_source_anim_key]:
                self.idle_image_base = self.animations[idle_source_anim_key][0] # Default idle is first frame of this anim
            elif self.animations: 
                first_anim_key = next(iter(self.animations))
                if self.animations[first_anim_key]:
                    self.idle_image_base = self.animations[first_anim_key][0]

        except pygame.error as e:
            print(f"ERROR loading NPC sprites for '{self.npc_type}' from '{sprite_sheet_path}': {e}")
        
        if self.idle_image_base is None: 
            self.idle_image_base = pygame.Surface((self.target_npc_width, self.target_npc_height), pygame.SRCALPHA)
            self.idle_image_base.fill((255,0,0,100)) 
        
        for anim_name_key in self.config["animations"].keys(): 
            if anim_name_key not in self.animations or not self.animations[anim_name_key]: 
                self.animations[anim_name_key] = [self.idle_image_base] # Ensure all anims have at least one frame

    def _calculate_target_screen_pos(self, grid_x, grid_y):
        base_x = grid_x * GRID_SIZE 
        base_y = grid_y * STAGGER_HEIGHT_PER_ROW 

        screen_x = base_x + (GRID_SIZE - self.target_npc_width) / 2.0
        
        feet_anchor_y_on_grid_surface = base_y + STAGGER_HEIGHT_PER_ROW
        screen_y = feet_anchor_y_on_grid_surface - self.target_npc_height 

        y_offset_from_config = self.config.get("y_draw_offset", 0) 
        screen_y += y_offset_from_config 

        if self.npc_type == "demon" and self.is_flying_high: 
            screen_y -= self.config.get("fly_height_offset", int(GRID_SIZE * 0.6)) 
        return screen_x, screen_y+15

    def _update_idle_image_and_flip_status(self):
        if self.npc_type == "orc" or self.npc_type == "orc2":
            anim_key = "walk_" + self.facing_direction
            if anim_key in self.animations and self.animations[anim_key]:
                self.current_base_image = self.animations[anim_key][0]
            else:
                self.current_base_image = self.idle_image_base 
            self.sprite_flipped = False
        
        elif self.npc_type == "demon":
            if "fly" in self.animations and self.animations["fly"]:
                self.current_base_image = self.animations["fly"][0]
            else:
                self.current_base_image = self.idle_image_base
            self.sprite_flipped = (self.facing_direction == "right")
        else:
            self.current_base_image = self.idle_image_base
            self.sprite_flipped = False

        if self.current_base_image is None:
             self.current_base_image = pygame.Surface((self.target_npc_width, self.target_npc_height), pygame.SRCALPHA); self.current_base_image.fill((255,0,255,100))


    def start_grid_move(self, dx, dy, player, other_npcs, allow_obstacle_fly=False):
        if self.is_grid_moving: return False

        next_grid_x, next_grid_y = self.grid_x + dx, self.grid_y + dy

        if not (0 <= next_grid_y < self.maze.height and 0 <= next_grid_x < self.maze.width):
            return False 

        target_tile_is_floor = self.maze.is_walkable(next_grid_x, next_grid_y) 
        target_tile_instance = self.maze.grid[next_grid_y][next_grid_x]

        can_move_to_target = False
        if target_tile_is_floor:
            can_move_to_target = True
            if self.npc_type == "demon" and self.is_flying_high:
                self.is_flying_high = False 
        elif self.npc_type == "demon" and allow_obstacle_fly and isinstance(target_tile_instance, (RockCube, WoodCube)): 
            can_move_to_target = True
            self.is_flying_high = True
        
        if not can_move_to_target:
            return False 

        if player and next_grid_x == player.grid_x and next_grid_y == player.grid_y:
            return False
        for other_npc in other_npcs:
            if next_grid_x == other_npc.grid_x and next_grid_y == other_npc.grid_y:
                return False
        
        self.grid_x, self.grid_y = next_grid_x, next_grid_y
        
        self.move_start_screen_x, self.move_start_screen_y = self.current_screen_x, self.current_screen_y
        self.target_screen_x, self.target_screen_y = self._calculate_target_screen_pos(self.grid_x, self.grid_y) 
        
        self.move_timer = 0.0
        self.is_grid_moving = True
        self.is_moving_animation_active = True
        self.anim_frame_index = 0
        self.anim_timer = 0.0

        if dx > 0: self.facing_direction = "right"
        elif dx < 0: self.facing_direction = "left"
        elif dy > 0: self.facing_direction = "down"
        elif dy < 0: self.facing_direction = "up"  
        
        if self.npc_type == "demon":
            self.sprite_flipped = (self.facing_direction == "right")
        else:
            self.sprite_flipped = False
        
        return True

    def update_fsm(self, dt, player, other_npcs):
        self.fsm_timer -= dt
        if self.fsm_state == 'idle':
            if self.fsm_timer <= 0 or self.blocked_attempts > 2:
                self.blocked_attempts = 0
                self.fsm_state = 'choosing_move'
        
        elif self.fsm_state == 'choosing_move':
            directions = [(0, 1, "down"), (0, -1, "up"), (1, 0, "right"), (-1, 0, "left")]
            random.shuffle(directions)
            moved_successfully = False
            for dx, dy, dir_name in directions:
                self.current_planned_dx, self.current_planned_dy = dx, dy
                
                attempt_fly_over = False
                if self.npc_type == "demon": 
                    potential_next_x, potential_next_y = self.grid_x + dx, self.grid_y + dy
                    if 0 <= potential_next_y < self.maze.height and 0 <= potential_next_x < self.maze.width:
                        tile = self.maze.grid[potential_next_y][potential_next_x]
                        if isinstance(tile, (RockCube, WoodCube)) and random.random() < self.config.get("fly_over_obstacle_chance", 0.7): 
                            attempt_fly_over = True
                
                if self.start_grid_move(dx, dy, player, other_npcs, allow_obstacle_fly=attempt_fly_over):
                    self.fsm_state = 'moving'
                    self.steps_to_take = random.randint(0, 2)
                    moved_successfully = True
                    break 
            
            if not moved_successfully:
                self.fsm_state = 'idle'
                self.fsm_timer = random.uniform(0.5, 1.5)
                self.blocked_attempts +=1
        
        elif self.fsm_state == 'moving':
            if not self.is_grid_moving:
                if self.steps_to_take > 0:
                    self.steps_to_take -= 1
                    
                    attempt_fly_over_continue = False
                    if self.npc_type == "demon" and self.is_flying_high:
                         potential_next_x, potential_next_y = self.grid_x + self.current_planned_dx, self.grid_y + self.current_planned_dy
                         if 0 <= potential_next_y < self.maze.height and 0 <= potential_next_x < self.maze.width:
                            tile = self.maze.grid[potential_next_y][potential_next_x]
                            if isinstance(tile, (RockCube, WoodCube)): 
                                attempt_fly_over_continue = True 
                    
                    if not self.start_grid_move(self.current_planned_dx, self.current_planned_dy, player, other_npcs, allow_obstacle_fly=attempt_fly_over_continue):
                        self.fsm_state = 'idle'
                        self.fsm_timer = random.uniform(1.0, 2.0)
                        self.blocked_attempts +=1 
                else:
                    self.fsm_state = 'idle'
                    self.fsm_timer = random.uniform(1.5, 4.0)

    def update_animation(self, dt):
        if not self.is_moving_animation_active:
            self._update_idle_image_and_flip_status()
            self.anim_frame_index = 0
            self.anim_timer = 0.0
            return

        current_anim_frames = []
        if self.npc_type == "orc" or self.npc_type == "orc2":
            anim_key = "walk_" + self.facing_direction
            current_anim_frames = self.animations.get(anim_key, [self.idle_image_base])
        elif self.npc_type == "demon":
            current_anim_frames = self.animations.get("fly", [self.idle_image_base])
        
        if not current_anim_frames:
            current_anim_frames = [self.idle_image_base]

        self.anim_timer += dt
        if self.anim_timer >= self.animation_playback_speed:
            self.anim_timer -= self.animation_playback_speed
            self.anim_frame_index = (self.anim_frame_index + 1) % len(current_anim_frames)
        
        self.current_base_image = current_anim_frames[self.anim_frame_index]

    def update(self, dt, player, other_npcs):
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
                self.current_screen_x = self.target_screen_x
                self.current_screen_y = self.target_screen_y
                
                if self.npc_type == "demon":
                    self.target_screen_x, self.target_screen_y = self._calculate_target_screen_pos(self.grid_x, self.grid_y)
                    self.current_screen_x = self.target_screen_x
                    self.current_screen_y = self.target_screen_y

        self.update_animation(dt)

    def draw(self, surface, maze_offset_x, maze_offset_y):
        image_to_blit = self.current_base_image 
        if not image_to_blit:
            image_to_blit = pygame.Surface((self.target_npc_width, self.target_npc_height), pygame.SRCALPHA)
            image_to_blit.fill((0,0,255,100))

        if self.sprite_flipped:
            image_to_blit = pygame.transform.flip(image_to_blit, True, False)
            
        draw_x = self.current_screen_x + maze_offset_x
        draw_y = self.current_screen_y + maze_offset_y
        surface.blit(image_to_blit, (draw_x, draw_y))