"""
3D Autonomous Sidewalk Delivery Robot Simulator - MAIN
=======================================================
Full-featured Weather-Adaptive Autonomous Delivery Robot Simulator.
Key Capabilities:
  - Strict Zebra Crossing Enforcement: Roadway crossing permitted exclusively at zebra crosswalk (z: 28.5–35.5)
  - Full Weather Simulation: Rain streaks, snowflakes, dense fog mist, and pitch night with optical vision degradation
  - Robot Forward Torch: High-intensity volumetric LED spotlight cutting through darkness and fog
  - Live Safety Rules Compliance Engine: Displays live compliance status for all 5 core ADAS rules
  - Obstacle Stop & Alternate Side Selection Detour
  - Pedestrian Mutual Collision Avoidance & Yielding
  - Full 360° Circular Heading Camera Following

Controls:
  SPACE      Start / Pause auto navigation
  M          Toggle Auto / Manual drive mode
  W/A/S/D    Manual drive (Forward, Reverse, Left, Right)
  X          Toggle Mission (Sidewalk Direct vs Zebra Crosswalk Mission)
  F          Cycle Weather (Clear, Rain, Heavy Rain, Fog, Night, Snow)
  T          Toggle Forward Robot Torch Spotlight
  1 / 2 / 3  Back-of-bot / Eye-level / 360° Orbit Camera
  C          Cycle Camera views
  B          Toggle 3D targeting laser beams
  R          Reset robot to start depot
  H          Toggle controls helper card
  ESC        Quit
"""
import math
import random

from ursina import (
    Ursina, Entity, Text, Sky, DirectionalLight, AmbientLight,
    camera, mouse, window, held_keys, application, destroy, invoke,
    Vec3, color, time, scene
)
from ursina.color import rgb32, rgba32

# ── Original modules (unchanged) ──────────────────────────────────────────
from environment.common_models  import get_cylinder, get_cone
from environment.road           import Road
from environment.sidewalk       import Sidewalk
from environment.city           import City
from environment.objects        import CityObjects
from environment.actors         import DynamicActorManager
from environment.weather        import WeatherSystem
from robot.humanoid_robot       import HumanoidDeliveryRobot
from robot.navigation           import RouteNavigator
from robot.movement             import MovementController
from sensors.sensor_manager     import SensorManager
from decision.safety_rules      import SafetyRulesEngine
from decision.rl_engine         import RLRewardEngine
from dashboard.ui               import DashboardUI
from camera_controller          import CameraController

# ═══════════════════════════════════════════════════════════════════════════
# SAFETY RULES SUPERVISOR (Dynamic Stop & Alternate Side Selection Detour)
# ═══════════════════════════════════════════════════════════════════════════

class FixedSafetyRulesEngine(SafetyRulesEngine):
    pass


# ═══════════════════════════════════════════════════════════════════════════
# FIXED CAMERA CONTROLLER
# (inherits original, fixes the BACK_OF_BOT snap startup lag)
# ═══════════════════════════════════════════════════════════════════════════

class FixedCameraController(CameraController):
    def __init__(self, target_robot):
        super().__init__(target_robot)
        # Force a hard snap on first frame so camera isn't at world origin
        self._first_frame = True

    def apply_camera_transform(self, dt):
        # On the very first frame snap directly (no lerp) to avoid camera
        # starting at Vec3(0,0,0) and slowly drifting to the right place.
        if self._first_frame:
            self._first_frame = False
            self.snap_to_target()
            return
        super().apply_camera_transform(dt)


# ═══════════════════════════════════════════════════════════════════════════
# SIMULATION SETUP & MAIN LOOP
# ═══════════════════════════════════════════════════════════════════════════

app = Ursina(
    title="3D Autonomous Sidewalk Delivery Robot Simulator",
    borderless=False,
    fullscreen=False,
    development_mode=False,
)
window.fps_counter.enabled = True
window.exit_button.visible = False

