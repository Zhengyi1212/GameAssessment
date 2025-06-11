# map_generator.py
import pygame
import random
from cube import FloorCube, WallCube, RockCube, WoodCube, GRID_SIZE
from player import Player
from npc import NPC
from menu import Menu
import sys

FLOOR_BACKGROUND_COLOR = (46, 80, 93)
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 700
STAGGER_HEIGHT_PER_ROW = int(GRID_SIZE * 0.8)
MAX_NPCS = 5

class Maze:
    def __init__(self, width, height, player_start_pos):
        self.width = width
        self.height = height
        self.grid = self._generate_maze()
        self.npcs = []
        self._spawn_npcs(player_start_pos)
        self._update_wall_adjacencies()
        
        self.offset_x = (SCREEN_WIDTH - self.width * GRID_SIZE) // 2
        cube_full_visual_height = int(GRID_SIZE * 1.2)
        height_of_staggered_rows = (self.height - 1) * STAGGER_HEIGHT_PER_ROW
        rendered_maze_height = height_of_staggered_rows + cube_full_visual_height
        self.offset_y = (SCREEN_HEIGHT - rendered_maze_height) // 2

    def _generate_maze(self):
        # Maze generation logic remains the same
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
                    if rand_val < 0.075: row.append(RockCube())
                    elif rand_val < 0.15: row.append(WoodCube())
                    else: row.append(FloorCube())
            maze.append(row)
        return maze

    def _spawn_npcs(self, player_start_pos):
        self.npcs = []
        possible_spawn_points = []
        for r in range(1, self.height - 1):
            for c in range(1, self.width - 1):
                if isinstance(self.grid[r][c], FloorCube) and (c, r) != player_start_pos:
                    possible_spawn_points.append((c, r))
        
        random.shuffle(possible_spawn_points)
        num_npcs_to_spawn = min(MAX_NPCS, len(possible_spawn_points))
        
        for i in range(num_npcs_to_spawn):
            grid_x, grid_y = possible_spawn_points[i]
            npc_type = random.choice(["orc", "orc2", "demon"]) 
            new_npc = NPC(grid_x, grid_y, self, npc_type=npc_type)
            self.npcs.append(new_npc)

    def _update_wall_adjacencies(self):
        # Wall adjacency logic remains the same
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
            return isinstance(self.grid[grid_y][grid_x], FloorCube)
        return False

    def draw(self, surface, player, npcs_list):
        render_ables = []
        for y_idx, row in enumerate(self.grid):
            for x_idx, cube in enumerate(row):
                screen_x = self.offset_x + x_idx * GRID_SIZE
                screen_y = self.offset_y + y_idx * STAGGER_HEIGHT_PER_ROW
                sort_key = screen_y if isinstance(cube, FloorCube) else screen_y + STAGGER_HEIGHT_PER_ROW
                render_ables.append({'sort_key': sort_key, 'type': 'cube', 'object': cube, 'pos': (screen_x, screen_y)})

        all_entities = [npc for npc in npcs_list if npc] + ([player] if player else [])
        for entity in all_entities:
            sort_key = self.offset_y + entity.grid_y * STAGGER_HEIGHT_PER_ROW + STAGGER_HEIGHT_PER_ROW
            sort_key += entity.current_screen_y / 1000.0
            render_ables.append({'sort_key': sort_key, 'type': 'entity', 'object': entity})

        render_ables.sort(key=lambda item: item['sort_key'])

        for item in render_ables:
            if item['type'] == 'cube':
                item['object'].draw(surface, item['pos'][0], item['pos'][1])
            elif item['type'] == 'entity':
                item['object'].draw(surface, self.offset_x, self.offset_y)

def draw_ui(screen, player):
    # --- Player Health Bar ---
    health_bar_bg = pygame.Rect(10, 10, 204, 24)
    pygame.draw.rect(screen, (50, 50, 50), health_bar_bg)
    
    health_ratio = player.health / player.max_health
    health_bar_fg = pygame.Rect(12, 12, 200 * health_ratio, 20)
    pygame.draw.rect(screen, (200, 20, 20), health_bar_fg)
    
    pygame.draw.rect(screen, (255, 255, 255), health_bar_bg, 2) # Border

def game_loop(screen):
    maze_width = SCREEN_WIDTH // GRID_SIZE
    maze_height = SCREEN_HEIGHT // GRID_SIZE
    
    player_start_x, player_start_y = 1, 1
    maze = Maze(maze_width, maze_height, (player_start_x, player_start_y))
    player = Player(player_start_x, player_start_y, maze)
    
    running = True
    clock = pygame.time.Clock()
    game_over = False
    game_over_font = pygame.font.SysFont("arial", 80, bold=True)
    game_over_text = game_over_font.render("GAME OVER", True, (255, 0, 0))
    game_over_rect = game_over_text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2))

    while running:
        dt = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: running = False
                
                if not game_over:
                    if event.key == pygame.K_UP: player.handle_key_down('up', maze.npcs)
                    elif event.key == pygame.K_DOWN: player.handle_key_down('down', maze.npcs)
                    elif event.key == pygame.K_LEFT: player.handle_key_down('left', maze.npcs)
                    elif event.key == pygame.K_RIGHT: player.handle_key_down('right', maze.npcs)
                    elif event.key == pygame.K_SPACE: player.start_attack()
                
                if event.key == pygame.K_r:
                    print("INFO: 'R' pressed. Resetting level.")
                    game_loop(screen) # Restart
                    return 

        # --- Updates ---
        if not game_over:
            player.update(dt, maze.npcs)
            
            # Update NPCs
            for i, npc_to_update in enumerate(maze.npcs):
                other_npcs = [npc for idx, npc in enumerate(maze.npcs) if idx != i]
                npc_to_update.update(dt, player, other_npcs)
            
            # Remove dead NPCs after their animation
            maze.npcs = [npc for npc in maze.npcs if not (npc.is_dead and npc.death_timer > npc.config["death_duration"])]

            # Check for game over
            if player.health <= 0:
                game_over = True

        # --- Drawing ---
        screen.fill(FLOOR_BACKGROUND_COLOR)
        maze.draw(screen, player, maze.npcs)
        draw_ui(screen, player) # Draw health bar

        if game_over:
            screen.blit(game_over_text, game_over_rect)

        pygame.display.flip()

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("A Man With a Sword")

    menu = Menu(screen)
    menu_choice = menu.run()

    if menu_choice == 'start':
        game_loop(screen)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
