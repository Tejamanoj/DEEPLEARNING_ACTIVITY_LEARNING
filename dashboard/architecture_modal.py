"""
Architecture Comparison & Deep Learning Theory Modal:
Provides an interactive, comprehensive visual and technical comparison between
Modular Perception-Planning-Control Architecture and End-to-End Learned Driving Architecture,
including detailed operational stages of YOLOv8 and NVIDIA PilotNet.
Fulfills Mandatory Requirements 5 & 6 for Student 2 ELA.
"""
from ursina import Entity, camera, color, Text, Vec2
from ursina.color import rgb32, rgba32

class ArchitectureComparisonModal(Entity):
    def __init__(self, **kwargs):
        super().__init__(parent=camera.ui, **kwargs)
        self.is_open = False
        self.enabled = False
        self._on_open_callback  = None
        self._on_close_callback = None
        
        # 1. Dark solid backdrop covering screen completely
        self.backdrop = Entity(
            parent=self,
            model='quad',
            scale=(2.1, 1.3),
            position=(0, 0, 0.10),
            color=rgba32(8, 12, 18, 255)
        )
        self.backdrop.set_depth_write(False)
        
        # 2. Main Outer Card Frame
        self.card_frame = Entity(
            parent=self,
            model='quad',
            scale=(1.78, 0.94),
            position=(0, 0, 0.05),
            color=rgba32(16, 22, 32, 255)
        )
        self.card_frame.set_depth_write(False)
        
        # Header border line
        h_line = Entity(parent=self.card_frame, model='quad', scale=(1.0, 0.004), position=(0, 0.40, 0.01), color=rgb32(0, 215, 255))
        h_line.set_depth_write(False)
        # Center vertical divider
        v_line = Entity(parent=self.card_frame, model='quad', scale=(0.003, 0.72), position=(0, -0.04, 0.01), color=rgba32(80, 100, 130, 180))
        v_line.set_depth_write(False)
        # Footer border line
        f_line = Entity(parent=self.card_frame, model='quad', scale=(1.0, 0.004), position=(0, -0.40, 0.01), color=rgba32(80, 100, 130, 180))
        f_line.set_depth_write(False)

        # 3. Main Title
        self.title = Text(
            text="AUTONOMOUS DRIVING ARCHITECTURES: MODULAR vs END-TO-END DEEP LEARNING",
            parent=self,
            position=(0, 0.44, -0.05),
            scale=1.12,
            color=rgb32(255, 215, 20),
            origin=(0, 0)
        )
        self.subtitle = Text(
            text="Deep Learning Experiential Learning Activity | Student 2: Animation, Simulation & Visualization",
            parent=self,
            position=(0, 0.405, -0.05),
            scale=0.76,
            color=rgb32(180, 210, 230),
            origin=(0, 0)
        )

        # ══════════════════════════════════════════════════════════════════
        # LEFT COLUMN: MODULAR PERCEPTION-PLANNING-CONTROL ARCHITECTURE
        # ══════════════════════════════════════════════════════════════════
        self.left_title = Text(
            text="APPROACH 1: MODULAR PIPELINE (INDUSTRY STANDARD)",
            parent=self,
            position=(-0.44, 0.355, -0.05),
            scale=0.92,
            color=rgb32(0, 235, 255),
            origin=(0, 0)
        )
        
        modular_content = (
            "1. PIPELINE WORKFLOW:\n"
            "   [Sensors] (Camera, LiDAR, Radar, IMU, GNSS)\n"
            "       |\n"
            "   [Deep Learning Perception] (YOLOv8 Detection / SegNet)\n"
            "       |  -> BBoxes, Class Labels, Lane/Curb Segmentation\n"
            "   [Multi-Sensor Fusion] (Kalman Filter / 3D Spatial Map)\n"
            "       |  -> Dynamic Actor Tracking, State Estimation\n"
            "   [Behavioral Planning & Rules] (Finite State Machine)\n"
            "       |  -> Corridor Hazard Evaluation, Detour Selection\n"
            "   [Control Dynamics] (PID, Pure Pursuit Kinematics)\n"
            "       |  -> Desired Steering Yaw, Target Linear Speed (m/s)\n"
            "       v\n"
            "   [Vehicle Actuation] (Throttle, Steering, Brake)\n\n"
            "2. DEEP LEARNING MODEL: YOLOv8 (You Only Look Once)\n"
            "   - Backbone: CSPDarknet with C2f modules extracts multi-scale\n"
            "     visual spatial features (P3, P4, P5 feature pyramids).\n"
            "   - Neck: PANet (Path Aggregation Network) fuses top-down\n"
            "     semantic context with bottom-up localization cues.\n"
            "   - Head: Decoupled anchor-free heads simultaneously compute\n"
            "     object classification loss and CIoU bounding box regression.\n\n"
            "3. ARCHITECTURAL EVALUATION:\n"
            "   - Interpretability : HIGH (Auditable intermediate states)\n"
            "   - Safety Validation: HIGH (Formal rule supervisor override)\n"
            "   - Failure Risk     : Error compounding between pipeline stages\n"
            "   - Production Use   : Waymo, Cruise, Zoox, Baidu Apollo"
        )
        self.left_text = Text(
            text=modular_content,
            parent=self,
            position=(-0.84, 0.32, -0.05),
            scale=0.68,
            color=rgb32(220, 230, 245),
            origin=(-0.5, 0.5)
        )

        # ══════════════════════════════════════════════════════════════════
        # RIGHT COLUMN: END-TO-END DEEP LEARNING ARCHITECTURE
        # ══════════════════════════════════════════════════════════════════
        self.right_title = Text(
            text="APPROACH 2: END-TO-END DEEP LEARNING (IMITATION / RL)",
            parent=self,
            position=(0.44, 0.355, -0.05),
            scale=0.92,
            color=rgb32(255, 140, 40),
            origin=(0, 0)
        )
        
        e2e_content = (
            "1. PIPELINE WORKFLOW:\n"
            "   [Raw Camera Image Input] (RGB Video Stream I_t)\n"
            "       |\n"
            "       v\n"
            "   +---------------------------------------------------+\n"
            "   |       DEEP CONVOLUTIONAL NEURAL NETWORK           |\n"
            "   |  (e.g., NVIDIA PilotNet / MobileNet-V3 / CNN-LSTM)|\n"
            "   |      Learned Policy: y = f_theta(Image_t)         |\n"
            "   +---------------------------------------------------+\n"
            "       |\n"
            "       v\n"
            "   [Direct Control Output] (Steering Angle theta_t, Speed v_t)\n"
            "       |\n"
            "       v\n"
            "   [Vehicle Actuation] (Steering Motor, Wheel Inverters)\n\n"
            "2. DEEP LEARNING MODEL: NVIDIA PilotNet Architecture\n"
            "   - Normalization: Hardwired YUV image color conversion.\n"
            "   - 5 Conv Layers: 3x (5x5 kernel, stride 2) for macro road\n"
            "     features + 2x (3x3 kernel, non-strided) for boundary cues.\n"
            "   - 4 Dense Layers: 1164 -> 100 -> 50 -> 10 -> 1 scalar output\n"
            "     directly predicting vehicle inverse turning radius (1/r).\n\n"
            "3. ARCHITECTURAL EVALUATION:\n"
            "   - Interpretability : LOW (Black-box latent representations)\n"
            "   - Safety Validation: VERY LOW (No formal verification possible)\n"
            "   - Failure Risk     : Silent catastrophic failure on out-of-dist data\n"
            "   - Production Status: Tesla FSD v12 (End-to-End Neural Net)"
        )
        self.right_text = Text(
            text=e2e_content,
            parent=self,
            position=(0.04, 0.32, -0.05),
            scale=0.68,
            color=rgb32(245, 230, 220),
            origin=(-0.5, 0.5)
        )

        # ══════════════════════════════════════════════════════════════════
        # FOOTER COMPARISON MATRIX & CLOSE INSTRUCTIONS
        # ══════════════════════════════════════════════════════════════════
        footer_summary = (
            "CRITICAL TAKEAWAY: Modular architectures guarantee formal safety compliance via deterministic rule supervisors\n"
            "(e.g., R1-R5 in this simulator), while End-to-End models excel at human-like fluidity but lack provable safety guarantees.\n"
            "PRESS [I] OR [TAB] TO TOGGLE THIS SCREEN  |  PRESS [ESC] TO CLOSE"
        )
        self.footer_text = Text(
            text=footer_summary,
            parent=self,
            position=(0, -0.42, -0.05),
            scale=0.70,
            color=rgb32(120, 255, 180),
            origin=(0, 0)
        )

    def toggle(self):
        self.is_open = not self.is_open
        self.enabled = self.is_open
        if self.is_open:
            if self._on_open_callback:
                self._on_open_callback()
        else:
            if self._on_close_callback:
                self._on_close_callback()
        return self.is_open

    def close(self):
        if self.is_open:
            self.is_open = False
            self.enabled = False
            if self._on_close_callback:
                self._on_close_callback()

