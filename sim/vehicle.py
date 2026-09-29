from dataclasses import dataclass, asdict


@dataclass
class Vehicle:
    id: str
    progress: float
    speed: float
    heading: float
    lane: int
    loaded: bool = False
    state: str = "return"
    trips: int = 0
    dwell: float = 0.0
    alert: str = "clear"
    limit_kmh: float = 40.0
    ttc: float | None = None
    def to_dict(self):
        d = asdict(self); d["loaded_state"] = "loaded" if self.loaded else "empty"
        return d
