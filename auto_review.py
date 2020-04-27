import random
from concurrent.futures import as_completed

import cv2
import numpy
import pygame


class Particle():

    def __init__(self, rect, w):

        self.rect = rect
        self.w = w
        self.dis = 0
        self.hist = []
        self.vx = 0
        self.vy = 0

    def update(self, pixelArray, width, height):
        self.rect.centerx = int(random.gauss(self.rect.centerx, 5))
        if self.rect.right >= width:
            self.rect.right = width - 1
        if self.rect.left < 0:
            self.rect.left = 0
        self.rect.centery = int(random.gauss(self.rect.centery, 5))
        if self.rect.bottom >= height:
            self.rect.bottom = height - 1
        if self.rect.top < 0:
            self.rect.top = 0

        bgr = pixelArray[self.rect.left:self.rect.right,
              self.rect.top:self.rect.bottom, ::-1]

        # 计算HSV直方图
        hsv = cv2.cvtColor(bgr, cv2.COLOR_RGB2HSV)
        targetH = cv2.calcHist([hsv], [0], None, [8], [0, 179])
        targetS = cv2.calcHist([hsv], [1], None, [8], [0, 255])

        self.hist = [targetH, targetS]

    def get_dis(self, target_hist):

        # 值越小，相似度越高
        disH = cv2.compareHist(target_hist[0], self.hist[0],
                               cv2.HISTCMP_BHATTACHARYYA)
        disS = cv2.compareHist(target_hist[1], self.hist[1],
                               cv2.HISTCMP_BHATTACHARYYA)

        self.dis = (disH + disS)
        if self.dis==0:
            self.dis=0.000001
        return self.dis

    def draw(self, screen):
        pygame.draw.rect(screen, (255, 0, 0), self.rect,
                         1)


class ParticleGroup():

    def __init__(self, rect, screen, feature, targetID, id):
        self.particle_num = 50
        self.particles = []
        self.rect = rect
        self.targetFea = feature
        self.targetID = targetID
        self.id = id
        for i in range(0, self.particle_num):
            self.particles.append(Particle(pygame.Rect(rect.left, rect.top,
                                                       rect.width, rect.height),
                                           1 / self.particle_num))
    def change_rect(self,rect,feature):
        self.particles.clear()
        for i in range(0,self.particle_num):
            self.particles.append(Particle(pygame.Rect(rect.left, rect.top,
                                                       rect.width, rect.height),
                                           1 / self.particle_num))
        self.targetFea=feature
        self.rect=rect

    def update_particles(self, pixelArray, width, height):
        # 权重归一化因子
        w = 0
        # 有效粒子数
        N = 0
        for particle in self.particles:
            particle.update(pixelArray, width, height)
            particle.w = 1 / particle.get_dis(self.targetFea) * particle.w
            w += particle.w

        for particle in self.particles:
            particle.w = particle.w / w
            N += particle.w ** 2

        N = 1 / N
        # print(N)
        if N < 0.9 * self.particle_num:
            self.resample()

        self.predict_pos()
        return self

    def resample(self):
        # 产生0到1的随机数
        stage = [random.uniform(0, 1) for i in range(0, self.particle_num)]

        sum = [0] * self.particle_num
        s = 0

        # 建立权重阶梯
        for i in range(0, self.particle_num):
            s += self.particles[i].w
            sum[i] = s

        # 计算随机数落到某一阶梯的个数
        times = [0] * self.particle_num
        for i in range(0, self.particle_num):
            j = 0
            while j < self.particle_num:
                if stage[i] > sum[j]:
                    j += 1
                else:
                    times[j] += 1
                    break

        cop = self.particles[:]
        self.particles.clear()

        # 根据比例重新生成粒子
        for i in range(0, self.particle_num):
            for j in range(0, times[i]):
                self.particles.append(Particle(pygame.Rect(cop[i].rect.left,
                                                           cop[i].rect.top,
                                                           cop[i].rect.width,
                                                           cop[i].rect.height),
                                               1 / self.particle_num))

    def predict_pos(self):
        x = 0
        y = 0
        for particle in self.particles:
            x += particle.w * particle.rect.left
            y += particle.w * particle.rect.top

        self.rect = pygame.Rect(x, y, self.rect.width, self.rect.height)

    def show_predict(self, screen):
        pygame.draw.rect(screen, (255, 0, 0), self.rect, 3)


