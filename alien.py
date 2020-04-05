import pygame
from pygame.sprite import Sprite


class Alien(Sprite):

    def __init__(self, ai_settings, screen, id):
        super().__init__()
        self.screen = screen
        self.ai_settings = ai_settings

        image = pygame.Surface.convert_alpha(pygame.image.load(
            'images/timg.jpg'))
        self.image = pygame.transform.scale(image, (64, 49))
        self.rect = self.image.get_rect()

        self.rect.x = self.rect.width
        self.rect.y = self.rect.height

        self.x = float(self.rect.x)
        self.y = float(self.rect.y)

        self.id = id

    def blitme(self):
        self.screen.blit(self.image, self.rect)

    def update(self):
        self.move_strategy()

    def check_edges(self):
        screen_rect = self.screen.get_rect()
        if self.rect.right >= screen_rect.right:
            return True
        elif self.rect.left <= 0:
            return True

    def move_strategy(self):
        self.x += self.ai_settings.alien_speed_factor * \
                  self.ai_settings.fleet_direction

        self.y += self.ai_settings.alien_speed_factor / 2
        self.rect.x = self.x
        self.rect.y = self.y
