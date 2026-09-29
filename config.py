"""Simulation assumptions and editable haul-road configuration."""
import os

SEED = 26007
TICK_HZ = 10
METRES_PER_MAP_UNIT = 5.0
FLEET_SIZE = int(os.getenv("FLEET_SIZE", "10"))
# Local screen-space road centerline: hairpins plus one uphill segment (x=60..85).
ROAD_WAYPOINTS = [
    [12, 90], [20, 90], [30, 88], [40, 82], [48, 72], [50, 62],
    [47, 53], [38, 48], [28, 47], [20, 43], [18, 35], [22, 27],
    [32, 24], [42, 26], [52, 30], [62, 34], [72, 37], [80, 43],
    [84, 52], [82, 61], [75, 67], [65, 68], [56, 66], [49, 61],
    [45, 54], [42, 45], [38, 36], [34, 28], [30, 18], [28, 10],
]
LOADING_POINT = [12, 90]
DUMP_YARD = [28, 10]
BLIND_CURVES = [[48, 62], [20, 35], [82, 55]]
JUNCTION = [52, 30]
ZONES = [
    {"name": "Hairpin Alpha", "center": [48, 62], "radius": 9, "limit_kmh": 12, "kind": "blind-curve"},
    {"name": "Hairpin Bravo", "center": [20, 35], "radius": 8, "limit_kmh": 12, "kind": "blind-curve"},
    {"name": "Hairpin Charlie", "center": [82, 55], "radius": 9, "limit_kmh": 12, "kind": "blind-curve"},
    {"name": "Junction", "center": JUNCTION, "radius": 7, "limit_kmh": 10, "kind": "junction"},
    {"name": "Dump Yard", "center": DUMP_YARD, "radius": 10, "limit_kmh": 8, "kind": "dump-yard"},
]
SENSOR = {
    "gnss_sigma_m": 0.02, "gnss_dropout_probability": 0.008,
    "radar_base_range_m": 110, "radar_fog_degradation": 0.16,
    "radar_range_noise_m": 0.8, "radar_position_sigma_m": 0.45,
    "imu_heading_sigma_deg": 0.5, "v2v_period_s": 0.1,
    "vision_brake_distance_m": 14, "radar_brake_distance_m": 20,
}
VEHICLE = {
    "max_speed_kmh": 40, "loaded_speed_factor": 0.76, "empty_speed_factor": 1.0,
    "acceleration_mps2": 1.15, "braking_mps2": 3.6, "baseline_braking_mps2": 2.5,
    "length_m": 8.0, "width_m": 3.2, "load_time_s": 16, "dump_time_s": 10,
    "headway_s": 1.1, "critical_headway_s": 1.7,
}
FOG_MODES = [
    {"name": "Normal", "min": 50, "limit_kmh": 40},
    {"name": "Assist", "min": 20, "limit_kmh": 25},
    {"name": "Convoy", "min": 5, "limit_kmh": 15},
    {"name": "Crawl", "min": 0, "limit_kmh": 8},
]
