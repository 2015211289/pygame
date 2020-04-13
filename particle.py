import math
import random

import pygame


class Particle():

    def __init__(self, rect, screen, w):

        self.rect = rect
        self.screen = screen
        self.w = w
        self.dis = 0
        self.hist = [0, 0, 0]

    def update(self, pixelArray):
        width, length = self.screen.get_size()
        self.rect.x = int(random.gauss(self.rect.x,20))
        if self.rect.right >= width:
            self.rect.right = width - 1
        if self.rect.left < 0:
            self.rect.left = 0
        self.rect.y = int(random.gauss(self.rect.y,20))
        if self.rect.bottom >= length:
            self.rect.bottom = length - 1
        if self.rect.top < 0:
            self.rect.top = 0

        for i in range(self.rect.left, self.rect.right + 1):
            for j in range(self.rect.top, self.rect.bottom + 1):
                for k in range(0, 3):
                    self.hist[k] += (pixelArray[i][j][k])

        self.hist[0] = self.hist[0] / (self.rect.width * self.rect.height)
        self.hist[1] = self.hist[1] / (self.rect.width * self.rect.height)
        self.hist[2] = self.hist[2] / (self.rect.width * self.rect.height)

    def get_dis(self, target_hist):

        rmean = (target_hist[0] + self.hist[0]) / 2
        r = target_hist[0] - self.hist[0]
        g = target_hist[1] - self.hist[1]
        b = target_hist[2] - self.hist[2]
        dis = math.sqrt((((512 + rmean) * r * r) / 256) + 4 * g * g + (
                ((767 - rmean) * b * b) / 256))

        self.dis = dis
        return self.dis

    def draw(self):
        pygame.draw.rect(self.screen, (255, 0, 0), self.rect,
                         1)
