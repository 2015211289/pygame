import random

import numpy
import pygame
from pygame.sprite import Sprite

from bullet import BulletBoard
from particle import Particle


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

        self.alien_map = {}
        self.avex = 0
        self.avey = 0

        self.target = []
        self.target_width = 0
        self.target_length = 0
        self.particles = []
        self.particles_num = 100
        self.recognize_rect = pygame.Rect(0, 0, 0, 0)

        self.bullet_num = [20, 10, 5]
        self.current_bullet = 1
        self.bullets_board = BulletBoard(ai_settings, screen, self)
        self.bullet = None
        self.shoot_light = 0

    def update(self):
        if self.moving_right and self.rect.right < self.screen_rect.right:
            self.center += self.ai_settings.ship_speed_factor
        if self.moving_left and self.rect.left > 0:
            self.center -= self.ai_settings.ship_speed_factor

        self.rect.centerx = self.center

    def blitme(self):
        self.screen.blit(self.image, self.rect)
        self.bullets_board.prep_bullets()
        self.bullets_board.show_board()

    def center_ship(self):
        self.center = self.screen_rect.centerx

    def shoot_strategy(self, id):
        traces = self.alien_map[id]
        ave_x = (traces[-1][0] - traces[0][0]) / len(traces)
        ave_y = (traces[-1][1] - traces[0][1]) / len(traces)
        self.avex = 0.9 * ave_x + 0.1 * self.avex
        self.avey = 0.9 * ave_y + 0.1 * self.avey
        return (traces[-1][0] + 15 * self.avex, traces[-1][1] + 15 * self.avey)

    def shoot_target(self):
        if 1 in self.alien_map:
            traces = self.alien_map[1]
            pygame.draw.circle(self.screen, (0, 0, 255),
                               (round(traces[-1][0] + 15 * self.avex),
                                round(traces[-1][1] + 15 * self.avey)),
                               5, 0)

    def getTarget(self, alien):
        width, length = alien.image.get_size()
        pixelArray = numpy.zeros((width, length, 3), dtype=int)
        pygame.pixelcopy.surface_to_array(pixelArray, alien.image)

        r = 0
        g = 0
        b = 0
        for i in range(0, width):
            for j in range(0, length):
                for k in range(0, 3):
                    r += pixelArray[i][j][0]
                    g += pixelArray[i][j][1]
                    b += pixelArray[i][j][2]

        del pixelArray
        self.target.append(r / (width * length))
        self.target.append(b / (width * length))
        self.target.append(b / (width * length))
        self.target_width = width
        self.target_length = length

    def init_parciles(self):
        for i in range(0, self.particles_num):
            rect = pygame.Rect(random.randint(0, self.screen_rect.width -
                                              self.target_width - 1),
                               random.randint(100, 150),
                               1, 1)
            p = Particle(rect, self.screen,1/self.particles_num)
            self.particles.append(p)

    def search_particles(self, screen):
        w = 0
        width, length = self.screen.get_size()
        pixelArray = numpy.zeros((width, length, 3), dtype=int)
        pygame.pixelcopy.surface_to_array(pixelArray, screen)

        for particle in self.particles:
            particle.update(pixelArray)
            particle.w = 1 / particle.get_dis(self.target) * particle.w
            w += particle.w
        N = 0
        del pixelArray
        for particle in self.particles:
            particle.w = particle.w / w
            N += particle.w * particle.w

        if N == 0:
            return
        N = 1 / N
        #print(N)
        if N < 60:
            self.resample()

        x = 0
        y = 0

        for particle in self.particles:
            x += particle.w * particle.rect.centerx
            y += particle.w * particle.rect.centery

        self.recognize_rect = pygame.Rect(x, y, self.target_width,
                                          self.target_length)
        self.recognize_rect.centerx=x
        self.recognize_rect.centery=y

    def resample(self):

        stage = [random.uniform(0, 1) for i in range(0, self.particles_num)]
        stage.sort()

        sum = [0 for i in range(0, self.particles_num)]
        s = 0

        for i in range(0, self.particles_num):
            s += self.particles[i].w
            sum[i] = s

        # print(sum)
        times = [0 for i in range(0, self.particles_num)]
        for i in range(0, self.particles_num):
            j = 0
            while j < self.particles_num:
                if stage[i] > sum[j]:
                    j += 1
                else:
                    times[j] += 1
                    break

        # print(times)
        cop = self.particles[:]
        self.particles.clear()

        for i in range(0, self.particles_num):
            for j in range(0, times[i]):
                self.particles.append(Particle(pygame.Rect(cop[i].rect.left,
                                                           cop[i].rect.top,
                                                           cop[i].rect.width,
                                                           cop[i].rect.height),
                                               self.screen,1/self.particles_num))


    def show_recognize(self):
        for particle in self.particles:
            particle.draw()
        pygame.draw.rect(self.screen, (255, 0, 0), self.recognize_rect,
                         1)