# ── Sky & Lighting ──────────────────────────────────────────────────────
sky = Sky()
sky.color = rgb32(100, 158, 228)

sun = DirectionalLight()
sun.look_at(Vec3(0.6, -1.4, 0.8))

ambient = AmbientLight()
ambient.color = color.Color(0.62, 0.62, 0.70, 1)

# ── Build world (Extended Big 280m City Metropolis) ─────────────────────
road = Road(length=280, road_width=12)
sidewalk = Sidewalk(length=280, road_width=12, sidewalk_width=6.0)
city = City(road_width=12, sidewalk_width=6.0, length=280)
objects = CityObjects(road_width=12, sidewalk_width=6.0, length=280)

# ── Dynamic actors ───────────────────────────────────────────────────────
actor_mgr = DynamicActorManager()

# ── Robot ────────────────────────────────────────────────────────────────
robot = HumanoidDeliveryRobot(position=(8.75, 0.28, -6))

# ── Navigator & movement ─────────────────────────────────────────────────
navigator  = RouteNavigator(robot)
controller = MovementController(robot)

# ── Sensors ─────────────────────────────────────────────────────────────
sensor_mgr = SensorManager(robot)

# ── Safety engine (fixed version) ────────────────────────────────────────
safety_engine = FixedSafetyRulesEngine()

# ── Reinforcement Learning Engine (MDP Rewards & Penalties) ──────────────
rl_engine = RLRewardEngine()

# ── Weather ──────────────────────────────────────────────────────────────
weather_sys = WeatherSystem(sky_entity=sky, sun_light=sun, ambient_light=ambient)
weather_sys.set_weather('clear')
weather_index = 0
WEATHER_CYCLE = ['clear', 'light_rain', 'heavy_rain', 'dense_fog', 'night', 'snowfall']

def _weather_speed():
    return weather_sys.get_speed_limit() / 1.6



# ── Camera (fixed) ───────────────────────────────────────────────────────
cam_ctrl = FixedCameraController(robot)

# ── Dashboard UI ─────────────────────────────────────────────────────────
dashboard = DashboardUI(robot, cam_ctrl, navigator, sensor_mgr, safety_engine, rl_engine=rl_engine)

# ═══════════════════════════════════════════════════════════════════════════
# STATE
# ═══════════════════════════════════════════════════════════════════════════
is_nav_running   = False   # SPACE starts/pauses
is_manual_mode   = False   # M toggles
show_lasers      = True
_manual_speed    = 0.0
_time_acc        = 0.0
_scenario_index  = -1      # V cycles through scenarios

# ─────────────────────────────────────────────────────────────────────────────
# SCENARIO SWITCHER DEFINITIONS (Req 4 – At Least 2 Safe Simulated Scenarios)
# ─────────────────────────────────────────────────────────────────────────────
SCENARIOS = [
    {
        "name": "SCN-1: CLEAR SIDEWALK CRUISING",
        "desc": "Nominal ADAS operation on empty East sidewalk at cruise speed.",
        "robot_pos": (8.75, 0.45, 0.0),
        "robot_rot": 0.0,
        "weather":   "clear",
        "failure":   "NORMAL",
    },
    {
        "name": "SCN-2: ZEBRA CROSSWALK + VEHICLE STOP",
        "desc": "Robot approaches South zebra crossing & halts for vehicle traffic.",
        "robot_pos": (8.75, 0.45, 20.0),
        "robot_rot": 0.0,
        "weather":   "clear",
        "failure":   "NORMAL",
    },
    {
        "name": "SCN-3: OBSTACLE DETOUR (CONSTRUCTION BARREL)",
        "desc": "Barrel blocks path; robot executes lateral avoidance maneuver.",
        "robot_pos": (8.75, 0.45, 50.0),
        "robot_rot": 0.0,
        "weather":   "clear",
        "failure":   "NORMAL",
    },
    {
        "name": "SCN-4: DENSE FOG + NIGHT TORCH",
        "desc": "Dense fog degrades vision to 5m; torch spotlight boosts forward detection.",
        "robot_pos": (8.75, 0.45, 100.0),
        "robot_rot": 0.0,
        "weather":   "dense_fog",
        "failure":   "NORMAL",
    },
    {
        "name": "SCN-5: PERCEPTION FAILURE — FALSE NEGATIVE",
        "desc": "Neural net misses forward pedestrian; fail-safe supervisor triggers emergency stop.",
        "robot_pos": (8.75, 0.45, 70.0),
        "robot_rot": 0.0,
        "weather":   "clear",
        "failure":   "FALSE_NEGATIVE",
    },
]

