# setup.py - Configuration file for global settings

import pygame

# Screen dimensions
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 800
GRID_SIZE = 80  # The logical size of a grid cell

# --- Colors inspired by "Square Meal" ---
FLOOR_BACKGROUND_COLOR = (46, 80, 93)  # Dark teal/blue for the main background
FLOOR_COLOR_FALLBACK = (60, 95, 110)  # Fallback for floor

# --- Perspective and 3D rendering parameters ---
Y_PERSPECTIVE_FACTOR = 0.9  # How much the Y dimension is squashed
CUBE_FRONT_FACE_HEIGHT_FACTOR = 0.4  # Height of the front face
LINE_THICKNESS_3D_EFFECT = 2  # Thickness for drawing lines

# Calculated visual dimensions
EFFECTIVE_TILE_SCREEN_DEPTH = int(GRID_SIZE * Y_PERSPECTIVE_FACTOR)
PROJECTED_CUBE_VISUAL_HEIGHT = int(GRID_SIZE * CUBE_FRONT_FACE_HEIGHT_FACTOR)

# --- Load textures ---
def load_texture(filename, fallback_color):
    """Helper function to load textures and provide a fallback surface."""
    try:
        texture = pygame.image.load(f'./assets/CubeTexture/{filename}')
        return pygame.transform.scale(texture, (GRID_SIZE, GRID_SIZE))
    except pygame.error as e:
        print(f"Error loading texture '{filename}': {e}. Using fallback color.")
        surface = pygame.Surface((GRID_SIZE, GRID_SIZE))
        surface.fill(fallback_color)
        return surface

# --- Block Textures ---
floor_texture_base = load_texture('Floor.png', FLOOR_COLOR_FALLBACK)
wall_texture_base = load_texture('Wall.png', (170, 170, 170))
rock_texture_base = load_texture('Rock.png', (150, 150, 150))
wood_texture_base = load_texture('Wood.png', (160, 110, 70))

# --- Helper Functions for Color Manipulation ---
def adjust_brightness(color, factor):
    """Adjust the brightness of a color by a factor. 
       Factor < 1 darkens, > 1 brightens."""
    r, g, b = color
    r = min(255, max(0, int(r * factor)))
    g = min(255, max(0, int(g * factor)))
    b = min(255, max(0, int(b * factor)))
    return (r, g, b)

def calculate_border_and_highlight(texture_color):
    """Calculate dynamic border color and highlight based on texture color."""
    shadow = adjust_brightness(texture_color, 0.7)  # Darker shadow for the border
    highlight = adjust_brightness(texture_color, 1.3)  # Lighter highlight for edge
    return shadow, highlight

# --- Default Front Face Colors (before dynamic calculation) ---
WALL_FRONT_COLOR = (100, 100, 100)  # Default color for the wall's front face
ROCK_CUBE_FRONT_COLOR = (80, 80, 80)
WOOD_CUBE_FRONT_COLOR = (139, 69, 19)

# Dynamically calculate border and highlight based on texture colors
WALL_BORDER_COLOR, WALL_HIGHLIGHT_COLOR = calculate_border_and_highlight(WALL_FRONT_COLOR)
ROCK_CUBE_BORDER_COLOR, ROCK_CUBE_HIGHLIGHT_COLOR = calculate_border_and_highlight(ROCK_CUBE_FRONT_COLOR)
WOOD_CUBE_BORDER_COLOR, WOOD_CUBE_HIGHLIGHT_COLOR = calculate_border_and_highlight(WOOD_CUBE_FRONT_COLOR)
