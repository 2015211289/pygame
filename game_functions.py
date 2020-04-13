import random
import sys
from time import sleep

import pygame

from alien import Alien
from bullet import Bullet


def exit_game():
    # pygame.mixer.music.fadeout(1000)
    sleep(1)
    sys.exit()


def ship_hit(ai_settings, screen, stats, sb, ship, aliens, bullets):
    if stats.ships_left > 0:

        stats.ships_left -= 1
        sb.prep_ships()

        aliens.empty()
        bullets.empty()

        create_fleet(ai_settings, screen, ship, aliens)
        ship.center_ship()

        sleep(0.5)
    else:
        stats.game_active = False
        pygame.mouse.set_visible(True)


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


def check_areas(ai_settings, screen, ship, aliens, area, bullets):
    for alien in aliens:
        if (ship.recognize_rect.x - area.rect.x) ** 2 + (
                ship.recognize_rect.y - area.rect.y) ** 2 <= area.radius ** 2:
            if alien.id in ship.alien_map:
                ship.alien_map[alien.id].append((ship.recognize_rect.x,
                                                 ship.recognize_rect.y))
            else:
                ship.alien_map[alien.id] = [(ship.recognize_rect.x,
                                             ship.recognize_rect.y)]

            fire_bullet(ai_settings, screen, ship, bullets,
                        ship.shoot_strategy(alien.id), alien)


def check_play_button(ai_settings, screen, stats, sb, play_button, ship, aliens,
                      bullets, mouse_x, mouse_y):
    if play_button.rect.collidepoint(mouse_x, mouse_y) and \
            not stats.game_active:
        # pygame.mixer.music.load('music/Tchaikovsky.MP3')
        # pygame.mixer.music.play(-1)
        ai_settings.initialize_dynamic_settings()

        stats.reset_stats()
        stats.game_active = True

        sb.prep_score()
        sb.prep_high_score()
        sb.prep_level()
        sb.prep_ships()

        aliens.empty()
        bullets.empty()

        create_fleet(ai_settings, screen, ship, aliens)
        ship.center_ship()


def check_keydown_events(event, ai_settings, screen, ship, bullets):
    if event.key == pygame.K_RIGHT:
        ship.moving_right = True
    elif event.key == pygame.K_LEFT:
        ship.moving_left = True
    elif event.key == pygame.K_SPACE:
        fire_bullet(ai_settings, screen, ship, bullets)
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
                  play_button, area):
    screen.fill(ai_settings.bg_color)
    for bullet in bullets.sprites():
        bullet.draw_bullet()

    ship.blitme()
    area.blitme()

    ship.shoot_target()
    # aliens.draw(screen)
    for alien in aliens:
        alien.blitme()

    ship.search_particles(screen)
    ship.show_recognize()

    sb.show_score()

    if not stats.game_active:
        play_button.draw_button()

    if ship.bullet and ship.bullet.type == 3:
        pygame.draw.line(screen, ship.bullet.color, (ship.bullet.ship.rect.x,
                                                     ship.bullet.ship.rect.y),
                         (ship.bullet.rect.x, ship.bullet.rect.y), 4)
        ship.bullet = None

    pygame.display.flip()


def update_bullets(ai_settings, screen, stats, sb, ship, aliens, bullets):
    bullets.update()
    for bullet in bullets.copy():
        if bullet.rect.bottom <= 0:
            bullets.remove(bullet)
    check_bullet_alien_collisions(ai_settings, screen, stats, sb, ship,
                                  aliens, bullets)


def check_bullet_alien_collisions(ai_settings, screen, stats, sb, ship,
                                  aliens, bullets):
    collisions = pygame.sprite.groupcollide(bullets, aliens, True, True)
    if collisions:
        for aliens in collisions.values():
            stats.score += ai_settings.alien_points * len(aliens)
            sb.prep_score()
        check_high_score(stats, sb)

    if len(aliens) == 0:
        bullets.empty()
        # ai_settings.increase_speed()

        stats.level += 1
        sb.prep_level()
        ship.alien_map.clear()
        create_fleet(ai_settings, screen, ship, aliens)


def fire_bullet(ai_settings, screen, ship, bullets, target, alien):
    if ship.bullet_num[ship.current_bullet - 1] > 0:
        new_bullet = Bullet(ai_settings, screen, ship, target,
                            ship.current_bullet, alien)
        bullets.add(new_bullet)
        ship.bullet_num[ship.current_bullet - 1] -= 1
        ship.bullet = new_bullet


def create_fleet(ai_settings, screen, ship, aliens):
    alien = Alien(ai_settings, screen, 1)
    alien.x = random.uniform(1, ai_settings.screen_width - alien.rect.width)
    aliens.add(alien)
    ship.alien_map.clear()
    ship.target.clear()
    ship.particles.clear()
    ship.getTarget(alien)
    ship.init_parciles()

    # number_aliens_x = get_number_aliens_x(ai_settings, alien.rect.width)
    # number_rows = get_number_rows(ai_settings, ship.rect.height,
    #                               alien.rect.height)
    # for row_number in range(number_rows):
    #     for alien_number in range(number_aliens_x):
    #         create_alien(ai_settings, screen, aliens, alien_number, row_number)


def get_number_aliens_x(ai_settings, alien_width):
    available_space_x = ai_settings.screen_width - 2 * alien_width
    number_aliens_x = int(available_space_x / (2 * alien_width))
    return number_aliens_x


def create_alien(ai_settings, screen, aliens, alien_number, row_number):
    alien = Alien(ai_settings, screen)
    alien_width = alien.rect.width
    alien.x = alien_width + 2 * alien_width * alien_number
    alien.rect.x = alien.x
    alien.rect.y = alien.rect.height + 2 * alien.rect.height * row_number
    aliens.add(alien)


def get_number_rows(ai_settings, ship_height, alien_height):
    available_space_y = (ai_settings.screen_height - (3 * alien_height)
                         - ship_height)
    number_rows = int(available_space_y / (2 * alien_height))
    return number_rows


def update_aliens(ai_settings, screen, stats, sb, ship, aliens, bullets):
    check_fleet_edges(ai_settings, aliens)
    aliens.update()

    if pygame.sprite.spritecollideany(ship, aliens):
        ship_hit(ai_settings, screen, stats, sb, ship, aliens, bullets)

    check_aliens_bottom(ai_settings, screen, stats, sb, ship, aliens,
                        bullets)


def check_fleet_edges(ai_settings, aliens):
    for alien in aliens.sprites():
        if alien.check_edges():
            change_fleet_direction(ai_settings, aliens)
            break


def change_fleet_direction(ai_settings, aliens):
    for alien in aliens.sprites():
        alien.rect.y += ai_settings.fleet_drop_speed
    ai_settings.fleet_direction *= -1


def check_aliens_bottom(ai_settings, screen, stats, sb, ship, aliens, bullets):
    screen_rect = screen.get_rect()
    for alien in aliens.sprites():
        if alien.rect.bottom >= screen_rect.bottom:
            ship_hit(ai_settings, screen, stats, sb, ship, aliens, bullets)
            break


def check_high_score(stats, sb):
    if stats.score > stats.high_score:
        stats.high_score = stats.score
        sb.prep_high_score()
