# Fog-Safe Haulage Digital Twin

A runnable software prototype for Smart India Hackathon PS 26007: **Safe and Efficient Operation of Mine Vehicles in Fog and Low-Visibility Conditions in Open Cast Iron Ore Mines** (NMDC, Bailadila). No physical hardware is used.

## Run

Requires Python 3.11 or newer.

```bash
cd fog-safe-haulage-digital-twin
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000. The Control Room has start, pause, reset, driving mode, and visibility controls. The Comparison page runs both modes for the same seed, fleet size, fog, and simulated duration. The In-cab HUD shows selected-truck telemetry and nearby traffic. Change `FLEET_SIZE` in the environment to configure the fleet.

## Deploy on Render

The repository includes `render.yaml` for a single-instance Render web service. Push this project folder to a GitHub repository, then in Render choose **New → Blueprint**, connect that repository, and deploy the `fog-safe-haulage-twin` service. Render reads the build and start commands from the Blueprint. When it finishes, open the service URL it provides. The single Gunicorn worker is intentional because simulation state is held in memory. Socket.IO can use its polling transport with this threaded worker.

You can also deploy the folder as a Python web service manually with build command `pip install -r requirements.txt` and start command `gunicorn --workers 1 --worker-class gthread --threads 100 --bind 0.0.0.0:$PORT app:app`.

## How it works

The road is a configurable waypoint polyline in `config.py`, with two directional lanes, three geofenced hairpins, a junction, a loading point, a dump yard, and a modeled uphill section. Ten synthetic dumpers move through empty return, loading, loaded haul, and dumping states on a fixed 10 Hz simulation clock. Flask-SocketIO streams the in-memory state to the dashboard.

Baseline trucks use a visibility-limited driver sight distance and late braking. Assisted trucks apply fog-mode speed caps and geofence limits, fuse noisy GNSS position updates through an Extended Kalman Filter, and use V2V traffic state plus noisy radar detections to calculate TTC and slow for conflicts. The Comparison API constructs independent baseline and assisted worlds with the same seed and scenario parameters.

### Presentation summary

“This digital twin models a two-way looping hilltop haul road and a fleet of dumpers working through load, haul, dump, and return cycles. We replay the same fog scenario with the same random seed under eyesight-only baseline driving and an assisted mode that combines V2V, GNSS/IMU filtering, radar, TTC alerts, and geofenced speed limits. In the prototype, these software-only assumptions allow us to compare throughput and proximity events consistently. The sensors and attenuation are simulated; this result is a concept demonstration and does not validate real equipment or mine safety performance.”

## Assumptions and limitations

- GNSS uses 2 cm Gaussian position noise and 0.8% independent per-tick dropouts. The filter is a linear constant-velocity Kalman approximation (the configured filter is used for position fusion); radar range and target positions have configurable noise.
- Radar nominal range is 110 m and degrades by up to 16% as visibility approaches zero. Driver sight distance equals the selected visibility. Road-map coordinates use a simple local scale: one map unit is treated as approximately 5 m for conflict-distance reporting.
- Dumper acceleration, braking, load/dump times, uphill speed, geofence radii, and zone limits are illustrative editable values in `config.py`, not NMDC equipment specifications.
- The comparison is a deterministic software experiment, not a measured field trial. Improve/decline percentages depend on duration and scenario. The app includes an honest sensor simulation notice.
- Chart.js and Socket.IO browser bundles are loaded from CDNs; an internet connection is needed for those UI libraries unless served locally.
