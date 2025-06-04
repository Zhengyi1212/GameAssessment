# map_generator.py
import pygame
import random
from cube import FloorCube, WallCube, RockCube, WoodCube, GRID_SIZE
from player import Player

FLOOR_BACKGROUND_COLOR = (46, 80, 93)
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 800
STAGGER_HEIGHT_PER_ROW = int(GRID_SIZE * 0.8)

class Maze:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.grid = self._generate_maze()
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
                    if rand_val < 0.075:
                        row.append(RockCube())
                    elif rand_val < 0.15:
                        row.append(WoodCube())
                    else:
                        row.append(FloorCube())
            maze.append(row)
        return maze

    def _update_wall_adjacencies(self):
        for r in range(self.height):
            for c in range(self.width):
                current_cube = self.grid[r][c]
                if isinstance(current_cube, WallCube):
                    if c > 0 and isinstance(self.grid[r][c - 1], WallCube): current_cube.adjacent_status[0] = 1
                    else: current_cube.adjacent_status[0] = -1
                    if r > 0 and isinstance(self.grid[r - 1][c], WallCube): current_cube.adjacent_status[1] = 1
                    else: current_cube.adjacent_status[1] = -1
                    if c < self.width - 1 and isinstance(self.grid[r][c + 1], WallCube): current_cube.adjacent_status[2] = 1
                    else: current_cube.adjacent_status[2] = -1
                    if r < self.height - 1 and isinstance(self.grid[r + 1][c], WallCube): current_cube.adjacent_status[3] = 1
                    else: current_cube.adjacent_status[3] = -1

    def is_walkable(self, grid_x, grid_y):
        if 0 <= grid_x < self.width and 0 <= grid_y < self.height:
            # Player cannot walk on WallCube, RockCube, or WoodCube
            current_tile = self.grid[grid_y][grid_x]
            return not isinstance(current_tile, (WallCube, RockCube, WoodCube))
        return False

    def draw(self, surface, player):
        for y_idx in range(self.height):
            for x_idx in range(self.width):
                cube = self.grid[y_idx][x_idx]
                screen_x = self.offset_x + x_idx * GRID_SIZE
                screen_y = self.offset_y + y_idx * STAGGER_HEIGHT_PER_ROW

                # always draw this grid first
                cube.draw(surface, screen_x, screen_y)

               
                player_draw_anchor_gx = player.grid_x
                player_draw_anchor_gy = player.grid_y 

                if player.is_grid_moving and player.current_move_dx < 0: # move left
                    player_draw_anchor_gx = player.grid_x + 1
             
                if y_idx == player_draw_anchor_gy and x_idx == player_draw_anchor_gx:
                    player.draw(surface, self.offset_x, self.offset_y)

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Guali's Adventure")

    maze_width = SCREEN_WIDTH // GRID_SIZE
    maze_height = SCREEN_HEIGHT // GRID_SIZE
    if maze_width < 3 or maze_height < 3 :
        print("CRITICAL ERROR: Maze dimensions (", maze_width, "x", maze_height, ") too small for default start position and borders.")
        return

    maze = Maze(maze_width, maze_height)

    player_start_x, player_start_y = int(maze_width/2), int(maze_height/2)
    if not maze.is_walkable(player_start_x, player_start_y):
        print(f"WARNING: Default start ({player_start_x},{player_start_y}) is not walkable. Scanning for alternative...")
        found_start = False
        for r_scan_idx in range(1, maze.height - 1):
            for c_scan_idx in range(1, maze.width - 1):
                if maze.is_walkable(c_scan_idx, r_scan_idx):
                    player_start_x, player_start_y = c_scan_idx, r_scan_idx
                    print(f"  INFO: Found alternative start at ({player_start_x},{player_start_y})")
                    found_start = True
                    break
            if found_start: break
        if not found_start:
            print("CRITICAL ERROR: No walkable start tile found for player! Defaulting to (1,1).")
            player_start_x, player_start_y = 1, 1

    player = Player(player_start_x, player_start_y, maze)

    running = True
    clock = pygame.time.Clock()

    while running:
        dt = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.K_ESCAPE:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r: # 'R' for Reset
                    print("INFO: 'R' pressed. Resetting maze and player.")
                    maze = Maze(maze_width, maze_height)
                    # Recalculate player_start_x, player_start_y for new maze
                    # (This logic could be extracted into a helper function for reuse)
                    temp_player_start_x, temp_player_start_y = int(maze_width/2), int(maze_height/2)
                    if not maze.is_walkable(temp_player_start_x, temp_player_start_y):
                        found_reset_start = False
                        for r_scan_idx in range(1, maze.height - 1):
                            for c_scan_idx in range(1, maze.width - 1):
                                if maze.is_walkable(c_scan_idx, r_scan_idx):
                                    temp_player_start_x, temp_player_start_y = c_scan_idx, r_scan_idx
                                    found_reset_start = True
                                    break
                            if found_reset_start: break
                        if not found_reset_start:
                            temp_player_start_x, temp_player_start_y = 1, 1
                    player = Player(temp_player_start_x, temp_player_start_y, maze)

                # --- Player Movement Input (Event-based) ---
                if not player.is_grid_moving: # Only allow new move if not already moving
                    dx_event, dy_event = 0, 0
                    if event.key == pygame.K_UP:
                        dy_event = -1
                    elif event.key == pygame.K_DOWN:
                        dy_event = 1
                    elif event.key == pygame.K_LEFT:
                        dx_event = -1
                    elif event.key == pygame.K_RIGHT:
                        dx_event = 1

                    if dx_event != 0 or dy_event != 0:
                        player.start_grid_move(dx_event, dy_event)

        player.update(dt)

        # --- Drawing ---
        screen.fill(FLOOR_BACKGROUND_COLOR)
        maze.draw(screen, player) # Pass player to maze for drawing order

        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()