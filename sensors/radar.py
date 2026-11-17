"""
Radar Sensor Module: 77GHz millimeter-wave forward radar cone visualizer
with animated expanding radar wave pulses.
"""
from ursina import Entity, color, Vec3
from ursina.color import rgb32, rgba32
from environment.common_models import get_cone
import math

class RadarVisualizer(Entity):
    def __init__(self, robot, max_range=18.0, **kwargs):
        super().__init__(**kwargs)
        self.robot = robot
        self.max_range = max_range
        self.is_enabled = True
        self.wave_pulse = 0.0
        
        cone = get_cone()
        
        # 1. Forward-projecting radar detection cone
        self.cone_mesh = Entity(
            parent=self,
            model=cone,
            rotation_x=-90,
            scale=(max_range * 0.75, max_range, max_range * 0.75),
            position=(0, 0.45, max_range / 2),
            color=rgba32(40, 180, 255, 25) # Soft translucent blue
        )
        
        # 2. Expanding Radar Ping Wave Ring
        self.ping_ring = Entity(
            parent=self,
            model='quad',
            rotation_x=90,
            scale=(2.0, 2.0),
            position=(0, 0.15, 2.0),
            color=rgba32(80, 215, 255, 90)
        )
        
    def toggle(self):
        self.is_enabled = not self.is_enabled
        self.enabled = self.is_enabled
        return self.is_enabled
        
    def update_radar(self, dt):
        if not self.is_enabled or not self.robot:
            return
            
        # Match robot position and heading
        self.position = self.robot.position
        self.rotation_y = self.robot.rotation_y
        
        # Animate radar wave ping expanding outward
        self.wave_pulse = (self.wave_pulse + dt * 1.5) % 1.0
        wave_dist = 1.0 + self.wave_pulse * (self.max_range - 1.0)
        self.ping_ring.z = wave_dist
        self.ping_ring.scale = (wave_dist * 0.7, wave_dist * 0.7)
        # Fade out towards max range
        alpha = int((1.0 - self.wave_pulse) * 80)
        self.ping_ring.color = rgba32(80, 215, 255, alpha)

