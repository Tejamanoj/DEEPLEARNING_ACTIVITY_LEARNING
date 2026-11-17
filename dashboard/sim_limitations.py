"""
Simulation Limitations & Sim-to-Real Gap Modal — Key [L]
===========================================================
Implements Student 2 Requirement 8:
  "Discuss safety checks, uncertainty and simulation limitations."

Presents a full-screen panel explaining:
  1. Simulation assumptions and what this sim CANNOT replicate
  2. Sim-to-Real Gap (Domain Randomization, Sensor Noise, Physics fidelity)
  3. Why rule-based supervisors are essential alongside neural inference
  4. Real-world deployment checks required before any real road test
"""
from ursina import Entity, Text, camera, color
from ursina.color import rgb32, rgba32


# ─────────────────────────────────────────────────────────────────────────────
LIMITATION_CONTENT = [
    # (section_title_text, section_title_color, body_lines_list, body_color)
    (
        "① SIM ASSUMPTIONS (WHAT THIS SIMULATOR CANNOT REPLICATE)",
        (255, 215, 0),
        [
            "• Rendering: Synthetic Ursina/Panda3D graphics ≠ Real camera RGB noise, lens flare,",
            "  motion blur, over/under-exposure or chromatic aberration.",
            "• Physics:   Rigid-body collider physics. No deformable surfaces, tire slip,",
            "  mud, gravel, wet pavement adhesion, or wind forces.",
            "• Actors:    Programmatic pedestrians walk in fixed patterns.",
            "  Real humans exhibit unpredictable gait, sudden stops, and crowd dynamics.",
            "• Sensors:   LiDAR, Radar, Camera use geometric ground-truth math.",
            "  Real sensors add Gaussian noise, ray misses, multipath reflections.",
        ],
        (200, 215, 230),
    ),
    (
        "② THE SIM-TO-REAL GAP (DOMAIN RANDOMIZATION NEEDED)",
        (60, 220, 80),
        [
            "• Visual Domain Gap: Neural networks trained on synthetic scenes often fail on",
            "  real images due to texture, shadow, and lighting distribution mismatch.",
            "• Fix: Domain Randomization — randomize textures, weather, lighting during",
            "  training so the network generalises to real visual distributions.",
            "• Sensor Noise Gap: Real LiDAR returns are sparse and noisy (beam divergence,",
            "  rain droplet interference). Sim uses idealized dense point clouds.",
            "• Fix: Add Gaussian noise, random dropouts, and calibration error to sim sensors.",
            "• Latency Gap: Real edge-AI inference has variable compute latency (5–450ms).",
            "  This sim injects latency only as a visual demonstration, not true async.",
        ],
        (180, 230, 200),
    ),
    (
        "③ WHY RULE-BASED SUPERVISORS REMAIN ESSENTIAL",
        (40, 220, 220),
        [
            "• Neural networks can fail silently — no exception, no crash, just wrong output.",
            "• Safety Rule Engine acts as a deterministic failsafe independent of AI.",
            "• This sim's Rule Engine enforces: Sidewalk Bounds, Zebra Crossing Only,",
            "  Pedestrian Buffer (> 2m), Forward Clearance, Weather Speed Caps.",
            "• False-Negative demo: When YOLO misses an obstacle, hardware proximity",
            "  ultrasonic sensor at 1.5m fires the emergency stop regardless.",
            "• Industry standard (ISO 26262 / SOTIF): Autonomous systems must pass",
            "  FMEA analysis and demonstrate safety even under perception failure.",
        ],
        (160, 240, 240),
    ),
    (
        "④ REAL-WORLD DEPLOYMENT CHECKLIST (PRE-FIELD REQUIREMENTS)",
        (255, 100, 180),
        [
            "• HIL Testing: Run full sensor stack on Hardware-in-the-Loop bench first.",
            "• Closed-track testing: Controlled environment with scripted pedestrians.",
            "• Edge-case dataset: Collect 10,000+ failure images for adversarial retraining.",
            "• Formal verification: Prove rule engine is deadlock-free using model checking.",
            "• Regulator approval: UK DfT / US NHTSA autonomous vehicle submission required.",
            "• Insurance & Liability: Real-time event data recorder (black box) mandatory.",
        ],
        (255, 180, 220),
    ),
]


