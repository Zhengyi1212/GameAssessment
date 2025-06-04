# map_generator.py
import pygame
import random
from cube import FloorCube, WallCube, RockCube, WoodCube, GRID_SIZE
from player import Player,TARGET_PLAYER_HEIGHT
from npc import NPC # Import the new NPC class

FLOOR_BACKGROUND_COLOR = (46, 80, 93)
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 800
STAGGER_HEIGHT_PER_ROW = int(GRID_SIZE * 0.8)
MAX_NPCS = 5 # Maximum number of NPCs to spawn

class Maze:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.grid = self._generate_maze() # Generates cubes
        self.npcs = [] # List to store NPC objects
        self._spawn_npcs() # Spawn NPCs after maze generation
        self._update_wall_adjacencies()
        
        self.offset_x = (SCREEN_WIDTH - self.width * GRID_SIZE) // 2

        cube_full_visual_height = int(GRID_SIZE * 1.2)
        if self.height == 0:
            rendered_maze_height = 0
        else:
            height_of_staggered_rows = (self.height - 1) * STAGGER_HEIGHT_PER_ROW
            rendered_maze_height = height_of_staggered_rows + cube_full_visual_height
        self.offset_y = (SCREEN_HEIGHT - rendered_maze_height) // 2


    def _generate_maze(self):
        maze = []
        for r_idx in range(self.height):
            row = []
            for c_idx in range(self.width):
                if r_idx == 1 and c_idx == 1: # Player start position
                    row.append(FloorCube())
                elif c_idx == 0 or r_idx == 0 or c_idx == self.width - 1 or r_idx == self.height - 1:
                    row.append(WallCube())
                else:
                    rand_val = random.random()
                    if rand_val < 0.075: # RockCube
                        row.append(RockCube())
                    elif rand_val < 0.15: # WoodCube
                        row.append(WoodCube())
                    else: # FloorCube
                        row.append(FloorCube())
            maze.append(row)
        return maze

    def _spawn_npcs(self):
        self.npcs = []
        possible_spawn_points = []
        for r in range(1, self.height - 1): # Avoid edges
            for c in range(1, self.width - 1):
                # NPCs should only spawn on FloorCubes initially
                if isinstance(self.grid[r][c], FloorCube):
                    # Avoid player's typical starting cell (1,1) if it's fixed
                    if r == 1 and c == 1 and (player_start_x == 1 and player_start_y == 1): # Check against actual player start
                        continue
                    possible_spawn_points.append((c, r))
        
        random.shuffle(possible_spawn_points)
        
        num_npcs_to_spawn = min(MAX_NPCS, len(possible_spawn_points))
        
        for i in range(num_npcs_to_spawn):
            grid_x, grid_y = possible_spawn_points[i]
            npc_type = random.choice(["orc", "demon"]) 
            new_npc = NPC(grid_x, grid_y, self, npc_type=npc_type)
            self.npcs.append(new_npc)
            # print(f"INFO: Spawned NPC '{npc_type}' at ({grid_x}, {grid_y})")


    def _update_wall_adjacencies(self):
        for r in range(self.height):
            for c in range(self.width):
                current_cube = self.grid[r][c]
                if isinstance(current_cube, WallCube):
                    current_cube.adjacent_status[0] = 1 if c > 0 and isinstance(self.grid[r][c - 1], WallCube) else -1
                    current_cube.adjacent_status[1] = 1 if r > 0 and isinstance(self.grid[r - 1][c], WallCube) else -1
                    current_cube.adjacent_status[2] = 1 if c < self.width - 1 and isinstance(self.grid[r][c + 1], WallCube) else -1
                    current_cube.adjacent_status[3] = 1 if r < self.height - 1 and isinstance(self.grid[r + 1][c], WallCube) else -1

    def is_walkable(self, grid_x, grid_y):
        # Checks map tile walkability: must be within bounds AND a FloorCube.
        if 0 <= grid_y < self.height and 0 <= grid_x < self.width:
            tile = self.grid[grid_y][grid_x]
            # Only FloorCubes are inherently walkable for ground units
            if isinstance(tile, FloorCube):
                 return True
            return False # Wall, RockCube, WoodCube, or other non-FloorCube type
        return False # Out of bounds


    def draw(self, surface, player, npcs):
        # 1. Draw map tiles first
        for y_idx in range(self.height):
            for x_idx in range(self.width):
                cube = self.grid[y_idx][x_idx]
                screen_x = self.offset_x + x_idx * GRID_SIZE
                screen_y = self.offset_y + y_idx * STAGGER_HEIGHT_PER_ROW
                cube.draw(surface, screen_x, screen_y)
        
        # Collect all entities that need sorted drawing
        sorted_entities = [player] + npcs
        
        def sort_key(entity):
            entity_height = TARGET_PLAYER_HEIGHT if isinstance(entity, Player) else entity.target_npc_height
            # Sort by grid_y, then by the "feet" y-position on screen.
            return (entity.grid_y, entity.current_screen_y + entity_height)

        sorted_entities.sort(key=sort_key)

        # 3. Draw sorted entities
        for entity in sorted_entities:
            entity.draw(surface, self.offset_x, self.offset_y)