class Target():

    def __init__(self, rect, feature, id):
        self.id = id
        self.rect = rect
        self.feature = feature


class Monitor():

    def __init__(self, screen, ai_settings, pool):
        self.screen = screen
        self.ai_settings = ai_settings
        self.pixelArray = None
        self.particle_groups = {}
        self.targets = {}
        self.targets_to_particle = {}
        self.target_num = 0
        self.particle_group_num = 0
        # 进程池
        self.pool = pool

    def backDiff(self):

        width, length = self.screen.get_size()
        pixelArray = numpy.zeros((width, length, 3), dtype='uint8')
        pygame.pixelcopy.surface_to_array(pixelArray, self.screen)
        self.pixelArray = pixelArray
        mark = numpy.zeros((width, length), dtype=int)

        # 发现前景图
        for i in range(0, width, 10):
            for j in range(0, length, 10):
                if mark[i, j] == 0:
                    pos = [i, i, j, j]
                    # 采用漫水法，寻找前景图
                    r = self.searchTarget(pixelArray, i, j, mark, width,
                                          length, pos)
                    if r == 1:
                        # 判断目标是否已跟踪
                        rect = pygame.Rect(pos[0], pos[2],
                                           pos[1] - pos[0] + 1,
                                           pos[3] - pos[2] + 1)
                        exit = False
                        Id=0
                        for id in self.targets.keys():
                            if self.targets[id].rect.colliderect(rect):
                                exit = True
                                Id=id
                                break

                        # 转换为HSV直方图
                        bgr = pixelArray[pos[0]:pos[1] + 1, pos[2]:pos[3] + 1,
                              ::-1]

                        hsv = cv2.cvtColor(bgr, cv2.COLOR_RGB2HSV)
                        targetH = cv2.calcHist([hsv], [0],
                                               None,
                                               [8], [0, 179])
                        targetS = cv2.calcHist([hsv], [1],
                                               None,
                                               [8], [0, 255])

                        # 目标重合
                        if exit and (rect.width>self.targets[Id].rect.width
                                or rect.height>self.targets[Id].rect.height):
                            self.targets[Id].rect=rect
                            self.targets[Id].feature=[targetH,targetS]
                            pgId=self.targets_to_particle[Id]
                            pg=self.particle_groups[pgId]
                            pg.change_rect(rect,[targetH,targetS])
                            print("overlap")
                        # 目标分离
                        elif exit and (rect.width<self.targets[Id].rect.width
                                and rect.height<self.targets[Id].rect.height):
                            del self.targets[Id]
                            pgId = self.targets_to_particle[Id]
                            del self.particle_groups[pgId]
                            del self.targets_to_particle[Id]
                            print("divide")
                        # 创建新目标
                        elif not exit:
                            target = Target(rect, [targetH, targetS],
                                        self.target_num)
                            self.target_num += 1
                            if self.target_num == 100:
                                self.target_num = 0
                            self.targets[target.id] = target
                            # 创建粒子滤波来跟踪此目标
                            pg = ParticleGroup(target.rect, self.screen,
                                               target.feature,
                                               target.id,
                                               self.particle_group_num)
                            self.particle_group_num += 1
                            if self.particle_group_num == 100:
                                self.particle_group_num = 0
                            self.particle_groups[pg.id] = pg
                            self.targets_to_particle[target.id] = pg.id
                            print("new")

    def targets_association(self):
        targets_to_particle = self.targets_to_particle.copy()
        targets = self.targets.copy()
        particle_groups = self.particle_groups.copy()
        compara=[]
        for i in self.targets.keys():
            # 处理目标消失
            disappear = True
            for x in range(self.targets[i].rect.left,
                           self.targets[i].rect.right, 10):
                for y in range(self.targets[i].rect.top,
                               self.targets[i].rect.bottom, 10):
                    r = abs(self.pixelArray[x, y, 0] -
                            self.ai_settings.bg_color[0])
                    g = abs(self.pixelArray[x, y, 1] -
                            self.ai_settings.bg_color[1])
                    b = abs(self.pixelArray[x, y, 2] -
                            self.ai_settings.bg_color[2])
                    t = 0.299 * r + 0.587 * g + 0.114 * b

                    if t > 30:
                        disappear = False
                    if not disappear: break
                if not disappear: break

            if disappear:
                del targets[i]
                id = self.targets_to_particle[i]
                del particle_groups[id]
                del targets_to_particle[i]
                continue

            # 处理目标重合
            for j in self.targets.keys():
                if j in compara:
                    continue
                if self.targets[i].rect.colliderect(self.targets[j].rect) and \
                    i != j:
                    dis = 0
                    for k in range(0, 2):
                        dis += cv2.compareHist(self.targets[i].feature[k],
                                               self.targets[j].feature[k],
                                               cv2.HISTCMP_BHATTACHARYYA)

                    if dis <= 0.001:
                        if j in targets.keys():
                            del targets[j]
                        id = self.targets_to_particle[j]
                        if id in particle_groups.keys():
                            del particle_groups[id]
                        if j in targets_to_particle.keys():
                            del targets_to_particle[j]
                    elif self.targets[i].rect.width>self.targets[
                        j].rect.width and self.targets[
                        i].rect.height>self.targets[j].rect.height:
                        if j in targets.keys():
                            del targets[j]
                        id = self.targets_to_particle[j]
                        if id in particle_groups.keys():
                            del particle_groups[id]
                        if j in targets_to_particle.keys():
                            del targets_to_particle[j]
                    elif self.targets[i].rect.width<=self.targets[
                        j].rect.width and self.targets[
                        i].rect.height<=self.targets[j].rect.height:
                        if i in targets.keys():
                            del targets[i]
                        id = self.targets_to_particle[i]
                        if id in particle_groups.keys():
                            del particle_groups[id]
                        if i in targets_to_particle.keys():
                            del targets_to_particle[i]

            compara.append(i)

        self.targets_to_particle = targets_to_particle
        self.targets = targets
        self.particle_groups = particle_groups


    def searchTarget(self, pixelArray, i, j, mark, width, length,
                     pos):

        q = [(i, j)]
        mark[i, j] = 1
        target = False
        while not len(q) == 0:
            (i, j) = q.pop(0)

            r = abs(pixelArray[i, j, 0] - self.ai_settings.bg_color[0])
            g = abs(pixelArray[i, j, 1] - self.ai_settings.bg_color[1])
            b = abs(pixelArray[i, j, 2] - self.ai_settings.bg_color[2])
            t = 0.299 * r + 0.587 * g + 0.114 * b

            if t > 30:
                target = True

                if i > pos[1]: pos[1] = i
                if i < pos[0]: pos[0] = i
                if j > pos[3]: pos[3] = j
                if j < pos[2]: pos[2] = j

                if i + 1 < width and mark[i + 1, j] == 0:
                    q.append((i + 1, j))
                    mark[i + 1, j] = 1
                if j + 1 < length and mark[i, j + 1] == 0:
                    q.append((i, j + 1))
                    mark[i, j + 1] = 1

                if i - 1 >= 0 and mark[i - 1, j] == 0:
                    q.append((i - 1, j))
                    mark[i - 1, j] = 1
                if j - 1 >= 0 and mark[i, j - 1] == 0:
                    q.append((i, j - 1))
                    mark[i, j - 1] = 1

        if target:
            return 1
        else:
            return 0

    def update_particle_groups(self):
        width, height = self.screen.get_size()
        tasks = [self.pool.submit(particle_group.update_particles,
                                  self.pixelArray, width, height) for
                 particle_group in
                 self.particle_groups.values()]

        process_results = [task.result() for task in as_completed(tasks)]
        for pg in process_results:
            self.particle_groups[pg.id] = pg
        for targetId in self.particle_groups.keys():
            pgID = self.targets_to_particle[targetId]
            self.targets[targetId].rect.left = self.particle_groups[
                pgID].rect.left
            self.targets[targetId].rect.top = self.particle_groups[
                pgID].rect.top

    def show_predicts(self):
        for particle_group in self.particle_groups.values():
            particle_group.show_predict(self.screen)

    def check_areas(self, ai_settings, screen, ship, area, bullets):
        for particle_group in self.particle_groups:
            target = particle_group.rect
            if (target.centerx - area.rect.centerx) ** 2 + (
                    target.centery - area.rect.y) ** 2 < area.radius ** 2:
                from game_manage.game_run import fire_bullet
                fire_bullet(ai_settings, screen, ship, bullets,
                            (target.centerx, target.centery))
