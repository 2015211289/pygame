import pygame
from pygame.sprite import Sprite


class Area(Sprite):

    def __init__(self, ai_settings, screen):
        super().__init__()
        self.screen = screen
        self.ai_settings = ai_settings
        self.screen_rect = self.screen.get_rect()

        self.center_point = (self.screen_rect.centerx, self.screen_rect.centery)
        self.radius = 200
        self.width = 2
        self.color = (255, 0, 0)
        # 用于API判定冲突,暂时没用到
        self.rect = pygame.Rect(self.screen_rect.centerx,
                                self.screen_rect.centery, 0, 0)

    def blitme(self):
        pygame.draw.circle(self.screen, self.color, self.center_point,
                           self.radius,
                           self.width)
