"""
Perception Failure & Uncertainty Injection Module.
Directly implements evaluation requirements for:
- Student 2 Requirement 7: Explain the impact of incorrect, delayed or uncertain perception.
- Student 2 Requirement 8: Discuss safety checks, uncertainty and simulation limitations.

Provides simulated real-world Edge-AI / Deep Learning failure modes:
1. NORMAL: Nominal YOLOv8n-ADAS + LiDAR + Radar sensor fusion.
2. FALSE_NEGATIVE: Deep Neural Network fails to detect closest forward obstacle/pedestrian.
3. FALSE_POSITIVE: Vision system hallucinates a phantom obstacle (ghost detection) on empty path.
4. LATENCY_DELAY: Neural inference queue latency (450ms delay) causing delayed braking reactions.
5. HIGH_UNCERTAINTY: Epistemic model ambiguity (confidence drops to 22-38%, bounding box jitter).
6. MISCLASSIFICATION: Semantic label confusion (pedestrian misclassified as static obstacle).
"""

import math
import random
from collections import deque
from ursina import Vec3
from ursina.color import rgb32, rgba32

class PhantomActor:
    """Simulated ghost detection hallucinated by edge-AI false positive."""
    def __init__(self, x, y, z, actor_type="OBSTACLE", name="GHOST_OBSTACLE"):
        self.x = x
        self.y = y
        self.z = z
        self.height = 1.2
        self.actor_type = actor_type
        self.name = name
        self.is_phantom = True
        self.rotation_y = 0.0

