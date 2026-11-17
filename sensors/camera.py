"""
Camera Sensor Module: Front-facing stereo optical camera field-of-view (FoV)
visual frustum pyramid and optical observation envelope.
"""
from ursina import Entity, color, Vec3
from ursina.color import rgb32, rgba32
from environment.common_models import get_cone
import math

class CameraFrustumVisualizer(Entity):
    def __init__(self, robot, fov_range=13.0, **kwargs):
        super().__init__(**kwargs)
        self.robot = robot
        self.fov_range = fov_range
        self.is_enabled = True
        
        cone = get_cone()
        
        # 1. Optical Vision Frustum (Semi-transparent golden/cyan pyramid cone)
        self.frustum = Entity(
            parent=self,
            model=cone,
            rotation_x=-90,
            scale=(fov_range * 0.9, fov_range, fov_range * 0.55),
            position=(0, 0.65, fov_range / 2),
            color=rgba32(255, 215, 0, 22) # Soft translucent golden optic vision cone
        )
        
    def toggle(self):
        self.is_enabled = not self.is_enabled
        self.enabled = self.is_enabled
        return self.is_enabled
        
    def update_frustum(self, dt):
        if not self.is_enabled or not self.robot:
            return
            
        self.position = self.robot.position
        self.rotation_y = self.robot.rotation_y

