"""
Sensor Manager Module: Orchestrates the multi-modal sensor suite (Camera, Radar, LiDAR),
dynamic laser tracking, and provides consolidated telemetry to the dashboard.
"""
from ursina import Entity, Vec3
from sensors.lidar import LiDARVisualizer
from sensors.radar import RadarVisualizer
from sensors.camera import CameraFrustumVisualizer
from sensors.laser_tracker import TargetLockTracker
from sensors.perception_failure import PerceptionFailureInjector
import math

class SensorManager(Entity):
    def __init__(self, robot, **kwargs):
        super().__init__(**kwargs)
        self.robot = robot
        
        # Instantiate visualizers
        self.lidar = LiDARVisualizer(robot=self.robot, parent=self)
        self.radar = RadarVisualizer(robot=self.robot, parent=self)
        self.camera_frustum = CameraFrustumVisualizer(robot=self.robot, parent=self)
        self.laser_tracker = TargetLockTracker(max_targets=8, parent=self)
        
        # Perception failure and uncertainty injector
        self.failure_injector = PerceptionFailureInjector()
        self.perceived_actors = []
        
        # Telemetry metrics
        self.closest_object_type = "NONE"
        self.closest_object_distance = 999.0
        self.threat_level = "SAFE"
        self.detected_count = 0
        self.vision_range = 16.0
        self.detection_confidence = 99
        self.weather_condition = "CLEAR"
        
    def cycle_failure_mode(self):
        return self.failure_injector.cycle_mode()
        
    def get_failure_mode_details(self):
        return self.failure_injector.get_details()
        
    def update_sensors(self, raw_actors, dt, weather_sys=None):
        if weather_sys:
            self.vision_range = weather_sys.get_visibility_range()
            self.detection_confidence = weather_sys.get_detection_confidence()
            self.weather_condition = weather_sys.current_weather
            # Scale camera optical frustum to match weather visibility
            if hasattr(self.camera_frustum, 'frustum'):
                self.camera_frustum.frustum.scale = (self.vision_range * 0.9, self.vision_range, self.vision_range * 0.55)
                self.camera_frustum.frustum.z = self.vision_range / 2
        
        # 1. Apply perception failure / uncertainty injection
        self.perceived_actors = self.failure_injector.filter_perceived_actors(
            self.robot, raw_actors, dt, weather_sys=weather_sys
        )
        
        # Override confidence if high uncertainty mode is active
        if self.failure_injector.simulated_conf_override is not None:
            self.detection_confidence = self.failure_injector.simulated_conf_override
        
        # 2. Update individual sensor sweeps
        self.lidar.update_sweep(dt)
        self.radar.update_radar(dt)
        self.camera_frustum.update_frustum(dt)
        
        # 3. Update dynamic laser targeting beams & bounding boxes
        self.laser_tracker.update_targets(
            self.robot, 
            self.perceived_actors, 
            dt, 
            weather_sys=weather_sys,
            conf_override=self.failure_injector.simulated_conf_override,
            active_failure_mode=self.failure_injector.active_mode
        )
        
        # 4. Compute closest obstacle telemetry from perceived actors
        min_dist = 999.0
        nearest_type = "NONE"
        detected_count = 0
        
        max_detect_limit = max(14.0, self.vision_range)
        for actor in self.perceived_actors:
            dx = actor.x - self.robot.x
            dz = actor.z - self.robot.z
            dist = math.sqrt(dx**2 + dz**2)
            if dist < max_detect_limit:
                detected_count += 1
                if dist < min_dist:
                    min_dist = dist
                    nearest_type = actor.actor_type
                    
        self.closest_object_distance = min_dist
        self.closest_object_type = nearest_type
        self.detected_count = detected_count
        
        if min_dist < 3.2:
            self.threat_level = "CRITICAL (STOP)"
        elif min_dist < 6.5:
            self.threat_level = "WARNING (YIELD)"
        elif min_dist < 14.0:
            self.threat_level = "TRACKING (CAUTION)"
        else:
            self.threat_level = "CLEAR"

