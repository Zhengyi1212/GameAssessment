# level_page.py
import pygame
import sys

class LevelPage:
    """Displays the level selection screen."""
    def __init__(self, screen, level_controller):
        self.screen = screen
        self.screen_rect = screen.get_rect()
        self.level_controller = level_controller
        self.clock = pygame.time.Clock()

        # --- Load Sound ---
        try:
            self.click_sound = pygame.mixer.Sound('./assets/click.mp3')
        except pygame.error as e:
            print(f"Warning: Could not load click sound: {e}")
            self.click_sound = None

        # --- Font Loading ---
        try:
            font_path = "./assets/font.ttf"
            self.title_font = pygame.font.Font(font_path, 72)
            self.level_font = pygame.font.Font(font_path, 48)
        except pygame.error:
            self.title_font = pygame.font.SysFont("arial", 60, bold=True)
            self.level_font = pygame.font.SysFont("arial", 40, bold=True)

        # --- Colors and Layout ---
        self.bg_color = (46, 80, 93)
        self.unlocked_color = (100, 180, 100)
        self.locked_color = (100, 100, 100)
        self.hover_color = (150, 220, 150)
        self.text_color = (255, 255, 255)

        self.level_rects = self._create_level_rects()

    def _create_level_rects(self):
        """Creates the clickable rectangles for each level."""
        rects = {}
        cols = 5
        rows = 2
        total_levels = 10
        
        rect_width = 150
        rect_height = 100
        h_spacing = 30
        v_spacing = 30
        
        grid_width = (cols * rect_width) + ((cols - 1) * h_spacing)
        start_x = (self.screen_rect.width - grid_width) // 2
        start_y = 200

        for i in range(total_levels):
            level_num = i + 1
            col = i % cols
            row = i // cols
            
            x = start_x + col * (rect_width + h_spacing)
            y = start_y + row * (rect_height + v_spacing)
            
            rects[level_num] = pygame.Rect(x, y, rect_width, rect_height)
        return rects

    def run(self, events):
        """The main loop for the level selection screen."""
        mouse_pos = pygame.mouse.get_pos()
        
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.click_sound:
                        self.click_sound.play()
                    return 'menu'
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                unlocked_count = self.level_controller.get_unlocked_level_count()
                for level_num, rect in self.level_rects.items():
                    if rect.collidepoint(mouse_pos) and level_num <= unlocked_count:
                        if self.click_sound:
                            self.click_sound.play()
                        return level_num

        # --- Drawing ---
        # The main loop now fills the screen, so we just draw our content.
        
        # Draw Title
        title_surf = self.title_font.render("Level", True, self.text_color)
        title_rect = title_surf.get_rect(center=(self.screen_rect.centerx, 100))
        self.screen.blit(title_surf, title_rect)

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