def _load_scenario(idx):
    """Teleport robot into pre-defined scenario and configure systems."""
    global is_nav_running, is_manual_mode, _manual_speed
    scn = SCENARIOS[idx]
    
    # Stop any active navigation
    is_nav_running = False
    is_manual_mode = False
    _manual_speed  = 0.0
    robot.speed    = 0.0
    robot.status   = "IDLE"
    
    # Teleport robot
    rx, ry, rz = scn["robot_pos"]
    robot.position   = (rx, ry, rz)
    robot.rotation_y = scn["robot_rot"]
    
    # Set weather
    weather_sys.set_weather(scn["weather"])
    global weather_index
    wname = scn["weather"]
    weather_index = WEATHER_CYCLE.index(wname) if wname in WEATHER_CYCLE else 0
    if hasattr(robot, 'set_torch_weather_mode'):
        robot.set_torch_weather_mode(wname)
    
    # Set perception failure injection mode
    fi = getattr(sensor_mgr, 'failure_injector', None)
    if fi:
        fi.set_mode(scn["failure"])
    
    # Reset safety engine state
    safety_engine.is_detouring = False
    safety_engine.detour_stage  = 0
    safety_engine._ped_yield_timer = 0.0
    safety_engine.is_crossing_zebra = False
    safety_engine.roadway_breach_active = False
    
    # Reset RL engine for fresh scenario scoring
    rl_engine.reset()
    
    # Update title pill to show active scenario
    dashboard.mode_pill.text  = f"[{scn['name']}]"
    dashboard.mode_pill.color = rgb32(255, 185, 30)
    dashboard.update_scenario_menu_text(scn['name'])
    
    # Resume auto-nav so the scenario runs immediately
    navigator.waypoints   = [Vec3(rx, ry, rz), Vec3(rx, ry, rz + 180.0)]
    navigator.current_idx = 0
    navigator.is_finished = False
    navigator.total_path_length = 180.0
    is_nav_running        = True

# ═══════════════════════════════════════════════════════════════════════════
# UPDATE
# ═══════════════════════════════════════════════════════════════════════════

