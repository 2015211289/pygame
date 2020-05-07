import random
from concurrent.futures import as_completed

import cv2
import numpy
import pygame


# 单个粒子
class Particle():

    def __init__(self, rect, w):

        self.rect = rect
        self.w = w
        self.dis = 0
        self.hist = []
        self.dx = 0
        self.dy = 0

    def update(self, pixelArray, width, height):
        self.rect.centerx = int(random.gauss(self.rect.centerx+self.dx, 5))
        if self.rect.right >= width:
            self.rect.right = width - 1
        if self.rect.left < 0:
            self.rect.left = 0
        self.rect.centery = int(random.gauss(self.rect.centery+self.dy, 5))
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
        if self.dis == 0:
            self.dis = 0.00001
        return self.dis

    def draw(self, screen):
        pygame.draw.rect(screen, (255, 0, 0), self.rect,
                         1)


# 粒子滤波，表示目标跟踪器
class Tracker():

    def __init__(self, rect, feature):
        self.particle_num = 50
        self.particles = []
        self.rect = rect
        self.last_pos=rect
        self.feature = feature
        self.dx = 0
        self.dy = 0
        for i in range(0, self.particle_num):
            self.particles.append(Particle(pygame.Rect(rect.left, rect.top,
                                                       rect.width, rect.height),
                                           1 / self.particle_num))

    def update(self, rect,dx,dy):
        for particle in self.particles:
            particle.rect=rect.copy()
            particle.w=1/self.particle_num
            particle.dx=dx
            particle.dy=dy
        self.rect = rect
        self.last_pos=rect
        self.dx=dx
        self.dy=dy

    def predict(self, pixelArray, width, height):
        # 权重归一化因子
        w = 0
        # 有效粒子数
        N = 0
        for particle in self.particles:
            particle.update(pixelArray, width, height)
            particle.w = 1 / particle.get_dis(self.feature) * particle.w
            w += particle.w

        for particle in self.particles:
            particle.w = particle.w / w
            N += particle.w ** 2

        N = 1 / N
        # print(N)
        if N < 0.9 * self.particle_num:
            self.resample()

        self.get_pos()
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
                self.particles.append(Particle(cop[i].rect.copy(),
                                               1 / self.particle_num))

    def get_pos(self):
        x = 0
        y = 0
        for particle in self.particles:
            x += particle.w * particle.rect.left
            y += particle.w * particle.rect.top

        self.rect = pygame.Rect(x, y, self.rect.width, self.rect.height)

    def show_predict(self, screen):
        pygame.draw.rect(screen, (255, 0, 0), self.rect, 3)


