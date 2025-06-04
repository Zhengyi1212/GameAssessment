# npc.py
import pygame
import random
from cube import FloorCube, RockCube, WoodCube # For checking tile types

# Constants
GRID_SIZE = 80
STAGGER_HEIGHT_PER_ROW = int(GRID_SIZE * 0.8)
ANIMATION_SPEED = 0.1
GRID_MOVE_DURATION = 0.3

NPC_CONFIGS = {
    "orc": {
        "sprite_sheet_path": "./assets/NPC/Orc/orc3_walk/orc3_walk_full.png",
        "orig_frame_width": 76, 
        "orig_frame_height": 64, 
        "scale_factor": 2.4,
        "y_draw_offset": 50, 
        "animations": { 
            "walk_down": (0, 5), 
            "walk_up": (1, 5), 
            "walk_left": (2, 5),
            "walk_right": (3, 5)  
        },
        "idle_frames_source": "walk_down",
        "movement_speed": GRID_MOVE_DURATION,
        "animation_speed": ANIMATION_SPEED
    },
    "demon": {
        "sprite_sheet_path": "./assets/NPC/Bird/FLYING.png",
        "orig_frame_width": 64, "orig_frame_height": 64, "scale_factor": 1.6,
        "animations": {"fly": (0, 4)},
        "idle_frames_source": "fly", "movement_speed": GRID_MOVE_DURATION * 0.8, "animation_speed": ANIMATION_SPEED * 0.8,
        "fly_over_obstacle_chance": 0.7,
        "fly_height_offset": int(GRID_SIZE * 0.6)
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

        self.animations = {}
        self.idle_image = None 
        self.load_sprites()

        self.current_base_image = self.idle_image 
        if self.current_base_image is None: 
            self.current_base_image = pygame.Surface((self.target_npc_width, self.target_npc_height), pygame.SRCALPHA)
            self.current_base_image.fill((255, 0, 255, 150)) 
            print(f"CRITICAL WARNING: NPC '{npc_type}' idle_image (and thus current_base_image) is None. Using fallback.")

        self.facing_direction = "down"
        self.sprite_flipped = False 

        self.is_moving_animation = False
        self.is_grid_moving = False

        self.move_start_screen_x = 0.0; self.move_start_screen_y = 0.0
        self.target_screen_x = 0.0; self.target_screen_y = 0.0
        self.current_screen_x = 0.0; self.current_screen_y = 0.0
        self.move_timer = 0.0
        self.grid_move_duration = self.config["movement_speed"]

        self.anim_frame_index = 0; self.anim_timer = 0
        self.animation_speed = self.config["animation_speed"]

        self.fsm_state = 'idle'; self.fsm_timer = random.uniform(1.5, 4.0)
        self.current_planned_dx = 0; self.current_planned_dy = 0
        self.steps_to_take = 0; self.blocked_attempts = 0

        self.is_flying_high = False

        initial_target_x, initial_target_y = self._calculate_target_screen_pos(self.grid_x, self.grid_y)
        self.current_screen_x = initial_target_x; self.current_screen_y = initial_target_y
        self.target_screen_x = initial_target_x; self.target_screen_y = initial_target_y

    def load_sprites(self):
        try:
            sprite_sheet = pygame.image.load(self.config["sprite_sheet_path"]).convert_alpha()
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
            
            idle_source_anim = self.config["idle_frames_source"]
            if idle_source_anim and idle_source_anim in self.animations and self.animations[idle_source_anim]:
                self.idle_image = self.animations[idle_source_anim][0] 
            elif self.animations: 
                self.idle_image = self.animations[next(iter(self.animations))][0]
        except pygame.error as e:
            print(f"ERROR loading NPC sprites for '{self.npc_type}': {e}")
            if self.idle_image is None: 
                self.idle_image = pygame.Surface((self.target_npc_width, self.target_npc_height), pygame.SRCALPHA)
                self.idle_image.fill((255,0,0,100)) 
            for anim_name_key in self.config["animations"].keys(): 
                if anim_name_key not in self.animations or not self.animations[anim_name_key]: 
                    self.animations[anim_name_key] = [self.idle_image]


    def _calculate_target_screen_pos(self, grid_x, grid_y):
        base_x = grid_x * GRID_SIZE #
        base_y = grid_y * STAGGER_HEIGHT_PER_ROW #
        screen_x = base_x + (GRID_SIZE - self.target_npc_width) / 2.0 #
        feet_anchor_y_offset = int(GRID_SIZE * 1.1) #
        screen_y = (base_y + feet_anchor_y_offset) - self.target_npc_height #

        # Apply type-specific y_draw_offset from config
        # Positive values shift the NPC downwards, negative values shift upwards.
        y_offset_from_config = self.config.get("y_draw_offset", 0) #
        screen_y += y_offset_from_config #

        if self.npc_type == "demon" and self.is_flying_high: #
            screen_y -= self.config.get("fly_height_offset", int(GRID_SIZE * 0.6)) #
        return screen_x, screen_y #

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
        elif self.npc_type == "demon" and allow_obstacle_fly and isinstance(target_tile_instance, (RockCube, WoodCube)): #
            can_move_to_target = True
            self.is_flying_high = True 
        
        if not can_move_to_target:
            return False 

        if player and next_grid_x == player.grid_x and next_grid_y == player.grid_y: return False
        for other_npc in other_npcs:
            if next_grid_x == other_npc.grid_x and next_grid_y == other_npc.grid_y: return False
        
        self.grid_x, self.grid_y = next_grid_x, next_grid_y
        self.move_start_screen_x, self.move_start_screen_y = self.current_screen_x, self.current_screen_y
        self.target_screen_x, self.target_screen_y = self._calculate_target_screen_pos(self.grid_x, self.grid_y) #
        
        self.move_timer = 0.0; self.is_grid_moving = True; self.is_moving_animation = True
        self.anim_frame_index = 0; self.anim_timer = 0

        if dx > 0: self.facing_direction = "right"; self.sprite_flipped = False
        elif dx < 0: self.facing_direction = "left"; self.sprite_flipped = True 
        elif dy > 0: self.facing_direction = "down"; self.sprite_flipped = False 
        elif dy < 0: self.facing_direction = "up"; self.sprite_flipped = False   
        
        if self.npc_type == "demon" and self.facing_direction not in ["left", "right"]:
             self.sprite_flipped = False

        return True

    def update_fsm(self, dt, player, other_npcs):
        self.fsm_timer -= dt
        if self.fsm_state == 'idle':
            if self.fsm_timer <= 0 or self.blocked_attempts > 2:
                self.blocked_attempts = 0; self.fsm_state = 'choosing_move'
        elif self.fsm_state == 'choosing_move':
            directions = [(0, 1, "down"), (0, -1, "up"), (1, 0, "right"), (-1, 0, "left")]
            random.shuffle(directions)
            moved_successfully = False
            for dx, dy, dir_name in directions:
                self.current_planned_dx, self.current_planned_dy = dx, dy
                
                attempt_fly_over = False
                if self.npc_type == "demon": #
                    potential_next_x, potential_next_y = self.grid_x + dx, self.grid_y + dy
                    if 0 <= potential_next_y < self.maze.height and 0 <= potential_next_x < self.maze.width:
                        tile = self.maze.grid[potential_next_y][potential_next_x]
                        if isinstance(tile, (RockCube, WoodCube)) and random.random() < self.config.get("fly_over_obstacle_chance", 0.7): #
                            attempt_fly_over = True
                
                if self.start_grid_move(dx, dy, player, other_npcs, allow_obstacle_fly=attempt_fly_over):
                    self.fsm_state = 'moving'
                    self.steps_to_take = random.randint(0, 2)
                    moved_successfully = True; break
            
            if not moved_successfully:
                self.fsm_state = 'idle'; self.fsm_timer = random.uniform(0.5, 1.5); self.blocked_attempts +=1
        elif self.fsm_state == 'moving':
            if not self.is_grid_moving:
                if self.steps_to_take > 0:
                    self.steps_to_take -= 1
                    current_tile_is_floor = isinstance(self.maze.grid[self.grid_y][self.grid_x], FloorCube)
                    if self.npc_type == "demon" and not current_tile_is_floor and not self.is_flying_high:
                        self.is_flying_high = False 
                    
                    attempt_fly_over_continue = False
                    if self.npc_type == "demon" and self.is_flying_high: 
                         potential_next_x, potential_next_y = self.grid_x + self.current_planned_dx, self.grid_y + self.current_planned_dy
                         if 0 <= potential_next_y < self.maze.height and 0 <= potential_next_x < self.maze.width:
                            tile = self.maze.grid[potential_next_y][potential_next_x]
                            if isinstance(tile, (RockCube, WoodCube)): attempt_fly_over_continue = True #
                    
                    if not self.start_grid_move(self.current_planned_dx, self.current_planned_dy, player, other_npcs, allow_obstacle_fly=attempt_fly_over_continue):
                        self.fsm_state = 'idle'; self.fsm_timer = random.uniform(1.0, 2.0); self.blocked_attempts +=1
                else:
                    self.fsm_state = 'idle'; self.fsm_timer = random.uniform(1.5, 4.0)

    def update_animation(self, dt):
        anim_key_suffix = self.facing_direction
        current_anim_key = ""
        if self.npc_type == "orc": 
            current_anim_key = "walk_" + anim_key_suffix
        elif self.npc_type == "demon": 
            current_anim_key = "fly" 
        else: 
            current_anim_key = self.config["idle_frames_source"]

        active_animation_frames = self.animations.get(current_anim_key, [self.idle_image])

        if self.is_moving_animation:
            self.anim_timer += dt
            if self.anim_timer >= self.animation_speed:
                self.anim_timer -= self.animation_speed
                self.anim_frame_index = (self.anim_frame_index + 1) % len(active_animation_frames)
            self.current_base_image = active_animation_frames[self.anim_frame_index]
        else: 
            self.current_base_image = active_animation_frames[0] if active_animation_frames else self.idle_image
            self.anim_frame_index = 0
            self.anim_timer = 0
        
    def update(self, dt, player, other_npcs):
        if not self.is_grid_moving:
            self.update_fsm(dt, player, other_npcs)

        if self.is_grid_moving:
            self.move_timer += dt
            progress = self.move_timer / self.grid_move_duration
            if progress >= 1.0:
                progress = 1.0; self.is_grid_moving = False
                if self.fsm_state != 'moving' or self.steps_to_take == 0: self.is_moving_animation = False
            
            self.current_screen_x = self.move_start_screen_x + (self.target_screen_x - self.move_start_screen_x) * progress
            self.current_screen_y = self.move_start_screen_y + (self.target_screen_y - self.move_start_screen_y) * progress
            
            if not self.is_grid_moving: 
                self.current_screen_x = self.target_screen_x
                self.current_screen_y = self.target_screen_y
                if self.npc_type == "demon": #
                    current_tile_is_floor = isinstance(self.maze.grid[self.grid_y][self.grid_x], FloorCube) #
                    if current_tile_is_floor and self.is_flying_high: #
                        self.is_flying_high = False #
                        self.target_screen_x, self.target_screen_y = self._calculate_target_screen_pos(self.grid_x, self.grid_y) #
                        self.current_screen_x, self.current_screen_y = self.target_screen_x, self.target_screen_y #
                    elif not current_tile_is_floor and not isinstance(self.maze.grid[self.grid_y][self.grid_x],(RockCube, WoodCube)) and self.is_flying_high: #
                        self.is_flying_high = False  #
                        self.target_screen_x, self.target_screen_y = self._calculate_target_screen_pos(self.grid_x, self.grid_y) #
                        self.current_screen_x, self.current_screen_y = self.target_screen_x, self.target_screen_y #
        self.update_animation(dt)

    def draw(self, surface, maze_offset_x, maze_offset_y):
        draw_y_pos = self.current_screen_y 

        image_to_blit = self.current_base_image 

        if self.current_base_image:
            if self.npc_type == "demon" and self.sprite_flipped: 
                image_to_blit = pygame.transform.flip(self.current_base_image, True, False)
            
            surface.blit(image_to_blit, (self.current_screen_x + maze_offset_x, draw_y_pos + maze_offset_y))
        else: 
            pygame.draw.rect(surface, (255,0,255, 150), 
                             (self.current_screen_x + maze_offset_x, draw_y_pos + maze_offset_y, 
                              self.target_npc_width, self.target_npc_height))