def update():
    global is_nav_running, is_manual_mode, _manual_speed, _time_acc

    dt = min(time.dt, 0.05)
    if dt <= 0:
        return

    robot_pos = robot.position

    # ── Weather tick (Falling rain, snow, drifting mist particles) ─────
    weather_sys.update(dt, robot_pos=robot_pos)

    # ── Actor tick ──────────────────────────────────────────────────────
    actor_mgr.update(dt, robot_pos=robot_pos)

    # ── Robot update (idle animations & LiDAR spin) ────────────────────
    robot.update()

    # ── Sensor tick (Pass weather for vision degradation & torch boost) ─
    sensor_mgr.update_sensors(actor_mgr.get_all_trackable_actors(), dt, weather_sys=weather_sys)

    # ══════════════════════════════════════════════════════════════════
    # MOVEMENT
    # ══════════════════════════════════════════════════════════════════
    if is_manual_mode:
        # ── MANUAL DRIVE (W/A/S/D, full 360°) ─────────────────────────
        base_speed = _weather_speed() * 2.0
        moved = False

        if held_keys['w']:
            controller.drive_autonomous(robot.rotation_y, base_speed, dt)
            _manual_speed = base_speed
            moved = True
        if held_keys['s']:
            controller.drive_autonomous(robot.rotation_y, -base_speed * 0.7, dt)
            _manual_speed = -base_speed * 0.7
            moved = True
        if held_keys['a']:
            robot.rotation_y -= 75 * dt
        if held_keys['d']:
            robot.rotation_y += 75 * dt

        if not moved:
            _manual_speed = max(0.0, _manual_speed - dt * 4.0)
            robot.speed = _manual_speed

        robot.update_walk(dt)

        # Road boundary & Zebra Crossing safety evaluation
        is_in_road = (robot.x < safety_engine.curb_threshold_x and robot.x > -safety_engine.curb_threshold_x)
        is_on_zebra = any(z_min <= robot.z <= z_max for z_min, z_max in safety_engine.crosswalks)
        
        if is_in_road:
            dashboard.emergency_banner_bg.enabled   = True
            dashboard.emergency_banner_text.enabled = True
            if is_on_zebra:
                # Road crossing permitted via zebra crossing!
                safety_engine.is_crossing_zebra = True
                safety_engine.roadway_breach_active = False
                dashboard.emergency_banner_bg.color = rgba32(20, 160, 80, 210)
                dashboard.emergency_banner_text.text = (
                    "✓ AUTHORIZED ROADWAY CROSSING: CROSSING SAFELY VIA DESIGNATED ZEBRA CROSSWALK ✓"
                )
            else:
                # Outside zebra crossing: critical violation!
                safety_engine.is_crossing_zebra = False
                safety_engine.roadway_breach_active = True
                dashboard.emergency_banner_bg.color = rgba32(220, 25, 25, 230)
                dashboard.emergency_banner_text.text = (
                    "⚠️ CRITICAL SAFETY VIOLATION: ILLEGAL ROAD CROSSING! ROAD CROSSING STRICTLY PERMITTED ONLY AT ZEBRA CROSSINGS (z: 32m or 160m) ⚠️"
                )
        else:
            safety_engine.is_crossing_zebra = False
            safety_engine.roadway_breach_active = False
            dashboard.emergency_banner_bg.enabled   = False
            dashboard.emergency_banner_text.enabled = False

    elif is_nav_running and not navigator.is_finished:
        # ── AUTO-NAVIGATION ─────────────────────────────────────────────
        all_actors = actor_mgr.get_all_trackable_actors()
        # Use perceived_actors from sensor_mgr (which applies failure injection)
        perceived = getattr(sensor_mgr, 'perceived_actors', all_actors) or all_actors
        failure_injector = getattr(sensor_mgr, 'failure_injector', None)
        safety_action, speed_mult, target_heading = safety_engine.evaluate(
            robot, perceived, dt, failure_injector=failure_injector
        )

        # Apply weather speed cap
        weather_speed = _weather_speed()
        effective_speed = speed_mult * weather_speed

        if safety_action == "PROCEED_SAFE":
            nav_heading, nav_speed, is_done = navigator.update(dt)
            if is_done:
                robot.speed = 0.0
                robot.status = "DESTINATION REACHED"
            else:
                target_drive_speed = nav_speed * weather_speed
                controller.drive_autonomous(nav_heading, target_drive_speed, dt)
                robot.update_walk(dt)

        elif safety_action in ("DETOUR_AVOIDANCE", "DETOUR_RETURN"):
            # Keep navigating z-wise while steering laterally
            navigator.update(dt)   # advance waypoint tracking
            controller.drive_autonomous(target_heading, effective_speed, dt)
            robot.update_walk(dt)

        elif safety_action == "YIELD_DECELERATE":
            navigator.update(dt)
            controller.drive_autonomous(robot.rotation_y, effective_speed * 0.4, dt)
            robot.update_walk(dt)

        elif safety_action == "EMERGENCY_STOP":
            controller.current_speed = max(0.0, controller.current_speed - dt * 6.0)
            robot.speed = controller.current_speed
            robot.update_walk(dt)

        elif safety_action == "EMERGENCY_RETURN":
            controller.drive_autonomous(target_heading, effective_speed, dt)
            robot.update_walk(dt)

    else:
        # Idle
        robot.speed = max(0.0, robot.speed - dt * 3.5)
        robot.update_walk(dt)

    # ── Celebration Sequence upon Target Arrival ────────────────────────
    if navigator.is_finished:
        if not hasattr(objects, '_has_celebrated') or not objects._has_celebrated:
            objects._has_celebrated = True
            if hasattr(objects, 'celebration'):
                objects.celebration.trigger(robot.position)
        if hasattr(robot, 'celebrate'):
            robot.celebrate(dt)

    # ── Reinforcement Learning (RL) Reward & Penalty Engine Evaluation ──
    all_actors = actor_mgr.get_all_trackable_actors()
    rl_engine.evaluate(robot, all_actors, navigator, safety_engine, weather_sys, dt)

    # ── Update Destination Marker & Celebration Confetti ────────────────
    if hasattr(objects, 'destination_hub'):
        objects.destination_hub.update()
    if hasattr(objects, 'celebration'):
        objects.celebration.update()

    # ── Camera ──────────────────────────────────────────────────────────
    cam_ctrl.update(dt)

    # ── Dashboard ───────────────────────────────────────────────────────
    is_auto_label = "AUTO-NAV" if is_nav_running else ("MANUAL" if is_manual_mode else "IDLE")
    dashboard.mode_pill.text = f"[MODE: {is_auto_label}]"
    dashboard.update(dt)


