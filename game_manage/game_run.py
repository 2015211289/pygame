import sys
from time import sleep
import concurrent.futures

import pygame.font

from auto_review import Monitor
from data_statistic import *
from game_env import *
from game_items import *
from game_manage.game_setup import Settings


def exit_game():
    sys.exit()


def ship_hit(ai_settings, screen, stats, sb, ship, aliens, bullets):
    if stats.ships_left > 0:

        # stats.ships_left -= 1
        sb.prep_ships()

        aliens.empty()
        bullets.empty()

        ship.center_ship()

        sleep(0.5)
    else:
        stats.game_active = False


def check_events(ai_settings, screen, stats, sb, play_button, ship,
                 aliens, bullets):
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            exit_game()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            check_play_button(ai_settings, screen, stats, sb,
                              play_button, ship, aliens, bullets,
                              mouse_x, mouse_y)

        elif event.type == pygame.KEYDOWN:
            check_keydown_events(event, ai_settings, screen, ship, bullets)

        elif event.type == pygame.KEYUP:
            check_keyup_events(event, ship)


def check_play_button(ai_settings, screen, stats, sb, play_button, ship, aliens,
                      bullets, mouse_x, mouse_y):
    if play_button.rect.collidepoint(mouse_x, mouse_y) and \
            not stats.game_active:
        ai_settings.initialize_dynamic_settings()

        stats.reset_stats()
        stats.game_active = True

        sb.prep_score()
        sb.prep_high_score()
        sb.prep_level()
        sb.prep_ships()

        aliens.empty()
        bullets.empty()

        ship.center_ship()


def check_keydown_events(event, ai_settings, screen, ship, bullets):
    if event.key == pygame.K_RIGHT:
        ship.moving_right = True
    elif event.key == pygame.K_LEFT:
        ship.moving_left = True
    elif event.key == pygame.K_SPACE:
        fire_bullet(ai_settings, screen, ship, bullets, (ship.rect.centerx, 0))
    elif event.key == pygame.K_q:
        exit_game()
    elif event.key == pygame.K_1:
        ship.current_bullet = 1
    elif event.key == pygame.K_2:
        ship.current_bullet = 2
    elif event.key == pygame.K_3:
        ship.current_bullet = 3


def check_keyup_events(event, ship):
    if event.key == pygame.K_RIGHT:
        ship.moving_right = False
    elif event.key == pygame.K_LEFT:
        ship.moving_left = False


def update_screen(ai_settings, screen, stats, sb, ship, aliens, bullets,
                  play_button, area, monitor):
    screen.fill(ai_settings.bg_color)
    for alien in aliens:
        alien.blitme()

    # 自动化运行
    if stats.game_active and ai_settings.auto:
        monitor.get_pixelArray()
        if ai_settings.time % 3 ==0:
            monitor.backDiff()
        monitor.update_particle_groups()
        monitor.targets_association()
        monitor.show_predicts()

    for bullet in bullets.sprites():
        bullet.draw_bullet()

    ship.blitme()
    area.blitme()

    sb.show_score()

    if not stats.game_active:
        play_button.draw_button()

    pygame.display.flip()


def update_bullets(ai_settings, screen, stats, sb, ship, aliens, bullets):
    bullets.update()
    for bullet in bullets.copy():
        if bullet.rect.bottom <= 0:
            bullets.remove(bullet)
    check_bullet_alien_collisions(ai_settings, stats, sb,
                                  aliens, bullets)


def check_bullet_alien_collisions(ai_settings, stats, sb,
                                  aliens, bullets):
    collisions = pygame.sprite.groupcollide(bullets, aliens, True, True)
    if collisions:
        for aliens in collisions.values():
            stats.score += ai_settings.alien_points * len(aliens)
            sb.prep_score()
        check_high_score(stats, sb)


def fire_bullet(ai_settings, screen, ship, bullets, target):
    if ship.bullet_num[ship.current_bullet - 1] > 0:
        new_bullet = Bullet(ai_settings, screen, ship, target,
                            ship.current_bullet)
        bullets.add(new_bullet)
        ship.bullet_num[ship.current_bullet - 1] -= 1


def create_alien(ai_settings, screen, aliens):
    type = random.randint(1, 3)
    image_type = random.randint(0, 1)
    alien = Alien(ai_settings, screen, type, image_type)
    width, height = screen.get_size()
    alien.rect.centerx = random.randint(alien.rect.width,
                                        width - alien.rect.width)
    alien.rect.centery = random.randint(alien.rect.height,
                                        height - alien.rect.height)
    aliens.add(alien)


def update_aliens(ai_settings, screen, stats, sb, ship, aliens, bullets):
    check_aliens_edges(ai_settings, aliens)
    aliens.update()

    # if pygame.sprite.spritecollideany(ship, aliens):
    #     ship_hit(ai_settings, screen, stats, sb, ship, aliens, bullets)

    check_aliens_bottom(ai_settings, screen, stats, sb, ship, aliens,
                        bullets)


def check_aliens_edges(ai_settings, aliens):
    for alien in aliens.sprites():
        if alien.check_edges():
            alien.direction *= -1


def check_aliens_bottom(ai_settings, screen, stats, sb, ship, aliens, bullets):
    screen_rect = screen.get_rect()
    for alien in aliens.copy():
        if alien.rect.bottom >= screen_rect.bottom:
            aliens.remove(alien)


def check_high_score(stats, sb):
    if stats.score > stats.high_score:
        stats.high_score = stats.score
        sb.prep_high_score()


def run_game(pool):
    # initiate
    pygame.init()
    FPS = 30  # frames per second setting
    fpsClock = pygame.time.Clock()

    ai_settings = Settings()
    screen = pygame.display.set_mode((ai_settings.screen_width,
                                      ai_settings.screen_height))
    pygame.display.set_caption('pygame')

    play_button = Button(screen, "play")
    ship = Ship(screen, ai_settings)
    area = Area(ai_settings, screen)
    bullets = Group()
    aliens = Group()

    stats = GameStats(ai_settings)
    sb = Scoreboard(ai_settings, screen, stats)
    monitor = Monitor(screen, ai_settings,pool)

    # recycle
    while True:
        check_events(ai_settings, screen, stats, sb, play_button, ship,
                     aliens,
                     bullets)

        if stats.game_active:

            if ai_settings.time % 10 == 0:
                create_alien(ai_settings, screen, aliens)
            ai_settings.time += 1
            ship.update()
            update_bullets(ai_settings, screen, stats, sb,
                           ship, aliens, bullets)
            update_aliens(ai_settings, screen, stats, sb, ship, aliens,
                          bullets)

        update_screen(ai_settings, screen, stats, sb, ship,
                      aliens, bullets, play_button, area, monitor)

        fpsClock.tick(FPS)


if __name__ == '__main__':
    pool=concurrent.futures.ProcessPoolExecutor()
    run_game(pool)
