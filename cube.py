# cube.py
import pygame
from abc import ABC, abstractmethod

# Constants primarily used by cube definitions and rendering
GRID_SIZE = 80
# BLACK_BORDER and WHITE_BORDER can be kept as fallbacks or for UI elements if any,
# but cube borders will now be dynamic.
DEFAULT_DARK_BORDER = (30, 30, 30)
DEFAULT_LIGHT_BORDER = (220, 220, 220)
FRONT_FACE_SHADOW_ALPHA = 75

# --- Texture Loading (remains the same) ---
def load_texture(filename, fallback_color):
    try:
        # Ensure your assets are in a folder named 'assets/CubeTexture/'
        # relative to where your script is run.
        texture = pygame.image.load(f'./assets/CubeTexture/{filename}')
        return pygame.transform.scale(texture, (GRID_SIZE, GRID_SIZE))
    except pygame.error as e:
        print(f"Error loading texture '{filename}': {e}. Using fallback color.")
        surface = pygame.Surface((GRID_SIZE, GRID_SIZE))
        surface.fill(fallback_color)
        return surface

floor_texture_base = load_texture('2.png', (60, 95, 110))
wall_texture_base = load_texture('Wall.png', (170, 170, 170))
rock_texture_base = load_texture('Rock.png', (150, 150, 150))
wood_texture_base = load_texture('Wood.png', (160, 110, 70))

# --- Helper function for border colors (as defined above) ---
def get_derived_border_colors(texture_surface, default_dark_color=DEFAULT_DARK_BORDER, default_light_color=DEFAULT_LIGHT_BORDER):
    if texture_surface is None:
        return default_dark_color, default_light_color
    try:
        avg_color = pygame.transform.average_color(texture_surface)
        darker_r = max(0, int(avg_color[0] * 0.7))
        darker_g = max(0, int(avg_color[1] * 0.7))
        darker_b = max(0, int(avg_color[2] * 0.7))
        if darker_r == avg_color[0] and darker_g == avg_color[1] and darker_b == avg_color[2] and sum(avg_color) < 120: # if color is dark and factor didn't change it
            darker_r, darker_g, darker_b = max(0, avg_color[0]-20), max(0, avg_color[1]-20), max(0, avg_color[2]-20)
        darker_border = (darker_r, darker_g, darker_b)

        lighter_r = min(255, avg_color[0] + 40) # Increased difference for lighter seam
        lighter_g = min(255, avg_color[1] + 40)
        lighter_b = min(255, avg_color[2] + 40)
        if lighter_r == avg_color[0] and lighter_g == avg_color[1] and lighter_b == avg_color[2] and sum(avg_color) > 600: # if color is light and offset didn't change it
             lighter_r, lighter_g, lighter_b = min(255, avg_color[0]+20), min(255, avg_color[1]+20), min(255, avg_color[2]+20)
        lighter_border = (lighter_r, lighter_g, lighter_b)
        
        return darker_border, lighter_border
    except Exception as e:
        print(f"Warning: Could not get average color for border derivation: {e}. Using default border colors.")
        return default_dark_color, default_light_color

class Cube(ABC):
    def __init__(self):
        self.top_texture = None
        self.front_texture = None
        
        # Derived border colors
        self.top_face_border_color = DEFAULT_DARK_BORDER
        self.front_face_border_color = DEFAULT_DARK_BORDER
        self.seam_line_color = DEFAULT_LIGHT_BORDER # Special case, often lighter

        self._load_textures()
        self._calculate_natural_border_colors()

    @abstractmethod
    def _load_textures(self):
        pass

    def _calculate_natural_border_colors(self):
        # Default implementation, can be overridden
        if self.top_texture:
            dark_top, light_top = get_derived_border_colors(self.top_texture)
            self.top_face_border_color = dark_top
            self.seam_line_color = light_top # Seam often based on top texture, made lighter

        if self.front_texture:
            dark_front, _ = get_derived_border_colors(self.front_texture)
            self.front_face_border_color = dark_front
        elif self.top_texture: # Fallback if no front texture, use top's dark border
            self.front_face_border_color = self.top_face_border_color


    @abstractmethod
    def draw(self, surface, x, y):
        pass

class FloorCube(Cube):
    def _load_textures(self):
        self.top_texture = floor_texture_base
        # No front_texture for FloorCube

    def _calculate_natural_border_colors(self):
        # Floor cube uses a single derived color for all its borders
        if self.top_texture:
            derived_color, _ = get_derived_border_colors(self.top_texture)
            self.top_face_border_color = derived_color
            # Not applicable or use same for consistency if base draw methods expect them
            self.front_face_border_color = derived_color 
            self.seam_line_color = derived_color


    def draw(self, surface, x, y):
        floor_y_position = y + int(GRID_SIZE * 0.4)
        scaled_floor_texture_height = int(GRID_SIZE * 0.8)
        # Texture blitting (ensure self.top_texture is valid)
        if self.top_texture:
            scaled_floor_texture = pygame.transform.scale(self.top_texture, (GRID_SIZE, scaled_floor_texture_height))
            surface.blit(scaled_floor_texture, (x, floor_y_position))
        else: # Fallback rendering if texture is missing
            pygame.draw.rect(surface, (60,95,110), (x, floor_y_position, GRID_SIZE, scaled_floor_texture_height))


        # All border lines use top_face_border_color
        color = self.top_face_border_color
        pygame.draw.line(surface, color, (x, floor_y_position), (x + GRID_SIZE - 1, floor_y_position))
        pygame.draw.line(surface, color, (x, floor_y_position), (x, floor_y_position + scaled_floor_texture_height - 1))
        pygame.draw.line(surface, color, (x + GRID_SIZE - 1, floor_y_position), (x + GRID_SIZE - 1, floor_y_position + scaled_floor_texture_height - 1))
        pygame.draw.line(surface, color, (x, floor_y_position + scaled_floor_texture_height - 1), (x + GRID_SIZE - 1, floor_y_position + scaled_floor_texture_height - 1))

