"""
Humanoid Autonomous Delivery Android Module:
Modeled precisely after the sleek bipedal AI robot aesthetic (Astro/Cyber Delivery Android).
Features a large spherical head with glossy black visor, dual glowing cyan circular camera eyes,
articulated bipedal walking legs, robotic arms, chest power core, and rear delivery backpack.
"""
from ursina import Entity, color, Vec3, Text
from ursina.color import rgb32, rgba32
from environment.common_models import get_cylinder, get_cone
import math

class HumanoidDeliveryRobot(Entity):
    def __init__(self, position=(8.75, 0.28, -6), **kwargs):
        super().__init__(position=position, **kwargs)
        self.actor_type = "HUMANOID_DELIVERY_ROBOT"
        
        cyl = get_cylinder()
        
        # Color palette
        white_shell = rgb32(248, 250, 254)       # Glossy ceramic white
        dark_mech   = rgb32(32, 35, 42)          # Matte titanium dark gray
        cyan_glow   = rgb32(0, 225, 255)         # Electric cyan LED optics
        eye_rim     = rgb32(50, 60, 72)          # Inner camera optic bezel
        blue_core   = rgb32(20, 160, 255)        # Torso power core
        accent_blue = rgb32(0, 195, 255)         # Boot sole glowing trims
        
        # 1. Base Pivot & Pelvis
        self.pelvis = Entity(
            parent=self,
            model='sphere',
            scale=(0.58, 0.42, 0.52),
            position=(0, 1.25, 0),
            color=dark_mech
        )
        
        # 2. Torso (Curved White Chest Shell)
        self.torso = Entity(
            parent=self.pelvis,
            model='sphere',
            scale=(1.45, 1.65, 1.35),
            position=(0, 0.95, 0),
            color=white_shell
        )
        
        # Chest Sensor / Delivery Hatch Panel
        self.chest_panel = Entity(
            parent=self.torso,
            model='cube',
            scale=(0.62, 0.55, 0.25),
            position=(0, 0.10, 0.45),
            color=rgb32(236, 240, 246)
        )
        
        # High-Power LED Forward Torch / Headlight Spotlight
        self.torch_bezel = Entity(
            parent=self.torso,
            model=cyl,
            rotation_x=90,
            scale=(0.32, 0.15, 0.32),
            position=(0, 0.18, 0.52),
            color=dark_mech
        )
        self.torch_lens = Entity(
            parent=self.torch_bezel,
            model='sphere',
            scale=(0.85, 0.35, 0.85),
            position=(0, 0.08, 0),
            color=rgb32(255, 255, 235) # High-intensity white-gold emitter
        )
        
        # Volumetric Forward Torch Light Beam (Illuminates corridor ahead)
        cone = get_cone()
        self.torch_enabled = True
        self.torch_beam = Entity(
            parent=self,
            model=cone,
            rotation_x=-90,
            scale=(2.6, 11.0, 2.6),
            position=(0, 1.45, 5.5),
            color=rgba32(255, 255, 215, 40)
        )
        # Ground Illumination Puddle (moves with robot)
        self.torch_ground_spot = Entity(
            parent=self,
            model='quad',
            rotation_x=90,
            scale=(2.8, 5.5),
            position=(0, 0.03, 5.5),
            color=rgba32(255, 255, 205, 65)
        )
        
        # Glowing Blue Arc Reactor / Power Core
        self.power_core = Entity(
            parent=self.torso,
            model=cyl,
            rotation_x=90,
            scale=(0.24, 0.08, 0.24),
            position=(0, -0.28, 0.48),
            color=blue_core
        )
        self.power_core_glow = Entity(
            parent=self.power_core,
            model=cyl,
            scale=(1.25, 0.8, 1.25),
            position=(0, 0, 0),
            color=rgba32(0, 225, 255, 120)
        )
        
        # Rear Delivery Cargo Backpack (Payload Container)
        self.cargo_backpack = Entity(
            parent=self.torso,
            model='cube',
            scale=(0.75, 0.85, 0.48),
            position=(0, 0.05, -0.55),
            color=white_shell
        )
        # Backpack Handle & Status LEDs
        Entity(parent=self.cargo_backpack, model='cube', scale=(0.45, 0.08, 0.12), position=(0, 0.48, 0), color=dark_mech)
        self.cargo_status_led = Entity(parent=self.cargo_backpack, model='quad', scale=(0.35, 0.06), position=(0, 0.15, -0.25), rotation_y=180, color=rgb32(0, 255, 140))
        
        # 3. Neck Gimbal Collar
        self.neck = Entity(
            parent=self.torso,
            model=cyl,
            scale=(0.38, 0.28, 0.38),
            position=(0, 0.85, 0),
            color=dark_mech
        )
        
        # 4. Large Spherical Android Head (Can turn independently to track targets!)
        self.head = Entity(
            parent=self.neck,
            model='sphere',
            scale=(2.4, 2.3, 2.3),
            position=(0, 0.95, 0.05),
            color=white_shell
        )
        
        # Dark Glossy Visor Screen
        self.visor = Entity(
            parent=self.head,
            model='sphere',
            scale=(0.88, 0.72, 0.45),
            position=(0, 0.02, 0.35),
            color=rgb32(16, 18, 24)
        )
        
        # Big Expressive Glowing Cyan Eyes (Dual Camera Optics)
        eye_radius = 0.22
        # Left Eye Assembly
        self.eye_left_bezel = Entity(
            parent=self.visor,
            model=cyl,
            rotation_x=90,
            scale=(eye_radius * 2.2, 0.12, eye_radius * 2.2),
            position=(-0.30, 0.06, 0.42),
            color=eye_rim
        )
        self.eye_left = Entity(
            parent=self.eye_left_bezel,
            model='sphere',
            scale=(0.75, 0.25, 0.75),
            position=(0, 0.05, 0),
            color=cyan_glow
        )
        
        # Right Eye Assembly
        self.eye_right_bezel = Entity(
            parent=self.visor,
            model=cyl,
            rotation_x=90,
            scale=(eye_radius * 2.2, 0.12, eye_radius * 2.2),
            position=(0.30, 0.06, 0.42),
            color=eye_rim
        )
        self.eye_right = Entity(
            parent=self.eye_right_bezel,
            model='sphere',
            scale=(0.75, 0.25, 0.75),
            position=(0, 0.05, 0),
            color=cyan_glow
        )
        
        # Ear Pod Sensors (Left & Right)
        Entity(parent=self.head, model=cyl, rotation_z=90, scale=(0.32, 0.12, 0.32), position=(-0.52, 0.02, 0), color=dark_mech)
        Entity(parent=self.head, model=cyl, rotation_z=90, scale=(0.32, 0.12, 0.32), position=(0.52, 0.02, 0), color=dark_mech)
        
        # Top Head LiDAR Scanner Ridge
        self.head_lidar = Entity(
            parent=self.head,
            model=cyl,
            scale=(0.28, 0.08, 0.28),
            position=(0, 0.52, 0),
            color=dark_mech
        )
        self.lidar_ring = Entity(
            parent=self.head_lidar,
            model=cyl,
            scale=(1.08, 0.35, 1.08),
            position=(0, 0, 0),
            color=rgb32(0, 225, 255)
        )
        
        # 5. Articulated Robotic Arms
        # Left Arm (Holding high-tech pose or swinging)
        self.shoulder_l = Entity(parent=self.torso, model='sphere', scale=(0.38, 0.38, 0.38), position=(-0.65, 0.35, 0), color=white_shell)
        self.arm_l = Entity(parent=self.shoulder_l, position=(0, -0.15, 0))
        self.upper_arm_l = Entity(parent=self.arm_l, model=cyl, scale=(0.22, 0.55, 0.22), position=(0, -0.22, 0), color=white_shell)
        self.forearm_l = Entity(parent=self.upper_arm_l, model=cyl, scale=(0.95, 0.95, 0.95), position=(0, -0.55, 0.08), rotation_x=-25, color=white_shell)
        self.hand_l = Entity(parent=self.forearm_l, model='sphere', scale=(0.28, 0.28, 0.28), position=(0, -0.45, 0), color=dark_mech)
        
        # Right Arm (Points forward during detection!)
        self.shoulder_r = Entity(parent=self.torso, model='sphere', scale=(0.38, 0.38, 0.38), position=(0.65, 0.35, 0), color=white_shell)
        self.arm_r = Entity(parent=self.shoulder_r, position=(0, -0.15, 0))
        self.upper_arm_r = Entity(parent=self.arm_r, model=cyl, scale=(0.22, 0.55, 0.22), position=(0, -0.22, 0), color=white_shell)
        self.forearm_r = Entity(parent=self.upper_arm_r, model=cyl, scale=(0.95, 0.95, 0.95), position=(0, -0.55, 0.08), rotation_x=-25, color=white_shell)
        self.hand_r = Entity(parent=self.forearm_r, model='sphere', scale=(0.28, 0.28, 0.28), position=(0, -0.45, 0), color=dark_mech)
        # Pointing index finger on right hand
        self.finger_r = Entity(parent=self.hand_r, model='cube', scale=(0.06, 0.16, 0.06), position=(0, -0.18, 0.08), rotation_x=-45, color=dark_mech)
        
        # 6. Bipedal Walking Legs & Cyber Boots
        # Left Leg
        self.hip_l = Entity(parent=self, position=(-0.28, 1.25, 0))
        self.thigh_l = Entity(parent=self.hip_l, model=cyl, scale=(0.26, 0.65, 0.26), position=(0, -0.32, 0), color=white_shell)
        self.knee_joint_l = Entity(parent=self.thigh_l, model='sphere', scale=(0.32, 0.25, 0.32), position=(0, -0.45, 0), color=dark_mech)
        self.calf_l = Entity(parent=self.knee_joint_l, model=cyl, scale=(0.95, 0.95, 0.95), position=(0, -0.52, 0), color=white_shell)
        # Left Boot
        self.boot_l = Entity(parent=self.calf_l, model='cube', scale=(0.34, 0.24, 0.58), position=(0, -0.48, 0.12), color=white_shell)
        self.boot_sole_l = Entity(parent=self.boot_l, model='cube', scale=(1.05, 0.18, 1.05), position=(0, -0.45, 0), color=dark_mech)
        self.boot_glow_l = Entity(parent=self.boot_l, model='quad', scale=(0.95, 0.06), position=(0, -0.38, 0.54), color=accent_blue)
        
        # Right Leg
        self.hip_r = Entity(parent=self, position=(0.28, 1.25, 0))
        self.thigh_r = Entity(parent=self.hip_r, model=cyl, scale=(0.26, 0.65, 0.26), position=(0, -0.32, 0), color=white_shell)
        self.knee_joint_r = Entity(parent=self.thigh_r, model='sphere', scale=(0.32, 0.25, 0.32), position=(0, -0.45, 0), color=dark_mech)
        self.calf_r = Entity(parent=self.knee_joint_r, model=cyl, scale=(0.95, 0.95, 0.95), position=(0, -0.52, 0), color=white_shell)
        # Right Boot
        self.boot_r = Entity(parent=self.calf_r, model='cube', scale=(0.34, 0.24, 0.58), position=(0, -0.48, 0.12), color=white_shell)
        self.boot_sole_r = Entity(parent=self.boot_r, model='cube', scale=(1.05, 0.18, 1.05), position=(0, -0.45, 0), color=dark_mech)
        self.boot_glow_r = Entity(parent=self.boot_r, model='quad', scale=(0.95, 0.06), position=(0, -0.38, 0.54), color=accent_blue)
        
        # 7. Fake Contact Shadow under feet
        self.shadow_decal = Entity(
            parent=self,
            model='quad',
            rotation_x=90,
            scale=(1.25, 1.25),
            position=(0, 0.02, 0),
            color=rgba32(15, 18, 22, 130)
        )
        
        # Dimensions & kinematics
        self.height = 2.1
        self.radius = 0.55
        self.speed = 0.0
        self.target_speed = 1.6
        self.max_speed = 2.5
        self.total_distance = 0.0
        self.walk_time = 0.0
        self.status = "IDLE"
        self.head_tracking_target = None
        
    def update(self):
        dt = 0.016
        
        # 1. Subtle idle core & eye breathing pulse
        pulse = 0.5 + 0.5 * math.sin(self.total_distance * 4.0 + self.walk_time * 3.0)
        if hasattr(self, 'power_core'):
            self.power_core_glow.scale = (1.1 + pulse * 0.25, 0.8, 1.1 + pulse * 0.25)
            
        # 2. Continuous LiDAR scanner rotation on crown
        if hasattr(self, 'head_lidar'):
            self.head_lidar.rotation_y += 360 * dt * 2.0
            
    def update_walk(self, dt):
        """Articulates bipedal leg and arm stride cycles synced with forward speed."""
        if abs(self.speed) > 0.02:
            self.walk_time += dt * (self.speed * 4.2)
            stride_angle = math.sin(self.walk_time) * 28.0
            
            # Legs swing opposite
            self.hip_l.rotation_x = stride_angle
            self.hip_r.rotation_x = -stride_angle
            
            # Arms swing opposite to legs
            self.arm_l.rotation_x = -stride_angle * 0.7
            self.arm_r.rotation_x = stride_angle * 0.7
            
            # Torso natural walking bounce
            self.pelvis.y = 1.25 + abs(math.sin(self.walk_time * 2.0)) * 0.04
        else:
            # Settle smoothly to neutral idle stance
            self.hip_l.rotation_x *= 0.85
            self.hip_r.rotation_x *= 0.85
            self.arm_l.rotation_x *= 0.85
            self.arm_r.rotation_x *= 0.85
            self.pelvis.y = 1.25 + math.sin(self.walk_time * 2.0) * 0.015
            self.walk_time += dt * 1.5
            
    def roll_wheels(self, distance_delta):
        """Called by kinematic controller to advance distance & stride."""
        self.total_distance += abs(distance_delta)
        # Advance walking strides
        self.update_walk(0.016)
        
    def look_at_target(self, world_target_pos):
        """Smoothly turns the head to gaze at detected actors or upcoming waypoints."""
        if not world_target_pos:
            self.head.rotation_y = 0.0
            self.head.rotation_x = 0.0
            return
            
        dx = world_target_pos.x - self.x
        dz = world_target_pos.z - self.z
        target_yaw = math.degrees(math.atan2(dx, dz)) - self.rotation_y
        target_yaw = (target_yaw + 180) % 360 - 180
        
        # Clamp head yaw to natural human range (±65 degrees)
        clamped_yaw = max(-65.0, min(65.0, target_yaw))
        self.head.rotation_y += (clamped_yaw - self.head.rotation_y) * 0.12

    def celebrate(self, dt):
        """Victory celebration wave & pose upon reaching destination target."""
        self.walk_time += dt * 4.0
        wave = math.sin(self.walk_time * 3.0) * 18.0
        self.arm_l.rotation_x = -135.0 + wave
        self.arm_r.rotation_x = -135.0 - wave
        self.arm_l.rotation_z = 24.0
        self.arm_r.rotation_z = -24.0
        self.head.rotation_x = -12.0
        self.pelvis.y = 1.25 + abs(math.sin(self.walk_time * 3.5)) * 0.08

    def toggle_torch(self):
        """Toggles the forward torch light spotlight on/off."""
        self.torch_enabled = not self.torch_enabled
        if hasattr(self, 'torch_beam'):
            self.torch_beam.enabled = self.torch_enabled
        if hasattr(self, 'torch_ground_spot'):
            self.torch_ground_spot.enabled = self.torch_enabled
        return self.torch_enabled

    def set_torch_weather_mode(self, weather_mode):
        """Dynamically tunes torch beam intensity and contrast based on weather/lighting."""
        if not hasattr(self, 'torch_beam') or not self.torch_enabled:
            return
            
        w = weather_mode.lower()
        if w == 'night':
            self.torch_beam.color = rgba32(255, 255, 210, 115) # Piercing beam in pitch darkness
            self.torch_ground_spot.color = rgba32(255, 255, 200, 140)
        elif 'fog' in w:
            self.torch_beam.color = rgba32(255, 255, 230, 95)  # Volumetric scattering in fog
            self.torch_ground_spot.color = rgba32(255, 255, 215, 105)
        elif 'rain' in w:
            self.torch_beam.color = rgba32(245, 250, 255, 75)  # Cool reflective tint in rain
            self.torch_ground_spot.color = rgba32(220, 240, 255, 115)
        elif 'snow' in w:
            self.torch_beam.color = rgba32(255, 255, 240, 70)
            self.torch_ground_spot.color = rgba32(240, 245, 255, 90)
        else:
            self.torch_beam.color = rgba32(255, 255, 215, 38)  # Gentle daylight fill beam
            self.torch_ground_spot.color = rgba32(255, 255, 205, 60)

