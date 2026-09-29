from threading import Lock
import time
import os
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO
import config
from sim.engine import Simulation

app=Flask(__name__); app.config["SECRET_KEY"]="fog-safe-twin-demo"
socketio=SocketIO(app,cors_allowed_origins="*",async_mode="threading")
lock=Lock(); sim=Simulation(); worker_started=False

def run_loop():
    deadline=time.monotonic()
    while True:
        socketio.sleep(0.1)
        with lock:
            if not sim.running: continue
            sim.tick(.1); state=sim.snapshot()
        socketio.emit("state",state)

@app.route("/")
def index(): return render_template("index.html")
@app.route("/compare")
def compare_page(): return render_template("compare.html")
@app.route("/hud")
def hud_page(): return render_template("hud.html")
@app.get("/api/state")
def api_state():
    with lock: return jsonify(sim.snapshot())
@app.post("/api/control")
def control():
    global sim,worker_started
    data=request.get_json(force=True); action=data.get("action")
    with lock:
        if action=="start": sim.running=True
        elif action=="pause": sim.running=False
        elif action=="reset":
            sim=Simulation(data.get("mode","ASSISTED"),data.get("visibility",12),data.get("seed",config.SEED),data.get("fleet_size"))
        elif action=="mode":
            sim=Simulation(data.get("mode","ASSISTED"),sim.visibility,config.SEED)
        elif action=="visibility": sim.set_visibility(data.get("visibility",sim.visibility))
        state=sim.snapshot()
    if not worker_started:
        socketio.start_background_task(run_loop); worker_started=True
    socketio.emit("state",state); return jsonify(state)
@app.post("/api/compare")
def compare():
    data=request.get_json(force=True); duration=max(60,min(3600,int(data.get("duration",600))))
    visibility=max(3,min(100,float(data.get("visibility",12)))); seed=int(data.get("seed",config.SEED)); n=int(data.get("fleet_size",config.FLEET_SIZE))
    results={}
    for mode in ("BASELINE","ASSISTED"):
        run=Simulation(mode,visibility,seed,n)
        for _ in range(duration*10): run.tick(.1)
        results[mode.lower()]={"kpis":run.kpis(),"alerts":run.alerts[-10:]}
    return jsonify({"seed":seed,"duration_s":duration,"visibility":visibility,"results":results})

if __name__=="__main__":
    port=int(os.environ.get("PORT",5000))
    print(f"Fog-Safe Haulage Digital Twin listening on port {port}")
    socketio.run(app,host="0.0.0.0",port=port,debug=False,allow_unsafe_werkzeug=True)