class _StandardDecorativeCube(Cube):
    # _load_textures is implemented by subclasses (RockCube, WoodCube)
    # _calculate_natural_border_colors uses the default Cube implementation which should work well.

    def draw(self, surface, x, y):
        top_face_height = int(GRID_SIZE * 0.8)
        front_face_height = int(GRID_SIZE * 0.4)

        if self.top_texture:
            scaled_top_texture = pygame.transform.scale(self.top_texture, (GRID_SIZE, top_face_height))
            surface.blit(scaled_top_texture, (x,y))
        # else: fallback drawing for missing top texture (can be added if needed)

        # Top face borders
        pygame.draw.line(surface, self.top_face_border_color, (x, y), (x + GRID_SIZE - 1, y))
        pygame.draw.line(surface, self.top_face_border_color, (x, y), (x, y + top_face_height - 1))
        pygame.draw.line(surface, self.top_face_border_color, (x + GRID_SIZE - 1, y), (x + GRID_SIZE - 1, y + top_face_height - 1))
        pygame.draw.line(surface, self.seam_line_color, (x, y + top_face_height - 1), (x + GRID_SIZE - 1, y + top_face_height - 1)) # Seam line

        front_face_y = y + top_face_height
        if self.front_texture:
            scaled_front_texture = pygame.transform.scale(self.front_texture, (GRID_SIZE, front_face_height))
            surface.blit(scaled_front_texture, (x, front_face_y))
        # else: fallback drawing for missing front texture (can be added if needed)


        if FRONT_FACE_SHADOW_ALPHA > 0:
            shadow_surface = pygame.Surface((GRID_SIZE, front_face_height), pygame.SRCALPHA)
            shadow_surface.fill((0, 0, 0, FRONT_FACE_SHADOW_ALPHA))
            surface.blit(shadow_surface, (x, front_face_y))

        # Front face borders
        pygame.draw.line(surface, self.front_face_border_color, (x, front_face_y), (x, front_face_y + front_face_height - 1))
        pygame.draw.line(surface, self.front_face_border_color, (x + GRID_SIZE - 1, front_face_y), (x + GRID_SIZE - 1, front_face_y + front_face_height - 1))
        pygame.draw.line(surface, self.front_face_border_color, (x, front_face_y + front_face_height - 1), (x + GRID_SIZE - 1, front_face_y + front_face_height - 1))


class RockCube(_StandardDecorativeCube):
    def _load_textures(self):
        self.top_texture = rock_texture_base
        self.front_texture = rock_texture_base

class WoodCube(_StandardDecorativeCube):
    def _load_textures(self):
        self.top_texture = wood_texture_base
        self.front_texture = wood_texture_base

class WallCube(Cube):
    def __init__(self):
        super().__init__() 
        self.adjacent_status = [-1, -1, -1, -1] 

    def _load_textures(self):
        self.top_texture = wall_texture_base
        self.front_texture = wall_texture_base 

    def _calculate_natural_border_colors(self):
        if self.top_texture: 
            derived_color, _ = get_derived_border_colors(self.top_texture)
            self.wall_border_color = derived_color
        else:
            self.wall_border_color = DEFAULT_DARK_BORDER
        
        self.top_face_border_color = self.wall_border_color
        self.front_face_border_color = self.wall_border_color
        self.seam_line_color = self.wall_border_color


    def draw(self, surface, x, y):
        top_face_h = int(GRID_SIZE * 0.8)
        front_face_h = int(GRID_SIZE * 0.4)
        width = GRID_SIZE

        if self.top_texture:
            scaled_top_texture = pygame.transform.scale(self.top_texture, (width, top_face_h))
            surface.blit(scaled_top_texture, (x,y))
        
        front_face_abs_y = y + top_face_h
        if self.front_texture:
            scaled_front_texture = pygame.transform.scale(self.front_texture, (width, front_face_h))
            surface.blit(scaled_front_texture, (x, front_face_abs_y))

        if FRONT_FACE_SHADOW_ALPHA > 0:
            shadow_surface = pygame.Surface((width, front_face_h), pygame.SRCALPHA)
            shadow_surface.fill((0, 0, 0, FRONT_FACE_SHADOW_ALPHA))
            surface.blit(shadow_surface, (x, front_face_abs_y))

        border_color = self.wall_border_color 

        if self.adjacent_status[1] == -1: 
            pygame.draw.line(surface, border_color, (x, y), (x + width - 1, y))
        if self.adjacent_status[0] == -1: 
            pygame.draw.line(surface, border_color, (x, y), (x, y + top_face_h - 1))
        if self.adjacent_status[2] == -1: 
            pygame.draw.line(surface, border_color, (x + width - 1, y), (x + width - 1, y + top_face_h - 1))
        
        pygame.draw.line(surface, border_color, (x, y + top_face_h - 1), (x + width - 1, y + top_face_h - 1)) # Seam

        if self.adjacent_status[0] == -1: 
            pygame.draw.line(surface, border_color, (x, front_face_abs_y), (x, front_face_abs_y + front_face_h - 1))
        if self.adjacent_status[2] == -1: 
            pygame.draw.line(surface, border_color, (x + width - 1, front_face_abs_y), (x + width - 1, front_face_abs_y + front_face_h - 1))
        if self.adjacent_status[3] == -1: 
            pygame.draw.line(surface, border_color, (x, front_face_abs_y + front_face_h - 1), (x + width - 1, front_face_abs_y + front_face_h - 1))