# level_controller.py
import pygame
import random
from cube import FloorCube, WallCube, RockCube, WoodCube, GRID_SIZE
from npc import NPC

# Constants
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 700
STAGGER_HEIGHT_PER_ROW = int(GRID_SIZE * 0.8)
PLAYER_START_POS = (1, 1)

# --- NEW: Level Difficulty Configuration ---
# Defines the number of NPCs and the available types for each level.
LEVEL_CONFIG = {
    1:  {'npc_count': 3, 'types': ['orc2']},
    2:  {'npc_count': 4, 'types': ['orc2']},
    3:  {'npc_count': 5, 'types': ['orc2']},
    4:  {'npc_count': 5, 'types': ['orc2', 'orc']},
    5:  {'npc_count': 6, 'types': ['orc2', 'orc']},
    6:  {'npc_count': 7, 'types': ['orc2', 'orc']},
    7:  {'npc_count': 6, 'types': ['orc', 'demon']},
    8:  {'npc_count': 7, 'types': ['orc', 'orc2', 'demon']},
    9:  {'npc_count': 8, 'types': ['orc', 'orc2', 'demon']},
    10: {'npc_count': 9, 'types': ['orc', 'demon']},
}


class Maze:
    """Represents a single level's map and NPCs."""
    def __init__(self, grid, player_start_pos, level_number):
        self.grid = grid
        self.height = len(grid)
        self.width = len(grid[0]) if self.height > 0 else 0
        self.npcs = []
        self.level_number = level_number
        
        self.offset_x = (SCREEN_WIDTH - self.width * GRID_SIZE) // 2
        cube_full_visual_height = int(GRID_SIZE * 1.2)
        height_of_staggered_rows = (self.height - 1) * STAGGER_HEIGHT_PER_ROW
        rendered_maze_height = height_of_staggered_rows + cube_full_visual_height
        self.offset_y = (SCREEN_HEIGHT - rendered_maze_height) // 2

        self._spawn_npcs(player_start_pos)
        self._update_wall_adjacencies()

    def _spawn_npcs(self, player_start_pos):
        """Spawns NPCs based on the level's configuration."""
        self.npcs = []
        if self.level_number not in LEVEL_CONFIG:
            print(f"Warning: No level config found for level {self.level_number}. No NPCs will spawn.")
            return

        config = LEVEL_CONFIG[self.level_number]
        num_npcs_to_spawn = config['npc_count']
        allowed_npc_types = config['types']

        possible_spawn_points = []
        for r in range(1, self.height - 1):
            for c in range(1, self.width - 1):
                if isinstance(self.grid[r][c], FloorCube) and (c, r) != player_start_pos:
                    possible_spawn_points.append((c, r))
        
        random.shuffle(possible_spawn_points)
        
        for i in range(min(num_npcs_to_spawn, len(possible_spawn_points))):
            grid_x, grid_y = possible_spawn_points[i]
            npc_type = random.choice(allowed_npc_types)
            new_npc = NPC(grid_x, grid_y, self, npc_type=npc_type)
            self.npcs.append(new_npc)

    def _update_wall_adjacencies(self):
        """Updates wall cubes to know if they have adjacent walls, for drawing borders correctly."""
        for r in range(self.height):
            for c in range(self.width):
                current_cube = self.grid[r][c]
                if isinstance(current_cube, WallCube):
                    current_cube.adjacent_status[0] = 1 if c > 0 and isinstance(self.grid[r][c - 1], WallCube) else -1
                    current_cube.adjacent_status[1] = 1 if r > 0 and isinstance(self.grid[r - 1][c], WallCube) else -1
                    current_cube.adjacent_status[2] = 1 if c < self.width - 1 and isinstance(self.grid[r][c + 1], WallCube) else -1
                    current_cube.adjacent_status[3] = 1 if r < self.height - 1 and isinstance(self.grid[r + 1][c], WallCube) else -1

    def is_walkable(self, grid_x, grid_y):
        """Checks if a tile at the given grid coordinates is walkable."""
        if 0 <= grid_y < self.height and 0 <= grid_x < self.width:
            return isinstance(self.grid[grid_y][grid_x], FloorCube)
        return False

    def draw(self, surface, player, npcs_list):
        """Draws the entire maze, including cubes and entities, in the correct Z-order."""
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

class LevelController:
    """Manages loading levels and tracking player progress."""
    def __init__(self, map_file='map.txt', progress_file='progress.txt'):
        self.levels = self._load_levels_from_file(map_file)
        self.progress_file = progress_file
        self.unlocked_levels = self._load_progress()

    def _load_levels_from_file(self, filename):
        """Loads all level maps from the map file."""
        levels = {}
        try:
            with open(filename, 'r') as f:
                content = f.read()
            
            level_chunks = content.split('#LEVEL ')[1:]
            for chunk in level_chunks:
                lines = chunk.strip().split('\n')
                level_num_str = lines[0].strip().split(' ')[0]
                if not level_num_str.isdigit(): continue
                
                level_num = int(level_num_str)
                map_data = [line for line in lines[1:] if not line.startswith('#ENDLEVEL')]
                
                grid = []
                for row_data in map_data:
                    row = []
                    for char in row_data:
                        if char == 'W': row.append(WallCube())
                        elif char == 'R': row.append(RockCube())
                        elif char == 'O': row.append(WoodCube())
                        elif char == 'P': row.append(FloorCube())
                        else: row.append(FloorCube())
                    grid.append(row)
                levels[level_num] = grid
        except FileNotFoundError:
            print(f"Error: Map file '{filename}' not found.")
        return levels

    def _load_progress(self):
        """Loads the unlocked levels from the progress file."""
        try:
            with open(self.progress_file, 'r') as f:
                unlocked_count = int(f.read().strip())
                return min(unlocked_count, len(self.levels))
        except (FileNotFoundError, ValueError):
            return 1
            
    def _save_progress(self):
        """Saves the number of unlocked levels to the progress file."""
        with open(self.progress_file, 'w') as f:
            f.write(str(self.unlocked_levels))

    def get_unlocked_level_count(self):
        """Returns the number of levels the player has access to."""
        return self.unlocked_levels

    def get_level(self, level_number):
        """Returns a Maze object for the requested level number."""
        if level_number in self.levels:
            return Maze(self.levels[level_number], PLAYER_START_POS, level_number)
        return None

    def unlock_next_level(self, completed_level_number):
        """Unlocks the next level if the completed one was the latest."""
        if completed_level_number == self.unlocked_levels and self.unlocked_levels < len(self.levels):
            self.unlocked_levels += 1
            self._save_progress()
            print(f"Level {self.unlocked_levels} unlocked!")
