"""
Camera Controller Module: Cinematic third-person follow cam framed above the robot,
true eye-level first-person vision with zero skull clipping,
and 360-degree free orbit view with mouse drag and wheel zoom.
"""
from ursina import camera, Vec3, held_keys, mouse, time
import math

class CameraController:
    def __init__(self, target_robot):
        self.target = target_robot
        self.modes = ["BACK_OF_BOT", "THROUGH_THE_EYE", "FREE_360_ORBIT", "ISOMETRIC_ADAS", "TOP_DOWN"]
        self.mode_index = 0
        self.mode = self.modes[self.mode_index]
        
        # Elevated, centered third-person chase parameters
        self.distance = 6.4
        self.height = 4.0
        self.smoothness = 6.0
        self.cam_yaw = getattr(target_robot, 'rotation_y', 0.0)
        
        # 360 Free orbit parameters
        self.orbit_yaw = 0.0
        self.orbit_pitch = 22.0
        self.orbit_distance = 6.4
        
        # Snap directly to initial camera position immediately (no startup lag!)
        self.snap_to_target()
        
    def snap_to_target(self):
        if not self.target:
            return
        target_pos = self.target.position
        is_humanoid = ("HUMANOID" in getattr(self.target, 'actor_type', ''))
        head_height = 2.45 if is_humanoid else 1.10
        self.cam_yaw = self.target.rotation_y
        rad = math.radians(self.cam_yaw)
        
        if self.mode == "BACK_OF_BOT":
            back_x = -math.sin(rad) * self.distance
            back_z = -math.cos(rad) * self.distance
            camera.position = Vec3(target_pos.x + back_x, target_pos.y + self.height, target_pos.z + back_z)
            look_ahead_x = math.sin(rad) * 6.5
            look_ahead_z = math.cos(rad) * 6.5
            camera.look_at(Vec3(target_pos.x + look_ahead_x, target_pos.y + 1.8, target_pos.z + look_ahead_z))
        elif self.mode == "THROUGH_THE_EYE":
            fx = math.sin(rad) * 0.55
            fz = math.cos(rad) * 0.55
            camera.position = Vec3(target_pos.x + fx, target_pos.y + head_height, target_pos.z + fz)
            camera.rotation_y = self.target.rotation_y
            camera.rotation_x = 2.0
            camera.rotation_z = 0.0
        elif self.mode == "FREE_360_ORBIT":
            ox = math.sin(math.radians(self.orbit_yaw)) * self.orbit_distance
            oz = -math.cos(math.radians(self.orbit_yaw)) * self.orbit_distance
            camera.position = Vec3(target_pos.x + ox, target_pos.y + 2.4, target_pos.z + oz)
            camera.look_at(Vec3(target_pos.x, target_pos.y + 1.4, target_pos.z))
        
    def set_target(self, new_target):
        # Restore visibility on previous target
        if self.target and hasattr(self.target, 'head'):
            self.target.head.visible = True
        self.target = new_target
        
    def set_mode_by_name(self, mode_name):
        if mode_name in self.modes:
            self.mode = mode_name
            self.mode_index = self.modes.index(mode_name)
            self._update_visibility()
            self.snap_to_target()
        return self.mode
        
    def next_mode(self):
        self.mode_index = (self.mode_index + 1) % len(self.modes)
        self.mode = self.modes[self.mode_index]
        self._update_visibility()
        self.snap_to_target()
        return self.mode
        
    def _update_visibility(self):
        """Hides the robot's head in first-person to guarantee zero polygon clipping."""
        if not self.target:
            return
        if hasattr(self.target, 'head'):
            if self.mode == "THROUGH_THE_EYE":
                self.target.head.visible = False
            else:
                self.target.head.visible = True
                
    def handle_scroll(self, delta):
        """Mouse wheel zoom in / out."""
        self.distance = max(2.2, min(14.0, self.distance - delta * 0.8))
        self.orbit_distance = max(2.2, min(14.0, self.orbit_distance - delta * 0.8))
        
    def apply_camera_transform(self, dt):
        if not self.target:
            return
            
        target_pos = self.target.position
        is_humanoid = ("HUMANOID" in getattr(self.target, 'actor_type', ''))
        head_height = 2.45 if is_humanoid else 1.10
        
        # 1. VIEW 1: BACK OF THE BOT (Centered, elevated third-person chase)
        if self.mode == "BACK_OF_BOT":
            target_yaw = self.target.rotation_y
            
            # Smoothly interpolate camera yaw along the shortest angular arc around the circle
            yaw_diff = (target_yaw - self.cam_yaw + 180.0) % 360.0 - 180.0
            self.cam_yaw = (self.cam_yaw + yaw_diff * min(1.0, dt * self.smoothness) + 180.0) % 360.0 - 180.0
            
            rad = math.radians(self.cam_yaw)
            
            # Orbiting smoothly behind the robot at fixed distance (never cuts through body when turning!)
            back_x = -math.sin(rad) * self.distance
            back_z = -math.cos(rad) * self.distance
            
            cam_x = target_pos.x + back_x
            cam_y = target_pos.y + self.height
            cam_z = target_pos.z + back_z
            camera.position = Vec3(cam_x, cam_y, cam_z)
            
            # Aim smoothly looking ahead in the direction the camera and robot are facing
            look_ahead_x = math.sin(rad) * 6.5
            look_ahead_z = math.cos(rad) * 6.5
            look_target = Vec3(target_pos.x + look_ahead_x, target_pos.y + 1.8, target_pos.z + look_ahead_z)
            camera.look_at(look_target)
            
        # 2. VIEW 2: THROUGH THE EYE (True first-person vision directly from the cyan eyes)
        elif self.mode == "THROUGH_THE_EYE":
            rad = math.radians(self.target.rotation_y)
            # Position slightly in front of the face
            fx = math.sin(rad) * 0.55
            fz = math.cos(rad) * 0.55
            
            camera.position = Vec3(target_pos.x + fx, target_pos.y + head_height, target_pos.z + fz)
            
            # Head tracking yaw
            head_yaw = self.target.rotation_y
            if hasattr(self.target, 'head') and hasattr(self.target.head, 'rotation_y'):
                head_yaw += self.target.head.rotation_y
                
            camera.rotation_y = head_yaw
            camera.rotation_x = 2.0 # Gentle forward road gaze
            camera.rotation_z = 0.0
            
        # 3. VIEW 3: 360-DEGREE FREE ORBIT VIEW
        elif self.mode == "FREE_360_ORBIT":
            # Left or Right mouse drag rotates 360° smoothly
            if mouse.right or mouse.left:
                self.orbit_yaw += mouse.velocity[0] * 260
                self.orbit_pitch = max(2.0, min(85.0, self.orbit_pitch - mouse.velocity[1] * 200))
                
            if held_keys['q']:
                self.orbit_yaw -= 75 * dt
            if held_keys['e']:
                self.orbit_yaw += 75 * dt
                
            rad_yaw = math.radians(self.orbit_yaw)
            rad_pitch = math.radians(self.orbit_pitch)
            
            ox = math.sin(rad_yaw) * math.cos(rad_pitch) * self.orbit_distance
            oy = math.sin(rad_pitch) * self.orbit_distance
            oz = -math.cos(rad_yaw) * math.cos(rad_pitch) * self.orbit_distance
            
            focal_y = target_pos.y + (1.4 if is_humanoid else 0.6)
            desired_pos = Vec3(target_pos.x + ox, focal_y + oy, target_pos.z + oz)
            camera.position = camera.position + (desired_pos - camera.position) * min(1.0, dt * 10.0)
            camera.look_at(Vec3(target_pos.x, focal_y, target_pos.z))
            
        # 4. VIEW 4: ISOMETRIC ADAS
        elif self.mode == "ISOMETRIC_ADAS":
            desired_pos = Vec3(target_pos.x + 9.5, target_pos.y + 8.5, target_pos.z - 8.5)
            camera.position = camera.position + (desired_pos - camera.position) * min(1.0, dt * 6.0)
            camera.look_at(Vec3(target_pos.x, target_pos.y + 1.2, target_pos.z + 2.5))
            
        # 5. VIEW 5: TOP DOWN
        elif self.mode == "TOP_DOWN":
            desired_pos = Vec3(target_pos.x, target_pos.y + 18.0, target_pos.z + 1.0)
            camera.position = camera.position + (desired_pos - camera.position) * min(1.0, dt * 6.0)
            camera.rotation = (85, 0, 0)
            
    def update(self, dt):
        self.apply_camera_transform(dt)
