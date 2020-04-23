from pygame.sprite import Group

from game_items import *


class GameStats():

    def __init__(self, ai_settings):
        self.ai_settings = ai_settings
        self.reset_stats()
        self.game_active = False
        self.high_score = 0

    def reset_stats(self):
        self.ships_left = self.ai_settings.ship_limit
        self.score = 0
        self.level = 1


class Scoreboard():

    def __init__(self, ai_settings, screen, stats):
        self.screen = screen
        self.screen_rect = screen.get_rect()

        self.ai_settings = ai_settings
        self.stats = stats

        self.text_color = (30, 30, 30)
        self.font = pygame.font.SysFont(None, 48)

        self.prep_score()
        self.prep_high_score()
        self.prep_level()
        self.prep_ships()

    def prep_score(self):
        rounded_score = round(self.stats.score, -1)
        score_str = "{:,}".format(rounded_score)
        self.score_image = self.font.render(score_str, True, self.text_color,
                                            self.ai_settings.bg_color)

        self.score_rect = self.score_image.get_rect()
        self.score_rect.right = self.screen_rect.right - 20
        self.score_rect.top = 10

    def prep_high_score(self):
        rounded_score = round(self.stats.high_score, -1)
        score_str = "{:,}".format(rounded_score)
        self.high_score_image = self.font.render(score_str, True,
                                                 self.text_color,
                                                 self.ai_settings.bg_color)

        self.high_score_rect = self.high_score_image.get_rect()
        self.high_score_rect.centerx = self.screen_rect.centerx
        self.high_score_rect.top = self.score_rect.top

    def prep_level(self):
        self.level_image = self.font.render(str(self.stats.level), True,
                                            self.text_color,
                                            self.ai_settings.bg_color)

        self.level_rect = self.level_image.get_rect()
        self.level_rect.right = self.score_rect.right
        self.level_rect.top = self.score_rect.bottom + 10

    def prep_ships(self):
        self.ships = Group()
        for ship_number in range(self.stats.ships_left):
            ship = Ship(self.screen, self.ai_settings)
            ship.rect.x = 10 + ship_number * ship.rect.width
            ship.rect.y = 10
            self.ships.add(ship)

    def show_score(self):
        self.screen.blit(self.score_image, self.score_rect)
        self.screen.blit(self.high_score_image, self.high_score_rect)
        self.screen.blit(self.level_image, self.level_rect)
        self.ships.draw(self.screen)


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