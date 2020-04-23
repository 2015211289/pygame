import pygame
from pygame.sprite import Sprite


class Area(Sprite):

    def __init__(self, ai_settings, screen):
        super().__init__()
        self.screen = screen
        self.ai_settings = ai_settings
        self.screen_rect = self.screen.get_rect()

        self.center_point = (self.screen_rect.centerx, self.screen_rect.centery)
        self.radius = self.ai_settings.area_radius
        self.width = self.ai_settings.area_width
        self.color = self.ai_settings.area_color

        self.rect = pygame.Rect(self.screen_rect.centerx,
                                self.screen_rect.centery, 0, 0)

    def blitme(self):
        pygame.draw.circle(self.screen, self.color, self.center_point,
                           self.radius,
                           self.width)