# ═══════════════════════════════════════════════════════════════════════════
# INPUT
# ═══════════════════════════════════════════════════════════════════════════

def input(key):
    global is_nav_running, is_manual_mode, weather_index, show_lasers, _scenario_index

    # ── If Options Menu is open, numbers [1-8] trigger menu options directly ──
    if getattr(dashboard, 'is_menu_open', False):
        if key == '1':
            weather_index = (weather_index + 1) % len(WEATHER_CYCLE)
            w_name = WEATHER_CYCLE[weather_index]
            weather_sys.set_weather(w_name)
            if hasattr(robot, 'set_torch_weather_mode'):
                robot.set_torch_weather_mode(w_name)
            dashboard._refresh_menu_display()
            return
        elif key == '2':
            _scenario_index = (_scenario_index + 1) % len(SCENARIOS)
            _load_scenario(_scenario_index)
            dashboard._refresh_menu_display()
            return
        elif key == '3':
            sensor_mgr.cycle_failure_mode()
            dashboard._refresh_menu_display()
            return
        elif key == '4':
            dashboard.close_options_menu()
            dashboard.toggle_neural_hud()
            return
        elif key == '5':
            dashboard.close_options_menu()
            dashboard.toggle_arch_modal()
            return
        elif key == '6':
            dashboard.close_options_menu()
            dashboard.toggle_sim_limits()
            return
        elif key == '7':
            cam_ctrl.next_mode()
            dashboard._refresh_menu_display()
            return
        elif key == '8':
            dashboard.toggle_detailed_hud()
            dashboard._refresh_menu_display()
            return
        elif key in ('tab', 'escape'):
            dashboard.close_options_menu()
            return

    # ── Universal Keys (Always Active) ───────────────────────────────────
    if key == 'tab':
        dashboard.toggle_options_menu()
        return

    # ── Navigation Start / Pause ─────────────────────────────────────────
    if key == 'space':
        if is_manual_mode:
            is_manual_mode = False
        is_nav_running = not is_nav_running
        if is_nav_running and navigator.is_finished:
            navigator.reset()
            safety_engine.is_detouring = False
            safety_engine.detour_stage  = 0
            rl_engine.reset()
            objects._has_celebrated = False

    elif key == 'm':
        is_manual_mode = not is_manual_mode
        if is_manual_mode:
            is_nav_running = False
        robot.speed = 0.0

    # ── Camera Modes ────────────────────────────────────────────────────
    elif key == '1':
        cam_ctrl.set_mode_by_name("BACK_OF_BOT")
    elif key == '2':
        cam_ctrl.set_mode_by_name("THROUGH_THE_EYE")
    elif key == '3':
        cam_ctrl.set_mode_by_name("FREE_360_ORBIT")
    elif key == 'c':
        cam_ctrl.next_mode()

    # ── Scroll Zoom ─────────────────────────────────────────────────────
    elif key == 'scroll up':
        cam_ctrl.handle_scroll(+1)
    elif key == 'scroll down':
        cam_ctrl.handle_scroll(-1)

    # ── Weather Cycle ───────────────────────────────────────────────────
    elif key == 'f':
        weather_index = (weather_index + 1) % len(WEATHER_CYCLE)
        w_name = WEATHER_CYCLE[weather_index]
        weather_sys.set_weather(w_name)
        if hasattr(robot, 'set_torch_weather_mode'):
            robot.set_torch_weather_mode(w_name)

    # ── Torch spotlight toggle ───────────────────────────────────────────
    elif key == 't':
        if hasattr(robot, 'toggle_torch'):
            robot.toggle_torch()

    # ── Mission route toggle (Grand Crosswalk vs Express) ───────────────
    elif key == 'x':
        navigator.toggle_mission()
        safety_engine.is_detouring = False
        safety_engine.detour_stage  = 0
        safety_engine.is_crossing_zebra = False
        safety_engine.roadway_breach_active = False
        rl_engine.reset()
        objects._has_celebrated = False
        if hasattr(objects, 'celebration'):
            objects.celebration.is_active = False
            for p in objects.celebration.particles:
                p.enabled = False

    # ── Laser targeting toggle ───────────────────────────────────────────
    elif key == 'b':
        sensor_mgr.laser_tracker.toggle()

    # ── Reset to Start ───────────────────────────────────────────────────
    elif key == 'r':
        navigator.reset()
        safety_engine.is_detouring = False
        safety_engine.detour_stage  = 0
        safety_engine._ped_yield_timer = 0.0
        safety_engine.is_crossing_zebra = False
        safety_engine.roadway_breach_active = False
        rl_engine.reset()
        objects._has_celebrated = False
        if hasattr(objects, 'celebration'):
            objects.celebration.is_active = False
            for p in objects.celebration.particles:
                p.enabled = False
        is_nav_running = False
        robot.speed    = 0.0
        robot.status   = "IDLE"

    # ── Direct Modal Shortcuts (Still work directly!) ───────────────────
    elif key == 'i':
        dashboard.toggle_arch_modal()
    elif key == 'n':
        dashboard.toggle_neural_hud()
    elif key == 'l':
        dashboard.toggle_sim_limits()

    # ── Direct Failure Injection Shortcut ───────────────────────────────
    elif key == 'u':
        new_mode = sensor_mgr.cycle_failure_mode()
        dashboard.mode_pill.text = f"[{new_mode}]"

    # ── Direct Scenario Switcher Shortcut ───────────────────────────────
    elif key == 'v':
        _scenario_index = (_scenario_index + 1) % len(SCENARIOS)
        _load_scenario(_scenario_index)

    # ── Detailed 4-Card HUD Toggle ──────────────────────────────────────
    elif key == 'h':
        dashboard.toggle_detailed_hud()

    # ── Escape Key: Dismiss any active modal/menu first, or quit ─────────
    elif key == 'escape':
        if getattr(dashboard, 'is_menu_open', False):
            dashboard.close_options_menu()
        elif hasattr(dashboard, 'arch_modal') and dashboard.arch_modal.is_open:
            dashboard.arch_modal.close()
        elif hasattr(dashboard, 'neural_hud') and dashboard.neural_hud.is_open:
            dashboard.neural_hud.close()
        elif hasattr(dashboard, 'sim_limits_modal') and dashboard.sim_limits_modal.is_open:
            dashboard.sim_limits_modal.close()
        else:
            application.quit()


# ═══════════════════════════════════════════════════════════════════════════
app.run()