# Player start position needs to be defined before _spawn_npcs uses it.
# Let's define it globally for setup, or pass it if main structure changes.
player_start_x, player_start_y = 1, 1

def main():
    global player_start_x, player_start_y # Allow main to set these for maze
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Guali's Adventure - Enhanced Physics")

    maze_width = SCREEN_WIDTH // GRID_SIZE
    maze_height = SCREEN_HEIGHT // GRID_SIZE
    if maze_width < 3 or maze_height < 3 :
        print(f"CRITICAL ERROR: Maze dimensions ({maze_width}x{maze_height}) too small.")
        return

    # Initial player start position determination
    player_start_x, player_start_y = 1, 1 # Default
    # Maze generation might be refactored to accept player_start to avoid spawning NPC there
    # For now, _spawn_npcs in Maze refers to global player_start_x, player_start_y

    maze = Maze(maze_width, maze_height) # Maze generation happens here

    # Ensure player's actual starting spot is valid after maze and NPCs are set up
    temp_player_start_x, temp_player_start_y = 1,1
    initial_player_pos_valid = False
    if maze.is_walkable(temp_player_start_x, temp_player_start_y):
        occupied_by_npc = any(npc.grid_x == temp_player_start_x and npc.grid_y == temp_player_start_y for npc in maze.npcs)
        if not occupied_by_npc:
            initial_player_pos_valid = True

    if not initial_player_pos_valid:
        print(f"WARNING: Default player start ({temp_player_start_x},{temp_player_start_y}) is not ideal. Scanning...")
        found_new_start = False
        for r_scan in range(1, maze.height - 1):
            for c_scan in range(1, maze.width - 1):
                if maze.is_walkable(c_scan, r_scan):
                    occupied = any(npc.grid_x == c_scan and npc.grid_y == r_scan for npc in maze.npcs)
                    if not occupied:
                        temp_player_start_x, temp_player_start_y = c_scan, r_scan
                        found_new_start = True
                        break
            if found_new_start: break
        if not found_new_start:
            print("CRITICAL ERROR: No suitable walkable start tile found for player! Defaulting, may cause issues.")
            # Keep temp_player_start_x, temp_player_start_y as 1,1 and hope for the best.
    
    player_start_x, player_start_y = temp_player_start_x, temp_player_start_y
    player = Player(player_start_x, player_start_y, maze)
    print(f"Player starting at: ({player_start_x}, {player_start_y})")


    running = True
    clock = pygame.time.Clock()

    while running:
        dt = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                if event.key == pygame.K_r:
                    print("INFO: 'R' pressed. Resetting maze, player, and NPCs.")
                    player_start_x, player_start_y = 1,1 # Reset before creating maze
                    maze = Maze(maze_width, maze_height)
                    # Re-validate player start after new maze & NPCs
                    temp_player_start_x, temp_player_start_y = 1,1
                    # (Simplified re-validation for reset, full scan omitted for brevity here)
                    if not maze.is_walkable(temp_player_start_x, temp_player_start_y) or \
                       any(npc.grid_x == temp_player_start_x and npc.grid_y == temp_player_start_y for npc in maze.npcs):
                        # Basic fallback: find first available floor tile if (1,1) is bad
                        for r_s in range(1, maze.height-1):
                            for c_s in range(1, maze.width-1):
                                if maze.is_walkable(c_s, r_s) and \
                                   not any(npc.grid_x == c_s and npc.grid_y == r_s for npc in maze.npcs):
                                    temp_player_start_x, temp_player_start_y = c_s, r_s
                                    break
                            if (temp_player_start_x, temp_player_start_y) != (1,1): break
                    player_start_x, player_start_y = temp_player_start_x, temp_player_start_y
                    player = Player(player_start_x, player_start_y, maze)
                    print(f"Player reset to: ({player_start_x}, {player_start_y})")


                if not player.is_grid_moving:
                    dx_event, dy_event = 0, 0
                    if event.key == pygame.K_UP: dy_event = -1
                    elif event.key == pygame.K_DOWN: dy_event = 1
                    elif event.key == pygame.K_LEFT: dx_event = -1
                    elif event.key == pygame.K_RIGHT: dx_event = 1

                    if dx_event != 0 or dy_event != 0:
                        player.start_grid_move(dx_event, dy_event, maze.npcs)

        player.update(dt, maze.npcs)

        for i, npc_to_update in enumerate(maze.npcs):
            other_npcs = [npc for idx, npc in enumerate(maze.npcs) if idx != i]
            npc_to_update.update(dt, player, other_npcs)

        screen.fill(FLOOR_BACKGROUND_COLOR)
        maze.draw(screen, player, maze.npcs)

        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()