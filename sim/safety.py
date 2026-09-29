import math
import config


def fog_mode(visibility):
    for mode in config.FOG_MODES:
        if visibility > mode["min"] or mode["min"] == 0: return mode
    return config.FOG_MODES[-1]


def ttc_and_alert(distance, closing_speed):
    if closing_speed <= 0: return None, "clear"
    ttc = distance / closing_speed
    if ttc < 3: return ttc, "critical"
    if ttc < 5: return ttc, "warning"
    if ttc < 8: return ttc, "caution"
    return ttc, "clear"


def zone_limit(position):
    limit, zone = float("inf"), None
    for z in config.ZONES:
        d = math.dist(position, z["center"])
        if d < z["radius"] and z["limit_kmh"] < limit:
            limit, zone = z["limit_kmh"], z["name"]
    return limit, zone
