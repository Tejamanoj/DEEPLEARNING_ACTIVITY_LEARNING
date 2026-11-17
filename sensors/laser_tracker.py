"""
Laser Tracker Module: High-tech ADAS targeting laser beams,
dynamic 3D bounding boxes, and live distance/confidence billboard tags
locking onto detected pedestrians, vehicles, and obstacles in real-time.
"""
from ursina import Entity, color, Vec3, Text, camera
from ursina.color import rgb32, rgba32
from environment.common_models import get_cylinder
import math

class TargetLockTracker(Entity):
    def __init__(self, max_targets=8, detection_range=16.0, **kwargs):
        super().__init__(**kwargs)
        self.max_targets = max_targets
        self.detection_range = detection_range
        self.is_enabled = True
        
        cyl = get_cylinder()
        
        # Pool of pre-allocated laser beams, bounding boxes, and billboard tags
        self.target_slots = []
        for i in range(max_targets):
            # 1. 3D Laser Beam (Cylinder connecting robot sensor to target)
            laser_beam = Entity(
                parent=self,
                model=cyl,
                scale=(0.045, 1.0, 0.045),
                color=rgb32(0, 255, 200),
                enabled=False
            )
            # Pulsing core glow inside beam
            laser_glow = Entity(
                parent=laser_beam,
                model=cyl,
                scale=(1.8, 1.0, 1.8),
                color=rgba32(0, 255, 255, 80)
            )
            
            # 2. 3D Bounding Box (Wireframe cube enclosing the target)
            bbox = Entity(
                parent=self,
                model='wireframe_cube',
                scale=(1.2, 2.0, 1.2),
                color=rgb32(0, 255, 200),
                enabled=False
            )
            
            # 3. Floating 3D Billboard Tag
            tag = Text(
                text="[DETECTED]",
                scale=7.5,
                color=rgb32(0, 255, 200),
                origin=(0, -0.5),
                enabled=False
            )
            
            self.target_slots.append({
                "beam": laser_beam,
                "glow": laser_glow,
                "bbox": bbox,
                "tag": tag,
                "active": False
            })
            
    def toggle(self):
        self.is_enabled = not self.is_enabled
        self.enabled = self.is_enabled
        for slot in self.target_slots:
            slot["beam"].enabled = False
            slot["bbox"].enabled = False
            slot["tag"].enabled = False
            slot["active"] = False
        return self.is_enabled
        
    def update_targets(self, robot, actors, dt, weather_sys=None, conf_override=None, active_failure_mode="NORMAL"):
        if not self.is_enabled or not robot:
            return
            
        robot_sensor_pos = Vec3(robot.x, robot.y + 0.95, robot.z)
        
        # Determine weather-adapted vision threshold & confidence
        effective_range = self.detection_range
        base_confidence = 98.0
        weather_label = ""
        
        if weather_sys:
            effective_range = weather_sys.get_visibility_range()
            base_confidence = weather_sys.get_detection_confidence()
            weather_label = f"[{weather_sys.current_weather}]"
            
        if conf_override is not None:
            base_confidence = conf_override
        
        heading_rad = math.radians(robot.rotation_y)
        fwd_vec = Vec3(math.sin(heading_rad), 0, math.cos(heading_rad))
        torch_on = getattr(robot, 'torch_enabled', True)
        
        # 1. Calculate distances from robot to all scene actors within visibility
        detected_actors = []
        for actor in actors:
            dx = actor.x - robot.x
            dz = actor.z - robot.z
            dist = math.sqrt(dx**2 + dz**2)
            
            # Check if actor is within optical sight range or illuminated by torch spotlight
            is_in_torch = False
            if dist > 0.01:
                fwd_dot = (dx * fwd_vec.x + dz * fwd_vec.z) / dist
                if fwd_dot > 0.72 and torch_on: # Within ~44° forward torch beam
                    is_in_torch = True
                    
            actor_vis_limit = effective_range
            actor_conf = base_confidence
            
            if is_in_torch and conf_override is None:
                actor_vis_limit = max(effective_range, 13.5)
                actor_conf = max(base_confidence, 92.0)
                
            if dist <= actor_vis_limit:
                detected_actors.append((dist, actor, actor_conf, is_in_torch))
                
        # Sort by closest first
        detected_actors.sort(key=lambda item: item[0])
        
        # 2. Update tracking slots
        slot_idx = 0
        for dist, actor, actor_conf, is_in_torch in detected_actors[:self.max_targets]:
            slot = self.target_slots[slot_idx]
            slot["active"] = True
            
            actor_center = Vec3(actor.x, actor.y + actor.height * 0.5, actor.z)
            is_phantom = getattr(actor, 'is_phantom', False)
            is_misclassified = "[MISCLASSIFIED" in getattr(actor, 'name', '')
            
            # Determine threat color based on distance: GREEN -> YELLOW -> RED
            if is_phantom:
                theme_color = rgb32(255, 140, 20) # ORANGE
                status_label = "PHANTOM GHOST DETECTION"
                beam_thickness = 0.05
            elif active_failure_mode == "HIGH_UNCERTAINTY":
                theme_color = rgb32(210, 80, 255) # MAGENTA / UNCERTAINTY
                status_label = "HIGH UNCERTAINTY"
                beam_thickness = 0.05
            elif is_misclassified:
                theme_color = rgb32(255, 100, 180) # PINK / MISCLASSIFICATION
                status_label = "LABEL CONFUSION"
                beam_thickness = 0.055
            elif dist < 3.2:
                # Critical Danger Stop: RED
                theme_color = rgb32(255, 30, 30)
                status_label = "CRITICAL PROXIMITY - STOP"
                beam_thickness = 0.075 + 0.02 * math.sin(actor.walk_time if hasattr(actor, 'walk_time') else 0 * 8.0)
            elif dist < 6.5:
                # Warning / Yield: YELLOW
                theme_color = rgb32(255, 200, 20)
                status_label = "CAUTION - YIELD"
                beam_thickness = 0.055
            else:
                # Safe Tracking: GREEN
                theme_color = rgb32(0, 240, 140)
                status_label = "TRACKING SAFE"
                beam_thickness = 0.04
                
            # A. Position & orient 3D Laser Beam from robot to actor
            beam = slot["beam"]
            beam.enabled = True
            beam.color = theme_color
            slot["glow"].color = rgba32(theme_color.r * 255, theme_color.g * 255, theme_color.b * 255, 90)
            
            # Midpoint between robot and actor
            midpoint = (robot_sensor_pos + actor_center) * 0.5
            beam.position = midpoint
            
            # Length and orientation
            delta = actor_center - robot_sensor_pos
            actual_dist = delta.length()
            beam.scale = (beam_thickness, actual_dist, beam_thickness)
            
            # Look at actor center and align cylinder vertical axis (Panda3D cylinders point up along Y)
            beam.look_at(actor_center)
            beam.rotation_x += 90 # Align cylinder Y axis with look vector
            
            # B. 3D Bounding Box around actor (Dynamic Green/Yellow/Red wireframe)
            bbox = slot["bbox"]
            bbox.enabled = True
            bbox.color = theme_color
            bbox.position = actor_center
            
            # Fitted bounding box size per actor type
            actor_type = getattr(actor, 'actor_type', '')
            if actor_type == 'VEHICLE':
                box_w, box_h, box_d = 2.2, 1.6, 4.4
            elif actor_type == 'BICYCLE':
                box_w, box_h, box_d = 0.8, 1.8, 1.8
            elif actor_type == 'OBSTACLE':
                box_w, box_h, box_d = 0.9, 1.25, 0.9
            else: # PEDESTRIAN
                box_w, box_h, box_d = 0.85, 2.0, 0.85
                
            # Jitter bounding box in high uncertainty mode
            if active_failure_mode == "HIGH_UNCERTAINTY":
                jitter_amt = math.sin(dist * 5.0 + (robot.walk_time if hasattr(robot, 'walk_time') else 0) * 10.0) * 0.18
                box_w += jitter_amt
                box_d += jitter_amt
                bbox.position = Vec3(actor_center.x + jitter_amt * 0.3, actor_center.y, actor_center.z)
                
            bbox.scale = (box_w, box_h, box_d)
                
            if hasattr(actor, 'rotation_y'):
                bbox.rotation_y = actor.rotation_y
                
            # C. Floating 3D Billboard Tag
            tag = slot["tag"]
            tag.enabled = True
            tag.color = theme_color
            tag.position = Vec3(actor.x, actor.y + actor.height + 0.35, actor.z)
            torch_tag = " (TORCH)" if is_in_torch else ""
            
            if is_phantom:
                tag.text = f"[GHOST OBSTACLE: {dist:.1f}m | Conf: 88% (HALLUCINATION)]"
            elif is_misclassified:
                tag.text = f"[PED -> CLASSIFIED AS OBSTACLE: {dist:.1f}m | Conf: 91%]"
            elif active_failure_mode == "HIGH_UNCERTAINTY":
                tag.text = f"[{actor.actor_type}: {dist:.1f}m | UNCERTAIN Conf: {int(actor_conf)}%]"
            else:
                tag.text = f"[{actor.actor_type}: {dist:.1f}m | Conf: {int(actor_conf)}%{torch_tag}]"
                
            # Always face camera
            tag.look_at(camera.world_position)
            tag.rotation_y += 180 # Text faces camera properly
            
            slot_idx += 1
            
        # Hide remaining unused slots
        while slot_idx < self.max_targets:
            slot = self.target_slots[slot_idx]
            slot["beam"].enabled = False
            slot["bbox"].enabled = False
            slot["tag"].enabled = False
            slot["active"] = False
            slot_idx += 1

