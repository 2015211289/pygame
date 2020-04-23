class Settings():
    def __init__(self):
        self.screen_width = 1200
        self.screen_height = 700
        self.bg_color = (230, 230, 230)
        self.ship_limit = 3

        self.bullet_width = 3
        self.bullet_height = 3
        self.bullet_color = (60, 60, 60)
        self.bullets_allowed = 100

        self.fleet_drop_speed = 10
        self.fleet_direction = 1

        self.speedup_scale = 1
        self.score_scale = 1

        self.area_radius = 200
        self.area_width = 2
        self.area_color = (255, 0, 0)
        self.auto=True
        self.time=0

        self.initialize_dynamic_settings()

    def initialize_dynamic_settings(self):
        self.ship_speed_factor = 30
        self.bullet_speed_factor = 30
        self.alien_speed_factor = 10

        self.fleet_direction = 1
        self.alien_points = 50

    def increase_speed(self):
        self.ship_speed_factor *= self.speedup_scale
        self.bullet_speed_factor *= self.speedup_scale
        self.alien_speed_factor *= self.speedup_scale

        self.alien_points = int(self.alien_points * self.score_scale)
