# map_generator.py
import pygame
import random
from cube import FloorCube, WallCube, RockCube, WoodCube, GRID_SIZE
from player import Player, TARGET_PLAYER_HEIGHT 
from npc import NPC
from menu import Menu # Import the new Menu class
import sys

FLOOR_BACKGROUND_COLOR = (46, 80, 93)
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 700
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
                if isinstance(self.grid[r][c], FloorCube):
                    # This check is now against the global vars defined in main()
                    if r == player_start_y and c == player_start_x:
                        continue
                    possible_spawn_points.append((c, r))
        
        random.shuffle(possible_spawn_points)
        
        num_npcs_to_spawn = min(MAX_NPCS, len(possible_spawn_points))
        
        for i in range(num_npcs_to_spawn):
            grid_x, grid_y = possible_spawn_points[i]
            # --- FIX: Added "orc2" to the list of possible spawns ---
            npc_type = random.choice(["orc", "orc2", "demon"]) 
            new_npc = NPC(grid_x, grid_y, self, npc_type=npc_type)
            self.npcs.append(new_npc)

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
        if 0 <= grid_y < self.height and 0 <= grid_x < self.width:
            tile = self.grid[grid_y][grid_x]
            if isinstance(tile, FloorCube):
                 return True
            return False
        return False


    def draw(self, surface, player, npcs_list):
        # A robust drawing method using an intelligent Y-sort to handle all occlusion scenarios.
        
        # Step 1: Collect all drawable objects into a single list with a calculated sort key.
        render_ables = []

        # Add all cubes to the list.
        for y_idx in range(self.height):
            for x_idx in range(self.width):
                cube = self.grid[y_idx][x_idx]
                screen_x = self.offset_x + x_idx * GRID_SIZE
                screen_y = self.offset_y + y_idx * STAGGER_HEIGHT_PER_ROW

                sort_key = 0
                # FloorCubes are flat. Their sort key is their top edge, so they are drawn early.
                if isinstance(cube, FloorCube):
                    sort_key = screen_y 
                # Tall cubes (Walls, Rocks) occlude things. Their sort key is their base.
                else:
                    sort_key = screen_y + STAGGER_HEIGHT_PER_ROW

                render_ables.append(
                    {'sort_key': sort_key, 'type': 'cube', 'object': cube, 'pos': (screen_x, screen_y)}
                )

        # Add all entities (player and NPCs) to the list.
        all_entities = npcs_list + [player]
        for entity in all_entities:
            # The key is based on the entity's logical grid position to prevent visual offsets from breaking the sort.
            sort_key = self.offset_y + entity.grid_y * STAGGER_HEIGHT_PER_ROW + STAGGER_HEIGHT_PER_ROW
            
            # For entities that are visually very close, add a small tie-breaker based on screen Y
            # to ensure they layer correctly over each other.
            sort_key += entity.current_screen_y / 1000.0

            render_ables.append(
                {'sort_key': sort_key, 'type': 'entity', 'object': entity}
            )

        # Step 2: Sort the entire list by the calculated 'sort_key'.
        render_ables.sort(key=lambda item: item['sort_key'])

        # Step 3: Draw all objects in their newly sorted order (back-to-front).
        for item in render_ables:
            if item['type'] == 'cube':
                item['object'].draw(surface, item['pos'][0], item['pos'][1])
            elif item['type'] == 'entity':
                item['object'].draw(surface, self.offset_x, self.offset_y)

# Player start position needs to be defined before _spawn_npcs uses it.
player_start_x, player_start_y = 1, 1

def game_loop(screen):
    """The main game loop, containing all logic for running the game itself."""
    global player_start_x, player_start_y
    
    maze_width = SCREEN_WIDTH // GRID_SIZE
    maze_height = SCREEN_HEIGHT // GRID_SIZE
    if maze_width < 3 or maze_height < 3:
        print(f"CRITICAL ERROR: Maze dimensions ({maze_width}x{maze_height}) too small.")
        return

    player_start_x, player_start_y = 1, 1
    maze = Maze(maze_width, maze_height)
    
    # Player start position validation
    temp_player_start_x, temp_player_start_y = player_start_x, player_start_y
    # ... (rest of validation logic is the same)
    
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
                    running = False # Exit game loop, will return to main and quit
                
                # Player input
                if event.key == pygame.K_UP:
                    player.handle_key_down('up',maze.npcs)
                elif event.key == pygame.K_DOWN:
                    player.handle_key_down('down',maze.npcs)
                elif event.key == pygame.K_LEFT:
                    player.handle_key_down('left',maze.npcs)
                elif event.key == pygame.K_RIGHT:
                    player.handle_key_down('right',maze.npcs)
                elif event.key == pygame.K_SPACE:
                    player.start_attack() 

                elif event.key == pygame.K_r:
                    # This now just restarts the game loop
                    print("INFO: 'R' pressed. Resetting level.")
                    game_loop(screen)
                    return # Exit the current (old) game loop

            if event.type == pygame.KEYUP:
                # Key up events
                if event.key == pygame.K_UP:
                    player.handle_key_up('up', maze.npcs)
                elif event.key == pygame.K_DOWN:
                    player.handle_key_up('down', maze.npcs)
                elif event.key == pygame.K_LEFT:
                    player.handle_key_up('left', maze.npcs)
                elif event.key == pygame.K_RIGHT:
                    player.handle_key_up('right', maze.npcs)
        
        player.update(dt, maze.npcs)

        for i, npc_to_update in enumerate(maze.npcs):
            other_npcs = [npc for idx, npc in enumerate(maze.npcs) if idx != i]
            npc_to_update.update(dt, player, other_npcs)

        screen.fill(FLOOR_BACKGROUND_COLOR)
        maze.draw(screen, player, maze.npcs)

        pygame.display.flip()

def main():
    """Main function to initialize pygame and run the menu and game."""
    global player_start_x, player_start_y 
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("A Man With a Sword")

    # --- Run the menu first ---
    menu = Menu(screen)
    menu_choice = menu.run()

    # --- Decide whether to start the game or exit ---
    if menu_choice == 'start':
        game_loop(screen) # Enter the main game loop

    # Quit pygame after the menu or game loop finishes
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()