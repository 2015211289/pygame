import random

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
        self.rect.centerx = int(random.gauss(self.rect.centerx + self.dx, 5))
        if self.rect.right >= width:
            self.rect.right = width - 1
        if self.rect.left < 0:
            self.rect.left = 0
        self.rect.centery = int(random.gauss(self.rect.centery + self.dy, 5))
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
        _targetH = numpy.zeros((8, 1))
        _targetS = numpy.zeros((8, 1))
        _targetH = cv2.normalize(targetH, _targetH)
        _targetS = cv2.normalize(targetS, _targetS)

        self.hist = [_targetH, _targetS]

    def get_dis(self, target_hist):
        # 值越小，相似度越高
        disH = cv2.compareHist(target_hist[0], self.hist[0],
                               cv2.HISTCMP_BHATTACHARYYA)
        disS = cv2.compareHist(target_hist[1], self.hist[1],
                               cv2.HISTCMP_BHATTACHARYYA)

        self.dis = (disH + disS)
        if self.dis == 0:
            self.dis = 0.0001
        return self.dis

    def draw(self, screen):
        pygame.draw.rect(screen, (255, 0, 0), self.rect,
                         1)


# 粒子滤波，表示目标跟踪器
class Tracker():
    count = 0

    def __init__(self, rect, feature):
        self.particle_num = 50
        self.particles = []
        self.rect = rect
        self.last_pos = rect
        self.feature = feature
        self.time_since_update = 0  # 表示距离上次匹配的帧数
        self.id = Tracker.count
        Tracker.count += 1
        self.history = []  # 跟踪历史
        self.hits = 0  # 匹配成功次数
        self.hit_streak = 0  # 连续匹配成功次数
        self.age = 0  # 跟踪帧数
        self.dx = 0
        self.dy = 0
        for i in range(0, self.particle_num):
            self.particles.append(Particle(rect.copy(),
                                           1 / self.particle_num))

    def update(self, rect, dx, dy):
        # 与detection匹配
        for particle in self.particles:
            particle.rect = rect.copy()
            particle.w = 1 / self.particle_num
            particle.dx = dx
            particle.dy = dy
        self.rect = rect
        self.last_pos = rect
        self.dx = dx
        self.dy = dy
        self.time_since_update = 0
        self.history = []
        self.hits += 1
        self.hit_streak += 1

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
        if N < 0.6 * self.particle_num:
            self.resample()
        self.get_pos()
        # 更新参数
        self.age += 1
        if self.time_since_update > 0:
            self.hit_streak = 0
        self.time_since_update += 1
        self.history.append(self.rect)

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

    def __init__(self, screen, ai_settings, max_age=1, min_hits=3):
        self.screen = screen
        self.ai_settings = ai_settings
        self.pixelArray = None
        self.trackers = []
        self.detections = []
        self.width, self.height = screen.get_size()
        self.max_age = max_age
        self.min_hits = min_hits

    def get_background(self):
        width, length = self.screen.get_size()
        self.pixelArray = numpy.zeros((width, length, 3), dtype='uint8')
        pygame.pixelcopy.surface_to_array(self.pixelArray, self.screen)

    def backDiff(self):
        # 背景差分法
        self.detections.clear()
        pixelArray = cv2.subtract(self.ai_settings.bg, self.pixelArray)
        gray_bg = cv2.cvtColor(pixelArray, cv2.COLOR_BGR2GRAY)
        ret, thresh = cv2.threshold(gray_bg, 10, 255, cv2.THRESH_BINARY)
        contours, hierarchy = cv2.findContours(thresh, cv2.RETR_EXTERNAL,
                                               cv2.CHAIN_APPROX_SIMPLE)
        for c in contours:
            y, x, h, w = cv2.boundingRect(c)
            rect = pygame.Rect(x, y, w, h)
            self.detections.append(rect)

    def associate_detections_to_trackers(self, iou_threshold=0.3):
        """
               Assigns detections to tracked object (both represented as bounding boxes)

               Returns 3 lists of matches, unmatched_detections and unmatched_trackers
               """
        if (len(self.trackers) == 0):
            return numpy.empty((0, 2), dtype=int), numpy.arange(
                len(self.detections)), numpy.empty((0, 5), dtype=int)

        iou_matrix = numpy.zeros((len(self.detections),
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

    def update(self):
        # 更新每个跟踪器
        for tracker in self.trackers:
            tracker.predict(self.pixelArray, self.width, self.height)
        # 用匹配结果更新跟踪器
        matched, unmatched_dets, unmatched_trks = \
            self.associate_detections_to_trackers()
        # update matched trackers with assigned detections
        for m in matched:
            rect = self.detections[m[0]]
            dx = rect.centerx - self.trackers[m[1]].last_pos.centerx
            dy = rect.centery - self.trackers[m[1]].last_pos.centery
            self.trackers[m[1]].update(rect, dx, dy)

        # create and initialise new trackers for unmatched detections
        for i in unmatched_dets:
            rect = self.detections[i]
            bgr = self.pixelArray[rect.left:rect.right,
                  rect.top:rect.bottom, ::-1]

            hsv = cv2.cvtColor(bgr, cv2.COLOR_RGB2HSV)
            targetH = cv2.calcHist([hsv], [0],
                                   None,
                                   [8], [0, 179])
            targetS = cv2.calcHist([hsv], [1],
                                   None,
                                   [8], [0, 255])
            _targetH = numpy.zeros((8, 1))
            _targetS = numpy.zeros((8, 1))
            _targetH = cv2.normalize(targetH, _targetH)
            _targetS = cv2.normalize(targetS, _targetS)
            trk = Tracker(rect.copy(), [_targetH, _targetS])
            self.trackers.append(trk)
        i = len(self.trackers)
        ret = []
        for trk in reversed(self.trackers):
            if (trk.time_since_update < 1) and trk.hit_streak >= self.min_hits:
                ret.append(trk)
            i -= 1
            # remove dead tracklet
            if (trk.time_since_update > self.max_age):
                self.trackers.pop(i)

        return ret

    def show_predicts(self, ret):
        for tracker in ret:
            tracker.show_predict(self.screen)

    def check_areas(self, ai_settings, screen, ship, area, bullets):
        for particle_group in self.trackers:
            target = particle_group.rect
            if (target.centerx - area.rect.centerx) ** 2 + (
                    target.centery - area.rect.y) ** 2 < area.radius ** 2:
                from game_manage.game_run import fire_bullet
                fire_bullet(ai_settings, screen, ship, bullets,
                            (target.centerx, target.centery))

    def linear_assignment(self, cost_matrix):
        try:
            import lap
            _, x, y = lap.lapjv(cost_matrix, extend_cost=True)
            return numpy.array([[y[i], i] for i in x if i >= 0])  #
        except ImportError:
            from scipy.optimize import linear_sum_assignment
            x, y = linear_sum_assignment(cost_matrix)
            return numpy.array(list(zip(x, y)))

    def iou(self, detection, tracker):
        """
        Computes IUO between two bboxes in the form [x1,y1,x2,y2]
        """
        bb_test = [detection.left, detection.top, detection.right - 1,
                   detection.bottom - 1]
        bb_gt = [tracker.left, tracker.top, tracker.right - 1,
                 tracker.bottom - 1]
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
