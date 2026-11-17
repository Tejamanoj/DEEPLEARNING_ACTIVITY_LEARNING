"""
Simulation Limitations & Sim-to-Real Gap Modal — Key [L]
===========================================================
Implements Student 2 Requirement 8:
  "Discuss safety checks, uncertainty and simulation limitations."

Presented as an academic 2x2 grid dashboard with high-contrast cards:
  Card 1 (Top-Left):     Simulation Assumptions (Graphics, Physics, Sensors)
  Card 2 (Top-Right):    Sim-to-Real Gap & Domain Randomization
  Card 3 (Bottom-Left):  Why Rule-Based Supervisors Remain Essential
  Card 4 (Bottom-Right): Real-World Deployment Verification Checklist
"""
from ursina import Entity, Text, camera
from ursina.color import rgb32, rgba32


class SimLimitationsModal:
    """Full-screen Simulation Limitations & Sim-to-Real Gap explanation panel (2x2 Grid)."""

    def __init__(self):
        self.is_open = False
        self._all_widgets = []
        self._on_open_callback  = None
        self._on_close_callback = None

        # ── 1. Full-screen dark opaque backdrop ────────────────────────────
        self.backdrop = Entity(
            parent=camera.ui,
            model='quad',
            scale=(2.1, 1.3),
            position=(0, 0, 0.10),
            color=rgba32(8, 12, 18, 255),
            enabled=False
        )
        self.backdrop.set_depth_write(False)
        self._all_widgets.append(self.backdrop)

        # ── 2. Top Title Bar ───────────────────────────────────────────────
        self.title_bar = Entity(
            parent=camera.ui,
            model='quad',
            scale=(1.82, 0.065),
            position=(0, 0.44, 0.05),
            color=rgba32(18, 30, 48, 255),
            enabled=False
        )
        self.title_bar.set_depth_write(False)
        self._all_widgets.append(self.title_bar)

        self.title_text = Text(
            text="SIMULATION LIMITATIONS & THE SIM-TO-REAL GAP (Student 2 ELA Requirement 8)",
            parent=camera.ui,
            position=(0, 0.445, -0.05),
            scale=0.88,
            color=rgb32(0, 220, 255),
            origin=(0, 0),
            enabled=False
        )
        self._all_widgets.append(self.title_text)

        # ── 3. Four Grid Cards (2x2 Layout) ────────────────────────────────
        # Card 1: Top-Left (-0.46, 0.20)
        c1_bg = Entity(
            parent=camera.ui,
            model='quad',
            scale=(0.88, 0.38),
            position=(-0.46, 0.20, 0.05),
            color=rgba32(16, 24, 36, 250),
            enabled=False
        )
        c1_bg.set_depth_write(False)
        self._all_widgets.append(c1_bg)
        c1_top = Entity(parent=camera.ui, model='quad', scale=(0.88, 0.005), position=(-0.46, 0.39, 0.01), color=rgb32(255, 215, 0), enabled=False)
        c1_top.set_depth_write(False)
        self._all_widgets.append(c1_top)
        
        c1_title = Text(
            text="1. SIMULATION ASSUMPTIONS (WHAT SIM CANNOT REPLICATE)",
            parent=camera.ui,
            position=(-0.88, 0.365, -0.05),
            scale=0.74,
            color=rgb32(255, 215, 0),
            origin=(-0.5, 0.5),
            enabled=False
        )
        self._all_widgets.append(c1_title)
        
        c1_body = (
            "- Rendering Gap: Synthetic graphics lack real camera noise, lens glare,\n"
            "  chromatic aberration, sensor exposure lag, and motion blur.\n"
            "- Physics Gap: Idealized kinematic movement with zero wheel slip, pavement\n"
            "  micro-texture friction, water puddles, mud, or cross-wind perturbations.\n"
            "- Agent Dynamics: Programmatic pedestrians follow scripted routes. Real humans\n"
            "  demonstrate unpredictable trajectories, sudden stops, and erratic gestures.\n"
            "- Idealized Sensors: LiDAR & Radar use mathematical ray-casting. Real sensors\n"
            "  suffer from multipath reflections, beam divergence, and weather backscatter."
        )
        c1_text = Text(
            text=c1_body,
            parent=camera.ui,
            position=(-0.88, 0.33, -0.05),
            scale=0.62,
            color=rgb32(210, 225, 240),
            origin=(-0.5, 0.5),
            enabled=False
        )
        self._all_widgets.append(c1_text)

        # Card 2: Top-Right (0.46, 0.20)
        c2_bg = Entity(
            parent=camera.ui,
            model='quad',
            scale=(0.88, 0.38),
            position=(0.46, 0.20, 0.05),
            color=rgba32(16, 24, 36, 250),
            enabled=False
        )
        c2_bg.set_depth_write(False)
        self._all_widgets.append(c2_bg)
        c2_top = Entity(parent=camera.ui, model='quad', scale=(0.88, 0.005), position=(0.46, 0.39, 0.01), color=rgb32(60, 225, 100), enabled=False)
        c2_top.set_depth_write(False)
        self._all_widgets.append(c2_top)
        
        c2_title = Text(
            text="2. THE SIM-TO-REAL GAP (DOMAIN RANDOMIZATION)",
            parent=camera.ui,
            position=(0.04, 0.365, -0.05),
            scale=0.74,
            color=rgb32(60, 225, 100),
            origin=(-0.5, 0.5),
            enabled=False
        )
        self._all_widgets.append(c2_title)
        
        c2_body = (
            "- Visual Domain Shift: Models trained purely on simulated imagery experience\n"
            "  severe distribution shift and drop accuracy drastically in real deployment.\n"
            "- Solution: Domain Randomization (DR) - aggressively perturb lighting,\n"
            "  sun angles, road textures, precipitation, and colors during model training.\n"
            "- Sensor Noise Emulation: Real LiDAR point clouds have dropouts and beam scatter.\n"
            "  Training pipelines must inject Gaussian noise and ray-dropout models.\n"
            "- Inference Latency Gap: Real edge chips (Jetson Orin) introduce 15-400ms lag.\n"
            "  This simulator models latency queues (Key [U]) to test delayed response."
        )
        c2_text = Text(
            text=c2_body,
            parent=camera.ui,
            position=(0.04, 0.33, -0.05),
            scale=0.62,
            color=rgb32(200, 235, 210),
            origin=(-0.5, 0.5),
            enabled=False
        )
        self._all_widgets.append(c2_text)

        # Card 3: Bottom-Left (-0.46, -0.21)
        c3_bg = Entity(
            parent=camera.ui,
            model='quad',
            scale=(0.88, 0.38),
            position=(-0.46, -0.21, 0.05),
            color=rgba32(16, 24, 36, 250),
            enabled=False
        )
        c3_bg.set_depth_write(False)
        self._all_widgets.append(c3_bg)
        c3_top = Entity(parent=camera.ui, model='quad', scale=(0.88, 0.005), position=(-0.46, -0.02, 0.01), color=rgb32(0, 215, 255), enabled=False)
        c3_top.set_depth_write(False)
        self._all_widgets.append(c3_top)
        
        c3_title = Text(
            text="3. WHY RULE-BASED SUPERVISORS REMAIN MANDATORY",
            parent=camera.ui,
            position=(-0.88, -0.045, -0.05),
            scale=0.74,
            color=rgb32(0, 215, 255),
            origin=(-0.5, 0.5),
            enabled=False
        )
        self._all_widgets.append(c3_title)
        
        c3_body = (
            "- Uncertified Nature of Deep Learning: Neural networks can fail silently\n"
            "  without raising exceptions - misclassifying or completely missing actors.\n"
            "- Deterministic Safety Envelope: Rule engines enforce provable bounds:\n"
            "  Sidewalk boundaries, strict zebra-crossing only, and minimum safety buffers.\n"
            "- Fail-Safe Proximity Supervisor: When YOLO drops a forward target (Key [U]),\n"
            "  the hardware tactile/ultrasonic barrier at 1.5m triggers emergency braking.\n"
            "- Regulatory Compliance: ISO 26262 & SOTIF standards require fail-operational\n"
            "  supervisors that can safely halt the robot under complete AI perception failure."
        )
        c3_text = Text(
            text=c3_body,
            parent=camera.ui,
            position=(-0.88, -0.08, -0.05),
            scale=0.62,
            color=rgb32(190, 235, 245),
            origin=(-0.5, 0.5),
            enabled=False
        )
        self._all_widgets.append(c3_text)

        # Card 4: Bottom-Right (0.46, -0.21)
        c4_bg = Entity(
            parent=camera.ui,
            model='quad',
            scale=(0.88, 0.38),
            position=(0.46, -0.21, 0.05),
            color=rgba32(16, 24, 36, 250),
            enabled=False
        )
        c4_bg.set_depth_write(False)
        self._all_widgets.append(c4_bg)
        c4_top = Entity(parent=camera.ui, model='quad', scale=(0.88, 0.005), position=(0.46, -0.02, 0.01), color=rgb32(255, 120, 180), enabled=False)
        c4_top.set_depth_write(False)
        self._all_widgets.append(c4_top)
        
        c4_title = Text(
            text="4. REAL-WORLD DEPLOYMENT VERIFICATION CHECKLIST",
            parent=camera.ui,
            position=(0.04, -0.045, -0.05),
            scale=0.74,
            color=rgb32(255, 120, 180),
            origin=(-0.5, 0.5),
            enabled=False
        )
        self._all_widgets.append(c4_title)
        
        c4_body = (
            "- Hardware-in-the-Loop (HIL) Testing: Execute camera & LiDAR pipelines on\n"
            "  target embedded hardware (NVIDIA Jetson) before mounting on physical chassis.\n"
            "- Closed-Course Track Trials: Validate emergency stop distance across wet,\n"
            "  dry, and snowy surfaces using soft foam dummy obstacles and pedestrian targets.\n"
            "- Adversarial Edge-Case Retraining: Collect 10k+ real-world failure frames\n"
            "  (glare, dirty lenses, shadows) and perform continuous active learning.\n"
            "- Black-Box Telemetry Logging: Tamper-proof crash recorder logs sensor frames,\n"
            "  AI bounding boxes, and rule engine decisions at 50 Hz for regulatory audit."
        )
        c4_text = Text(
            text=c4_body,
            parent=camera.ui,
            position=(0.04, -0.08, -0.05),
            scale=0.62,
            color=rgb32(245, 205, 225),
            origin=(-0.5, 0.5),
            enabled=False
        )
        self._all_widgets.append(c4_text)

        # ── 4. Bottom Footer Bar ───────────────────────────────────────────
        self.footer_bar = Entity(
            parent=camera.ui,
            model='quad',
            scale=(1.82, 0.05),
            position=(0, -0.45, 0.05),
            color=rgba32(18, 30, 48, 255),
            enabled=False
        )
        self.footer_bar.set_depth_write(False)
        self._all_widgets.append(self.footer_bar)

        self.footer_text = Text(
            text="[L] or [ESC] : Return to 3D Simulation  |  Notice: Conceptual Educational Demonstration (No Real Hardware)",
            parent=camera.ui,
            position=(0, -0.45, -0.05),
            scale=0.72,
            color=rgb32(160, 200, 230),
            origin=(0, 0),
            enabled=False
        )
        self._all_widgets.append(self.footer_text)

    def _set_all_enabled(self, state):
        for w in self._all_widgets:
            w.enabled = state

    def toggle(self):
        self.is_open = not self.is_open
        if self.is_open:
            if self._on_open_callback:
                self._on_open_callback()
            self._set_all_enabled(True)
        else:
            self._set_all_enabled(False)
            if self._on_close_callback:
                self._on_close_callback()
        return self.is_open

    def close(self):
        if self.is_open:
            self.is_open = False
            self._set_all_enabled(False)
            if self._on_close_callback:
                self._on_close_callback()
