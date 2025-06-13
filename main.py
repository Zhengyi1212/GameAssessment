# main.py
import pygame
import sys
from game_manager import GameManager

def main():
    """Main function to initialize and run the game."""
    pygame.init()
    pygame.mixer.init()

    # --- Initialize and run the game manager ---
    game_manager = GameManager()
    game_manager.run()

    # --- Cleanup ---
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()