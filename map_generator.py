# main_game.py
import pygame
import random
from cube import FloorCube, WallCube, RockCube, WoodCube, GRID_SIZE

FLOOR_BACKGROUND_COLOR = (46, 80, 93)
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 800

class Maze:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.grid = self._generate_maze()
        self._update_wall_adjacencies()

    def _generate_maze(self):
        # ... (this method remains the same)
        maze = []
        for r_idx in range(self.height):
            row = []
            for c_idx in range(self.width):
                if c_idx == 0 or r_idx == 0 or c_idx == self.width - 1 or r_idx == self.height - 1:
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
        # ... (this method remains the same)
        for r in range(self.height):
            for c in range(self.width):
                current_cube = self.grid[r][c]
                if isinstance(current_cube, WallCube):
                    # Check Left
                    if c > 0:
                        if isinstance(self.grid[r][c - 1], WallCube):
                            current_cube.adjacent_status[0] = 1
                        else: 
                            current_cube.adjacent_status[0] = -1
                    # Check Up
                    if r > 0:
                        if isinstance(self.grid[r - 1][c], WallCube):
                            current_cube.adjacent_status[1] = 1
                        else: 
                            current_cube.adjacent_status[1] = -1
                    # Check Right
                    if c < self.width - 1: 
                        if isinstance(self.grid[r][c + 1], WallCube):
                            current_cube.adjacent_status[2] = 1
                        else: 
                            current_cube.adjacent_status[2] = -1
                    # Check Down
                    if r < self.height - 1: 
                        if isinstance(self.grid[r + 1][c], WallCube):
                            current_cube.adjacent_status[3] = 1
                        else: 
                            current_cube.adjacent_status[3] = -1
    
    def draw(self, surface):
        # Horizontal centering (remains the same)
        offset_x = (SCREEN_WIDTH - self.width * GRID_SIZE) // 2
        
        # --- Updated vertical centering ---
        stagger_height_per_row = int(GRID_SIZE * 0.8)
        # Visual height of a single cube from its logical 'y' to its bottommost pixel
        # Top face (0.8*GRID_SIZE) + Front face (0.4*GRID_SIZE) = 1.2*GRID_SIZE
        # FloorCube also extends to y + 1.2*GRID_SIZE from its logical 'y'
        cube_full_visual_height = int(GRID_SIZE * 1.2) 

        if self.height == 0:
            rendered_maze_height = 0
        else: # For self.height >= 1
            # Height from the top of the first row to the top of the last row
            height_of_staggered_rows = (self.height - 1) * stagger_height_per_row
            # Add the full height of the last row of cubes
            rendered_maze_height = height_of_staggered_rows + cube_full_visual_height
            
        offset_y = (SCREEN_HEIGHT - rendered_maze_height) // 2
        # Optional: ensure maze doesn't start above screen top if it's too large
        # offset_y = max(0, offset_y) 
        # --- End of updated vertical centering ---

        for y_idx in range(self.height):
            for x_idx in range(self.width):
                cube = self.grid[y_idx][x_idx]
                screen_x = offset_x + x_idx * GRID_SIZE
                # screen_y is the 'top' y for the current row's drawing operations
                screen_y = offset_y + y_idx * stagger_height_per_row 
                cube.draw(surface, screen_x, screen_y)

# Main Game Loop (remains the same)
def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Guali's Adventure")

    maze_width = SCREEN_WIDTH // GRID_SIZE
    maze_height = SCREEN_HEIGHT // GRID_SIZE 
    maze = Maze(maze_width, maze_height)

    running = True
    clock = pygame.time.Clock()

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                if event.key == pygame.K_r:
                    maze = Maze(maze_width, maze_height) 

        screen.fill(FLOOR_BACKGROUND_COLOR)
        maze.draw(screen)
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()