class Monitor():

    def __init__(self, screen, ai_settings, pool):
        self.screen = screen
        self.ai_settings = ai_settings
        self.pixelArray = None
        self.trackers = []
        self.detections = []
        # 进程池,用于并行粒子滤波
        self.pool = pool
        self.width,self.height=screen.get_size()

    def get_pixelArray(self):
        width, length = self.screen.get_size()
        self.pixelArray = numpy.zeros((width, length, 3), dtype='uint8')
        pygame.pixelcopy.surface_to_array(self.pixelArray, self.screen)

    def backDiff(self):
        # 背景差分法
        pixelArray = (self.pixelArray - self.ai_settings.bg_color[0])
        gray = cv2.cvtColor(pixelArray, cv2.COLOR_BGR2GRAY)
        ret, thresh1 = cv2.threshold(gray, 5, 255, cv2.THRESH_BINARY)
        contours, hierarchy=cv2.findContours(thresh1, cv2.RETR_EXTERNAL,
                                               cv2.CHAIN_APPROX_SIMPLE)
        for c in contours:
            y, x, h, w = cv2.boundingRect(c)
            rect = pygame.Rect(x, y,w,h)
            self.detections.append(rect)

        # # 发现前景图
        # found=list(self.targets.keys())
        # for i in range(0, width, 50):
        #     for j in range(0, length, 50):
        #         if mark.item(i, j) == 0:
        #             pos = [i, i, j, j]
        #             # 采用漫水法，寻找前景图
        #             r = self.searchTarget(pixelArray, i, j, mark, width,
        #                                   length, pos)
        #             if r == 1:
        #                 # 判断目标是否已跟踪
        #                 rect = pygame.Rect(pos[0], pos[2],
        #                                    pos[1] - pos[0] + 1,
        #                                    pos[3] - pos[2] + 1)
        #                 exit = False
        #                 Id = 0
        #                 for id in found:
        #                     if self.targets[id].rect.colliderect(rect):
        #                         exit = True
        #                         Id = id
        #                         break
        #
        #                 # 目标重合
        #                 if exit:
        #                     found.remove(Id)
        #                     if (rect.width > self.targets[Id].rect.width
        #                             or rect.height > self.targets[
        #                                 Id].rect.height):
        #                         # 转换为HSV直方图
        #                         bgr = self.pixelArray[pos[0]:pos[1] + 1,
        #                               pos[2]:pos[3] + 1, ::-1]
        #
        #                         hsv = cv2.cvtColor(bgr, cv2.COLOR_RGB2HSV)
        #                         targetH = cv2.calcHist([hsv], [0],
        #                                                None,
        #                                                [8], [0, 179])
        #                         targetS = cv2.calcHist([hsv], [1],
        #                                                None,
        #                                                [8], [0, 255])
        #                         self.targets[Id].rect = rect
        #                         self.targets[Id].feature = [targetH, targetS]
        #                         pgId = self.targets_to_particle[Id]
        #                         pg = self.particle_groups[pgId]
        #                         pg.change_rect(rect, [targetH, targetS])
        #                         # print("overlap")
        #                     # 目标分离
        #                     elif (rect.width < self.targets[Id].rect.width
        #                           and rect.height < self.targets[
        #                               Id].rect.height):
        #                         del self.targets[Id]
        #                         pgId = self.targets_to_particle[Id]
        #                         del self.particle_groups[pgId]
        #                         del self.targets_to_particle[Id]
        #                         # print("divide")
        #                 # 创建新目标
        #                 else:
        #                     # 转换为HSV直方图
        #                     bgr = self.pixelArray[pos[0]:pos[1] + 1,
        #                           pos[2]:pos[3] + 1, ::-1]
        #
        #                     hsv = cv2.cvtColor(bgr, cv2.COLOR_RGB2HSV)
        #                     targetH = cv2.calcHist([hsv], [0],
        #                                            None,
        #                                            [8], [0, 179])
        #                     targetS = cv2.calcHist([hsv], [1],
        #                                            None,
        #                                            [8], [0, 255])
        #                     target = Target(rect, [targetH, targetS],
        #                                     self.target_num)
        #                     self.target_num += 1
        #                     if self.target_num == 100:
        #                         self.target_num = 0
        #                     self.targets[target.id] = target
        #                     # 创建粒子滤波来跟踪此目标
        #                     pg = ParticleGroup(target.rect, self.screen,
        #                                        target.feature,
        #                                        target.id,
        #                                        self.particle_group_num)
        #                     self.particle_group_num += 1
        #                     if self.particle_group_num == 100:
        #                         self.particle_group_num = 0
        #                     self.particle_groups[pg.id] = pg
        #                     self.targets_to_particle[target.id] = pg.id
        #                     # print("new")

    # def searchTarget(self, pixelArray, i, j, mark, width, length,
    #                  pos):
    #
    #     q = [(i, j)]
    #     mark.itemset((i, j), 1)
    #     target = False
    #     while not len(q) == 0:
    #         (i, j) = q.pop(0)
    #
    #         r = pixelArray.item(i, j, 0)
    #         g = pixelArray.item(i, j, 1)
    #         b = pixelArray.item(i, j, 2)
    #         t = 0.299 * r + 0.587 * g + 0.114 * b
    #
    #         if t > 30:
    #             target = True
    #
    #             if i > pos[1]:
    #                 pos[1] = i
    #             elif i < pos[0]:
    #                 pos[0] = i
    #             if j > pos[3]:
    #                 pos[3] = j
    #             elif j < pos[2]:
    #                 pos[2] = j
    #
    #             if i + 1 < width and mark.item(i + 1, j) == 0:
    #                 q.append((i + 1, j))
    #                 mark.itemset((i + 1, j), 1)
    #             if j + 1 < length and mark.item(i, j + 1) == 0:
    #                 q.append((i, j + 1))
    #                 mark.itemset((i, j + 1), 1)
    #             if i - 1 >= 0 and mark.item(i - 1, j) == 0:
    #                 q.append((i - 1, j))
    #                 mark.itemset((i - 1, j), 1)
    #             if j - 1 >= 0 and mark.item(i, j - 1) == 0:
    #                 q.append((i, j - 1))
    #                 mark.itemset((i, j - 1), 1)
    #
    #     if target:
    #         return 1
    #     else:
    #         return 0

    def associate_detections_to_trackers(self,iou_threshold=0.3):
        """
               Assigns detections to tracked object (both represented as bounding boxes)

               Returns 3 lists of matches, unmatched_detections and unmatched_trackers
               """
        if (len(self.trackers) == 0):
            return numpy.empty((0, 2), dtype=int), numpy.arange(
                len(self.detections)), numpy.empty((0, 5), dtype=int)

        iou_matrix=numpy.zeros((len(self.detections),
                                len(self.trackers)))
        for d, det in enumerate(self.detections):
            for t, trk in enumerate(self.trackers):
                iou_matrix[d, t] = self.iou(det, trk.rect)

        if min(iou_matrix.shape) > 0:
            a = (iou_matrix > iou_threshold).astype(numpy.int32)
            if a.sum(1).max() == 1 and a.sum(0).max() == 1:
                matched_indices = numpy.stack(numpy.where(a), axis=1)
            else:
                matched_indices = self.linear_assignment(-iou_matrix)
        else:
            matched_indices = numpy.empty(shape=(0, 2))

        unmatched_detections = []
        for d, det in enumerate(self.detections):
            if (d not in matched_indices[:, 0]):
                unmatched_detections.append(d)
        unmatched_trackers = []
        for t, trk in enumerate(self.trackers):
            if (t not in matched_indices[:, 1]):
                unmatched_trackers.append(t)

        # filter out matched with low IOU
        matches = []
        for m in matched_indices:
            if (iou_matrix[m[0], m[1]] < iou_threshold):
                unmatched_detections.append(m[0])
                unmatched_trackers.append(m[1])
            else:
                matches.append(m.reshape(1, 2))
        if (len(matches) == 0):
            matches = numpy.empty((0, 2), dtype=int)
        else:
            matches = numpy.concatenate(matches, axis=0)

        return matches, numpy.array(unmatched_detections), numpy.array(
            unmatched_trackers)
        # targets_to_particle = self.targets_to_particle.copy()
        # targets = self.targets.copy()
        # particle_groups = self.particle_groups.copy()
        # compared = set()
        # for i in self.targets.keys():
        #     if i in compared:
        #         continue
        #     compared.add(i)
        #     # 处理目标消失
        #     disappear = True
        #     for x in range(self.targets[i].rect.left,
        #                    self.targets[i].rect.right, 10):
        #         for y in range(self.targets[i].rect.top,
        #                        self.targets[i].rect.bottom, 10):
        #             r = abs(self.pixelArray.item(x, y, 0) -
        #                     self.ai_settings.bg_color[0])
        #             g = abs(self.pixelArray.item(x, y, 1) -
        #                     self.ai_settings.bg_color[1])
        #             b = abs(self.pixelArray.item(x, y, 2) -
        #                     self.ai_settings.bg_color[2])
        #             t = 0.299 * r + 0.587 * g + 0.114 * b
        #
        #             if t > 30:
        #                 disappear = False
        #             if not disappear:
        #                 break
        #         if not disappear:
        #             break
        #
        #     # 删除空粒子滤波和目标
        #     if disappear:
        #         del targets[i]
        #         id = self.targets_to_particle[i]
        #         del particle_groups[id]
        #         del targets_to_particle[i]
        #         continue
        #
        #     # 处理目标重合
        #     for j in self.targets.keys():
        #         if j in compared:
        #             continue
        #         if self.targets[i].rect.colliderect(self.targets[j].rect):
        #             dis = 0
        #             for k in range(0, 2):
        #                 dis += cv2.compareHist(self.targets[i].feature[k],
        #                                        self.targets[j].feature[k],
        #                                        cv2.HISTCMP_BHATTACHARYYA)
        #             # 删除重合目标和粒子滤波
        #             if dis <= 0.001:
        #
        #                 del targets[j]
        #                 id = self.targets_to_particle[j]
        #
        #                 del particle_groups[id]
        #
        #                 del targets_to_particle[j]
        #                 compared.add(j)
        #             elif self.targets[i].rect.width > self.targets[
        #                 j].rect.width and self.targets[
        #                 i].rect.height > self.targets[j].rect.height:
        #
        #                 del targets[j]
        #                 id = self.targets_to_particle[j]
        #
        #                 del particle_groups[id]
        #
        #                 del targets_to_particle[j]
        #                 compared.add(j)
        #             elif self.targets[i].rect.width <= self.targets[
        #                 j].rect.width and self.targets[
        #                 i].rect.height <= self.targets[j].rect.height:
        #                 if i in targets.keys():
        #                     del targets[i]
        #                 id = self.targets_to_particle[i]
        #
        #                 del particle_groups[id]
        #
        #                 del targets_to_particle[i]
        #
        # self.targets_to_particle = targets_to_particle
        # self.targets = targets
        # self.particle_groups = particle_groups

    def update(self):
        # 并行更新每个跟踪器
        tasks = [self.pool.submit(particle_group.update_particles,
                                  self.pixelArray, self.width, self.height)
                 for
                 particle_group in
                 self.trackers]

        self.trackers = [task.result() for task in as_completed(tasks)]
        # 用匹配结果更新跟踪器
        matched, unmatched_dets, unmatched_trks = \
            self.associate_detections_to_trackers()
        # update matched trackers with assigned detections
        for m in matched:
            rect=self.detections[m[0]]
            dx=rect.cetnerx-self.trackers[m[1]].last_pos.centerx
            dy=rect.centery-self.trackers[m[1]].last_pos.centery
            self.trackers[m[1]].update(rect,dx,dy)

        # create and initialise new trackers for unmatched detections
        for i in unmatched_dets:
            rect=self.detections[i]
            bgr = self.pixelArray[rect.left:rect.right,
                  rect.top:rect.bottom,::-1]

            hsv = cv2.cvtColor(bgr, cv2.COLOR_RGB2HSV)
            targetH = cv2.calcHist([hsv], [0],
                                   None,
                                   [8], [0, 179])
            targetS = cv2.calcHist([hsv], [1],
                                   None,
                                   [8], [0, 255])
            _targetH=numpy.zeros((8,1))
            _targetS=numpy.zeros((8,1))
            _targetH=cv2.normalize(targetH,_targetH)
            _targetS=cv2.normalize(targetS,_targetS)
            trk = Tracker(rect.copy(),[_targetH,_targetS])
            self.trackers.append(trk)
        i = len(self.trackers)
        for trk in reversed(self.trackers):
            # remove dead tracklet
            if (trk.time_since_update > self.max_age):
                self.trackers.pop(i)
        if (len(ret) > 0):
            return np.concatenate(ret)
        return np.empty((0, 5))


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



    def linear_assignment(self,cost_matrix):
        try:
            import lap
            _, x, y = lap.lapjv(cost_matrix, extend_cost=True)
            return numpy.array([[y[i], i] for i in x if i >= 0])  #
        except ImportError:
            from scipy.optimize import linear_sum_assignment
            x, y = linear_sum_assignment(cost_matrix)
            return numpy.array(list(zip(x, y)))

    def iou(self,detection, tracker):
        """
        Computes IUO between two bboxes in the form [x1,y1,x2,y2]
        """
        bb_test=[detection.left,detection.top,detection.right-1,
                 detection.bottom-1]
        bb_gt=[tracker.left,tracker.top,tracker.right-1,tracker.bottom-1]
        xx1 = numpy.maximum(bb_test[0], bb_gt[0])
        yy1 = numpy.maximum(bb_test[1], bb_gt[1])
        xx2 = numpy.minimum(bb_test[2], bb_gt[2])
        yy2 = numpy.minimum(bb_test[3], bb_gt[3])
        w = numpy.maximum(0., xx2 - xx1)
        h = numpy.maximum(0., yy2 - yy1)
        wh = w * h
        o = wh / ((bb_test[2] - bb_test[0]) * (bb_test[3] - bb_test[1])
                  + (bb_gt[2] - bb_gt[0]) * (bb_gt[3] - bb_gt[1]) - wh)
        return o

