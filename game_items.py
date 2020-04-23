import math

import pygame
from pygame.sprite import Sprite


class Alien(Sprite):

    def __init__(self, ai_settings, screen,type):
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

        self.type = type
        self.strategy = {
            1: self.move_strategy_A,
            2: self.move_strategy_B,
            3: self.move_strategy_C
        }
        self.direction=1

    def blitme(self):
        self.screen.blit(self.image, self.rect)

    def update(self):
        self.strategy[self.type]()

    def check_edges(self):
        screen_rect = self.screen.get_rect()
        if self.rect.right >= screen_rect.right:
            return True
        elif self.rect.left <= 0:
            return True

    def move_strategy_A(self):
        self.x += self.ai_settings.alien_speed_factor * \
                  self.ai_settings.fleet_direction

        self.y += self.ai_settings.alien_speed_factor / 2
        self.rect.x = self.x
        self.rect.y = self.y

    def move_strategy_B(self):
        self.y += self.ai_settings.alien_speed_factor / 2
        self.x = math.sin(self.rect.y % math.pi) + \
                 self.ai_settings.alien_speed_factor / 2 + self.x
        self.rect.x = self.x
        self.rect.y = self.y

    def move_strategy_C(self):
        self.y += self.ai_settings.alien_speed_factor / 2
        self.rect.y = self.y


class Ship(Sprite):
    def __init__(self, screen, ai_settings):
        super().__init__()
        self.screen = screen
        image = pygame.image.load('images/doctor.jpg')
        self.image = pygame.transform.scale(image, (50, 50))
        self.rect = self.image.get_rect()
        self.screen_rect = screen.get_rect()
        self.rect.centerx = self.screen_rect.centerx
        self.rect.bottom = self.screen_rect.bottom

        self.ai_settings = ai_settings
        self.center = float(self.rect.centerx)

        self.moving_right = False
        self.moving_left = False

        self.bullet_num = [20, 10, 5]
        self.current_bullet = 1

    def update(self):
        if self.moving_right and self.rect.right < self.screen_rect.right:
            self.center += self.ai_settings.ship_speed_factor
        if self.moving_left and self.rect.left > 0:
            self.center -= self.ai_settings.ship_speed_factor

        self.rect.centerx = self.center

    def blitme(self):
        self.screen.blit(self.image, self.rect)

    def center_ship(self):
        self.center = self.screen_rect.centerx


class Bullet(Sprite):

    def __init__(self, ai_settings, screen, ship, target, type):
        super().__init__()
        self.screen = screen
        self.ai_setting = ai_settings
        self.type = type
        self.set_type()
        self.rect.centerx = ship.rect.centerx
        self.rect.top = ship.rect.top
        self.ship = ship

        self.y = float(self.rect.y)
        self.x = float(self.rect.x)

        self.target = target
        dis = math.sqrt((self.target[1] - self.rect.y) ** 2 + (
                self.target[0] - self.rect.x) ** 2)

        self.sin = -(self.target[1] - self.rect.y) / dis
        self.cos = -(self.target[0] - self.rect.x) / dis

    def update(self):
        if self.type == 1 or self.type == 2:
            self.y -= self.speed_factor * self.sin
            self.rect.y = self.y
            self.x -= self.speed_factor * self.cos
            self.rect.x = self.x
        elif self.type == 3:
            self.rect.y = self.target[1]
            self.rect.x = self.target[0]

    def draw_bullet(self):
        if self.type == 1 or self.type == 2:
            pygame.draw.rect(self.screen, self.color, self.rect)
        else:
            pygame.draw.line(self.screen, self.color, (self.ship.rect.centerx,
                                                       self.ship.rect.centery),
                             (self.target[0], self.target[1]), 2)

    def set_type(self):
        if self.type == 1:
            self.rect = pygame.Rect(0, 0, 3,
                                    3)
            self.color = (60, 60, 60)
            self.speed_factor = 30

        elif self.type == 2:
            self.rect = pygame.Rect(0, 0, 6,
                                    6)
            self.color = (0, 0, 0)
            self.speed_factor = 60

        elif self.type == 3:
            self.rect = pygame.Rect(0, 0, 3,
                                    3)
            self.color = (255, 255, 0)
            self.speed_factor = 0


class Button():
    def __init__(self, screen, msg):
        self.screen = screen
        self.screen_rect = self.screen.get_rect()

        self.width, self.height = 200, 50
        self.button_color = (0, 255, 0)
        self.text_color = (255, 255, 255)
        self.font = pygame.font.SysFont(None, 48)

        self.rect = pygame.Rect(0, 0, self.width, self.height)
        self.rect.center = self.screen_rect.center

        self.prep_msg(msg)

    def prep_msg(self, msg):
        self.msg_image = self.font.render(msg, True, self.text_color,
                                          self.button_color)
        self.msg_image_rect = self.msg_image.get_rect()
        self.msg_image_rect.center = self.rect.center

    def draw_button(self):
        self.screen.fill(self.button_color, self.rect)
        self.screen.blit(self.msg_image, self.msg_image_rect)