class PerceptionFailureInjector:
    MODES = [
        "NORMAL",
        "FALSE_NEGATIVE",
        "FALSE_POSITIVE",
        "LATENCY_DELAY",
        "HIGH_UNCERTAINTY",
        "MISCLASSIFICATION"
    ]
    
    MODE_DETAILS = {
        "NORMAL": {
            "title": "NOMINAL PERCEPTION",
            "badge": "[MODE: NOMINAL]",
            "color": (80, 255, 120),
            "description": "Nominal YOLOv8n + LiDAR + Radar sensor fusion. All actors tracked correctly.",
            "impact": "Stable trajectory planning, compliant pedestrian yielding & smooth detours."
        },
        "FALSE_NEGATIVE": {
            "title": "FALSE NEGATIVE (MISSED DETECTION)",
            "badge": "[INJECTION: FALSE NEGATIVE]",
            "color": (255, 60, 60),
            "description": "Deep neural network misses forward obstacle/pedestrian (occlusion / glare failure).",
            "impact": "Normal planning fails to brake early! Low-level safety supervisor triggers at 1.5m."
        },
        "FALSE_POSITIVE": {
            "title": "FALSE POSITIVE (PHANTOM GHOST)",
            "badge": "[INJECTION: FALSE POSITIVE]",
            "color": (255, 160, 40),
            "description": "Perception hallucinates a phantom obstacle 2.8m ahead on clear sidewalk.",
            "impact": "Causes sudden 'Phantom Braking' and unnecessary stopping on an empty sidewalk."
        },
        "LATENCY_DELAY": {
            "title": "LATENCY DELAY (450ms LAG)",
            "badge": "[INJECTION: LATENCY DELAY]",
            "color": (255, 220, 50),
            "description": "Edge-AI inference compute backlog introduces a 450ms observation delay.",
            "impact": "Late perception reaction time; delayed braking reduces stopping safety buffer."
        },
        "HIGH_UNCERTAINTY": {
            "title": "HIGH EPISTEMIC UNCERTAINTY",
            "badge": "[INJECTION: UNCERTAINTY]",
            "color": (210, 100, 255),
            "description": "Model ambiguity: Detection confidence drops to 25-38% with bounding box jitter.",
            "impact": "Safety envelope enforces cautious crawl speed (0.5 m/s) due to low confidence."
        },
        "MISCLASSIFICATION": {
            "title": "INCORRECT CLASSIFICATION",
            "badge": "[INJECTION: MISCLASSIFICATION]",
            "color": (255, 100, 180),
            "description": "Semantic classifier confuses pedestrian for static crate/barrel.",
            "impact": "Planner attempts an aggressive lateral detour instead of courteous pedestrian yield!"
        }
    }
    
    def __init__(self):
        self.current_mode_index = 0
        self.active_mode = self.MODES[self.current_mode_index]
        self.latency_queue = deque() # Stores historical actor states for 450ms delay
        self.queue_time = 0.45 # 450ms
        self.safety_supervisor_tripped = False
        self.phantom_actor = PhantomActor(8.75, 0.0, 0.0, "OBSTACLE", "GHOST_OBSTACLE")
        self.uncertainty_jitter_timer = 0.0
        self.simulated_conf_override = None
        
    def cycle_mode(self):
        self.current_mode_index = (self.current_mode_index + 1) % len(self.MODES)
        self.active_mode = self.MODES[self.current_mode_index]
        self.latency_queue.clear()
        self.safety_supervisor_tripped = False
        return self.active_mode
        
    def set_mode(self, mode_name):
        if mode_name in self.MODES:
            self.current_mode_index = self.MODES.index(mode_name)
            self.active_mode = mode_name
            self.latency_queue.clear()
            self.safety_supervisor_tripped = False
            
    def get_details(self):
        return self.MODE_DETAILS[self.active_mode]

    def filter_perceived_actors(self, robot, raw_actors, dt, weather_sys=None):
        """
        Applies active failure injection to the list of raw actors before passing
        to SensorManager, LaserTracker, and SafetyRulesEngine.
        """
        self.uncertainty_jitter_timer += dt
        self.safety_supervisor_tripped = False
        self.simulated_conf_override = None
        
        mode = self.active_mode
        heading_rad = math.radians(robot.rotation_y)
        fwd_vec = Vec3(math.sin(heading_rad), 0, math.cos(heading_rad))
        
        # ── 1. NOMINAL MODE ───────────────────────────────────────────────
        if mode == "NORMAL":
            return list(raw_actors)
            
        # ── 2. FALSE NEGATIVE (Missed closest forward actor) ──────────────
        elif mode == "FALSE_NEGATIVE":
            # Find the closest forward actor in path
            closest_fwd_actor = None
            closest_dist = 999.0
            
            for actor in raw_actors:
                dx = actor.x - robot.x
                dz = actor.z - robot.z
                dist = math.sqrt(dx**2 + dz**2)
                if dist < 0.01:
                    continue
                fwd_dot = (dx * fwd_vec.x + dz * fwd_vec.z) / dist
                if fwd_dot > 0.55 and dist < 8.0:
                    if dist < closest_dist:
                        closest_dist = dist
                        closest_fwd_actor = actor
                        
            # If closest obstacle is too close (< 1.6m), trigger low-level safety supervisor!
            if closest_fwd_actor and closest_dist < 1.6:
                self.safety_supervisor_tripped = True
                # In fail-safe mode, tactile/ultrasonic sensor catches it at the last second
                return list(raw_actors)
                
            # Otherwise drop closest forward actor from AI perception!
            filtered = [a for a in raw_actors if a != closest_fwd_actor]
            return filtered
            
        # ── 3. FALSE POSITIVE (Phantom ghost obstacle) ────────────────────
        elif mode == "FALSE_POSITIVE":
            # Synthesize a phantom obstacle 2.8m in front of robot
            self.phantom_actor.x = robot.x + fwd_vec.x * 2.8
            self.phantom_actor.y = 0.0
            self.phantom_actor.z = robot.z + fwd_vec.z * 2.8
            self.phantom_actor.actor_type = "OBSTACLE"
            self.phantom_actor.name = "GHOST_OBSTACLE"
            return list(raw_actors) + [self.phantom_actor]
            
        # ── 4. LATENCY DELAY (450ms observation delay buffer) ─────────────
        elif mode == "LATENCY_DELAY":
            # Snapshot current positions
            snapshot = []
            for a in raw_actors:
                class ActorSnapshot:
                    pass
                s = ActorSnapshot()
                s.x = a.x
                s.y = getattr(a, 'y', 0.0)
                s.z = a.z
                s.height = getattr(a, 'height', 1.8)
                s.actor_type = getattr(a, 'actor_type', 'PEDESTRIAN')
                s.name = getattr(a, 'name', 'ACTOR')
                s.rotation_y = getattr(a, 'rotation_y', 0.0)
                snapshot.append(s)
                
            self.latency_queue.append((snapshot, dt))
            
            # Accumulate time in queue until 0.45s reached
            accum_t = sum(item[1] for item in self.latency_queue)
            if accum_t >= self.queue_time and len(self.latency_queue) > 1:
                delayed_snapshot, _ = self.latency_queue.popleft()
                return delayed_snapshot
            else:
                return list(raw_actors)
                
        # ── 5. HIGH UNCERTAINTY (Low confidence & jitter) ─────────────────
        elif mode == "HIGH_UNCERTAINTY":
            # Jitter confidence between 22% and 38%
            conf_jitter = 30.0 + 8.0 * math.sin(self.uncertainty_jitter_timer * 12.0)
            self.simulated_conf_override = max(18.0, min(42.0, conf_jitter))
            return list(raw_actors)
            
        # ── 6. MISCLASSIFICATION ──────────────────────────────────────────
        elif mode == "MISCLASSIFICATION":
            # Wrap actors: if PEDESTRIAN, present as OBSTACLE to planner
            altered = []
            for a in raw_actors:
                if getattr(a, 'actor_type', '') == 'PEDESTRIAN':
                    class MisclassifiedActor:
                        pass
                    m = MisclassifiedActor()
                    m.x = a.x
                    m.y = getattr(a, 'y', 0.0)
                    m.z = a.z
                    m.height = getattr(a, 'height', 1.8)
                    m.actor_type = "OBSTACLE" # Classified as static crate/barrel
                    m.name = f"{getattr(a, 'name', 'PED')} [MISCLASSIFIED AS OBSTACLE]"
                    m.rotation_y = getattr(a, 'rotation_y', 0.0)
                    altered.append(m)
                else:
                    altered.append(a)
            return altered
            
        return list(raw_actors)

