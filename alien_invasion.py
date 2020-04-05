import pygame
from pygame.sprite import Group

import game_functions as gf
from button import Button
from game_stats import GameStats
from scoreboard import Scoreboard
from settings import Settings
from ship import Ship
from shoot_area import Area


def run_game():
    # initiate
    pygame.init()
    FPS = 30  # frames per second setting
    fpsClock = pygame.time.Clock()

    ai_settings = Settings()
    screen = pygame.display.set_mode((ai_settings.screen_width,
                                      ai_settings.screen_height))
    pygame.display.set_caption('Fight the virus')

    play_button = Button(ai_settings, screen, "play")
    ship = Ship(screen, ai_settings)
    area=Area(ai_settings,screen)
    bullets = Group()

    aliens = Group()

    stats = GameStats(ai_settings)
    sb = Scoreboard(ai_settings, screen, stats)

    # recycle
    while True:
        gf.check_events(ai_settings, screen, stats, sb, play_button, ship,
                        aliens,
                        bullets)
        gf.check_areas(ai_settings,screen,ship,aliens,area,bullets)


        if stats.game_active:
            ship.update()
            gf.update_bullets(ai_settings, screen, stats, sb,
                              ship, aliens, bullets)
            gf.update_aliens(ai_settings, screen, stats, sb, ship, aliens,
                             bullets)

        gf.update_screen(ai_settings, screen, stats, sb, ship,
                         aliens, bullets, play_button, area)

        fpsClock.tick(FPS)


if __name__ == '__main__':
    run_game()
