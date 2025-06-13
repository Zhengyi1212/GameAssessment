# level_page.py
import pygame
import sys

class LevelPage:
    """Displays the level selection screen."""
    def __init__(self, screen, level_controller):
        self.screen = screen
        self.screen_rect = screen.get_rect()
        self.level_controller = level_controller

        # --- Load Assets ---
        try:
            self.back_button_img = pygame.transform.scale(
                pygame.image.load('./assets/Menu/back.png').convert_alpha(), (50, 50)
            )
            self.back_button_rect = self.back_button_img.get_rect(topleft=(20, 20))
        except pygame.error as e:
            print(f"Warning: Could not load back button image: {e}")
            self.back_button_img = None

        # --- Font Loading ---
        try:
            font_path = "./assets/font.ttf"
            self.title_font = pygame.font.Font(font_path, 72)
            self.level_font = pygame.font.Font(font_path, 48)
        except pygame.error:
            self.title_font = pygame.font.SysFont("arial", 60, bold=True)
            self.level_font = pygame.font.SysFont("arial", 40, bold=True)

        # --- Colors and Layout ---
        self.text_color = (255, 255, 255)
        self.unlocked_color = (100, 180, 100)
        self.locked_color = (100, 100, 100)
        self.hover_color = (150, 220, 150)
        self.level_rects = self._create_level_rects()

    def _create_level_rects(self):
        """Creates the clickable rectangles for each level."""
        rects = {}
        cols, rect_width, rect_height, h_spacing, v_spacing = 5, 150, 100, 30, 30
        grid_width = (cols * rect_width) + ((cols - 1) * h_spacing)
        start_x = (self.screen_rect.width - grid_width) // 2
        start_y = 200

        for i in range(10): # 10 total levels
            level_num = i + 1
            x = start_x + (i % cols) * (rect_width + h_spacing)
            y = start_y + (i // cols) * (rect_height + v_spacing)
            rects[level_num] = pygame.Rect(x, y, rect_width, rect_height)
        return rects

    def run(self, events):
        """Processes events for the level page and returns a choice."""
        mouse_pos = pygame.mouse.get_pos()
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return 'menu'
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.back_button_rect and self.back_button_rect.collidepoint(mouse_pos):
                    return 'menu'
                unlocked_count = self.level_controller.get_unlocked_level_count()
                for level_num, rect in self.level_rects.items():
                    if rect.collidepoint(mouse_pos) and level_num <= unlocked_count:
                        return level_num
        return None

    def draw(self):
        """Draws the entire level selection screen."""
        mouse_pos = pygame.mouse.get_pos()
        
        # Draw Title
        title_surf = self.title_font.render("Level", True, self.text_color)
        title_rect = title_surf.get_rect(center=(self.screen_rect.centerx, 100))
        self.screen.blit(title_surf, title_rect)

        # Draw Back Button
        if self.back_button_img:
            self.screen.blit(self.back_button_img, self.back_button_rect)

        # Draw level boxes
        unlocked_count = self.level_controller.get_unlocked_level_count()
        for level_num, rect in self.level_rects.items():
            is_unlocked = level_num <= unlocked_count
            is_hovered = rect.collidepoint(mouse_pos)

            color = self.locked_color
            if is_unlocked:
                color = self.hover_color if is_hovered else self.unlocked_color
            
            pygame.draw.rect(self.screen, color, rect, border_radius=10)
            pygame.draw.rect(self.screen, self.text_color, rect, 2, border_radius=10)

            level_text_surf = self.level_font.render(str(level_num), True, self.text_color)
            level_text_rect = level_text_surf.get_rect(center=rect.center)
            self.screen.blit(level_text_surf, level_text_rect)