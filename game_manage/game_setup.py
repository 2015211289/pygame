import numpy as np

class Settings():
    def __init__(self):
        self.screen_width = 1200
        self.screen_height = 700
        self.bg_color = (230, 230, 230)
        self.bg=np.array(self.bg_color*self.screen_width*self.screen_height
                         ,dtype='uint8').reshape((self.screen_width,
                                              self.screen_height,3))
        self.ship_limit = 3

        self.fleet_drop_speed = 5

        self.speedup_scale = 1
        self.score_scale = 1

        self.auto=True
        self.time=0

        self.initialize_dynamic_settings()

    def initialize_dynamic_settings(self):
        self.ship_speed_factor = 2
        self.bullet_speed_factor = 2
        self.alien_speed_factor = 2

        self.alien_points = 50

    def increase_speed(self):
        self.ship_speed_factor *= self.speedup_scale
        self.bullet_speed_factor *= self.speedup_scale
        self.alien_speed_factor *= self.speedup_scale

        self.alien_points = int(self.alien_points * self.score_scale)
