"""Synthetic sensor models; all noise and dropout assumptions live in config.py."""
import math, random
import numpy as np
from filterpy.kalman import ExtendedKalmanFilter
import config


class SensorSuite:
    def __init__(self, rng):
        self.rng = rng
        self.filters = {}

    def fused_position(self, vehicle, truth):
        kf = self.filters.get(vehicle.id)
        if kf is None:
            kf = ExtendedKalmanFilter(dim_x=4, dim_z=2)
            kf.x = np.array([truth[0], truth[1], 0., 0.])
            kf.F = np.array([[1,0,.1,0],[0,1,0,.1],[0,0,1,0],[0,0,0,1.]])
            kf.H = np.array([[1,0,0,0],[0,1,0,0.]])
            kf.P *= 2; kf.R *= config.SENSOR["gnss_sigma_m"] ** 2
            kf.Q *= .03; self.filters[vehicle.id] = kf
        dt=.1
        kf.F = np.array([[1,0,dt,0],[0,1,0,dt],[0,0,1,0],[0,0,0,1.]])
        imu_heading=math.radians(vehicle.heading+self.rng.normal(0,config.SENSOR["imu_heading_sigma_deg"]))
        kf.x[2]=vehicle.speed*math.cos(imu_heading); kf.x[3]=vehicle.speed*math.sin(imu_heading)
        kf.predict()
        if self.rng.random() >= config.SENSOR["gnss_dropout_probability"]:
            z = np.array(truth) + self.rng.normal(0, config.SENSOR["gnss_sigma_m"] / config.METRES_PER_MAP_UNIT, 2)
            kf.update(z, HJacobian=lambda x: kf.H, Hx=lambda x: kf.H @ x)
        return kf.x[:2].tolist()

    def radar_range(self, visibility):
        base = config.SENSOR["radar_base_range_m"]
        degradation = config.SENSOR["radar_fog_degradation"] * max(0, 1 - visibility / 100)
        return max(20, base * (1 - degradation) + float(self.rng.normal(0, config.SENSOR["radar_range_noise_m"])))

    def radar_detects(self, distance, visibility):
        return distance <= self.radar_range(visibility)
