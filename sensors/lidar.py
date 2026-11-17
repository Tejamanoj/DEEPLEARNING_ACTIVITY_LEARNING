"""
LiDAR Sensor Module: 360-degree spinning laser fan visualizer,
concentric range rings, and simulated point-cloud reflections.
Optimized for 60 FPS on integrated graphics.
"""
from ursina import Entity, color, Vec3
from ursina.color import rgb32, rgba32
from environment.common_models import get_cylinder
import math

class LiDARVisualizer(Entity):
    def __init__(self, robot, max_range=16.0, **kwargs):
        super().__init__(**kwargs)
        self.robot = robot
        self.max_range = max_range
        self.is_enabled = True
        
        cyl = get_cylinder()
        
        # 1. Concentric Ground Range Rings (5m, 10m, 15m)
        self.range_rings = []
        for r in [5.0, 10.0, 15.0]:
            ring = Entity(
                parent=self,
                model=cyl,
                scale=(r * 2, 0.02, r * 2),
                position=(0, 0.05, 0),
                color=rgba32(0, 215, 255, 30) # Soft electric cyan
            )
            self.range_rings.append(ring)
            
        # 2. Rotating 360° Laser Sweep Beam Arc (Semi-transparent fan sector)
        self.sweep_sector = Entity(
            parent=self,
            model='quad',
            rotation_x=90,
            scale=(max_range * 0.9, max_range * 0.9),
            position=(0, 0.08, 0),
            color=rgba32(0, 230, 255, 35)
        )
        
        # 3. Rotating Laser Sweep Lines (Radial scanning rays)
        self.sweep_rays = []
        for i in range(4):
            ray = Entity(
                parent=self,
                model='cube',
                scale=(0.04, 0.02, max_range),
                rotation_y=i * 90,
                position=(0, 0.09, 0),
                color=rgba32(0, 255, 240, 90)
            )
            self.sweep_rays.append(ray)
            
        self.rotation_speed = 360.0 # deg/sec
        
    def toggle(self):
        self.is_enabled = not self.is_enabled
        self.enabled = self.is_enabled
        return self.is_enabled
        
    def update_sweep(self, dt):
        if not self.is_enabled or not self.robot:
            return
            
        # Keep centered at robot position on the ground
        self.position = Vec3(self.robot.x, self.robot.y, self.robot.z)
        
        # Spin laser sweep rays
        rot_delta = self.rotation_speed * dt
        self.rotation_y = (self.rotation_y + rot_delta) % 360

