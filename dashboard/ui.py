"""
Dashboard UI Module: High-contrast, clean HUD overlay showing live telemetry,
dedicated safety rule compliance engine, weather vision degradation metrics,
Reinforcement Learning (RL) rewards/penalties, destination target celebration banner,
and interactive control guidance. Optimized for 1080p and 4K displays.
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
        self.show_help = True
        self.alert_flash_timer = 0.0
        self.celebration_timer = 0.0
        self._failure_badge_pulse = 0.0
        
        # Architecture Comparison Screen (Modular vs End-to-End Deep Learning)
        self.arch_modal = ArchitectureComparisonModal()
        
        # Neural Perception HUD (key [N]) — YOLOv8 detections + Segmentation + TSR
        self.neural_hud = NeuralPerceptionHUD()
        
        # Simulation Limitations & Sim-to-Real Gap (key [L]) — Req 8
        self.sim_limits_modal = SimLimitationsModal()
        
        # 1. Top Header Bar
        self.header_bg = Entity(
            parent=camera.ui,
            model='quad',
            scale=(2.0, 0.08),
            position=(0, 0.46),
            color=rgba32(16, 20, 28, 225)
        )
        
        self.title_text = Text(
            text="AUTONOMOUS SIDEWALK DELIVERY ROBOT SIMULATOR",
            parent=camera.ui,
            position=(-0.82, 0.48),
            scale=1.10,
            color=rgb32(0, 215, 255),
            origin=(-0.5, 0.5)
        )
        
        chassis_name = "HUMANOID ANDROID" if "HUMANOID" in getattr(self.robot, 'actor_type', '') else "WHEELED ROVER"
        self.chassis_pill = Text(
            text=f"[{chassis_name}]",
            parent=camera.ui,
            position=(0.14, 0.48),
            scale=0.85,
            color=rgb32(255, 185, 30),
            origin=(-0.5, 0.5)
        )
        
        self.mode_pill = Text(
            text="[MODE: AUTO-NAV]",
            parent=camera.ui,
            position=(0.38, 0.48),
            scale=0.85,
            color=rgb32(100, 255, 150),
            origin=(-0.5, 0.5)
        )
        
        self.cam_pill = Text(
            text=f"[CAM: {self.camera_ctrl.mode}]",
            parent=camera.ui,
            position=(0.58, 0.48),
            scale=0.85,
            color=rgb32(255, 215, 0),
            origin=(-0.5, 0.5)
        )
        
        # 2. EMERGENCY INTRUSION & ZEBRA CROSSING STATUS BANNER
        self.emergency_banner_bg = Entity(
            parent=camera.ui,
            model='quad',
            scale=(1.75, 0.075),
            position=(0, 0.38),
            color=rgba32(220, 30, 30, 230),
            enabled=False
        )
        self.emergency_banner_text = Text(
            text="⚠️ ROADWAY INTRUSION ALERT! CROSSING PERMITTED AT ZEBRA CROSSING ONLY (z: 32m or 160m) ⚠️",
            parent=camera.ui,
            position=(0, 0.38),
            scale=0.95,
            color=color.white,
            origin=(0, 0),
            enabled=False
        )
        
        # 3. Bottom Telemetry Card (Left)
        self.telemetry_bg = Entity(
            parent=camera.ui,
            model='quad',
            scale=(0.70, 0.14),
            position=(-0.52, -0.41),
            color=rgba32(16, 20, 28, 215)
        )
        
        self.telemetry_title = Text(
            text="ROBOT KINEMATICS & DECISION STATUS",
            parent=camera.ui,
            position=(-0.85, -0.35),
            scale=0.82,
            color=rgb32(180, 200, 220),
            origin=(-0.5, 0.5)
        )
        
        self.speed_text = Text(
            text="Speed: 0.0 m/s (0.0 km/h)",
            parent=camera.ui,
            position=(-0.85, -0.39),
            scale=1.02,
            color=color.white,
            origin=(-0.5, 0.5)
        )
        
        self.pos_text = Text(
            text="Position: (8.75, 0.00, -6.00) | Heading: 0.0°",
            parent=camera.ui,
            position=(-0.85, -0.43),
            scale=0.82,
            color=rgb32(200, 210, 220),
            origin=(-0.5, 0.5)
        )
        
        self.progress_text = Text(
            text="Mission: GRAND ZEBRA CROSSWALK MISSION [0.0%]",
            parent=camera.ui,
            position=(-0.85, -0.46),
            scale=0.82,
            color=rgb32(0, 215, 255),
            origin=(-0.5, 0.5)
        )
        
        # 4. REINFORCEMENT LEARNING (RL) REWARDS & PENALTIES CARD (Bottom Middle)
        self.rl_bg = Entity(
            parent=camera.ui,
            model='quad',
            scale=(0.68, 0.165),
            position=(0.14, -0.405),
            color=rgba32(16, 20, 28, 225)
        )
        
        self.rl_title = Text(
            text="REINFORCEMENT LEARNING REWARDS & PENALTIES (MDP)",
            parent=camera.ui,
            position=(-0.18, -0.33),
            scale=0.82,
            color=rgb32(255, 215, 0),
            origin=(-0.5, 0.5)
        )
        
        self.rl_score_text = Text(
            text="Net Reward: +0.0 pts | Step: +0.00",
            parent=camera.ui,
            position=(-0.18, -0.365),
            scale=0.96,
            color=rgb32(100, 255, 180),
            origin=(-0.5, 0.5)
        )
        
        self.rl_breakdown_text = Text(
            text="Rewards: +0.0 pts (Progress: +0.0 | Zebra: +0.0 | Goal: +0.0)",
            parent=camera.ui,
            position=(-0.18, -0.40),
            scale=0.74,
            color=rgb32(110, 230, 255),
            origin=(-0.5, 0.5)
        )
        
        self.rl_penalties_breakdown_text = Text(
            text="Penalties: -0.0 pts (Road: -0.0 | Vehicle: -0.0 | Obs: -0.0 | Ped: -0.0)",
            parent=camera.ui,
            position=(-0.18, -0.43),
            scale=0.74,
            color=rgb32(255, 120, 120),
            origin=(-0.5, 0.5)
        )
        
        self.rl_penalty_text = Text(
            text="Live Event: EPISODE READY",
            parent=camera.ui,
            position=(-0.18, -0.46),
            scale=0.74,
            color=rgb32(255, 220, 60),
            origin=(-0.5, 0.5)
        )
        
        # 5. Perception & Weather Vision Card (Top Left)
        self.sensor_bg = Entity(
            parent=camera.ui,
            model='quad',
            scale=(0.68, 0.27),
            position=(-0.54, 0.265),
            color=rgba32(16, 20, 28, 210)
        )
        
        self.sensor_title = Text(
            text="ADAS PERCEPTION & WEATHER ADAPTATION",
            parent=camera.ui,
            position=(-0.86, 0.38),
            scale=0.80,
            color=rgb32(0, 235, 255),
            origin=(-0.5, 0.5)
        )
        
        self.target_text = Text(
            text="Closest Object: NONE | Range: --- m",
            parent=camera.ui,
            position=(-0.86, 0.34),
            scale=0.80,
            color=color.white,
            origin=(-0.5, 0.5)
        )
        
        self.forward_corridor_text = Text(
            text="Decision: PATH CLEAR (Cruising safe)",
            parent=camera.ui,
            position=(-0.86, 0.30),
            scale=0.80,
            color=rgb32(80, 255, 120),
            origin=(-0.5, 0.5)
        )
        
        self.weather_vision_text = Text(
            text="Weather: CLEAR | Vision Range: 16.0m | Confidence: 99%",
            parent=camera.ui,
            position=(-0.86, 0.26),
            scale=0.74,
            color=rgb32(255, 220, 60),
            origin=(-0.5, 0.5)
        )
        
        self.torch_status_text = Text(
            text="Robot Torch: ON (Illuminating Path) | LiDAR: 360° | Radar: ON",
            parent=camera.ui,
            position=(-0.86, 0.22),
            scale=0.72,
            color=rgb32(180, 230, 255),
            origin=(-0.5, 0.5)
        )
        
        # Perception Failure Injection badge (Step 2 – key [U])
        self.failure_badge_bg = Entity(
            parent=camera.ui,
            model='quad',
            scale=(0.68, 0.045),
            position=(-0.54, 0.165),
            color=rgba32(16, 20, 28, 220),
            enabled=True
        )
        self.failure_badge_text = Text(
            text="[PERCEPTION: NOMINAL] [U]: Cycle Failure Injection Mode",
            parent=camera.ui,
            position=(-0.86, 0.17),
            scale=0.72,
            color=rgb32(80, 255, 120),
            origin=(-0.5, 0.5)
        )
        
        # 6. Dedicated Safety Rules Compliance Engine Card (Top Right)
        self.safety_card_bg = Entity(
            parent=camera.ui,
            model='quad',
            scale=(0.68, 0.23),
            position=(0.54, 0.28),
            color=rgba32(16, 20, 28, 210)
        )
        
        self.safety_card_title = Text(
            text="SAFETY RULES ENGINE (LIVE COMPLIANCE)",
            parent=camera.ui,
            position=(0.22, 0.38),
            scale=0.80,
            color=rgb32(0, 255, 175),
            origin=(-0.5, 0.5)
        )
        
        self.rule1_text = Text(
            text="R1 Sidewalk Boundary  : [COMPLIANT - ON SIDEWALK]",
            parent=camera.ui,
            position=(0.22, 0.34),
            scale=0.72,
            color=rgb32(140, 255, 170),
            origin=(-0.5, 0.5)
        )
        
        self.rule2_text = Text(
            text="R2 Zebra Crossing Only: [STRICT: CROSS ONLY AT ZEBRA]",
            parent=camera.ui,
            position=(0.22, 0.30),
            scale=0.72,
            color=rgb32(100, 230, 255),
            origin=(-0.5, 0.5)
        )
        
        self.rule3_text = Text(
            text="R3 Pedestrian Buffer  : [SAFE CLEARANCE (>2.0m)]",
            parent=camera.ui,
            position=(0.22, 0.26),
            scale=0.72,
            color=rgb32(140, 255, 170),
            origin=(-0.5, 0.5)
        )
        
        self.rule4_text = Text(
            text="R4 Obstacle Detour    : [PATH CLEAR - CENTERLINE]",
            parent=camera.ui,
            position=(0.22, 0.22),
            scale=0.72,
            color=rgb32(180, 220, 240),
            origin=(-0.5, 0.5)
        )
        
        self.rule5_text = Text(
            text="R5 Weather Speed Cap  : [COMPLIANT (1.6 m/s)]",
            parent=camera.ui,
            position=(0.22, 0.18),
            scale=0.72,
            color=rgb32(255, 215, 60),
            origin=(-0.5, 0.5)
        )
        
        # 7. Interactive Controls Helper Box (Right Side)
        self.help_bg = Entity(
            parent=camera.ui,
            model='quad',
            scale=(0.46, 0.52),
            position=(0.65, -0.21),
            color=rgba32(16, 20, 28, 205)
        )
        
        help_content = (
            "CAMERA & DRIVING CONTROLS\n"
            "----------------------------\n"
            "[1, 2, 3]  : Back / Eye / 360° Cam\n"
            "[C]        : Cycle Camera Angles\n"
            "Mouse Drag : 360° Free Camera Pan\n"
            "Mouse Wheel: Zoom In / Zoom Out\n"
            "[SPACE]    : Start / Pause Auto-Nav\n"
            "[M]        : Toggle Auto / Manual\n"
            "[W,A,S,D]  : Full 360° Manual Drive\n"
            "[X]        : Toggle Mission Route\n"
            "             (Grand Crosswalk / Express)\n"
            "[V]        : Cycle ELA Scenario\n"
            "             (5 pre-set scenes)\n"
            "[F]        : Cycle Weather Presets\n"
            "             (Rain, Snow, Fog, Night)\n"
            "[T]        : Toggle Torch Spotlight\n"
            "[I] / [TAB]: Compare AI Architectures\n"
            "             (Modular vs End-to-End DL)\n"
            "[N]        : Neural Perception HUD\n"
            "             (YOLO + Seg + TSR Panel)\n"
            "[L]        : Sim Limitations\\n"
            "             (Sim-to-Real / Req 8)\\n"
            "[U]        : Cycle Perception Failures\n"
            "             (False-Neg/Pos/Delay…)\n"
            "[B]        : Toggle 3D Laser Trackers\n"
            "[R]        : Reset Robot to Start\n"
            "[H]        : Toggle Controls Card"
        )
        
        self.help_text = Text(
            text=help_content,
            parent=camera.ui,
            position=(0.44, -0.05),
            scale=0.70,
            color=rgb32(230, 235, 245),
            origin=(-0.5, 0.5)
        )
        
        # 8. DESTINATION TARGET CELEBRATION OVERLAY BANNER
        self.celebration_banner_bg = Entity(
            parent=camera.ui,
            model='quad',
            scale=(1.75, 0.18),
            position=(0, 0.04),
            color=rgba32(12, 18, 28, 240),
            enabled=False
        )
        self.celebration_banner_title = Text(
            text="🎉 DELIVERY TARGET REACHED! MISSION ACCOMPLISHED! 🎉",
            parent=camera.ui,
            position=(0, 0.08),
            scale=1.28,
            color=rgb32(255, 215, 20),
            origin=(0, 0),
            enabled=False
        )
        self.celebration_banner_sub = Text(
            text="★ Delivery Completed at Central Terminal! +150.0 RL Terminal Reward Awarded! ★",
            parent=camera.ui,
            position=(0, 0.01),
            scale=0.92,
            color=rgb32(100, 255, 180),
            origin=(0, 0),
            enabled=False
        )
        
    def set_robot(self, new_robot):
        self.robot = new_robot
        chassis_name = "HUMANOID ANDROID" if "HUMANOID" in getattr(self.robot, 'actor_type', '') else "WHEELED ROVER"
        self.chassis_pill.text = f"[{chassis_name}]"
        
    def toggle_help(self):
        self.show_help = not self.show_help
        self.help_bg.enabled = self.show_help
        self.help_text.enabled = self.show_help
        
    def toggle_arch_modal(self):
        """Toggles the Deep Learning Architecture Comparison Screen (Req 5 & 6)."""
        return self.arch_modal.toggle()
        
    def toggle_neural_hud(self):
        """Toggles the Neural Perception HUD (Req 2 – YOLOv8 detections, Segmentation, TSR)."""
        if hasattr(self, 'neural_hud'):
            if not self.neural_hud.is_open:
                # Hide overlapping HUD cards when opening (non-full-screen, partial hide)
                self.sensor_bg.enabled     = False
                self.sensor_title.enabled  = False
                self.safety_card_bg.enabled = False
                self.help_bg.enabled       = False
                self.help_text.enabled     = False
            else:
                # Restore on close
                self.sensor_bg.enabled     = True
                self.sensor_title.enabled  = True
                self.safety_card_bg.enabled = True
                self.help_bg.enabled       = self.show_help
                self.help_text.enabled     = self.show_help
            return self.neural_hud.toggle()
        return False
        
    def toggle_sim_limits(self):
        """Toggles the Simulation Limitations & Sim-to-Real Gap modal (Req 8)."""
        if hasattr(self, 'sim_limits_modal'):
            # Wire callbacks so modal can hide/restore the main HUD
            self.sim_limits_modal._on_open_callback  = self._hide_main_hud
            self.sim_limits_modal._on_close_callback = self._show_main_hud
            return self.sim_limits_modal.toggle()
        return False
    
    def _get_main_hud_widgets(self):
        """Returns all permanent HUD widgets that should be hidden during full-screen modals."""
        return [
            self.header_bg, self.title_text, self.chassis_pill, self.mode_pill, self.cam_pill,
            self.emergency_banner_bg, self.emergency_banner_text,
            self.telemetry_bg, self.telemetry_title, self.speed_text, self.pos_text, self.progress_text,
            self.rl_bg, self.rl_title, self.rl_score_text, self.rl_breakdown_text,
            self.rl_penalties_breakdown_text, self.rl_penalty_text,
            self.sensor_bg, self.sensor_title, self.target_text, self.forward_corridor_text,
            self.weather_vision_text, self.torch_status_text,
            self.failure_badge_bg, self.failure_badge_text,
            self.safety_card_bg, self.safety_card_title,
            self.rule1_text, self.rule2_text, self.rule3_text, self.rule4_text, self.rule5_text,
            self.help_bg, self.help_text,
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
        # Restore help visibility based on user preference
        self.help_bg.enabled   = self.show_help
        self.help_text.enabled = self.show_help
        
    def update(self, dt):
        self.alert_flash_timer += dt * 4.0
        
        spd_ms = self.robot.speed
        spd_kmh = spd_ms * 3.6
        self.speed_text.text = f"Speed: {spd_ms:4.1f} m/s ({spd_kmh:4.1f} km/h)"
        
        pos = self.robot.position
        heading = (self.robot.rotation_y % 360)
        self.pos_text.text = f"Position: ({pos.x:.2f}, {pos.y:.2f}, {pos.z:.2f}) | Heading: {heading:5.1f}°"
        
        pct = self.navigator.get_progress_percent()
        mission_name = self.navigator.get_mission_name() if hasattr(self.navigator, 'get_mission_name') else "ROUTE"
        status_label = "ARRIVED" if self.navigator.is_finished else f"{pct:4.1f}%"
        self.progress_text.text = f"Mission: {mission_name} [{status_label}]"
        
        self.cam_pill.text = f"[CAM: {self.camera_ctrl.mode}]"
        
        # Sensor & Weather Vision Telemetry + Perception Failure Badge
        if self.sensor_mgr:
            d = self.sensor_mgr.closest_object_distance
            d_str = f"{d:.1f} m" if d < 100 else "--- m"
            self.target_text.text = f"Closest Object: [{self.sensor_mgr.closest_object_type}] at {d_str}"
            
            w_cond = getattr(self.sensor_mgr, 'weather_condition', 'CLEAR')
            v_range = getattr(self.sensor_mgr, 'vision_range', 16.0)
            v_conf = getattr(self.sensor_mgr, 'detection_confidence', 99)
            self.weather_vision_text.text = f"Weather: {w_cond} | Vision: {v_range:.1f}m | Conf: {int(v_conf)}%"
            
            torch_active = getattr(self.robot, 'torch_enabled', True)
            torch_str = "ON (Illuminating Corridor)" if torch_active else "OFF"
            self.torch_status_text.text = f"Robot Torch: {torch_str} | LiDAR: 360° | Radar: ON"
            
            # Update perception failure injection badge
            fi = getattr(self.sensor_mgr, 'failure_injector', None)
            if fi:
                self.alert_flash_timer += 0  # already ticked
                mode = fi.active_mode
                details = fi.get_details()
                badge_text = details["badge"]
                col = details["color"]
                badge_color = rgb32(*col)
                
                if mode == "NORMAL":
                    self.failure_badge_text.text = f"{badge_text} | [U]: Cycle Failure Injection"
                    self.failure_badge_text.color = rgb32(80, 255, 120)
                    self.failure_badge_bg.color = rgba32(16, 20, 28, 220)
                elif mode == "FALSE_NEGATIVE":
                    supervisor = getattr(fi, 'safety_supervisor_tripped', False)
                    sup_tag = " ⚠️ SUPERVISOR OVERRIDE!" if supervisor else ""
                    self.failure_badge_text.text = f"{badge_text}: Obstacle suppressed{sup_tag}"
                    self.failure_badge_text.color = badge_color
                    pulse_a = int(200 + 55 * math.sin(self.alert_flash_timer * 5.0))
                    self.failure_badge_bg.color = rgba32(80, 10, 10, pulse_a)
                elif mode == "FALSE_POSITIVE":
                    self.failure_badge_text.text = f"{badge_text}: Phantom obstacle 2.8m ahead!"
                    self.failure_badge_text.color = badge_color
                    pulse_a = int(200 + 55 * math.sin(self.alert_flash_timer * 4.0))
                    self.failure_badge_bg.color = rgba32(80, 40, 5, pulse_a)
                elif mode == "LATENCY_DELAY":
                    self.failure_badge_text.text = f"{badge_text}: 450ms inference lag active"
                    self.failure_badge_text.color = badge_color
                    self.failure_badge_bg.color = rgba32(60, 50, 10, 220)
                elif mode == "HIGH_UNCERTAINTY":
                    conf_val = int(v_conf) if fi.simulated_conf_override else 99
                    self.failure_badge_text.text = f"{badge_text}: Conf={conf_val}% | Speed capped to 0.5m/s"
                    self.failure_badge_text.color = badge_color
                    pulse_a = int(200 + 55 * math.sin(self.alert_flash_timer * 7.0))
                    self.failure_badge_bg.color = rgba32(55, 15, 70, pulse_a)
                elif mode == "MISCLASSIFICATION":
                    self.failure_badge_text.text = f"{badge_text}: PED label swapped to OBSTACLE"
                    self.failure_badge_text.color = badge_color
                    self.failure_badge_bg.color = rgba32(60, 20, 40, 220)
                    
                self.failure_badge_text.enabled = True
                self.failure_badge_bg.enabled = True
            
        # Neural Perception HUD tick (key [N])
        if hasattr(self, 'neural_hud') and self.neural_hud.is_open:
            fi = getattr(self.sensor_mgr, 'failure_injector', None) if self.sensor_mgr else None
            self.neural_hud.update(dt, self.robot, sensor_mgr=self.sensor_mgr, failure_injector=fi)
            
        # RL Telemetry
        if self.rl_engine:
            tot = self.rl_engine.cumulative_reward
            step_r = self.rl_engine.last_step_reward
            pos_r = getattr(self.rl_engine, 'total_positive_rewards', 0.0)
            tot_p = getattr(self.rl_engine, 'total_penalties', 0.0)
            
            self.rl_score_text.text = f"Net Reward: {tot:+7.1f} pts | Step: {step_r:+5.2f}"
            if tot >= 0:
                self.rl_score_text.color = rgb32(100, 255, 180)
            else:
                self.rl_score_text.color = rgb32(255, 75, 75)
                
            prog_r = self.rl_engine.total_progress_reward
            zeb_r = self.rl_engine.total_zebra_reward
            goal_r = self.rl_engine.total_goal_reward
            self.rl_breakdown_text.text = (
                f"Rewards: +{pos_r:.1f} pts (Progress: +{prog_r:.1f} | Zebra: +{zeb_r:.1f} | Goal: +{goal_r:.0f})"
            )
            
            road_p = self.rl_engine.total_road_penalty
            veh_p = self.rl_engine.total_collision_penalty
            obs_p = getattr(self.rl_engine, 'total_obstacle_penalty', 0.0)
            ped_p = self.rl_engine.total_pedestrian_penalty
            self.rl_penalties_breakdown_text.text = (
                f"Penalties: -{tot_p:.1f} pts (Road: -{road_p:.0f} | Veh: -{veh_p:.0f} | Obs: -{obs_p:.0f} | Ped: -{ped_p:.0f})"
            )
            if tot_p > 0:
                self.rl_penalties_breakdown_text.color = rgb32(255, 80, 80)
            else:
                self.rl_penalties_breakdown_text.color = rgb32(180, 200, 210)
                
            if len(self.rl_engine.recent_events) > 0:
                last_event = self.rl_engine.recent_events[-1]
                if "PENALTY" in last_event:
                    self.rl_penalty_text.text = f"⚠️ {last_event}"
                    self.rl_penalty_text.color = rgb32(255, 60, 60)
                    self.rl_bg.color = rgba32(60, 15, 20, 240) # Flash card deep red on penalty
                else:
                    self.rl_penalty_text.text = f"✓ {last_event}"
                    self.rl_penalty_text.color = rgb32(100, 255, 180)
                    self.rl_bg.color = rgba32(16, 20, 28, 225)
            
        # Safety Rules Engine Telemetry
        if self.safety_engine:
            action = self.safety_engine.safety_action
            if action == "DETOUR_AVOIDANCE":
                self.forward_corridor_text.text = f"Decision: AVOIDANCE DETOUR -> BYPASSING {self.safety_engine.blocking_actor_name}"
                self.forward_corridor_text.color = rgb32(0, 225, 255)
            elif action == "DETOUR_RETURN":
                self.forward_corridor_text.text = "Decision: DETOUR COMPLETE -> RETURNING TO CENTERLINE"
                self.forward_corridor_text.color = rgb32(100, 255, 180)
            elif action == "EMERGENCY_STOP":
                fwd_d = self.safety_engine.obstacle_ahead_distance
                self.forward_corridor_text.text = f"Decision: YIELDING TO {self.safety_engine.blocking_actor_name} ({fwd_d:.1f}m)"
                self.forward_corridor_text.color = rgb32(255, 45, 45)
            elif action == "YIELD_DECELERATE":
                fwd_d = self.safety_engine.obstacle_ahead_distance
                self.forward_corridor_text.text = f"Decision: PEDESTRIAN NEARBY ({fwd_d:.1f}m) -> SLOWING"
                self.forward_corridor_text.color = rgb32(255, 205, 30)
            else:
                self.forward_corridor_text.text = "Decision: PATH CLEAR (Cruising safe)"
                self.forward_corridor_text.color = rgb32(80, 255, 120)
                
            # Rule 1 & Rule 2: Sidewalk Boundaries & Zebra Crossing Status
            is_crossing_zebra = getattr(self.safety_engine, 'is_crossing_zebra', False)
            roadway_breach = getattr(self.safety_engine, 'roadway_breach_active', False)
            
            if roadway_breach:
                self.emergency_banner_bg.enabled = True
                self.emergency_banner_text.enabled = True
                flash_alpha = 180 + int(70 * math.sin(self.alert_flash_timer * 3.0))
                self.emergency_banner_bg.color = rgba32(220, 25, 25, flash_alpha)
                self.emergency_banner_text.text = (
                    "⚠️ CRITICAL SAFETY VIOLATION: ILLEGAL ROAD CROSSING! ROAD CROSSING STRICTLY PERMITTED ONLY AT ZEBRA CROSSINGS (z: 32m or 160m) ⚠️"
                )
                self.rule1_text.text = "R1 Sidewalk Boundary  : [CRITICAL VIOLATION - IN ROAD]"
                self.rule1_text.color = rgb32(255, 45, 45)
                self.rule2_text.text = "R2 Zebra Crossing Only: [VIOLATION: CROSSING OUTSIDE ZEBRA ZONE!]"
                self.rule2_text.color = rgb32(255, 45, 45)
            elif is_crossing_zebra:
                self.emergency_banner_bg.enabled = True
                self.emergency_banner_text.enabled = True
                self.emergency_banner_bg.color = rgba32(20, 160, 80, 210)
                self.emergency_banner_text.text = (
                    "✓ AUTHORIZED ROADWAY CROSSING: CROSSING SAFELY VIA DESIGNATED ZEBRA CROSSWALK ✓"
                )
                self.rule1_text.text = "R1 Sidewalk Boundary  : [COMPLIANT - ZEBRA CROSSING]"
                self.rule1_text.color = rgb32(100, 255, 160)
                self.rule2_text.text = "R2 Zebra Crossing Only: [AUTHORIZED - SAFE CROSSWALK PASSAGE]"
                self.rule2_text.color = rgb32(0, 255, 180)
            else:
                self.emergency_banner_bg.enabled = False
                self.emergency_banner_text.enabled = False
                self.rule1_text.text = "R1 Sidewalk Boundary  : [COMPLIANT - ON SIDEWALK]"
                self.rule1_text.color = rgb32(140, 255, 170)
                self.rule2_text.text = "R2 Zebra Crossing Only: [STRICT: CROSS ONLY AT ZEBRA]"
                self.rule2_text.color = rgb32(100, 230, 255)
                
            # Rule 3: Pedestrian Buffer
            if action == "EMERGENCY_STOP":
                self.rule3_text.text = f"R3 Pedestrian Buffer  : [STOPPING - YIELDING TO PEDESTRIAN]"
                self.rule3_text.color = rgb32(255, 60, 60)
            elif action == "YIELD_DECELERATE":
                self.rule3_text.text = f"R3 Pedestrian Buffer  : [CAUTION - SLOWING DOWN]"
                self.rule3_text.color = rgb32(255, 200, 40)
            else:
                self.rule3_text.text = f"R3 Pedestrian Buffer  : [COMPLIANT - CLEAR (>2.0m)]"
                self.rule3_text.color = rgb32(140, 255, 170)
                
            # Rule 4: Obstacle Detour
            if action == "DETOUR_AVOIDANCE":
                side = getattr(self.safety_engine, 'chosen_side', 'CLEAR')
                self.rule4_text.text = f"R4 Obstacle Detour    : [DETOURING VIA {side} SIDE]"
                self.rule4_text.color = rgb32(0, 225, 255)
            elif action == "DETOUR_RETURN":
                self.rule4_text.text = f"R4 Obstacle Detour    : [RETURNING TO CENTERLINE]"
                self.rule4_text.color = rgb32(100, 255, 180)
            else:
                self.rule4_text.text = f"R4 Obstacle Detour    : [PATH CLEAR - CENTERLINE]"
                self.rule4_text.color = rgb32(180, 220, 240)
                
            # Rule 5: Speed Compliance
            self.rule5_text.text = f"R5 Speed Compliance   : [COMPLIANT ({spd_ms:3.1f} m/s)]"

        # Celebration Banner Handling
        if self.navigator and self.navigator.is_finished:
            self.celebration_timer += dt
            self.celebration_banner_bg.enabled = True
            self.celebration_banner_title.enabled = True
            self.celebration_banner_sub.enabled = True
            pulse = 1.25 + 0.08 * math.sin(self.celebration_timer * 6.0)
            self.celebration_banner_title.scale = pulse
        else:
            self.celebration_timer = 0.0
            self.celebration_banner_bg.enabled = False
            self.celebration_banner_title.enabled = False
            self.celebration_banner_sub.enabled = False
