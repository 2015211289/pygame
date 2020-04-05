import pygame
from pygame.sprite import Sprite
import math

class Bullet(Sprite):

    def __init__(self, ai_settings, screen, ship, target, type,alien):
        super().__init__()
        self.screen = screen
        self.ai_setting=ai_settings
        self.set_type(type)
        self.type=type
        self.rect.centerx = ship.rect.centerx
        self.rect.top = ship.rect.top
        self.ship=ship

        self.y = float(self.rect.y)
        self.x = float(self.rect.x)

        self.target = target
        self.alien=alien
        dis = math.sqrt((self.target[1] - self.rect.y) ** 2 + (
                    self.target[0] - self.rect.x) ** 2)

        self.sin = -(self.target[1] - self.rect.y) / dis
        self.cos = -(self.target[0] - self.rect.x)/ dis


    def update(self):
        if self.type==1 or self.type==2:
            self.y -= self.speed_factor * self.sin
            self.rect.y = self.y
            self.x -= self.speed_factor * self.cos
            self.rect.x = self.x
        elif self.type==3:
            traces = self.ship.alien_map[self.alien.id]
            self.rect.y=traces[-1][1]
            self.rect.x=traces[-1][0]




    def draw_bullet(self):
        if self.type==1 or self.type==2:
            pygame.draw.rect(self.screen, self.color, self.rect)


    def set_type(self,type):
        if type ==1:
            self.rect = pygame.Rect(0, 0, 3,
                                    3)
            self.color = (60,60,60)
            self.speed_factor = 30

        elif type == 2:
            self.rect = pygame.Rect(0, 0, 6,
                                    6)
            self.color = (0, 0, 0)
            self.speed_factor = 60

        elif type == 3:
            self.rect = pygame.Rect(0, 0, 3,
                                    3)
            self.color = (255, 255, 0)
            self.speed_factor = 0

class BulletBoard():
    def __init__(self,ai_settings, screen,ship):
        self.screen = screen
        self.screen_rect = screen.get_rect()

        self.ai_settings = ai_settings

        self.text_color = (0, 0, 0)
        self.font = pygame.font.SysFont(None, 48)
        self.ship=ship

    def prep_bullets(self):
        bullets_str = "{0[0]} {0[1]} {0[2]}".format(self.ship.bullet_num)
        self.bullet_image = self.font.render(bullets_str, True,
                                             self.text_color,
                                            self.ai_settings.bg_color)

        self.score_rect = self.bullet_image.get_rect()
        self.score_rect.right = self.screen_rect.right - 20
        self.score_rect.bottom = self.screen_rect.bottom

    def show_board(self):
        self.screen.blit(self.bullet_image, self.score_rect)