class SimLimitationsModal:
    """Full-screen Simulation Limitations & Sim-to-Real Gap explanation panel."""

    def __init__(self):
        self.is_open = False
        self._all_widgets = []
        self._on_open_callback  = None   # called with True when opening
        self._on_close_callback = None   # called when closing

        # ── Dark backdrop (created LAST so it draws on top via creation order) ─
        # Note: actual occlusion of old HUD is handled via callbacks to DashboardUI

        # ── Top title bar ─────────────────────────────────────────────────
        self.title_bar = Entity(
            parent=camera.ui,
            model='quad',
            scale=(2.1, 0.07),
            position=(0, 0.59),
            color=rgba32(30, 60, 100, 255),
            enabled=False
        )
        self._all_widgets.append(self.title_bar)

        self.title_text = Text(
            text=(
                "SIMULATION LIMITATIONS & SIM-TO-REAL GAP  —  "
                "Student 2 ELA Requirement 8  |  [L] or [ESC] to Close"
            ),
            parent=camera.ui,
            position=(0, 0.595),
            scale=0.82,
            color=rgb32(0, 215, 255),
            origin=(0, 0.5),
            enabled=False
        )
        self._all_widgets.append(self.title_text)

        # ── Build content panels ───────────────────────────────────────────
        y_cursor = 0.52
        for sect_title, sect_col, body_lines, body_col in LIMITATION_CONTENT:
            st = Text(
                text=sect_title,
                parent=camera.ui,
                position=(-0.90, y_cursor),
                scale=0.76,
                color=rgb32(*sect_col),
                origin=(-0.5, 0.5),
                enabled=False
            )
            self._all_widgets.append(st)
            y_cursor -= 0.038

            full_body = "\n".join(body_lines)
            bt = Text(
                text=full_body,
                parent=camera.ui,
                position=(-0.90, y_cursor),
                scale=0.66,
                color=rgb32(*body_col),
                origin=(-0.5, 0.5),
                enabled=False
            )
            self._all_widgets.append(bt)
            y_cursor -= len(body_lines) * 0.028 + 0.025

        # ── Bottom disclaimer bar ─────────────────────────────────────────
        self.disclaimer = Text(
            text=(
                "⚠  CONCEPTUAL DEMONSTRATION — No real AI weights or sensor hardware. "
                "All detections are geometry-driven simulation for educational purposes."
            ),
            parent=camera.ui,
            position=(0, -0.59),
            scale=0.65,
            color=rgb32(180, 130, 60),
            origin=(0, 0.5),
            enabled=False
        )
        self._all_widgets.append(self.disclaimer)

        # ── Dark backdrop created AFTER content so it renders BEHIND modal text
        # but OVER the old HUD. We hide old HUD via callback instead.
        self.backdrop = Entity(
            parent=camera.ui,
            model='quad',
            scale=(2.1, 1.3),
            position=(0, 0),
            color=rgba32(6, 8, 14, 252),
            enabled=False
        )
        # Insert backdrop at front of list so it enables/disables first
        self._all_widgets.insert(0, self.backdrop)

    def _set_all_enabled(self, state):
        for w in self._all_widgets:
            w.enabled = state

    def toggle(self):
        self.is_open = not self.is_open
        if self.is_open:
            # 1. Hide existing HUD first
            if self._on_open_callback:
                self._on_open_callback()
            # 2. Show modal on top
            self._set_all_enabled(True)
        else:
            # 1. Hide modal
            self._set_all_enabled(False)
            # 2. Restore existing HUD
            if self._on_close_callback:
                self._on_close_callback()
        return self.is_open

    def close(self):
        if self.is_open:
            self.is_open = False
            self._set_all_enabled(False)
            if self._on_close_callback:
                self._on_close_callback()


