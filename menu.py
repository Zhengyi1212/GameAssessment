# menu.py
import pygame
import sys
from player import Player, TARGET_PLAYER_HEIGHT
from npc import NPC

class Menu:
    """Manages the main menu screen, its buttons, and character showcase."""
    def __init__(self, screen):
        self.screen = screen
        self.screen_rect = screen.get_rect()
        self.clock = pygame.time.Clock()

        # --- Load Assets ---
        self.background_image = self._load_image("./assets/Menu/Background.jpg", self.screen_rect.size)
        self.start_button_img = self._load_image("./assets/Menu/Start.png")
        self.exit_button_img = self._load_image("./assets/Menu/Exit.png")

        # --- FIX: Load a custom .ttf font for the title ---
        try:
            # NOTE: Change "Silver.ttf" to the actual name of your font file in the assets folder.
            title_font_path = "./assets/font.ttf"
            self.title_font = pygame.font.Font(title_font_path, 72)
        except pygame.error as e:
            print(f"Warning: Could not load custom font at '{title_font_path}'. Error: {e}")
            print("Falling back to default system font.")
            self.title_font = pygame.font.SysFont("arial", 60)


        # Create button rectangles and position them
        if self.start_button_img:
            self.start_button_rect = self.start_button_img.get_rect(center=(self.screen_rect.centerx, self.screen_rect.centery - 50))
        else: # Fallback if image is missing
            self.start_button_rect = pygame.Rect(0, 0, 200, 50)
            self.start_button_rect.center = (self.screen_rect.centerx, self.screen_rect.centery - 50)

        if self.exit_button_img:
            self.exit_button_rect = self.exit_button_img.get_rect(center=(self.screen_rect.centerx, self.screen_rect.centery + 50))
        else: # Fallback if image is missing
            self.exit_button_rect = pygame.Rect(0, 0, 200, 50)
            self.exit_button_rect.center = (self.screen_rect.centerx, self.screen_rect.centery + 50)

        # Create the title text surface and position it
        self.title_text = "A MAN WITH A SWORD"
        self.title_surface = self.title_font.render(self.title_text, True, (255, 255, 255)) # White text
        self.title_rect = self.title_surface.get_rect()
        self.title_rect.centerx = self.screen_rect.centerx
        self.title_rect.bottom = self.start_button_rect.top - 20 # 20 pixels above the start button

        # --- Character Showcase Setup ---
        self.showcase_player = {}
        self.showcase_npcs = []
        self._setup_characters()
        
        # Use a single, unified timer for all showcase animations.
        self.showcase_timer = 0
        self.showcase_switch_interval = 2 # 2-second interval between each animation state

    def _load_image(self, path, scale_to=None):
        """Helper function to load an image and handle errors."""
        try:
            image = pygame.image.load(path).convert_alpha()
            if scale_to:
                image = pygame.transform.scale(image, scale_to)
            return image
        except pygame.error:
            print(f"Warning: Could not load image at '{path}'.")
            return None

    def _setup_characters(self):
        """Create and position the characters for the showcase."""
        # Player setup (on the left)
        player = Player(0, 0, None)
        player.facing_direction = "down"
        player.current_screen_x = 40
        player.current_screen_y = self.screen_rect.height - (TARGET_PLAYER_HEIGHT * 1.3) - 30
        self.showcase_player = {
            'object': player,
            'animations': ['idle', 'attack'],
            'current_anim_index': 0
        }

        # Adjust X position to make more room for larger sprites
        right_side_x = self.screen_rect.width - 100

        # Create Orc1
        orc1 = NPC(0, 0, None, npc_type="orc")
        orc1.current_screen_x = right_side_x - 110
        orc1.current_screen_y = self.screen_rect.centery - 45 
        self.showcase_npcs.append({
            'object': orc1,
            'animations': ['walk_down', 'idle', 'walk_up', 'idle', 'walk_left', 'idle', 'walk_right', 'idle'],
            'current_anim_index': 0
        })

        # Create Orc2
        orc2 = NPC(0, 0, None, npc_type="orc2")
        orc2.current_screen_x = right_side_x - 180
        orc2.current_screen_y = self.screen_rect.centery + 60
        self.showcase_npcs.append({
            'object': orc2,
            'animations': ['walk_down', 'idle', 'walk_up', 'idle', 'walk_left', 'idle', 'walk_right', 'idle'],
            'current_anim_index': 4 
        })
        
        # Create Demon
        demon = NPC(0, 0, None, npc_type="demon")
        demon.current_screen_x = right_side_x - 320
        demon.current_screen_y = self.screen_rect.centery + 120
        self.showcase_npcs.append({
            'object': demon,
            'animations': ['idle', 'fly'], 
            'current_anim_index': 0
        })

        # Set initial animation state for all NPCs
        self._update_character_animation_states()

    def _update_character_animation_states(self):
        """Sets the internal state of ALL characters based on their individual showcase animation sequence."""
        # Update Player State
        player_obj = self.showcase_player['object']
        player_anim_name = self.showcase_player['animations'][self.showcase_player['current_anim_index']]
        if player_anim_name == 'idle':
            player_obj.current_action = 'idle'
        elif player_anim_name == 'attack':
            player_obj.start_attack()

        # Update NPC States
        for npc_info in self.showcase_npcs:
            npc = npc_info['object']
            anim_list = npc_info['animations']
            current_index = npc_info['current_anim_index']
            animation_name = anim_list[current_index]

            if animation_name == 'idle':
                npc.is_moving_animation_active = False
            elif animation_name == 'fly':
                npc.is_moving_animation_active = True
                npc.facing_direction = 'right'
            elif 'walk' in animation_name:
                npc.is_moving_animation_active = True
                direction = animation_name.split('_')[-1]
                npc.facing_direction = direction

    def run(self):
        """The main loop for the menu. Returns the user's choice."""
        while True:
            dt = self.clock.tick(60) / 1000.0

            # --- Event Handling ---
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "exit"
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return "exit"
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        if self.start_button_rect.collidepoint(event.pos):
                            return "start"
                        if self.exit_button_rect.collidepoint(event.pos):
                            return "exit"

            # --- Update Logic ---
            # Use the single, unified timer to switch all character animations.
            self.showcase_timer += dt
            if self.showcase_timer >= self.showcase_switch_interval:
                self.showcase_timer = 0
                
                # Advance the animation index for the player
                self.showcase_player['current_anim_index'] = \
                    (self.showcase_player['current_anim_index'] + 1) % len(self.showcase_player['animations'])

                # Advance the animation index for each NPC independently
                for npc_info in self.showcase_npcs:
                    npc_info['current_anim_index'] = (npc_info['current_anim_index'] + 1) % len(npc_info['animations'])
                
                # Apply all the new states to the character objects
                self._update_character_animation_states()

            # Update all character animation frames (this runs the animation itself)
            self.showcase_player['object'].update(dt, [])
            for npc_info in self.showcase_npcs:
                npc_info['object'].update_animation(dt)

            # --- Drawing Logic ---
            if self.background_image:
                self.screen.blit(self.background_image, (0, 0))
            else:
                self.screen.fill((46, 80, 93))

            # Draw the title
            self.screen.blit(self.title_surface, self.title_rect)

            # Buttons
            if self.start_button_img:
                self.screen.blit(self.start_button_img, self.start_button_rect)
            else:
                pygame.draw.rect(self.screen, (0, 150, 0), self.start_button_rect)
                font = pygame.font.Font(None, 36)
                text = font.render("START", True, (255, 255, 255))
                self.screen.blit(text, text.get_rect(center=self.start_button_rect.center))
            
            if self.exit_button_img:
                self.screen.blit(self.exit_button_img, self.exit_button_rect)
            else:
                pygame.draw.rect(self.screen, (150, 0, 0), self.exit_button_rect)
                font = pygame.font.Font(None, 36)
                text = font.render("EXIT", True, (255, 255, 255))
                self.screen.blit(text, text.get_rect(center=self.exit_button_rect.center))

            # New character drawing logic to scale them up by 1.3x
            # Draw Player
            player_obj = self.showcase_player['object']
            if player_obj.current_image:
                original_size = player_obj.current_image.get_size()
                new_size = (int(original_size[0] * 1.3), int(original_size[1] * 1.3))
                scaled_image = pygame.transform.scale(player_obj.current_image, new_size)
                self.screen.blit(scaled_image, (player_obj.current_screen_x, player_obj.current_screen_y))

            # Draw NPCs
            for npc_info in self.showcase_npcs:
                npc_obj = npc_info['object']
                image_to_draw = npc_obj.current_base_image
                if image_to_draw:
                    if npc_obj.sprite_flipped:
                        image_to_draw = pygame.transform.flip(image_to_draw, True, False)
                    
                    original_size = image_to_draw.get_size()
                    new_size = (int(original_size[0] * 1.3), int(original_size[1] * 1.3))
                    scaled_image = pygame.transform.scale(image_to_draw, new_size)
                    self.screen.blit(scaled_image, (npc_obj.current_screen_x, npc_obj.current_screen_y))

            pygame.display.flip()