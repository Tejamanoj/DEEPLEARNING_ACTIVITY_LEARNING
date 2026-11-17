"""
Dashboard UI Module: Sleek, high-contrast, uncluttered autonomous driving HUD.
Neatly arranged into 4 balanced corner cards, a slim top header, and an unobtrusive
quick-control strip. Fully modal-isolated so no text ever overlaps or bleeds through.
"""
from ursina import Entity, camera, color, Vec2, Text, window
from ursina.color import rgb32, rgba32
import math
from .architecture_modal import ArchitectureComparisonModal
from .neural_hud import NeuralPerceptionHUD
from .sim_limitations import SimLimitationsModal

class DashboardUI:
    def __init__(self, robot, camera_ctrl, navigator, sensor_mgr=None, safety_engine=None, rl_engine=None):
        self.robot = robot
        self.camera_ctrl = camera_ctrl
        self.navigator = navigator
        self.sensor_mgr = sensor_mgr
        self.safety_engine = safety_engine
        self.rl_engine = rl_engine
        self.show_help = False  # Collapsed by default to keep screen clean!
        self.alert_flash_timer = 0.0
        self.celebration_timer = 0.0
        
        # ── Modals (Deep Learning Theory, Perception HUD, Sim Limitations) ───
        self.arch_modal = ArchitectureComparisonModal()
        self.neural_hud = NeuralPerceptionHUD()
        self.sim_limits_modal = SimLimitationsModal()
        
        # Wire modal callbacks to auto-hide main HUD when any modal is open
        self.arch_modal._on_open_callback = self._hide_main_hud
        self.arch_modal._on_close_callback = self._show_main_hud
        self.neural_hud._on_open_callback = self._hide_main_hud
        self.neural_hud._on_close_callback = self._show_main_hud
        self.sim_limits_modal._on_open_callback = self._hide_main_hud
        self.sim_limits_modal._on_close_callback = self._show_main_hud

        # ══════════════════════════════════════════════════════════════════
        # 1. SLIM TOP HEADER BAR
        # ══════════════════════════════════════════════════════════════════
        self.header_bg = Entity(
            parent=camera.ui,
            model='quad',
            scale=(2.0, 0.052),
            position=(0, 0.474),
            color=rgba32(10, 16, 26, 235)
        )
        
        self.title_text = Text(
            text="AUTONOMOUS SIDEWALK DELIVERY ROBOT",
            parent=camera.ui,
            position=(-0.92, 0.485),
            scale=0.92,
            color=rgb32(0, 220, 255),
            origin=(-0.5, 0.5)
        )
        
        chassis_name = "HUMANOID ANDROID" if "HUMANOID" in getattr(self.robot, 'actor_type', '') else "WHEELED ROVER"
        self.chassis_pill = Text(
            text=f"[{chassis_name}]",
            parent=camera.ui,
            position=(0.18, 0.485),
            scale=0.78,
            color=rgb32(255, 185, 30),
            origin=(-0.5, 0.5)
        )
        
        self.mode_pill = Text(
            text="[MODE: AUTO-NAV]",
            parent=camera.ui,
            position=(0.46, 0.485),
            scale=0.78,
            color=rgb32(100, 255, 150),
            origin=(-0.5, 0.5)
        )
        
        self.cam_pill = Text(
            text=f"[CAM: {self.camera_ctrl.mode}]",
            parent=camera.ui,
            position=(0.72, 0.485),
            scale=0.78,
            color=rgb32(255, 215, 0),
            origin=(-0.5, 0.5)
        )

        # ══════════════════════════════════════════════════════════════════
        # 2. EMERGENCY / ZEBRA CROSSWALK BANNER (Appears only on event)
        # ══════════════════════════════════════════════════════════════════
        self.emergency_banner_bg = Entity(
            parent=camera.ui,
            model='quad',
            scale=(1.60, 0.055),
            position=(0, 0.415),
            color=rgba32(220, 30, 30, 230),
            enabled=False
        )
        self.emergency_banner_text = Text(
            text="⚠️ ROADWAY INTRUSION ALERT! CROSS ONLY AT ZEBRA CROSSING ⚠️",
            parent=camera.ui,
            position=(0, 0.415),
            scale=0.85,
            color=color.white,
            origin=(0, 0),
            enabled=False
        )

        # ══════════════════════════════════════════════════════════════════
        # 3. TOP-LEFT CARD: AI SENSOR PERCEPTION & VISION
        # ══════════════════════════════════════════════════════════════════
        self.sensor_bg = Entity(
            parent=camera.ui,
            model='quad',
            scale=(0.58, 0.18),
            position=(-0.60, 0.33),
            color=rgba32(12, 18, 28, 220)
        )
        self.sensor_border = Entity(
            parent=camera.ui,
            model='quad',
            scale=(0.58, 0.003),
            position=(-0.60, 0.42),
            color=rgb32(0, 220, 255)
        )
        self.sensor_title = Text(
            text="AI SENSOR PERCEPTION & FUSION",
            parent=camera.ui,
            position=(-0.87, 0.405),
            scale=0.76,
            color=rgb32(0, 220, 255),
            origin=(-0.5, 0.5)
        )
        self.target_text = Text(
            text="Closest Object: NONE | Range: --- m",
            parent=camera.ui,
            position=(-0.87, 0.375),
            scale=0.72,
            color=color.white,
            origin=(-0.5, 0.5)
        )
        self.weather_vision_text = Text(
            text="Weather: CLEAR | Vision: 16.0m | Conf: 99%",
            parent=camera.ui,
            position=(-0.87, 0.345),
            scale=0.68,
            color=rgb32(255, 220, 60),
            origin=(-0.5, 0.5)
        )
        self.torch_status_text = Text(
            text="Torch: ON | LiDAR: 360° Sweep | Radar: ACTIVE",
            parent=camera.ui,
            position=(-0.87, 0.318),
            scale=0.66,
            color=rgb32(180, 225, 245),
            origin=(-0.5, 0.5)
        )
        self.failure_badge_text = Text(
            text="Perception: [NOMINAL]  [U]: Cycle Failure Modes",
            parent=camera.ui,
            position=(-0.87, 0.290),
            scale=0.68,
            color=rgb32(80, 255, 120),
            origin=(-0.5, 0.5)
        )

        # ══════════════════════════════════════════════════════════════════
        # 4. TOP-RIGHT CARD: SAFETY RULES COMPLIANCE ENGINE
        # ══════════════════════════════════════════════════════════════════
        self.safety_card_bg = Entity(
            parent=camera.ui,
            model='quad',
            scale=(0.58, 0.18),
            position=(0.60, 0.33),
            color=rgba32(12, 18, 28, 220)
        )
        self.safety_card_border = Entity(
            parent=camera.ui,
            model='quad',
            scale=(0.58, 0.003),
            position=(0.60, 0.42),
            color=rgb32(60, 225, 100)
        )
        self.safety_card_title = Text(
            text="SAFETY RULES ENGINE (LIVE COMPLIANCE)",
            parent=camera.ui,
            position=(0.33, 0.405),
            scale=0.76,
            color=rgb32(60, 225, 100),
            origin=(-0.5, 0.5)
        )
        self.rule1_text = Text(
            text="R1 Sidewalk: [COMPLIANT] | R2 Zebra: [COMPLIANT]",
            parent=camera.ui,
            position=(0.33, 0.375),
            scale=0.68,
            color=rgb32(140, 255, 170),
            origin=(-0.5, 0.5)
        )
        self.rule3_text = Text(
            text="R3 Pedestrian Buffer  : [SAFE CLEARANCE (>2.0m)]",
            parent=camera.ui,
            position=(0.33, 0.345),
            scale=0.68,
            color=rgb32(140, 255, 170),
            origin=(-0.5, 0.5)
        )
        self.rule4_text = Text(
            text="R4 Obstacle Detour    : [PATH CLEAR - CENTERLINE]",
            parent=camera.ui,
            position=(0.33, 0.318),
            scale=0.68,
            color=rgb32(180, 220, 240),
            origin=(-0.5, 0.5)
        )
        self.forward_corridor_text = Text(
            text="Action: PATH CLEAR (Cruising safe)",
            parent=camera.ui,
            position=(0.33, 0.290),
            scale=0.68,
            color=rgb32(80, 255, 120),
            origin=(-0.5, 0.5)
        )

        # ══════════════════════════════════════════════════════════════════
        # 5. BOTTOM-LEFT CARD: ROBOT KINEMATICS & MISSION
        # ══════════════════════════════════════════════════════════════════
        self.telemetry_bg = Entity(
            parent=camera.ui,
            model='quad',
            scale=(0.58, 0.13),
            position=(-0.60, -0.405),
            color=rgba32(12, 18, 28, 220)
        )
        self.telemetry_border = Entity(
            parent=camera.ui,
            model='quad',
            scale=(0.58, 0.003),
            position=(-0.60, -0.34),
            color=rgb32(0, 215, 255)
        )
        self.telemetry_title = Text(
            text="ROBOT KINEMATICS & MISSION",
            parent=camera.ui,
            position=(-0.87, -0.355),
            scale=0.74,
            color=rgb32(180, 215, 240),
            origin=(-0.5, 0.5)
        )
        self.speed_text = Text(
            text="Speed: 0.0 m/s (0.0 km/h) | Heading: 0.0°",
            parent=camera.ui,
            position=(-0.87, -0.385),
            scale=0.76,
            color=color.white,
            origin=(-0.5, 0.5)
        )
        self.pos_text = Text(
            text="Position: (8.75, 0.28, -6.00)",
            parent=camera.ui,
            position=(-0.87, -0.415),
            scale=0.68,
            color=rgb32(190, 205, 220),
            origin=(-0.5, 0.5)
        )
        self.progress_text = Text(
            text="Mission: GRAND ZEBRA CROSSWALK [0.0%]",
            parent=camera.ui,
            position=(-0.87, -0.445),
            scale=0.72,
            color=rgb32(0, 220, 255),
            origin=(-0.5, 0.5)
        )

        # ══════════════════════════════════════════════════════════════════
        # 6. BOTTOM-RIGHT CARD: RL REWARDS & PENALTIES (MDP)
        # ══════════════════════════════════════════════════════════════════
        self.rl_bg = Entity(
            parent=camera.ui,
            model='quad',
            scale=(0.58, 0.13),
            position=(0.60, -0.405),
            color=rgba32(12, 18, 28, 220)
        )
        self.rl_border = Entity(
            parent=camera.ui,
            model='quad',
            scale=(0.58, 0.003),
            position=(0.60, -0.34),
            color=rgb32(255, 215, 20)
        )
        self.rl_title = Text(
            text="REINFORCEMENT LEARNING REWARD (MDP)",
            parent=camera.ui,
            position=(0.33, -0.355),
            scale=0.74,
            color=rgb32(255, 215, 20),
            origin=(-0.5, 0.5)
        )
        self.rl_score_text = Text(
            text="Net Reward: +0.0 pts | Step: +0.00",
            parent=camera.ui,
            position=(0.33, -0.385),
            scale=0.78,
            color=rgb32(100, 255, 180),
            origin=(-0.5, 0.5)
        )
        self.rl_breakdown_text = Text(
            text="Rewards: +0.0 | Penalties: -0.0",
            parent=camera.ui,
            position=(0.33, -0.415),
            scale=0.68,
            color=rgb32(180, 220, 240),
            origin=(-0.5, 0.5)
        )
        self.rl_penalty_text = Text(
            text="Live Event: EPISODE READY",
            parent=camera.ui,
            position=(0.33, -0.445),
            scale=0.68,
            color=rgb32(255, 220, 60),
            origin=(-0.5, 0.5)
        )

        # ══════════════════════════════════════════════════════════════════
        # 7. BOTTOM CENTER: SLEEK QUICK CONTROLS BAR
        # ══════════════════════════════════════════════════════════════════
        self.quick_bar_bg = Entity(
            parent=camera.ui,
            model='quad',
            scale=(1.35, 0.038),
            position=(0, -0.478),
            color=rgba32(10, 16, 26, 220)
        )
        self.quick_bar_text = Text(
            text="[SPACE] Drive  |  [V] Scenarios  |  [F] Weather  |  [U] Failures  |  [N] Vision HUD  |  [I] AI Arch  |  [L] Limits  |  [H] Controls Guide",
            parent=camera.ui,
            position=(0, -0.478),
            scale=0.70,
            color=rgb32(170, 210, 235),
            origin=(0, 0)
        )

        # ══════════════════════════════════════════════════════════════════
        # 8. CONTROLS GUIDE MODAL (Opens cleanly on [H], dismissed with [H]/[ESC])
        # ══════════════════════════════════════════════════════════════════
        self.help_modal_widgets = []
        self.help_backdrop = Entity(
            parent=camera.ui,
            model='quad',
            scale=(1.40, 0.72),
            position=(0, 0),
            color=rgba32(8, 14, 22, 250),
            enabled=False
        )
        self.help_modal_widgets.append(self.help_backdrop)

        self.help_title = Text(
            text="SIMULATOR CONTROLS GUIDE  —  Press [H] or [ESC] to Dismiss",
            parent=camera.ui,
            position=(0, 0.31),
            scale=0.88,
            color=rgb32(0, 220, 255),
            origin=(0, 0),
            enabled=False
        )
        self.help_modal_widgets.append(self.help_title)

        col1_text = (
            "CAMERA & DRIVING CONTROLS\n"
            "─────────────────────────\n"
            "[SPACE]     : Start / Pause Auto-Nav\n"
            "[M]         : Toggle Auto / Manual Drive\n"
            "[W, A, S, D]: Manual Steering & Throttle\n"
            "[1, 2, 3]   : Back / Eye / Orbit Camera\n"
            "[C]         : Cycle Camera Modes\n"
            "Mouse Drag  : 360° Free Orbit Pan\n"
            "Mouse Wheel : Zoom In / Zoom Out\n"
            "[R]         : Reset Robot to Start Depot"
        )
        self.help_col1 = Text(
            text=col1_text,
            parent=camera.ui,
            position=(-0.60, 0.25),
            scale=0.72,
            color=rgb32(210, 230, 245),
            origin=(-0.5, 0.5),
            enabled=False
        )
        self.help_modal_widgets.append(self.help_col1)

        col2_text = (
            "DEEP LEARNING & EVALUATION FEATURES\n"
            "───────────────────────────────────\n"
            "[V]         : Cycle 5 Pre-set ELA Scenarios\n"
            "[F]         : Cycle Weather (Rain/Fog/Night/Snow)\n"
            "[T]         : Toggle Forward Torch Spotlight\n"
            "[U]         : Inject Perception Failures (6 Modes)\n"
            "[N]         : Toggle Neural Perception HUD (YOLO/Seg)\n"
            "[I] / [TAB] : Compare Modular vs End-to-End DL\n"
            "[L]         : Sim Limitations & Sim-to-Real Gap\n"
            "[B]         : Toggle 3D Laser Targeting Beams"
        )
        self.help_col2 = Text(
            text=col2_text,
            parent=camera.ui,
            position=(0.04, 0.25),
            scale=0.72,
            color=rgb32(210, 230, 245),
            origin=(-0.5, 0.5),
            enabled=False
        )
        self.help_modal_widgets.append(self.help_col2)

        # ══════════════════════════════════════════════════════════════════
        # 9. DESTINATION TARGET CELEBRATION BANNER
        # ══════════════════════════════════════════════════════════════════
        self.celebration_banner_bg = Entity(
            parent=camera.ui,
            model='quad',
            scale=(1.60, 0.16),
            position=(0, 0.04),
            color=rgba32(10, 16, 26, 245),
            enabled=False
        )
        self.celebration_banner_title = Text(
            text="MISSION ACCOMPLISHED! TARGET REACHED!",
            parent=camera.ui,
            position=(0, 0.08),
            scale=1.20,
            color=rgb32(255, 215, 20),
            origin=(0, 0),
            enabled=False
        )
        self.celebration_banner_sub = Text(
            text="★ Delivery Completed at Central Terminal! +150.0 RL Terminal Reward Awarded! ★",
            parent=camera.ui,
            position=(0, 0.01),
            scale=0.88,
            color=rgb32(100, 255, 180),
            origin=(0, 0),
            enabled=False
        )

    # ══════════════════════════════════════════════════════════════════════
    # MODAL & HUD ISOLATION ENGINE
    # ══════════════════════════════════════════════════════════════════════
    def _get_main_hud_widgets(self):
        """Returns all main HUD elements that should hide during full-screen modal overlays."""
        return [
            self.header_bg, self.title_text, self.chassis_pill, self.mode_pill, self.cam_pill,
            self.sensor_bg, self.sensor_border, self.sensor_title,
            self.target_text, self.weather_vision_text, self.torch_status_text, self.failure_badge_text,
            self.safety_card_bg, self.safety_card_border, self.safety_card_title,
            self.rule1_text, self.rule3_text, self.rule4_text, self.forward_corridor_text,
            self.telemetry_bg, self.telemetry_border, self.telemetry_title,
            self.speed_text, self.pos_text, self.progress_text,
            self.rl_bg, self.rl_border, self.rl_title,
            self.rl_score_text, self.rl_breakdown_text, self.rl_penalty_text,
            self.quick_bar_bg, self.quick_bar_text,
        ]

    def _hide_main_hud(self):
        for w in self._get_main_hud_widgets():
            try:
                w.enabled = False
            except Exception:
                pass

    def _show_main_hud(self):
        for w in self._get_main_hud_widgets():
            try:
                w.enabled = True
            except Exception:
                pass

    def toggle_help(self):
        self.show_help = not self.show_help
        if self.show_help:
            self._hide_main_hud()
            for w in self.help_modal_widgets:
                w.enabled = True
        else:
            for w in self.help_modal_widgets:
                w.enabled = False
            self._show_main_hud()

    def toggle_arch_modal(self):
        return self.arch_modal.toggle()

    def toggle_neural_hud(self):
        return self.neural_hud.toggle()

    def toggle_sim_limits(self):
        return self.sim_limits_modal.toggle()

    def set_robot(self, new_robot):
        self.robot = new_robot
        chassis_name = "HUMANOID ANDROID" if "HUMANOID" in getattr(self.robot, 'actor_type', '') else "WHEELED ROVER"
        self.chassis_pill.text = f"[{chassis_name}]"

    # ══════════════════════════════════════════════════════════════════════
    # LIVE TELEMETRY UPDATE TICK
    # ══════════════════════════════════════════════════════════════════
    def update(self, dt):
        self.alert_flash_timer += dt * 4.0
        
        # 1. Kinematics
        spd_ms = self.robot.speed
        spd_kmh = spd_ms * 3.6
        heading = (self.robot.rotation_y % 360)
        self.speed_text.text = f"Speed: {spd_ms:4.1f} m/s ({spd_kmh:4.1f} km/h) | Heading: {heading:5.1f}°"
        
        pos = self.robot.position
        self.pos_text.text = f"Position: ({pos.x:.2f}, {pos.y:.2f}, {pos.z:.2f})"
        
        pct = self.navigator.get_progress_percent()
        mission_name = self.navigator.get_mission_name() if hasattr(self.navigator, 'get_mission_name') else "ROUTE"
        status_label = "ARRIVED" if self.navigator.is_finished else f"{pct:4.1f}%"
        self.progress_text.text = f"Mission: {mission_name} [{status_label}]"
        
        self.cam_pill.text = f"[CAM: {self.camera_ctrl.mode}]"
        
        # 2. Sensor & Weather Vision Telemetry
        if self.sensor_mgr:
            d = self.sensor_mgr.closest_object_distance
            d_str = f"{d:.1f} m" if d < 100 else "--- m"
            self.target_text.text = f"Closest: [{self.sensor_mgr.closest_object_type}] at {d_str} | Threat: [{self.sensor_mgr.threat_level}]"
            
            w_cond = getattr(self.sensor_mgr, 'weather_condition', 'CLEAR')
            v_range = getattr(self.sensor_mgr, 'vision_range', 16.0)
            v_conf = getattr(self.sensor_mgr, 'detection_confidence', 99)
            self.weather_vision_text.text = f"Weather: {w_cond} | Vision: {v_range:.1f}m | Conf: {int(v_conf)}%"
            
            torch_active = getattr(self.robot, 'torch_enabled', True)
            torch_str = "ON" if torch_active else "OFF"
            self.torch_status_text.text = f"Torch: {torch_str} | LiDAR: 360° Sweep | Radar: ACTIVE"
            
            # Perception Failure Badge Update
            fi = getattr(self.sensor_mgr, 'failure_injector', None)
            if fi:
                mode = fi.active_mode
                details = fi.get_details()
                badge_text = details["badge"]
                col = details["color"]
                
                if mode == "NORMAL":
                    self.failure_badge_text.text = f"Perception: [NOMINAL]  [U]: Cycle Failures"
                    self.failure_badge_text.color = rgb32(80, 255, 120)
                elif mode == "FALSE_NEGATIVE":
                    supervisor = getattr(fi, 'safety_supervisor_tripped', False)
                    sup_tag = " ⚠️ SUPERVISOR BRAKE" if supervisor else " (MISSED TARGET)"
                    self.failure_badge_text.text = f"{badge_text}{sup_tag}"
                    self.failure_badge_text.color = rgb32(*col)
                elif mode == "FALSE_POSITIVE":
                    self.failure_badge_text.text = f"{badge_text}: Ghost at 2.8m (Phantom Stop)"
                    self.failure_badge_text.color = rgb32(*col)
                elif mode == "LATENCY_DELAY":
                    self.failure_badge_text.text = f"{badge_text}: 450ms Lag (Late Braking)"
                    self.failure_badge_text.color = rgb32(*col)
                elif mode == "HIGH_UNCERTAINTY":
                    conf_val = int(v_conf) if fi.simulated_conf_override else 99
                    self.failure_badge_text.text = f"{badge_text}: Conf={conf_val}% (Speed Capped)"
                    self.failure_badge_text.color = rgb32(*col)
                elif mode == "MISCLASSIFICATION":
                    self.failure_badge_text.text = f"{badge_text}: Pedestrian -> Obstacle"
                    self.failure_badge_text.color = rgb32(*col)

        # 3. Neural Perception HUD tick (if active)
        if hasattr(self, 'neural_hud') and self.neural_hud.is_open:
            fi = getattr(self.sensor_mgr, 'failure_injector', None) if self.sensor_mgr else None
            self.neural_hud.update(dt, self.robot, sensor_mgr=self.sensor_mgr, failure_injector=fi)

        # 4. RL Telemetry
        if self.rl_engine:
            tot = self.rl_engine.cumulative_reward
            step_r = self.rl_engine.last_step_reward
            pos_r = getattr(self.rl_engine, 'total_positive_rewards', 0.0)
            tot_p = getattr(self.rl_engine, 'total_penalties', 0.0)
            
            self.rl_score_text.text = f"Net Reward: {tot:+7.1f} pts | Step: {step_r:+5.2f}"
            self.rl_score_text.color = rgb32(100, 255, 180) if tot >= 0 else rgb32(255, 75, 75)
            
            self.rl_breakdown_text.text = f"Rewards: +{pos_r:.1f} pts | Penalties: -{tot_p:.1f} pts"
            
            if len(self.rl_engine.recent_events) > 0:
                last_event = self.rl_engine.recent_events[-1]
                if "PENALTY" in last_event:
                    self.rl_penalty_text.text = f"⚠️ {last_event}"
                    self.rl_penalty_text.color = rgb32(255, 60, 60)
                else:
                    self.rl_penalty_text.text = f"✓ {last_event}"
                    self.rl_penalty_text.color = rgb32(100, 255, 180)

        # 5. Safety Rules Engine
        if self.safety_engine:
            action = self.safety_engine.safety_action
            if action == "DETOUR_AVOIDANCE":
                self.forward_corridor_text.text = f"Action: DETOURING -> BYPASSING {self.safety_engine.blocking_actor_name}"
                self.forward_corridor_text.color = rgb32(0, 225, 255)
            elif action == "DETOUR_RETURN":
                self.forward_corridor_text.text = "Action: DETOUR COMPLETE -> RETURNING"
                self.forward_corridor_text.color = rgb32(100, 255, 180)
            elif action == "EMERGENCY_STOP":
                fwd_d = self.safety_engine.obstacle_ahead_distance
                self.forward_corridor_text.text = f"Action: YIELDING / STOPPING ({fwd_d:.1f}m)"
                self.forward_corridor_text.color = rgb32(255, 45, 45)
            elif action == "YIELD_DECELERATE":
                fwd_d = self.safety_engine.obstacle_ahead_distance
                self.forward_corridor_text.text = f"Action: SLOWING FOR PEDESTRIAN ({fwd_d:.1f}m)"
                self.forward_corridor_text.color = rgb32(255, 205, 30)
            else:
                self.forward_corridor_text.text = "Action: PATH CLEAR (Cruising safe)"
                self.forward_corridor_text.color = rgb32(80, 255, 120)

            # Roadway & Zebra Status
            is_crossing_zebra = getattr(self.safety_engine, 'is_crossing_zebra', False)
            roadway_breach = getattr(self.safety_engine, 'roadway_breach_active', False)
            
            if roadway_breach:
                self.emergency_banner_bg.enabled = True
                self.emergency_banner_text.enabled = True
                flash_alpha = 180 + int(70 * math.sin(self.alert_flash_timer * 3.0))
                self.emergency_banner_bg.color = rgba32(220, 25, 25, flash_alpha)
                self.emergency_banner_text.text = "⚠️ CRITICAL SAFETY VIOLATION: ILLEGAL ROAD CROSSING! USE ZEBRA ZONE (z: 32m or 160m) ⚠️"
                self.rule1_text.text = "R1 Sidewalk: [VIOLATION - IN ROAD] | R2 Zebra: [VIOLATION]"
                self.rule1_text.color = rgb32(255, 45, 45)
            elif is_crossing_zebra:
                self.emergency_banner_bg.enabled = True
                self.emergency_banner_text.enabled = True
                self.emergency_banner_bg.color = rgba32(20, 160, 80, 210)
                self.emergency_banner_text.text = "✓ AUTHORIZED ROADWAY CROSSING: SAFELY VIA DESIGNATED ZEBRA CROSSWALK ✓"
                self.rule1_text.text = "R1 Sidewalk: [ZEBRA PASSAGE] | R2 Zebra: [AUTHORIZED]"
                self.rule1_text.color = rgb32(0, 255, 180)
            else:
                self.emergency_banner_bg.enabled = False
                self.emergency_banner_text.enabled = False
                self.rule1_text.text = "R1 Sidewalk: [COMPLIANT] | R2 Zebra: [COMPLIANT]"
                self.rule1_text.color = rgb32(140, 255, 170)

            # Pedestrian Buffer
            if action == "EMERGENCY_STOP":
                self.rule3_text.text = "R3 Ped Buffer: [STOPPING - YIELDING]"
                self.rule3_text.color = rgb32(255, 60, 60)
            elif action == "YIELD_DECELERATE":
                self.rule3_text.text = "R3 Ped Buffer: [CAUTION - SLOWING]"
                self.rule3_text.color = rgb32(255, 200, 40)
            else:
                self.rule3_text.text = "R3 Ped Buffer: [SAFE CLEARANCE (>2.0m)]"
                self.rule3_text.color = rgb32(140, 255, 170)

            # Obstacle Detour
            if action == "DETOUR_AVOIDANCE":
                side = getattr(self.safety_engine, 'chosen_side', 'CLEAR')
                self.rule4_text.text = f"R4 Obstacle Detour    : [BYPASSING VIA {side} SIDE]"
                self.rule4_text.color = rgb32(0, 225, 255)
            elif action == "DETOUR_RETURN":
                self.rule4_text.text = "R4 Obstacle Detour    : [RETURNING TO CENTERLINE]"
                self.rule4_text.color = rgb32(100, 255, 180)
            else:
                self.rule4_text.text = "R4 Obstacle Detour    : [PATH CLEAR - CENTERLINE]"
                self.rule4_text.color = rgb32(180, 220, 240)

        # 6. Destination Celebration Banner
        if self.navigator and self.navigator.is_finished:
            self.celebration_timer += dt
            self.celebration_banner_bg.enabled = True
            self.celebration_banner_title.enabled = True
            self.celebration_banner_sub.enabled = True
            pulse = 1.15 + 0.06 * math.sin(self.celebration_timer * 6.0)
            self.celebration_banner_title.scale = pulse
        else:
            self.celebration_timer = 0.0
            self.celebration_banner_bg.enabled = False
            self.celebration_banner_title.enabled = False
            self.celebration_banner_sub.enabled = False
