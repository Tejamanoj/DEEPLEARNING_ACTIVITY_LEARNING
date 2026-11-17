"""
Neural Perception HUD Module — Key [N]
=======================================
Implements Student 2 Requirement 2:
  "Show object detection, lane/road segmentation and traffic sign recognition."

Displays a toggleable 2D Neural Perception HUD panel showing:
  1. YOLOv8n-ADAS Object Detection feed with class labels + confidence badges
  2. Semantic Segmentation color overlay legend (Sidewalk / Road / Crosswalk / Building)
  3. Traffic Sign Recognition boxes (CROSSWALK / STOP / SPEED 15)
  4. Edge-AI inference telemetry ticker (Model, Latency, Resolution, FPS)

All detection data is geometry-driven simulation (no live GPU inference) but visually
demonstrates exactly what a real YOLOv8 + DeepLab segmentation pipeline would show.
"""
import math
import random
from ursina import Entity, Text, camera, color, Vec3
from ursina.color import rgb32, rgba32


class NeuralPerceptionHUD:
    """
    2D Neural Perception HUD overlaid on the camera viewport.
    Shows simulated YOLOv8 detections, semantic segmentation, and traffic sign recognition.
    """

    # Semantic class → (display name, color RGB)
    SEG_CLASSES = [
        ("SIDEWALK",   (60, 220, 80)),
        ("ROAD",       (170, 70, 200)),
        ("CROSSWALK",  (40, 220, 220)),
        ("BUILDING",   (200, 130, 50)),
        ("VEGETATION", (30, 160, 50)),
        ("SKY",        (100, 160, 230)),
    ]

    SIGN_LABELS = {
        "crosswalk": ("SIGN: PEDESTRIAN XWALK", (40, 220, 220)),
        "stop":      ("SIGN: STOP AHEAD",        (255, 55, 55)),
        "speed_15":  ("SIGN: SPEED LIMIT 15",    (255, 220, 40)),
    }

    def __init__(self):
        self.is_open = False
        self._ticker_t = 0.0
        self._latency_jitter = 0.0
        self._conf_jitter = 0.0
        self._all_widgets = []

        # ── Background panel (right-center, non-obstructing)
        self.panel_bg = Entity(
            parent=camera.ui,
            model='quad',
            scale=(0.56, 0.72),
            position=(0.63, 0.08),
            color=rgba32(10, 14, 22, 230),
            enabled=False
        )
        self._all_widgets.append(self.panel_bg)

        # ── Title bar
        self.title = Text(
            text="╔══ NEURAL PERCEPTION HUD ══╗",
            parent=camera.ui,
            position=(0.37, 0.43),
            scale=0.80,
            color=rgb32(0, 215, 255),
            origin=(-0.5, 0.5),
            enabled=False
        )
        self._all_widgets.append(self.title)

        # ── Model telemetry ticker row
        self.ticker = Text(
            text="Model: YOLOv8n-ADAS | Latency: 11.4ms | Res: 640×640 | FPS: 60",
            parent=camera.ui,
            position=(0.37, 0.405),
            scale=0.68,
            color=rgb32(180, 230, 255),
            origin=(-0.5, 0.5),
            enabled=False
        )
        self._all_widgets.append(self.ticker)

        # ── Divider
        self.div1 = Text(
            text="─────────────────────────────────",
            parent=camera.ui,
            position=(0.37, 0.385),
            scale=0.70,
            color=rgb32(50, 80, 100),
            origin=(-0.5, 0.5),
            enabled=False
        )
        self._all_widgets.append(self.div1)

        # ── Section: Object Detection (YOLOv8)
        self.det_title = Text(
            text="① YOLO OBJECT DETECTION",
            parent=camera.ui,
            position=(0.37, 0.365),
            scale=0.76,
            color=rgb32(255, 215, 0),
            origin=(-0.5, 0.5),
            enabled=False
        )
        self._all_widgets.append(self.det_title)

        # Detection rows (live-updated per frame with nearest actors)
        self.det_rows = []
        for i in range(6):
            t = Text(
                text=f"  [--] ---: ---m | Conf: ---%",
                parent=camera.ui,
                position=(0.37, 0.340 - i * 0.030),
                scale=0.70,
                color=rgb32(140, 200, 240),
                origin=(-0.5, 0.5),
                enabled=False
            )
            self.det_rows.append(t)
            self._all_widgets.append(t)

        # ── Divider
        self.div2 = Text(
            text="─────────────────────────────────",
            parent=camera.ui,
            position=(0.37, 0.155),
            scale=0.70,
            color=rgb32(50, 80, 100),
            origin=(-0.5, 0.5),
            enabled=False
        )
        self._all_widgets.append(self.div2)

        # ── Section: Semantic Segmentation
        self.seg_title = Text(
            text="② SEMANTIC SEGMENTATION",
            parent=camera.ui,
            position=(0.37, 0.135),
            scale=0.76,
            color=rgb32(60, 220, 80),
            origin=(-0.5, 0.5),
            enabled=False
        )
        self._all_widgets.append(self.seg_title)

        # Segmentation color legend rows
        self.seg_rows = []
        for i, (cls_name, cls_col) in enumerate(self.SEG_CLASSES):
            t = Text(
                text=f"  ■ {cls_name:<12} [DeepLabV3+ class {i}]",
                parent=camera.ui,
                position=(0.37, 0.108 - i * 0.027),
                scale=0.68,
                color=rgb32(*cls_col),
                origin=(-0.5, 0.5),
                enabled=False
            )
            self.seg_rows.append(t)
            self._all_widgets.append(t)

        # ── Divider
        self.div3 = Text(
            text="─────────────────────────────────",
            parent=camera.ui,
            position=(0.37, -0.060),
            scale=0.70,
            color=rgb32(50, 80, 100),
            origin=(-0.5, 0.5),
            enabled=False
        )
        self._all_widgets.append(self.div3)

        # ── Section: Traffic Sign Recognition
        self.tsr_title = Text(
            text="③ TRAFFIC SIGN RECOGNITION",
            parent=camera.ui,
            position=(0.37, -0.080),
            scale=0.76,
            color=rgb32(40, 220, 220),
            origin=(-0.5, 0.5),
            enabled=False
        )
        self._all_widgets.append(self.tsr_title)

        self.tsr_rows = []
        sign_defs = [
            ("crosswalk", 25.0),
            ("crosswalk", 153.0),
            ("speed_15",  -5.0),
            ("stop",      255.0),
        ]
        for i, (stype, sz) in enumerate(sign_defs):
            label, col = self.SIGN_LABELS[stype]
            t = Text(
                text=f"  [{label}] z≈{sz:.0f}m | Conf: 97%",
                parent=camera.ui,
                position=(0.37, -0.106 - i * 0.028),
                scale=0.68,
                color=rgb32(*col),
                origin=(-0.5, 0.5),
                enabled=False
            )
            self.tsr_rows.append(t)
            self._all_widgets.append(t)

        # ── Divider
        self.div4 = Text(
            text="─────────────────────────────────",
            parent=camera.ui,
            position=(0.37, -0.225),
            scale=0.70,
            color=rgb32(50, 80, 100),
            origin=(-0.5, 0.5),
            enabled=False
        )
        self._all_widgets.append(self.div4)

        # ── DL Pipeline info footer
        self.footer = Text(
            text=(
                "  Backbone: CSPDarknet53-C2f\n"
                "  Neck:     PANet FPN (P3/P4/P5)\n"
                "  Head:     Anchor-Free Decoupled\n"
                "  Seg:      DeepLabV3+ (ResNet50)"
            ),
            parent=camera.ui,
            position=(0.37, -0.248),
            scale=0.65,
            color=rgb32(130, 150, 170),
            origin=(-0.5, 0.5),
            enabled=False
        )
        self._all_widgets.append(self.footer)

        # close hint
        self.close_hint = Text(
            text="[N]: Close Neural Perception HUD",
            parent=camera.ui,
            position=(0.37, -0.365),
            scale=0.68,
            color=rgb32(80, 120, 150),
            origin=(-0.5, 0.5),
            enabled=False
        )
        self._all_widgets.append(self.close_hint)

    def _set_all_enabled(self, state):
        for w in self._all_widgets:
            w.enabled = state

    def toggle(self):
        self.is_open = not self.is_open
        self._set_all_enabled(self.is_open)
        return self.is_open

    def close(self):
        self.is_open = False
        self._set_all_enabled(False)

    # ─────────────────────────────────────────────────────────────────────
    def update(self, dt, robot, sensor_mgr=None, failure_injector=None):
        if not self.is_open:
            return

        self._ticker_t += dt
        self._latency_jitter += dt

        # 1. Live model ticker (jitter latency like a real edge-AI chip)
        base_lat = 11.4
        if failure_injector and getattr(failure_injector, 'active_mode', 'NORMAL') == 'LATENCY_DELAY':
            base_lat = 450.0 + 30.0 * math.sin(self._latency_jitter * 3.0)
            lat_col = rgb32(255, 220, 50)
        elif failure_injector and getattr(failure_injector, 'active_mode', 'NORMAL') == 'HIGH_UNCERTAINTY':
            base_lat = 18.0 + 5.0 * math.sin(self._latency_jitter * 8.0)
            lat_col = rgb32(210, 100, 255)
        else:
            base_lat = 11.4 + 1.5 * math.sin(self._latency_jitter * 11.0)
            lat_col = rgb32(180, 230, 255)

        fps_val = max(30, int(60 - base_lat * 0.03))
        self.ticker.text = (
            f"Model: YOLOv8n-ADAS | Latency: {base_lat:.1f}ms | "
            f"Res: 640×640 | FPS: {fps_val}"
        )
        self.ticker.color = lat_col

        # 2. Detection rows — driven by sensor_mgr perceived actors
        perceived = []
        if sensor_mgr and hasattr(sensor_mgr, 'perceived_actors'):
            perceived = sensor_mgr.perceived_actors or []

        # Sort by distance
        actor_dists = []
        for a in perceived:
            dx = a.x - robot.x
            dz = a.z - robot.z
            dist = math.sqrt(dx**2 + dz**2)
            actor_dists.append((dist, a))
        actor_dists.sort(key=lambda x: x[0])

        for idx, row_text in enumerate(self.det_rows):
            if idx < len(actor_dists):
                dist, actor = actor_dists[idx]
                atype = getattr(actor, 'actor_type', 'PEDESTRIAN')
                is_phantom = getattr(actor, 'is_phantom', False)
                is_misc = "[MISCLASSIFIED" in getattr(actor, 'name', '')

                # Determine confidence
                if failure_injector:
                    fm = failure_injector.active_mode
                    if fm == 'HIGH_UNCERTAINTY':
                        conf = 25.0 + 13.0 * math.sin(self._ticker_t * 7.0 + idx * 1.5)
                        conf = max(18, min(42, conf))
                    elif is_phantom:
                        conf = 88.0
                    else:
                        base_conf = getattr(sensor_mgr, 'detection_confidence', 98)
                        conf = base_conf
                else:
                    conf = getattr(sensor_mgr, 'detection_confidence', 98)

                # Determine color based on threat distance
                if dist < 3.2:
                    r_col = rgb32(255, 60, 60)
                elif dist < 6.5:
                    r_col = rgb32(255, 200, 30)
                else:
                    r_col = rgb32(80, 240, 150)

                if is_phantom:
                    r_col = rgb32(255, 140, 20)
                    label_text = f"  [GHOST] OBSTACLE: {dist:.1f}m | Conf: {int(conf)}% ⚠️"
                elif is_misc:
                    r_col = rgb32(255, 100, 180)
                    label_text = f"  [WRONG] PED→OBSTACLE: {dist:.1f}m | Conf: {int(conf)}%"
                elif failure_injector and failure_injector.active_mode == 'HIGH_UNCERTAINTY':
                    label_text = f"  [???] {atype}: {dist:.1f}m | UNCERT Conf: {int(conf)}%"
                else:
                    label_text = f"  [YOLO] {atype}: {dist:.1f}m | Conf: {int(conf)}%"

                row_text.text = label_text
                row_text.color = r_col
                row_text.enabled = True
            else:
                row_text.text = "  [--] No detection"
                row_text.color = rgb32(70, 90, 110)
                row_text.enabled = True

        # 3. Update TSR confidence (small jitter per sign)
        for i, row in enumerate(self.tsr_rows):
            jit = int(95 + 3 * math.sin(self._ticker_t * 4.0 + i * 2.3))
            existing = row.text
            # Update only the confidence part
            prefix = existing.rsplit("| Conf:", 1)[0]
            row.text = f"{prefix}| Conf: {jit}%"
