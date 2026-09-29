import math
import numpy as np
from shapely.geometry import LineString, Point
import config


class HaulRoad:
    def __init__(self):
        self.waypoints = np.asarray(config.ROAD_WAYPOINTS, dtype=float)
        self.line = LineString(self.waypoints.tolist())
        self.length = self.line.length

    def point(self, progress, lane=0):
        d = float(progress) % self.length
        p = self.line.interpolate(d)
        before = self.line.interpolate(max(0, d - .5)); after = self.line.interpolate(min(self.length, d + .5))
        dx, dy = after.x - before.x, after.y - before.y
        norm = math.hypot(dx, dy) or 1
        # Two-way lanes, offset perpendicular to direction.
        sign = 1 if lane == 0 else -1
        return [p.x - dy / norm * 1.8 * sign, p.y + dx / norm * 1.8 * sign]

    def heading(self, progress):
        a = self.point(progress); b = self.point(progress + 1)
        return math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))

    def nearest_progress(self, xy):
        return self.line.project(Point(float(xy[0]), float(xy[1])))

    def is_uphill(self, progress):
        return 60 <= self.line.interpolate(progress % self.length).x <= 85
