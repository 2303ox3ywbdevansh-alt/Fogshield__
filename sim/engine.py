import math, random, time
import numpy as np
import config
from sim.road import HaulRoad
from sim.vehicle import Vehicle
from sim.sensors import SensorSuite
from sim.safety import fog_mode, ttc_and_alert, zone_limit


class Simulation:
    def __init__(self, mode="ASSISTED", visibility=12, seed=config.SEED, fleet_size=None):
        self.mode = mode.upper(); self.visibility = float(visibility); self.seed = int(seed)
        self.rng = random.Random(self.seed); self.np_rng = np.random.default_rng(self.seed)
        self.road = HaulRoad(); self.sensors = SensorSuite(self.np_rng)
        self.vehicles = []
        n = fleet_size or config.FLEET_SIZE
        gap = self.road.length / n
        for i in range(n):
            p = (i * gap) % self.road.length
            state="return" if i % 2 == 0 else "haul"
            self.vehicles.append(Vehicle(f"D-{i+1:02d}", p, 0, self.road.heading(p), 0 if state=="return" else 1, state=="haul", state))
        self.time = 0.; self.running = False; self.alerts = []; self.near_misses = 0; self.collisions = 0
        self.min_pair_dist = 999.; self.speed_samples=[]; self.started = time.time()
        self._near_active=set(); self._collision_active=set(); self.cycle_durations=[]
        self.trip_started={v.id:0.0 for v in self.vehicles}

    def set_visibility(self, value): self.visibility = max(3., min(100., float(value)))

    def _alert(self, v, level, message):
        if level != "clear":
            entry={"time":round(self.time,1),"vehicle":v.id,"level":level,"message":message}
            if not self.alerts or (self.alerts[-1]["vehicle"],self.alerts[-1]["level"],self.alerts[-1]["message"]) != (v.id,level,message):
                self.alerts.append(entry); self.alerts=self.alerts[-80:]

    def tick(self, dt=0.1):
        self.time += dt; mode=fog_mode(self.visibility); positions={}
        for v in self.vehicles:
            positions[v.id]=self.road.point(v.progress,v.lane)
        for i,v in enumerate(self.vehicles):
            v.lane=0 if v.state in ("return","load") else 1
            pos=positions[v.id]; heading=self.road.heading(v.progress)+(180 if v.state=="return" else 0); v.heading=heading
            zone_speed,zone=zone_limit(pos)
            limit=min(config.VEHICLE["max_speed_kmh"],mode["limit_kmh"],zone_speed)
            if self.mode == "BASELINE":
                # Vision only; severe fog produces cautious crawling or complete stop.
                limit=min(40., self.visibility * .65)
                if self.visibility < 5: limit=0.
                v.alert="clear"; v.ttc=None
            else:
                fused=self.sensors.fused_position(v,pos)
                if v.loaded:
                    limit=min(limit,config.VEHICLE["max_speed_kmh"]*config.VEHICLE["loaded_speed_factor"])
                limit=min(limit, 15 if self.road.is_uphill(v.progress) and v.loaded else 40)
                v.alert="clear"; v.ttc=None
                for other in self.vehicles:
                    if other is v: continue
                    op=positions[other.id]; dist=math.dist(pos,op)*config.METRES_PER_MAP_UNIT; self.min_pair_dist=min(self.min_pair_dist,dist)
                    same=other.lane==v.lane
                    # Oncoming vehicle conflicts count only within a bend / junction.
                    bend=any(math.dist(pos,z["center"]) < z["radius"]+4 for z in config.ZONES)
                    forward=(v.progress-other.progress)%self.road.length if v.state=="return" else (other.progress-v.progress)%self.road.length
                    gap=forward*config.METRES_PER_MAP_UNIT if same else 0
                    relevant=(same and other.state==v.state and 0<gap<220) or (not same and bend and dist<24)
                    if not relevant: continue
                    radar_ok=self.sensors.radar_detects(dist,self.visibility)
                    # V2V provides position and speed even when radar is occluded.
                    if not radar_ok and dist > 24: continue
                    closing=max(.05,(v.speed+other.speed) if not same else max(0,v.speed-other.speed))
                    ttc,alert=ttc_and_alert(max(0,dist-8),closing)
                    if ttc is not None and (v.ttc is None or ttc<v.ttc): v.ttc=ttc; v.alert=alert
                if v.alert=="critical":
                    limit=min(limit,8); self._alert(v,"critical",f"Auto-slow: TTC {v.ttc:.1f}s")
                elif v.alert in ("warning","caution"):
                    self._alert(v,v.alert,f"TTC {v.ttc:.1f}s to nearby vehicle")
                v.fused_position=fused
                # Maintain a stopping buffer behind a same-lane leader. This is
                # the low-speed safety envelope used when the TTC alert triggers.
                for other in self.vehicles:
                    if other is v or other.lane!=v.lane: continue
                    if other.state==v.state:
                        along=((v.progress-other.progress) if v.state=="return" else (other.progress-v.progress))%self.road.length
                        gap=along*config.METRES_PER_MAP_UNIT
                    elif other.speed < .2 and v.id > other.id:
                        gap=math.dist(pos,positions[other.id])*config.METRES_PER_MAP_UNIT
                    else:
                        continue
                    if 0 < gap < 120:
                        buffer=max(0.,gap-9.)
                        safe_speed=math.sqrt(max(0.,other.speed**2+2*config.VEHICLE["braking_mps2"]*buffer))
                        limit=min(limit,safe_speed*3.6)
                # Endpoint lane changes and opposing vehicles near tight bends
                # share a small local crossing envelope even across lane IDs.
                for other in self.vehicles:
                    if other is v: continue
                    distance=math.dist(pos,positions[other.id])*config.METRES_PER_MAP_UNIT
                    if distance < 20 and v.id > other.id:
                        limit=min(limit,max(0.,(distance-3.)/2.)*3.6)
            v.limit_kmh=limit
            target=limit/3.6
            if v.dwell>0:
                v.dwell=max(0,v.dwell-dt); target=0
                if v.dwell==0 and v.state=="load": v.loaded=True; v.state="haul"
                elif v.dwell==0 and v.state=="dump":
                    v.loaded=False; v.state="return"; v.trips+=1
                    self.cycle_durations.append(self.time-self.trip_started[v.id]); self.trip_started[v.id]=self.time
            else:
                # Baseline late reaction: eyesight range shrinks with fog, little forward planning.
                for other in self.vehicles:
                    if other is v or other.lane!=v.lane: continue
                    delta=other.progress-v.progress
                    if 0<delta<self.visibility/config.METRES_PER_MAP_UNIT and self.mode=="BASELINE":
                        target=min(target,max(0,other.speed-config.VEHICLE["baseline_braking_mps2"]*.2))
                if self.mode=="ASSISTED" and v.ttc is not None and v.ttc<3: target=min(target,2.2)
                if self.road.is_uphill(v.progress) and v.loaded: target=min(target,4.2)
                accel=config.VEHICLE["acceleration_mps2"]
                if v.speed>target: v.speed=max(target,v.speed-config.VEHICLE["braking_mps2"]*dt)
                else: v.speed=min(target,v.speed+accel*dt)
                direction=1 if v.state in ("haul","load") else -1
                v.progress=(v.progress + direction*v.speed*dt/config.METRES_PER_MAP_UNIT) % self.road.length
                at_load=math.dist(self.road.point(v.progress),config.LOADING_POINT)<3.5
                at_dump=math.dist(self.road.point(v.progress),config.DUMP_YARD)<3.5
                if not v.loaded and v.state=="return" and at_load: v.state="load"; v.dwell=config.VEHICLE["load_time_s"]
                elif v.loaded and v.state=="haul" and at_dump: v.state="dump"; v.dwell=config.VEHICLE["dump_time_s"]
            self.speed_samples.append(v.speed*3.6)
        # Count proximity events once per pair per tick, in either operating mode.
        live_near=set();live_collision=set()
        for i,a in enumerate(self.vehicles):
            for b in self.vehicles[i+1:]:
                d=math.dist(positions[a.id],positions[b.id])*config.METRES_PER_MAP_UNIT; key=tuple(sorted((a.id,b.id)))
                self.min_pair_dist=min(self.min_pair_dist,d)
                if d<5:
                    live_near.add(key)
                if d<5 and key not in self._near_active:
                    self.near_misses+=1
                    self._alert(a,"warning",f"Near miss: {d:.1f} m from {b.id}")
                if d<2:
                    live_collision.add(key)
                if d<2 and key not in self._collision_active:
                    self.collisions+=1
                    self._alert(a,"critical",f"Collision: {d:.1f} m from {b.id}")
        self._near_active=live_near; self._collision_active=live_collision

    def kpis(self):
        trips=sum(v.trips for v in self.vehicles)
        return {"trips":trips,"near_misses":self.near_misses,"collisions":self.collisions,
            "avg_speed_kmh":round(float(np.mean(self.speed_samples[-1000:])) if self.speed_samples else 0,1),
            "utilization_pct":round(sum(v.speed>.5 for v in self.vehicles)/len(self.vehicles)*100,1),
            "avg_cycle_min":round(float(np.mean(self.cycle_durations))/60,1) if self.cycle_durations else 0,
            "time_s":round(self.time,1),"min_distance_m":round(self.min_pair_dist,1) if self.min_pair_dist<999 else None}

    def snapshot(self):
        trucks=[]
        for v in self.vehicles:
            d=v.to_dict(); d["position"]=self.road.point(v.progress,v.lane); d["heading"]=self.road.heading(v.progress)+(180 if v.state=="return" else 0)
            d["nearby"]=[]
            for other in self.vehicles:
                if other.id!=v.id:
                    dist=math.dist(d["position"],self.road.point(other.progress,other.lane))*config.METRES_PER_MAP_UNIT
                    if dist<250: d["nearby"].append({"id":other.id,"distance_m":round(dist,1),"speed_kmh":round(other.speed*3.6,1),"lane":other.lane,"alert":other.alert})
            trucks.append(d)
        return {"mode":self.mode,"visibility":self.visibility,"fog_mode":fog_mode(self.visibility)["name"],"time":round(self.time,1),
            "road":config.ROAD_WAYPOINTS,"zones":config.ZONES,"vehicles":trucks,"kpis":self.kpis(),"alerts":self.alerts[-30:]}
