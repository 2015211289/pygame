import random
import numpy
import cv2 as cv
from game_manage.game_run import *


class Particle():

    def __init__(self, rect, screen, w):

        self.rect = rect
        self.screen = screen
        self.w = w
        self.dis = 0
        self.hist = [0, 0, 0]

    def update(self, pixelArray):
        width, length = self.screen.get_size()
        self.rect.x = int(random.gauss(self.rect.x, 20))
        if self.rect.right >= width:
            self.rect.right = width - 1
        if self.rect.left < 0:
            self.rect.left = 0
        self.rect.y = int(random.gauss(self.rect.y, 20))
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


class Monitor():

    def __init__(self,screen):
        self.screen=screen
        self.particle_groups = []
        self.tracking_targets = []
        self.alien_map = {}
        self.particles_num = 10

    def getTarget(self):

        width, length = self.screen.get_size()
        pixelArray = numpy.zeros((width, length, 3), dtype=int)
        pygame.pixelcopy.surface_to_array(pixelArray, self.screen)
        mark = numpy.zeros((width, length, 1), dtype=int)

        self.find = False
        for i in range(0, width):
            for j in range(0, length):
                if mark[i][j][0] == 0:
                    pos = [i, i, j, j]

                    r = self.searchTarget(pixelArray, i, j, mark, width,
                                          length, pos)
                    if r == 1 and not self.find:
                        rgb = numpy.zeros(
                            (pos[1] - pos[0] + 1, pos[3] - pos[2] + 1, 3),
                            dtype='uint8')
                        for x in range(pos[0], pos[1] + 1):
                            for y in range(pos[2], pos[3] + 1):
                                for k in range(0, 3):
                                    rgb[x - pos[0]][y - pos[2]][k] = \
                                    pixelArray[x][
                                        y][2 - k]
                                    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
                                    self.targetH = cv2.calcHist([hsv], [0],
                                                                None,
                                                                [8], [0, 179])
                                    self.targetS = cv2.calcHist([hsv], [1],
                                                                None,
                                                                [8], [0, 255])
                                    self.targetV = cv2.calcHist([hsv], [2],
                                                                None,
                                                                [4], [0, 255])

                        self.init_parciles(pos[0], pos[2], pos[1] - pos[0],
                                           pos[3] - pos[2])
                        print("new enemy")

                    elif self.find:
                        self.find = False

    def searchTarget(self, pixelArray, i, j, mark, width, length,
                     pos):

        q = []
        q.append((i, j))
        mark[i][j][0] = 1
        target = False
        while not len(q) == 0:
            (i, j) = q.pop(0)

            r = abs(pixelArray[i][j][0] - self.ai_settings.bg_color[0])
            g = abs(pixelArray[i][j][1] - self.ai_settings.bg_color[1])
            b = abs(pixelArray[i][j][2] - self.ai_settings.bg_color[2])
            t = 0.299 * r + 0.587 * g + 0.114 * b

            if t > 30:
                target = True

                if self.recognize_rect.centerx == i and \
                        self.recognize_rect.centery == j:
                    self.find = True

                if i > pos[1]: pos[1] = i
                if i < pos[0]: pos[0] = i
                if j > pos[3]: pos[3] = j
                if j < pos[2]: pos[2] = j

                if i + 1 < width and mark[i + 1][j][0] == 0:
                    q.append((i + 1, j))
                    mark[i + 1][j][0] = 1
                if j + 1 < length and mark[i][j + 1][0] == 0:
                    q.append((i, j + 1))
                    mark[i][j + 1][0] = 1

                if i - 1 >= 0 and mark[i - 1][j][0] == 0:
                    q.append((i - 1, j))
                    mark[i - 1][j][0] = 1
                if j - 1 >= 0 and mark[i][j - 1][0] == 0:
                    q.append((i, j - 1))
                    mark[i][j - 1][0] = 1

        if target:
            return 1
        else:
            return 0

    def init_parciles(self, x, y, w, h):
        for i in range(0, self.particles_num):
            rect = pygame.Rect(x, y,
                               w, h)
            p = Particle(rect, self.screen, 1 / self.particles_num)
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
        # print(N)
        if N < 60:
            self.resample()

        x = 0
        y = 0

        for particle in self.particles:
            x += particle.w * particle.rect.centerx
            y += particle.w * particle.rect.centery

        self.recognize_rect = pygame.Rect(x, y, self.target_width,
                                          self.target_length)
        self.recognize_rect.centerx = x
        self.recognize_rect.centery = y

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
                                               self.screen,
                                               1 / self.particles_num))

    def show_recognize(self):
        for particle in self.particles:
            particle.draw()
        pygame.draw.rect(self.screen, (255, 0, 0), self.recognize_rect,
                         1)

    def check_areas(self, ai_settings, screen, ship, area, bullets):
        for target in self.tracking_targets:
            if (target.centerx - area.rect.centerx) ** 2 + (
                    target.centery - area.rect.y) ** 2 <= area.radius ** 2:
                fire_bullet(ai_settings, screen, ship, bullets, target)
