import math
import random

import numpy
import pygame
from pygame.sprite import Sprite

from particle import Particle
from bullet import BulletBoard


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
        self.particles = []
        self.particles_num = 200
        self.recognize_x = 0
        self.recognize_y = 0

        self.bullet_num=[20,10,5]
        self.current_bullet=1
        self.bullets_board=BulletBoard(ai_settings,screen,self)
        self.bullet=None
        self.shoot_light=0

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
        r = g = b = 0
        for i in range(0, width):
            for j in range(0, length):
                r += pixelArray[i][j][0]
                g += pixelArray[i][j][1]
                b += pixelArray[i][j][2]

        r = r / (length * width)
        g = g / (length * width)
        b = b / (length * width)
        self.target.append(r)
        self.target.append(g)
        self.target.append(b)

    def init_parciles(self):
        for i in range(0, self.particles_num):
            p = Particle(random.randint(0, self.screen_rect.width - 50),
                         random.randint(100, 150),
                         self.screen, (0, 0, 0))
            self.particles.append(p)

    def search_particles(self):
        width, length = self.screen.get_size()
        pixelArray = numpy.zeros((width, length, 3), dtype=int)
        pygame.pixelcopy.surface_to_array(pixelArray, self.screen)

        for p in self.particles:
            p.x = random.normalvariate(p.x, 20)
            if p.x >= width: p.x = width - 1
            if p.x < 0: p.x = 0
            p.y = random.normalvariate(p.y, 20)
            if p.y >= length: p.y = length - 1
            if p.y < 0: p.y = 0

            p.pixel = pixelArray[int(p.x)][int(p.y)]

        del pixelArray
        w = 0
        for p in self.particles:
            rmean = (p.pixel[0] + self.target[0]) / 2
            r = p.pixel[0] - self.target[0]
            g = p.pixel[1] - self.target[1]
            b = p.pixel[2] - self.target[2]
            p.dis = math.sqrt((((512 + rmean) * r * r) / 256) + 4 * g * g + (((
                        767 - rmean) * b * b) / 256))
            p.w = 1 / p.dis
            w += p.w


        N = 0

        for p in self.particles:
            x = p.w
            p.w = p.w / w
            N += x * x


        N = 1 / N

        if N < 100:
            self.resample()

        x = 0
        y = 0

        for i in self.particles:
            x += i.w * i.x
            y += i.w * i.y

        self.recognize_x = x
        self.recognize_y = y

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
                self.particles.append(Particle(cop[i].x,cop[i].y,self.screen,
                                               cop[i].pixel))

        for i in self.particles:
            i.w = 1 / len(self.particles)


    def show_particles(self):
        for p in self.particles:
            pygame.draw.circle(self.screen, (255, 0, 0), (int(p.x), int(p.y)),
                               2, 0)
