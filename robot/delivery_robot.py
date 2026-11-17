"""
Delivery Robot Module: A high-fidelity 3D autonomous sidewalk delivery robot
modeled after real-world units (e.g., Starship Technologies / Serve Robotics).
Features 4 independently rotating wheels, articulated LiDAR dome, stereo cameras,
radar dome, ultrasonic sensor pucks, LED headlights, and safety flag.
"""
from ursina import Entity, color, Vec3, Text, load_texture
from ursina.color import rgb32, rgba32
from environment.common_models import get_cylinder, get_cone
import math

class DeliveryRobot(Entity):
    def __init__(self, position=(8.75, 0.45, -6), **kwargs):
        super().__init__(position=position, **kwargs)
        
        cyl = get_cylinder()
        cone = get_cone()
        
        # Color palette
        chassis_white = rgb32(248, 250, 252)
        accent_dark = rgb32(35, 40, 48)
        accent_blue = rgb32(20, 140, 245)
        tire_rubber = rgb32(25, 25, 28)
        rim_silver = rgb32(195, 200, 205)
        
        # 1. Main Lower Chassis Frame
        self.chassis = Entity(
            parent=self,
            model='cube',
            scale=(1.05, 0.35, 1.45),
            position=(0, 0.22, 0),
            color=accent_dark
        )
        
        # 2. Sleek Delivery Cargo Pod (Main Body)
        self.body = Entity(
            parent=self,
            model='cube',
            scale=(1.12, 0.58, 1.42),
            position=(0, 0.54, 0),
            color=chassis_white
        )
        
        # Top Cargo Lid
        self.cargo_lid = Entity(
            parent=self,
            model='cube',
            scale=(0.95, 0.08, 1.15),
            position=(0, 0.85, -0.05),
            color=rgb32(235, 238, 242)
        )
        # Lid Handle
        self.lid_handle = Entity(
            parent=self,
            model='cube',
            scale=(0.35, 0.04, 0.12),
            position=(0, 0.90, -0.05),
            color=accent_blue
        )
        
        # 3. Front Sensor Visor & Perception Array
        self.front_visor = Entity(
            parent=self,
            model='cube',
            scale=(1.02, 0.36, 0.15),
            position=(0, 0.52, 0.72),
            color=rgb32(18, 20, 24)
        )
        
        # Stereo Optical Cameras
        self.cam_left = Entity(
            parent=self.front_visor,
            model=cyl,
            rotation_x=90,
            scale=(0.14, 0.15, 0.14),
            position=(-0.32, 0.1, 0.45),
            color=rgb32(40, 180, 255)
        )
        self.cam_right = Entity(
            parent=self.front_visor,
            model=cyl,
            rotation_x=90,
            scale=(0.14, 0.15, 0.14),
            position=(0.32, 0.1, 0.45),
            color=rgb32(40, 180, 255)
        )
        
        # Center Long-Range Radar Dome
        self.radar_dome = Entity(
            parent=self.front_visor,
            model='sphere',
            scale=(0.28, 0.18, 0.22),
            position=(0, -0.15, 0.4),
            color=rgb32(30, 32, 38)
        )
        
        # Ultrasonic Sensor Pucks
        self.ultrasonics = []
        for ux in [-0.42, -0.18, 0.18, 0.42]:
            u = Entity(
                parent=self,
                model=cyl,
                rotation_x=90,
                scale=(0.06, 0.04, 0.06),
                position=(ux, 0.22, 0.73),
                color=rgb32(80, 85, 95)
            )
            self.ultrasonics.append(u)
            
        # 4. Top 360-Degree Spinning LiDAR Mast
        self.lidar_mast = Entity(
            parent=self,
            model=cyl,
            scale=(0.14, 0.22, 0.14),
            position=(0, 0.95, 0.35),
            color=accent_dark
        )
        self.lidar_head = Entity(
            parent=self,
            model=cyl,
            scale=(0.32, 0.22, 0.32),
            position=(0, 1.10, 0.35),
            color=rgb32(25, 28, 35)
        )
        # Glowing 360 LiDAR Scanning Ring
        self.lidar_ring = Entity(
            parent=self.lidar_head,
            model=cyl,
            scale=(1.05, 0.25, 1.05),
            position=(0, 0, 0),
            color=rgb32(0, 215, 255)
        )
        
        # 5. Front LED Headlights
        self.headlight_left = Entity(
            parent=self,
            model='sphere',
            scale=(0.14, 0.12, 0.08),
            position=(-0.42, 0.34, 0.72),
            color=rgb32(255, 255, 230)
        )
        self.headlight_right = Entity(
            parent=self,
            model='sphere',
            scale=(0.14, 0.12, 0.08),
            position=(0.42, 0.34, 0.72),
            color=rgb32(255, 255, 230)
        )
        
        # Front Projection Light Beams
        self.light_beam_left = Entity(
            parent=self.headlight_left,
            model=cone,
            rotation_x=-90,
            scale=(1.4, 6.0, 1.4),
            position=(0, 0, 3.0),
            color=rgba32(255, 255, 210, 35),
            enabled=True
        )
        self.light_beam_right = Entity(
            parent=self.headlight_right,
            model=cone,
            rotation_x=-90,
            scale=(1.4, 6.0, 1.4),
            position=(0, 0, 3.0),
            color=rgba32(255, 255, 210, 35),
            enabled=True
        )
        
        # 6. Rear Tail Lights
        self.tail_light_bar = Entity(
            parent=self,
            model='cube',
            scale=(0.85, 0.08, 0.05),
            position=(0, 0.65, -0.72),
            color=rgb32(240, 25, 25)
        )
        
        # 7. Safety Flag & Antenna
        self.antenna_pole = Entity(
            parent=self,
            model=cyl,
            scale=(0.025, 1.85, 0.025),
            position=(-0.44, 1.70, -0.55),
            color=rgb32(180, 185, 190)
        )
        self.safety_flag = Entity(
            parent=self.antenna_pole,
            model='quad',
            rotation_y=90,
            scale=(0.35, 0.25),
            position=(0, 0.85, 0.15),
            color=rgb32(255, 105, 0)
        )
        
        # 8. Four Wheels
        wheel_radius = 0.26
        wheel_width = 0.16
        wheel_track_x = 0.58
        wheel_base_z = 0.48
        
        self.wheels = []
        wheel_positions = [
            (-wheel_track_x, wheel_radius,  wheel_base_z),
            ( wheel_track_x, wheel_radius,  wheel_base_z),
            (-wheel_track_x, wheel_radius, -wheel_base_z),
            ( wheel_track_x, wheel_radius, -wheel_base_z),
        ]
        
        for i, pos in enumerate(wheel_positions):
            wheel_hub = Entity(parent=self, position=pos)
            
            tire = Entity(
                parent=wheel_hub,
                model=cyl,
                rotation_z=90,
                scale=(wheel_radius * 2, wheel_width, wheel_radius * 2),
                color=tire_rubber
            )
            rim = Entity(
                parent=wheel_hub,
                model=cyl,
                rotation_z=90,
                scale=(wheel_radius * 1.3, wheel_width + 0.02, wheel_radius * 1.3),
                color=rim_silver
            )
            Entity(
                parent=wheel_hub,
                model=cyl,
                rotation_z=90,
                scale=(0.1, wheel_width + 0.04, 0.1),
                color=accent_blue
            )
            Entity(
                parent=wheel_hub,
                model='cube',
                rotation_z=90,
                scale=(0.04, wheel_width + 0.01, wheel_radius * 1.95),
                color=rgb32(55, 60, 68)
            )
            Entity(
                parent=wheel_hub,
                model='cube',
                rotation_z=90,
                rotation_x=90,
                scale=(0.04, wheel_width + 0.01, wheel_radius * 1.95),
                color=rgb32(55, 60, 68)
            )
            
            self.wheels.append(wheel_hub)
            
        # 9. Fake Contact Shadow under robot
        self.shadow_decal = Entity(
            parent=self,
            model='quad',
            rotation_x=90,
            scale=(1.45, 1.85),
            position=(0, -0.15, 0),
            color=rgba32(15, 18, 22, 130)
        )
        
        # State & Telemetry
        self.speed = 0.0
        self.target_speed = 1.6
        self.max_speed = 2.5
        self.acceleration = 1.8
        self.steering_angle = 0.0
        self.total_distance = 0.0
        self.status = "IDLE"
        
    def update(self):
        if hasattr(self, 'lidar_head'):
            self.lidar_head.rotation_y += 360 * 0.016 * 2.5
            
        if hasattr(self, 'safety_flag'):
            self.safety_flag.rotation_z = 8 * math.sin(self.total_distance * 4.0 + self.rotation_y * 0.1)
            
    def roll_wheels(self, distance_delta):
        self.total_distance += abs(distance_delta)
        wheel_radius = 0.26
        deg_delta = (distance_delta / wheel_radius) * (180.0 / math.pi)
        for w in self.wheels:
            w.rotation_x += deg_delta

    def toggle_torch(self):
        """Toggles the forward headlights/torch on/off."""
        is_on = not self.light_beam_left.enabled
        self.light_beam_left.enabled = is_on
        self.light_beam_right.enabled = is_on
        return is_on

    def set_torch_weather_mode(self, weather_mode):
        """Tunes headlight beam intensity based on weather conditions."""
        w = weather_mode.lower()
        if w == 'night':
            c = rgba32(255, 255, 210, 110)
        elif 'fog' in w:
            c = rgba32(255, 255, 230, 95)
        elif 'rain' in w:
            c = rgba32(230, 245, 255, 80)
        else:
            c = rgba32(255, 255, 210, 35)
        self.light_beam_left.color = c
        self.light_beam_right.color = c
