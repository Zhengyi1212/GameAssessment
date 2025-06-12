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
        self.background_image = self._load_image("./assets/Menu/Background.png", self.screen_rect.size)
        
        # --- Font Loading ---
        try:
            font_path = "./assets/font.ttf"
            self.title_font = pygame.font.Font(font_path, 72)
            self.vs_font = pygame.font.Font(font_path, 90)
            self.button_font = pygame.font.Font(font_path, 65)
        except pygame.error as e:
            print(f"Warning: Could not load custom font at '{font_path}'. Falling back to default font.")
            self.title_font = pygame.font.SysFont("arial", 60, bold=True)
            self.vs_font = pygame.font.SysFont("arial", 80, bold=True)
            self.button_font = pygame.font.SysFont("arial", 40,bold=True),

        # --- Title and UI Text ---
        self.title_surface = self.title_font.render("A MAN WITH A SWORD", True, (255, 255, 255))
        self.title_rect = self.title_surface.get_rect(center=(self.screen_rect.centerx, 100))

        self.vs_text_surface = self.vs_font.render("VS", True, (200, 200, 220))
        self.vs_text_rect = self.vs_text_surface.get_rect(center=(self.screen_rect.centerx - 30, self.screen_rect.centery + 250))

        # --- New Button System ---
        self.buttons = []
        self._create_text_buttons()

        # --- Character Showcase Setup ---
        self.showcase_player, self.showcase_npcs = {}, []
        self._setup_characters()
        
        self.showcase_timer, self.showcase_switch_interval = 0, 2 

    def _load_image(self, path, scale_to=None):
        try:
            image = pygame.image.load(path).convert_alpha()
            if scale_to: image = pygame.transform.scale(image, scale_to)
            return image
        except pygame.error:
            print(f"Warning: Could not load image at '{path}'.")
            return None

    def _create_text_buttons(self):
        start_y = self.screen_rect.centery - 60
        for i, text in enumerate(['Start', 'Exit']):
            surface = self.button_font.render(text, True, (255, 255, 255))
            rect = pygame.Rect(0, 0, 220, 70)
            rect.center = (self.screen_rect.right - 150, start_y + i * 100)
            self.buttons.append({'surface': surface, 'rect': rect, 'action': text.lower(), 'hovered': False})

    def _setup_characters(self):
        ground_y = self.screen_rect.height - (TARGET_PLAYER_HEIGHT * 1.3) + 60

        player = Player(0, 0, None)
        player.facing_direction = "right"
        player.current_screen_x, player.current_screen_y = 180, ground_y
        self.showcase_player = {'object': player, 'animations': ['idle', 'attack'], 'current_anim_index': 0}

        base_x = self.screen_rect.width - 200
        npc_data = [
            ("orc", base_x - 90, ground_y+155, ['idle', 'walk_left']),
            ("orc2", base_x - 160, ground_y+155, ['idle', 'walk_left']),
            ("demon", base_x - 220, ground_y+160, ['idle', 'fly'])
        ]
        for type, x, y, anims in npc_data:
            npc = NPC(0, 0, None, npc_type=type)
            npc.facing_direction = 'left'
            npc.current_screen_x, npc.current_screen_y = x, y
            self.showcase_npcs.append({'object': npc, 'animations': anims, 'current_anim_index': 0})
        self._update_character_animation_states()

    def _update_character_animation_states(self):
        p_info = self.showcase_player
        player_obj = p_info['object']
        p_anim = p_info['animations'][p_info['current_anim_index']]
        
        if p_anim == 'attack':
            player_obj.start_attack()
        else:
            player_obj.current_action = 'idle'
            player_obj.is_attacking = False


        for n_info in self.showcase_npcs:
            npc, n_anim = n_info['object'], n_info['animations'][n_info['current_anim_index']]
            npc.is_moving_animation_active = 'walk' in n_anim or 'fly' in n_anim
            if npc.is_moving_animation_active: 
                direction = n_anim.split('_')[-1]
                npc.facing_direction = direction

    def _draw_characters(self):
        # Draw Player
        player_obj = self.showcase_player['object']
        if player_obj.current_image:
            w, h = player_obj.current_image.get_size()
            scaled_image = pygame.transform.scale(player_obj.current_image, (int(w * 1.3), int(h * 1.3)))
            self.screen.blit(scaled_image, (player_obj.current_screen_x, player_obj.current_screen_y))

        # Draw NPCs
        for npc_info in self.showcase_npcs:
            npc_obj = npc_info['object']
            image_to_draw = npc_obj.current_base_image
            if image_to_draw:
                if npc_obj.sprite_flipped:
                    image_to_draw = pygame.transform.flip(image_to_draw, True, False)
                w, h = image_to_draw.get_size()
                scaled_image = pygame.transform.scale(image_to_draw, (int(w * 1.3), int(h * 1.3)))
                self.screen.blit(scaled_image, (npc_obj.current_screen_x, npc_obj.current_screen_y))

    def run(self, events):
        dt, mouse_pos = self.clock.tick(60) / 1000.0, pygame.mouse.get_pos()

        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE: 
                return "exit"
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for button in self.buttons:
                    if button['rect'].collidepoint(mouse_pos): 
                        return button['action']

        for button in self.buttons: 
            button['hovered'] = button['rect'].collidepoint(mouse_pos)

        self.showcase_timer += dt
        if self.showcase_timer >= self.showcase_switch_interval:
            self.showcase_timer = 0
            self.showcase_player['current_anim_index'] = (self.showcase_player['current_anim_index'] + 1) % len(self.showcase_player['animations'])
            for info in self.showcase_npcs: 
                info['current_anim_index'] = (info['current_anim_index'] + 1) % len(info['animations'])
            self._update_character_animation_states()

        self.showcase_player['object'].update(dt, [])
        for info in self.showcase_npcs: 
            info['object'].update_animation(dt)

        if self.background_image: self.screen.blit(self.background_image, (0, 0))
        else: self.screen.fill((46, 80, 93))
        
        self.screen.blit(self.title_surface, self.title_rect)
        self.screen.blit(self.vs_text_surface, self.vs_text_rect)

        for button in self.buttons:
            if button['hovered']:
                hover_surf = pygame.Surface(button['rect'].size, pygame.SRCALPHA)
                hover_surf.fill((128, 128, 128, 160))
                self.screen.blit(hover_surf, button['rect'].topleft)
            text_rect = button['surface'].get_rect(center=button['rect'].center)
            self.screen.blit(button['surface'], text_rect)

        self._draw_characters()
