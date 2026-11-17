"""
Dashboard UI Module: Ultra-clean, uncluttered autonomous driving HUD.
By default presents a minimalist, non-intrusive cinematic HUD (Top status strip + Bottom quick bar).
Provides an interactive [TAB] Options Menu for one-touch switching of all simulation features,
and a toggleable [H] 4-corner detailed telemetry HUD for deep engineering analysis.
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
        
        # State: detailed cards hidden by default for maximum screen cleanliness!
        self.show_detailed_hud = False
        self.is_menu_open = False
        self.alert_flash_timer = 0.0
        self.celebration_timer = 0.0
        
        # ── Modals (Deep Learning Architecture, Neural HUD, Sim Limitations) ─
        self.arch_modal = ArchitectureComparisonModal()
        self.neural_hud = NeuralPerceptionHUD()
        self.sim_limits_modal = SimLimitationsModal()
        
        # Wire modal callbacks to auto-hide all HUD widgets during overlays
        self.arch_modal._on_open_callback = self._hide_all_hud
        self.arch_modal._on_close_callback = self._restore_hud_after_modal
        self.neural_hud._on_open_callback = self._hide_all_hud
        self.neural_hud._on_close_callback = self._restore_hud_after_modal
        self.sim_limits_modal._on_open_callback = self._hide_all_hud
        self.sim_limits_modal._on_close_callback = self._restore_hud_after_modal

        # ══════════════════════════════════════════════════════════════════
        # 1. SLEEK MINIMAL TOP STATUS STRIP (Always visible, very slim)
        # ══════════════════════════════════════════════════════════════════
        self.header_bg = Entity(
            parent=camera.ui,
            model='quad',
            scale=(2.0, 0.048),
            position=(0, 0.476, 0.05),
            color=rgba32(10, 16, 26, 240)
        )
        self.header_bg.set_depth_write(False)
        
        # Left: Robot identity
        chassis_name = "HUMANOID" if "HUMANOID" in getattr(self.robot, 'actor_type', '') else "ROVER"
        self.title_text = Text(
            text=f"AUTONOMOUS ROBOT [{chassis_name}]",
            parent=camera.ui,
            position=(-0.92, 0.485, -0.05),
            scale=0.86,
            color=rgb32(0, 220, 255),
            origin=(-0.5, 0.5)
        )
        self.mode_pill = Text(
            text="[AUTO-NAV]",
            parent=camera.ui,
            position=(-0.52, 0.485, -0.05),
            scale=0.80,
            color=rgb32(100, 255, 150),
            origin=(-0.5, 0.5)
        )
        
        # Center: Kinematics & Live Action
        self.top_center_text = Text(
            text="Speed: 0.0 m/s  |  Status: PATH CLEAR  |  Mission: 0.0%",
            parent=camera.ui,
            position=(-0.24, 0.485, -0.05),
            scale=0.82,
            color=color.white,
            origin=(-0.5, 0.5)
        )
        
        # Right: Weather & Net RL Score
        self.top_right_text = Text(
            text="Weather: CLEAR  |  Reward: +0.0 pts",
            parent=camera.ui,
            position=(0.48, 0.485, -0.05),
            scale=0.80,
            color=rgb32(255, 215, 60),
            origin=(-0.5, 0.5)
        )

        # ══════════════════════════════════════════════════════════════════
        # 2. EMERGENCY BANNER (Pops up only on violations / zebra crossings)
        # ══════════════════════════════════════════════════════════════════
        self.emergency_banner_bg = Entity(
            parent=camera.ui,
            model='quad',
            scale=(1.60, 0.052),
            position=(0, 0.42, 0.05),
            color=rgba32(220, 30, 30, 230),
            enabled=False
        )
        self.emergency_banner_bg.set_depth_write(False)
        self.emergency_banner_text = Text(
            text="ROADWAY INTRUSION ALERT! CROSS ONLY AT ZEBRA CROSSING",
            parent=camera.ui,
            position=(0, 0.42, -0.05),
            scale=0.82,
            color=color.white,
            origin=(0, 0),
            enabled=False
        )

        # ══════════════════════════════════════════════════════════════════
        # 3. SLEEK MINIMAL BOTTOM BAR
        # ══════════════════════════════════════════════════════════════════
        self.quick_bar_bg = Entity(
            parent=camera.ui,
            model='quad',
            scale=(1.45, 0.038),
            position=(0, -0.478, 0.05),
            color=rgba32(10, 16, 26, 230)
        )
        self.quick_bar_bg.set_depth_write(False)
        self.quick_bar_text = Text(
            text="[SPACE] Start/Pause  |  [TAB] Options Menu  |  [H] Toggle Detailed Telemetry Cards",
            parent=camera.ui,
            position=(0, -0.478, -0.05),
            scale=0.74,
            color=rgb32(180, 220, 245),
            origin=(0, 0)
        )

        # ══════════════════════════════════════════════════════════════════
        # 4. OPTIONAL DETAILED 4-CORNER HUD (Toggled with [H] or Menu)
        # ══════════════════════════════════════════════════════════════════
        # Top-Left: AI Perception Card
        self.sensor_bg = Entity(
            parent=camera.ui, model='quad', scale=(0.58, 0.17), position=(-0.60, 0.33, 0.05),
            color=rgba32(12, 18, 28, 225), enabled=False
        )
        self.sensor_bg.set_depth_write(False)
        self.sensor_border = Entity(
            parent=camera.ui, model='quad', scale=(0.58, 0.003), position=(-0.60, 0.415, 0.01),
            color=rgb32(0, 220, 255), enabled=False
        )
        self.sensor_border.set_depth_write(False)
        self.sensor_title = Text(
            text="AI SENSOR PERCEPTION & FUSION", parent=camera.ui,
            position=(-0.87, 0.40, -0.05), scale=0.74, color=rgb32(0, 220, 255), origin=(-0.5, 0.5), enabled=False
        )
        self.target_text = Text(
            text="Closest: NONE | Range: --- m", parent=camera.ui,
            position=(-0.87, 0.37, -0.05), scale=0.70, color=color.white, origin=(-0.5, 0.5), enabled=False
        )
        self.weather_vision_text = Text(
            text="Weather: CLEAR | Vision: 16.0m | Conf: 99%", parent=camera.ui,
            position=(-0.87, 0.34, -0.05), scale=0.66, color=rgb32(255, 220, 60), origin=(-0.5, 0.5), enabled=False
        )
        self.torch_status_text = Text(
            text="Torch: ON | LiDAR: 360 Sweep | Radar: ACTIVE", parent=camera.ui,
            position=(-0.87, 0.312, -0.05), scale=0.64, color=rgb32(180, 225, 245), origin=(-0.5, 0.5), enabled=False
        )
        self.failure_badge_text = Text(
            text="Perception: [NOMINAL]", parent=camera.ui,
            position=(-0.87, 0.285, -0.05), scale=0.66, color=rgb32(80, 255, 120), origin=(-0.5, 0.5), enabled=False
        )

        # Top-Right: Safety Rules Engine Card
        self.safety_card_bg = Entity(
            parent=camera.ui, model='quad', scale=(0.58, 0.17), position=(0.60, 0.33, 0.05),
            color=rgba32(12, 18, 28, 225), enabled=False
        )
        self.safety_card_bg.set_depth_write(False)
        self.safety_card_border = Entity(
            parent=camera.ui, model='quad', scale=(0.58, 0.003), position=(0.60, 0.415, 0.01),
            color=rgb32(60, 225, 100), enabled=False
        )
        self.safety_card_border.set_depth_write(False)
        self.safety_card_title = Text(
            text="SAFETY RULES ENGINE (LIVE COMPLIANCE)", parent=camera.ui,
            position=(0.33, 0.40, -0.05), scale=0.74, color=rgb32(60, 225, 100), origin=(-0.5, 0.5), enabled=False
        )
        self.rule1_text = Text(
            text="R1 Sidewalk: [COMPLIANT] | R2 Zebra: [COMPLIANT]", parent=camera.ui,
            position=(0.33, 0.37, -0.05), scale=0.66, color=rgb32(140, 255, 170), origin=(-0.5, 0.5), enabled=False
        )
        self.rule3_text = Text(
            text="R3 Pedestrian Buffer  : [SAFE CLEARANCE (>2.0m)]", parent=camera.ui,
            position=(0.33, 0.34, -0.05), scale=0.66, color=rgb32(140, 255, 170), origin=(-0.5, 0.5), enabled=False
        )
        self.rule4_text = Text(
            text="R4 Obstacle Detour    : [PATH CLEAR - CENTERLINE]", parent=camera.ui,
            position=(0.33, 0.312, -0.05), scale=0.66, color=rgb32(180, 220, 240), origin=(-0.5, 0.5), enabled=False
        )
        self.forward_corridor_text = Text(
            text="Action: PATH CLEAR (Cruising safe)", parent=camera.ui,
            position=(0.33, 0.285, -0.05), scale=0.66, color=rgb32(80, 255, 120), origin=(-0.5, 0.5), enabled=False
        )

        # Bottom-Left: Kinematics & Navigation Card
        self.telemetry_bg = Entity(
            parent=camera.ui, model='quad', scale=(0.58, 0.13), position=(-0.60, -0.405, 0.05),
            color=rgba32(12, 18, 28, 225), enabled=False
        )
        self.telemetry_bg.set_depth_write(False)
        self.telemetry_border = Entity(
            parent=camera.ui, model='quad', scale=(0.58, 0.003), position=(-0.60, -0.34, 0.01),
            color=rgb32(0, 215, 255), enabled=False
        )
        self.telemetry_border.set_depth_write(False)
        self.telemetry_title = Text(
            text="ROBOT KINEMATICS & MISSION", parent=camera.ui,
            position=(-0.87, -0.355, -0.05), scale=0.72, color=rgb32(180, 215, 240), origin=(-0.5, 0.5), enabled=False
        )
        self.speed_text = Text(
            text="Speed: 0.0 m/s (0.0 km/h) | Heading: 0.0°", parent=camera.ui,
            position=(-0.87, -0.385, -0.05), scale=0.74, color=color.white, origin=(-0.5, 0.5), enabled=False
        )
        self.pos_text = Text(
            text="Position: (8.75, 0.28, -6.00)", parent=camera.ui,
            position=(-0.87, -0.415, -0.05), scale=0.66, color=rgb32(190, 205, 220), origin=(-0.5, 0.5), enabled=False
        )
        self.progress_text = Text(
            text="Mission: GRAND ZEBRA CROSSWALK [0.0%]", parent=camera.ui,
            position=(-0.87, -0.445, -0.05), scale=0.70, color=rgb32(0, 220, 255), origin=(-0.5, 0.5), enabled=False
        )

        # Bottom-Right: RL Rewards & Penalties Card
        self.rl_bg = Entity(
            parent=camera.ui, model='quad', scale=(0.58, 0.13), position=(0.60, -0.405, 0.05),
            color=rgba32(12, 18, 28, 225), enabled=False
        )
        self.rl_bg.set_depth_write(False)
        self.rl_border = Entity(
            parent=camera.ui, model='quad', scale=(0.58, 0.003), position=(0.60, -0.34, 0.01),
            color=rgb32(255, 215, 20), enabled=False
        )
        self.rl_border.set_depth_write(False)
        self.rl_title = Text(
            text="REINFORCEMENT LEARNING REWARD (MDP)", parent=camera.ui,
            position=(0.33, -0.355, -0.05), scale=0.72, color=rgb32(255, 215, 20), origin=(-0.5, 0.5), enabled=False
        )
        self.rl_score_text = Text(
            text="Net Reward: +0.0 pts | Step: +0.00", parent=camera.ui,
            position=(0.33, -0.385, -0.05), scale=0.76, color=rgb32(100, 255, 180), origin=(-0.5, 0.5), enabled=False
        )
        self.rl_breakdown_text = Text(
            text="Rewards: +0.0 | Penalties: -0.0", parent=camera.ui,
            position=(0.33, -0.415, -0.05), scale=0.66, color=rgb32(180, 220, 240), origin=(-0.5, 0.5), enabled=False
        )
        self.rl_penalty_text = Text(
            text="Live Event: EPISODE READY", parent=camera.ui,
            position=(0.33, -0.445, -0.05), scale=0.66, color=rgb32(255, 220, 60), origin=(-0.5, 0.5), enabled=False
        )

        # Grouping for detailed HUD toggling
        self.detailed_hud_widgets = [
            self.sensor_bg, self.sensor_border, self.sensor_title,
            self.target_text, self.weather_vision_text, self.torch_status_text, self.failure_badge_text,
            self.safety_card_bg, self.safety_card_border, self.safety_card_title,
            self.rule1_text, self.rule3_text, self.rule4_text, self.forward_corridor_text,
            self.telemetry_bg, self.telemetry_border, self.telemetry_title,
            self.speed_text, self.pos_text, self.progress_text,
            self.rl_bg, self.rl_border, self.rl_title,
            self.rl_score_text, self.rl_breakdown_text, self.rl_penalty_text,
        ]

        # ══════════════════════════════════════════════════════════════════
        # 5. SIMPLE UNIFIED [TAB] OPTIONS MENU / CONTROL CENTER
        # ══════════════════════════════════════════════════════════════════
        self.menu_widgets = []
        
        self.menu_backdrop = Entity(
            parent=camera.ui,
            model='quad',
            scale=(2.1, 1.3),
            position=(0, 0, 0.10),
            color=rgba32(6, 10, 16, 245),
            enabled=False
        )
        self.menu_backdrop.set_depth_write(False)
        self.menu_widgets.append(self.menu_backdrop)

        self.menu_card = Entity(
            parent=camera.ui,
            model='quad',
            scale=(1.30, 0.72),
            position=(0, 0, 0.05),
            color=rgba32(16, 22, 34, 255),
            enabled=False
        )
        self.menu_card.set_depth_write(False)
        self.menu_widgets.append(self.menu_card)

        self.menu_card_top = Entity(
            parent=camera.ui,
            model='quad',
            scale=(1.30, 0.005),
            position=(0, 0.36, 0.01),
            color=rgb32(0, 220, 255),
            enabled=False
        )
        self.menu_card_top.set_depth_write(False)
        self.menu_widgets.append(self.menu_card_top)

        self.menu_title = Text(
            text="SIMULATOR OPTIONS & EVALUATION CENTER",
            parent=camera.ui,
            position=(0, 0.31, -0.05),
            scale=0.96,
            color=rgb32(0, 220, 255),
            origin=(0, 0),
            enabled=False
        )
        self.menu_widgets.append(self.menu_title)

        self.menu_subtitle = Text(
            text="Press a number [1 - 8] on your keyboard to instantly select an option:",
            parent=camera.ui,
            position=(0, 0.27, -0.05),
            scale=0.72,
            color=rgb32(180, 210, 230),
            origin=(0, 0),
            enabled=False
        )
        self.menu_widgets.append(self.menu_subtitle)

        # 8 Options Rows
        self.menu_opt_texts = []
        opt_templates = [
            ("[1] Weather Preset       : CLEAR (Rain, Snow, Fog, Night)", rgb32(255, 220, 60)),
            ("[2] Evaluation Scenario  : SCN-1 (Clear Sidewalk Cruise)", rgb32(100, 255, 160)),
            ("[3] Perception Failure   : NOMINAL (Inject False Neg/Ghost/Lag)", rgb32(255, 140, 60)),
            ("[4] Neural Perception HUD: [Open YOLO Detection & Seg View]", rgb32(0, 220, 255)),
            ("[5] Deep Learning Arch   : [Open Modular vs End-to-End View]", rgb32(140, 210, 255)),
            ("[6] Sim Limitations      : [Open Sim-to-Real Analysis]", rgb32(255, 120, 180)),
            ("[7] Camera View Angle    : BACK_OF_BOT (Cycle Views)", rgb32(255, 215, 0)),
            ("[8] Detailed 4-Card HUD  : OFF (Press 8 to Show/Hide)", rgb32(180, 230, 255)),
        ]
        
        y_pos = 0.20
        for text_str, text_col in opt_templates:
            t = Text(
                text=text_str,
                parent=camera.ui,
                position=(-0.56, y_pos, -0.05),
                scale=0.76,
                color=text_col,
                origin=(-0.5, 0.5),
                enabled=False
            )
            self.menu_opt_texts.append(t)
            self.menu_widgets.append(t)
            y_pos -= 0.052

        # Menu Footer
        self.menu_footer = Text(
            text="[SPACE] Start/Pause Drive  |  [M] Manual Mode  |  [R] Reset  |  Press [TAB] or [ESC] to Close",
            parent=camera.ui,
            position=(0, -0.30, -0.05),
            scale=0.72,
            color=rgb32(140, 180, 210),
            origin=(0, 0),
            enabled=False
        )
        self.menu_widgets.append(self.menu_footer)

        # ══════════════════════════════════════════════════════════════════
        # 6. DESTINATION TARGET CELEBRATION BANNER
        # ══════════════════════════════════════════════════════════════════
        self.celebration_banner_bg = Entity(
            parent=camera.ui,
            model='quad',
            scale=(1.60, 0.16),
            position=(0, 0.04, 0.05),
            color=rgba32(10, 16, 26, 245),
            enabled=False
        )
        self.celebration_banner_bg.set_depth_write(False)
        self.celebration_banner_title = Text(
            text="MISSION ACCOMPLISHED! TARGET REACHED!",
            parent=camera.ui,
            position=(0, 0.08, -0.05),
            scale=1.20,
            color=rgb32(255, 215, 20),
            origin=(0, 0),
            enabled=False
        )
        self.celebration_banner_sub = Text(
            text="★ Delivery Completed at Central Terminal! +150.0 RL Terminal Reward Awarded! ★",
            parent=camera.ui,
            position=(0, 0.01, -0.05),
            scale=0.88,
            color=rgb32(100, 255, 180),
            origin=(0, 0),
            enabled=False
        )

    # ══════════════════════════════════════════════════════════════════════
    # VISIBILITY & TOGGLE HANDLERS
    # ══════════════════════════════════════════════════════════════════
    def toggle_detailed_hud(self):
        """Toggles the 4 corner detailed telemetry cards (Key [H] or Menu Option 8)."""
        self.show_detailed_hud = not self.show_detailed_hud
        for w in self.detailed_hud_widgets:
            w.enabled = self.show_detailed_hud
        self.quick_bar_text.text = (
            "[SPACE] Start/Pause  |  [TAB] Options Menu  |  [H] Detailed HUD: " + 
            ("ON" if self.show_detailed_hud else "OFF")
        )
        return self.show_detailed_hud

    def toggle_options_menu(self):
        """Toggles the simple unified options menu (Key [TAB])."""
        if hasattr(self, 'arch_modal') and getattr(self.arch_modal, 'is_open', False):
            self.arch_modal.close()
        if hasattr(self, 'neural_hud') and getattr(self.neural_hud, 'is_open', False):
            self.neural_hud.close()
        if hasattr(self, 'sim_limits_modal') and getattr(self.sim_limits_modal, 'is_open', False):
            self.sim_limits_modal.close()

        self.is_menu_open = not self.is_menu_open
        if self.is_menu_open:
            self._hide_all_hud()
            self._refresh_menu_display()
            for w in self.menu_widgets:
                w.enabled = True
        else:
            for w in self.menu_widgets:
                w.enabled = False
            self._restore_hud_after_modal()
        return self.is_menu_open

    def close_options_menu(self):
        if self.is_menu_open:
            self.is_menu_open = False
            for w in self.menu_widgets:
                w.enabled = False
            self._restore_hud_after_modal()

    def _refresh_menu_display(self):
        """Updates live status values inside the Options Menu."""
        w_cond = getattr(self.sensor_mgr, 'weather_condition', 'CLEAR') if self.sensor_mgr else 'CLEAR'
        self.menu_opt_texts[0].text = f"[1] Weather Preset       : {w_cond.upper()} (Press 1 to Cycle)"
        
        fi = getattr(self.sensor_mgr, 'failure_injector', None) if self.sensor_mgr else None
        f_mode = fi.active_mode if fi else 'NORMAL'
        self.menu_opt_texts[2].text = f"[3] Perception Failure   : {f_mode} (Press 3 to Inject)"
        
        cam_mode = getattr(self.camera_ctrl, 'mode', 'BACK_OF_BOT')
        self.menu_opt_texts[6].text = f"[7] Camera View Angle    : {cam_mode} (Press 7 to Cycle)"
        
        hud_state = "ON" if self.show_detailed_hud else "OFF"
        self.menu_opt_texts[7].text = f"[8] Detailed 4-Card HUD  : {hud_state} (Press 8 to Toggle)"

    def update_scenario_menu_text(self, scenario_name):
        if len(self.menu_opt_texts) > 1:
            self.menu_opt_texts[1].text = f"[2] Evaluation Scenario  : {scenario_name} (Press 2 to Cycle)"

    def _hide_all_hud(self):
        self.header_bg.enabled = False
        self.title_text.enabled = False
        self.mode_pill.enabled = False
        self.top_center_text.enabled = False
        self.top_right_text.enabled = False
        self.quick_bar_bg.enabled = False
        self.quick_bar_text.enabled = False
        for w in self.detailed_hud_widgets:
            w.enabled = False

    def _restore_hud_after_modal(self):
        self.header_bg.enabled = True
        self.title_text.enabled = True
        self.mode_pill.enabled = True
        self.top_center_text.enabled = True
        self.top_right_text.enabled = True
        self.quick_bar_bg.enabled = True
        self.quick_bar_text.enabled = True
        for w in self.detailed_hud_widgets:
            w.enabled = self.show_detailed_hud

    def toggle_arch_modal(self):
        self.close_options_menu()
        if hasattr(self, 'neural_hud') and getattr(self.neural_hud, 'is_open', False):
            self.neural_hud.close()
        if hasattr(self, 'sim_limits_modal') and getattr(self.sim_limits_modal, 'is_open', False):
            self.sim_limits_modal.close()
        return self.arch_modal.toggle()

    def toggle_neural_hud(self):
        self.close_options_menu()
        if hasattr(self, 'arch_modal') and getattr(self.arch_modal, 'is_open', False):
            self.arch_modal.close()
        if hasattr(self, 'sim_limits_modal') and getattr(self.sim_limits_modal, 'is_open', False):
            self.sim_limits_modal.close()
        return self.neural_hud.toggle()

    def toggle_sim_limits(self):
        self.close_options_menu()
        if hasattr(self, 'arch_modal') and getattr(self.arch_modal, 'is_open', False):
            self.arch_modal.close()
        if hasattr(self, 'neural_hud') and getattr(self.neural_hud, 'is_open', False):
            self.neural_hud.close()
        return self.sim_limits_modal.toggle()

    def set_robot(self, new_robot):
        self.robot = new_robot
        chassis_name = "HUMANOID" if "HUMANOID" in getattr(self.robot, 'actor_type', '') else "ROVER"
        self.title_text.text = f"AUTONOMOUS ROBOT [{chassis_name}]"

    # ══════════════════════════════════════════════════════════════════════
    # LIVE TELEMETRY UPDATE TICK
    # ══════════════════════════════════════════════════════════════════
    def update(self, dt):
        self.alert_flash_timer += dt * 4.0
        
        spd_ms = self.robot.speed
        spd_kmh = spd_ms * 3.6
        heading = (self.robot.rotation_y % 360)
        pos = self.robot.position
        pct = self.navigator.get_progress_percent()
        mission_name = self.navigator.get_mission_name() if hasattr(self.navigator, 'get_mission_name') else "ROUTE"
        status_label = "ARRIVED" if self.navigator.is_finished else f"{pct:4.1f}%"
        
        # 1. Update Minimal Top Status Strip
        action_text = "PATH CLEAR"
        if self.safety_engine:
            action = self.safety_engine.safety_action
            if action == "DETOUR_AVOIDANCE":
                action_text = f"DETOURING ({self.safety_engine.chosen_side})"
            elif action == "DETOUR_RETURN":
                action_text = "RETURNING TO CENTER"
            elif action == "EMERGENCY_STOP":
                action_text = "STOPPING / YIELDING"
            elif action == "YIELD_DECELERATE":
                action_text = "SLOWING FOR PED"
            else:
                action_text = "PATH CLEAR"
                
        self.top_center_text.text = f"Speed: {spd_ms:4.1f} m/s  |  Status: {action_text}  |  Mission: {status_label}"
        
        w_cond = getattr(self.sensor_mgr, 'weather_condition', 'CLEAR') if self.sensor_mgr else 'CLEAR'
        tot_r = self.rl_engine.cumulative_reward if self.rl_engine else 0.0
        self.top_right_text.text = f"Weather: {w_cond}  |  Reward: {tot_r:+5.1f} pts"

        # 2. Roadway Breach & Zebra Crosswalk Banner
        if self.safety_engine:
            is_crossing_zebra = getattr(self.safety_engine, 'is_crossing_zebra', False)
            roadway_breach = getattr(self.safety_engine, 'roadway_breach_active', False)
            
            if roadway_breach:
                self.emergency_banner_bg.enabled = True
                self.emergency_banner_text.enabled = True
                flash_alpha = 180 + int(70 * math.sin(self.alert_flash_timer * 3.0))
                self.emergency_banner_bg.color = rgba32(220, 25, 25, flash_alpha)
                self.emergency_banner_text.text = "⚠️ CRITICAL SAFETY VIOLATION: ILLEGAL ROAD CROSSING! USE ZEBRA ZONE (z: 32m or 160m) ⚠️"
            elif is_crossing_zebra:
                self.emergency_banner_bg.enabled = True
                self.emergency_banner_text.enabled = True
                self.emergency_banner_bg.color = rgba32(20, 160, 80, 210)
                self.emergency_banner_text.text = "✓ AUTHORIZED ROADWAY CROSSING: SAFELY VIA DESIGNATED ZEBRA CROSSWALK ✓"
            else:
                self.emergency_banner_bg.enabled = False
                self.emergency_banner_text.enabled = False

        # 3. If Detailed HUD is Enabled, update the 4 corner cards
        if self.show_detailed_hud:
            self.speed_text.text = f"Speed: {spd_ms:4.1f} m/s ({spd_kmh:4.1f} km/h) | Heading: {heading:5.1f}°"
            self.pos_text.text = f"Position: ({pos.x:.2f}, {pos.y:.2f}, {pos.z:.2f})"
            self.progress_text.text = f"Mission: {mission_name} [{status_label}]"
            
            if self.sensor_mgr:
                d = self.sensor_mgr.closest_object_distance
                d_str = f"{d:.1f} m" if d < 100 else "--- m"
                self.target_text.text = f"Closest: [{self.sensor_mgr.closest_object_type}] at {d_str} | Threat: [{self.sensor_mgr.threat_level}]"
                v_range = getattr(self.sensor_mgr, 'vision_range', 16.0)
                v_conf = getattr(self.sensor_mgr, 'detection_confidence', 99)
                self.weather_vision_text.text = f"Weather: {w_cond} | Vision: {v_range:.1f}m | Conf: {int(v_conf)}%"
                torch_active = getattr(self.robot, 'torch_enabled', True)
                self.torch_status_text.text = f"Torch: {'ON' if torch_active else 'OFF'} | LiDAR: 360° Sweep | Radar: ACTIVE"
                
                fi = getattr(self.sensor_mgr, 'failure_injector', None)
                if fi:
                    self.failure_badge_text.text = f"Perception: {fi.get_details()['badge']}"
                    self.failure_badge_text.color = rgb32(*fi.get_details()['color'])

            if self.safety_engine:
                self.forward_corridor_text.text = f"Action: {action_text}"
                
            if self.rl_engine:
                pos_r = getattr(self.rl_engine, 'total_positive_rewards', 0.0)
                tot_p = getattr(self.rl_engine, 'total_penalties', 0.0)
                step_r = self.rl_engine.last_step_reward
                self.rl_score_text.text = f"Net Reward: {tot_r:+7.1f} pts | Step: {step_r:+5.2f}"
                self.rl_breakdown_text.text = f"Rewards: +{pos_r:.1f} | Penalties: -{tot_p:.1f}"
                if len(self.rl_engine.recent_events) > 0:
                    self.rl_penalty_text.text = f"Event: {self.rl_engine.recent_events[-1]}"

        # 4. Neural Perception HUD tick (if active)
        if hasattr(self, 'neural_hud') and self.neural_hud.is_open:
            fi = getattr(self.sensor_mgr, 'failure_injector', None) if self.sensor_mgr else None
            self.neural_hud.update(dt, self.robot, sensor_mgr=self.sensor_mgr, failure_injector=fi)

        # 5. Destination Celebration Banner
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
