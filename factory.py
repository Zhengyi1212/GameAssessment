# factory.py
from cube import FloorCube, WallCube, RockCube, WoodCube

class CubeFactory:
    """A factory for creating different types of Cube objects."""
    
    # Map characters from the map file to their corresponding cube classes
    _cube_map = {
        'W': WallCube,
        'R': RockCube,
        'O': WoodCube,
        'P': FloorCube
    }

    @staticmethod
    def create_cube(cube_char):
        """
        Creates a cube instance based on a character symbol.
        Defaults to FloorCube if the character is not recognized.
        """
        cube_class = CubeFactory._cube_map.get(cube_char, FloorCube)
        return cube_class()