"""
Safety Rules & Decision Module: Evaluates forward corridor obstacles,
executes autonomous obstacle detour avoidance maneuvers,
and enforces safety boundaries with automated roadway intrusion protection.
"""
from ursina import Vec3
import math

class SafetyRulesEngine:
    def __init__(self):
        self.curb_threshold_x = 6.35
        self.sidewalk_safe_center_x = 8.75
        self.crosswalk_z_min = 28.5
        self.crosswalk_z_max = 35.5
        # Dual authorized zebra crosswalk zones across 280m city map
        self.crosswalks = [
            (28.5, 35.5),   # South Crosswalk at z=32
            (156.5, 163.5), # North Crosswalk at z=160
        ]
        
        # State
        self.is_on_roadway = False
        self.is_crossing_zebra = False
        self.roadway_breach_active = False
        self.forward_path_blocked = False
        self.obstacle_ahead_distance = 999.0
        self.blocking_actor_name = "NONE"
        self.safety_action = "PROCEED_SAFE"
        self.active_alert_message = "ALL SAFETY RULES COMPLIANT"
        self.emergency_return_heading = 0.0
        
        # Detour avoidance state
        self.is_detouring = False
        self.detour_stage = 0 # 0: stop & scan, 1: steer bypass, 2: return
        self.detour_target_x = 7.35 # Left clear sidewalk corridor
        self.detour_obstacle_z = 0.0
        self.detour_pause_timer = 0.0
        self.chosen_side = "LEFT"
        self._ped_yield_timer = 0.0
        
        self.rule_statuses = {
            "RULE_1_SIDEWALK_BOUNDS": "COMPLIANT",
            "RULE_2_ZEBRA_CROSSING_ONLY": "COMPLIANT",
            "RULE_3_PEDESTRIAN_BUFFER": "COMPLIANT",
            "RULE_4_FORWARD_CLEARANCE": "COMPLIANT",
            "RULE_5_SPEED_COMPLIANCE": "COMPLIANT",
        }
        
    def evaluate(self, robot, actors, dt, failure_injector=None):
        pos = robot.position
        heading_rad = math.radians(robot.rotation_y)
        fwd_vec = Vec3(math.sin(heading_rad), 0, math.cos(heading_rad))
        right_vec = Vec3(math.cos(heading_rad), 0, -math.sin(heading_rad))
        
        # 0. LOW-LEVEL SAFETY SUPERVISOR (FAIL-SAFE PROXIMITY BARRIER)
        if failure_injector and getattr(failure_injector, 'safety_supervisor_tripped', False):
            self.safety_action = "EMERGENCY_STOP"
            self.active_alert_message = (
                "⚠️ FAIL-SAFE SUPERVISOR OVERRIDE! Neural perception missed obstacle; "
                "hardware proximity barrier engaged emergency stop! ⚠️"
            )
            self.rule_statuses["RULE_4_FORWARD_CLEARANCE"] = "OVERRIDE - EMERGENCY PROXIMITY"
            return ("EMERGENCY_STOP", 0.0, robot.rotation_y)
        
        # 1. RULES 1 & 2: SIDEWALK BOUNDARIES & STRICT ZEBRA CROSSING ENFORCEMENT
        # Right sidewalk is x >= 6.35, Left sidewalk is x <= -6.35
        # Road lane is between x = -6.35 and x = 6.35
        is_on_right_sidewalk = (pos.x >= self.curb_threshold_x)
        is_on_left_sidewalk  = (pos.x <= -self.curb_threshold_x)
        is_on_any_sidewalk   = is_on_right_sidewalk or is_on_left_sidewalk
        is_in_road_lane      = not is_on_any_sidewalk
        # Zebra zones have generous margin (±4.0m) to allow smooth entry and exit from curb ramps
        is_in_zebra_crossing = any((z_min - 0.75) <= pos.z <= (z_max + 0.75) for z_min, z_max in self.crosswalks)
        
        if is_in_road_lane:
            self.is_on_roadway = True
            if is_in_zebra_crossing:
                # LEGAL ROAD CROSSING AT DESIGNATED ZEBRA CROSSING!
                self.is_crossing_zebra = True
                self.roadway_breach_active = False
                self.rule_statuses["RULE_1_SIDEWALK_BOUNDS"] = "COMPLIANT (ZEBRA CROSSING)"
                self.rule_statuses["RULE_2_ZEBRA_CROSSING_ONLY"] = "AUTHORIZED - ZEBRA CROSSWALK"
            else:
                # ILLEGAL ROAD CROSSING OUTSIDE ZEBRA CROSSING!
                self.is_crossing_zebra = False
                self.roadway_breach_active = True
                self.rule_statuses["RULE_1_SIDEWALK_BOUNDS"] = "VIOLATION - IN ROAD"
                self.rule_statuses["RULE_2_ZEBRA_CROSSING_ONLY"] = "CRITICAL VIOLATION: CROSSING OUTSIDE ZEBRA ZONE!"
                self.active_alert_message = "CRITICAL VIOLATION: ILLEGAL ROAD CROSSING! MUST CROSS AT ZEBRA CROSSINGS (z: 32m or 160m)"
                self.safety_action = "EMERGENCY_RETURN"
                
                safe_target_x = self.sidewalk_safe_center_x if pos.x >= 0 else -self.sidewalk_safe_center_x
                dx = safe_target_x - pos.x
                dz = 0.5
                self.emergency_return_heading = math.degrees(math.atan2(dx, dz))
                return ("EMERGENCY_RETURN", 0.9, self.emergency_return_heading)
        else:
            self.is_on_roadway = False
            self.is_crossing_zebra = False
            self.roadway_breach_active = False
            self.rule_statuses["RULE_1_SIDEWALK_BOUNDS"] = "COMPLIANT"
            self.rule_statuses["RULE_2_ZEBRA_CROSSING_ONLY"] = "STANDBY - SIDEWALK ZONE"
            
        # 2. DETOUR AVOIDANCE STATE MACHINE
        # Detour is ONLY active on sidewalks. Never detour laterally off a zebra crossing!
        if self.is_detouring and not is_in_road_lane:
            center_x = self.sidewalk_safe_center_x if pos.x >= 0 else -self.sidewalk_safe_center_x
            # If past the obstacle z, steer back to sidewalk center
            if pos.z >= self.detour_obstacle_z + 2.5:
                self.detour_stage = 2
                dx = center_x - pos.x
                return_heading = math.degrees(math.atan2(dx, 3.5))
                if abs(pos.x - center_x) < 0.28:
                    # Detour complete!
                    self.is_detouring = False
                    self.detour_stage = 0
                    self.safety_action = "PROCEED_SAFE"
                    self.active_alert_message = "DETOUR COMPLETE: BACK ON CENTERLINE"
                    if hasattr(robot, 'look_at_target'):
                        robot.look_at_target(None)
                    return ("PROCEED_SAFE", 1.6, robot.rotation_y)
                else:
                    self.safety_action = "DETOUR_RETURN"
                    self.active_alert_message = f"DETOUR COMPLETE: RETURNING FROM {self.chosen_side} TO CENTER"
                    return ("DETOUR_RETURN", 1.3, return_heading)

            # Stage 0: Stop, gaze at obstacle & select path
            if self.detour_stage == 0:
                self.detour_pause_timer -= dt
                dx = self.detour_target_x - pos.x
                detour_heading = math.degrees(math.atan2(dx, 3.5))
                if self.detour_pause_timer > 0:
                    self.safety_action = "DETOUR_AVOIDANCE"
                    self.active_alert_message = f"OBSTACLE STOP: EVALUATING & SELECTING {self.chosen_side} SIDE"
                    self.rule_statuses["RULE_4_FORWARD_CLEARANCE"] = "STOPPING_TO_EVALUATE"
                    return ("DETOUR_AVOIDANCE", 0.0, detour_heading)
                else:
                    self.detour_stage = 1

            # Stage 1: Bypass obstacle along chosen side
            if self.detour_stage == 1:
                dx = self.detour_target_x - pos.x
                detour_heading = math.degrees(math.atan2(dx, 3.5))
                self.safety_action = "DETOUR_AVOIDANCE"
                self.active_alert_message = f"AVOIDANCE MANEUVER: BYPASSING {self.blocking_actor_name} VIA {self.chosen_side} SIDE"
                self.rule_statuses["RULE_4_FORWARD_CLEARANCE"] = "DETOURING"
                return ("DETOUR_AVOIDANCE", 1.25, detour_heading)
        elif self.is_detouring and is_in_road_lane:
            # On crosswalk, cancel detour so robot stays straight on zebra stripes!
            self.is_detouring = False
            self.detour_stage = 0
                    
        # 3. EVALUATE FORWARD CORRIDOR OBSTACLES
        self.forward_path_blocked = False
        min_fwd_dist = 999.0
        blocking_actor = None
        corridor_half_width = 0.60
        
        for actor in actors:
            delta_x = actor.x - pos.x
            delta_z = actor.z - pos.z
            fwd_dist = delta_x * fwd_vec.x + delta_z * fwd_vec.z
            lateral_dist = delta_x * right_vec.x + delta_z * right_vec.z
            
            # Forward corridor detection cone
            if 0.15 < fwd_dist < 6.5 and abs(lateral_dist) < corridor_half_width:
                if fwd_dist < min_fwd_dist:
                    min_fwd_dist = fwd_dist
                    blocking_actor = actor
                    
        self.obstacle_ahead_distance = min_fwd_dist
        if blocking_actor:
            self.blocking_actor_name = getattr(blocking_actor, 'actor_type', 'OBSTACLE')
        else:
            self.blocking_actor_name = "NONE"
            
        # 4. DECISION LOGIC: VEHICLE STOP vs OBSTACLE DETOUR vs PEDESTRIAN YIELD
        if blocking_actor and min_fwd_dist < 5.0:
            self.forward_path_blocked = True
            
            # VEHICLE in path: Absolute STOP! Wait until vehicle crosses!
            if self.blocking_actor_name == "VEHICLE":
                self.safety_action = "EMERGENCY_STOP"
                self.active_alert_message = f"APPROACHING VEHICLE DETECTED ({min_fwd_dist:.1f}m) -> WAITING FOR VEHICLE TO PASS"
                self.rule_statuses["RULE_4_FORWARD_CLEARANCE"] = "YIELD_TO_VEHICLE"
                if hasattr(robot, 'look_at_target'):
                    robot.look_at_target(Vec3(blocking_actor.x, 0.8, blocking_actor.z))
                return ("EMERGENCY_STOP", 0.0, robot.rotation_y)
            
            # If on zebra crosswalk: NEVER detour sideways off the zebra stripes! Stop and wait!
            if is_in_road_lane:
                if min_fwd_dist < 2.0:
                    self.safety_action = "EMERGENCY_STOP"
                    self.active_alert_message = f"CROSSWALK CLEARANCE: YIELDING TO PEDESTRIAN ({min_fwd_dist:.1f}m)"
                    return ("EMERGENCY_STOP", 0.0, robot.rotation_y)
                else:
                    self.safety_action = "YIELD_DECELERATE"
                    self.active_alert_message = f"CROSSWALK CLEARANCE: SLOWING DOWN ({min_fwd_dist:.1f}m)"
                    return ("YIELD_DECELERATE", 0.4, robot.rotation_y)
            
            # If obstacle (barrel/crate) on sidewalk, STOP & SELECT CLEAR ALTERNATE SIDE!
            if self.blocking_actor_name == "OBSTACLE":
                self.is_detouring = True
                self.detour_stage = 0 # Stage 0: Stop & evaluate
                self.detour_pause_timer = 0.85 # Stop for 0.85 seconds
                self.detour_obstacle_z = blocking_actor.z
                
                # Dynamic side selection for current sidewalk:
                if pos.x >= 0:
                    # East sidewalk: center is 8.75. Left is 7.35 (inner), Right is 10.15 (outer)
                    obs_x = blocking_actor.x
                    left_threats = sum(1 for a in actors if a != blocking_actor and abs(a.z - pos.z) < 6.0 and a.x < 8.75)
                    if obs_x >= 8.75:
                        self.chosen_side = "LEFT" if left_threats == 0 else "RIGHT"
                        self.detour_target_x = 7.35 if left_threats == 0 else 10.15
                    else:
                        self.chosen_side = "RIGHT"
                        self.detour_target_x = 10.15
                else:
                    # West sidewalk: center is -8.75. Left is -10.15 (outer), Right is -7.35 (inner)
                    obs_x = blocking_actor.x
                    if obs_x <= -8.75:
                        self.chosen_side = "RIGHT"
                        self.detour_target_x = -7.35
                    else:
                        self.chosen_side = "LEFT"
                        self.detour_target_x = -10.15
                
                dx = self.detour_target_x - pos.x
                detour_heading = math.degrees(math.atan2(dx, 3.5))
                self.safety_action = "DETOUR_AVOIDANCE"
                self.active_alert_message = f"OBSTACLE DETECTED ({min_fwd_dist:.1f}m) -> STOPPING & SELECTING {self.chosen_side} SIDE"
                
                if hasattr(robot, 'look_at_target'):
                    robot.look_at_target(Vec3(blocking_actor.x, 1.2, blocking_actor.z))
                    
                return ("DETOUR_AVOIDANCE", 0.0, detour_heading)
                
            # If pedestrian on sidewalk, yield politely or detour if blocked for >1.5s
            elif self.blocking_actor_name == "PEDESTRIAN":
                self._ped_yield_timer += dt
                if min_fwd_dist < 2.0:
                    if self._ped_yield_timer < 1.5:
                        self.safety_action = "EMERGENCY_STOP"
                        self.active_alert_message = f"PEDESTRIAN NEARBY ({min_fwd_dist:.1f}m) -> COURTEOUS YIELD STOP"
                        if hasattr(robot, 'look_at_target'):
                            robot.look_at_target(Vec3(blocking_actor.x, 1.4, blocking_actor.z))
                        return ("EMERGENCY_STOP", 0.0, robot.rotation_y)
                    else:
                        # Stationary pedestrian on path: smoothly detour around them
                        self.is_detouring = True
                        self.detour_stage = 1
                        self.detour_obstacle_z = blocking_actor.z
                        if pos.x >= 0:
                            self.chosen_side = "LEFT" if blocking_actor.x >= 8.75 else "RIGHT"
                            self.detour_target_x = 7.35 if self.chosen_side == "LEFT" else 10.15
                        else:
                            self.chosen_side = "RIGHT" if blocking_actor.x <= -8.75 else "LEFT"
                            self.detour_target_x = -7.35 if self.chosen_side == "RIGHT" else -10.15
                        dx = self.detour_target_x - pos.x
                        detour_heading = math.degrees(math.atan2(dx, 3.5))
                        self.safety_action = "DETOUR_AVOIDANCE"
                        self.active_alert_message = f"PEDESTRIAN STATIONARY -> BYPASSING VIA {self.chosen_side} SIDE"
                        return ("DETOUR_AVOIDANCE", 0.9, detour_heading)
                else:
                    self._ped_yield_timer = 0.0
                    self.safety_action = "YIELD_DECELERATE"
                    self.active_alert_message = f"PEDESTRIAN IN PATH ({min_fwd_dist:.1f}m) -> SLOWING DOWN"
                    return ("YIELD_DECELERATE", 0.5, robot.rotation_y)
                    
        # PATH CLEAR
        self.rule_statuses["RULE_4_FORWARD_CLEARANCE"] = "COMPLIANT"
        self.rule_statuses["RULE_3_PEDESTRIAN_BUFFER"] = "COMPLIANT"
        
        # Uncertainty speed throttling safety policy
        if failure_injector and getattr(failure_injector, 'active_mode', '') == 'HIGH_UNCERTAINTY':
            self.rule_statuses["RULE_5_SPEED_COMPLIANCE"] = "CAUTIOUS CRAWL (UNCERTAINTY CAP: 0.5 m/s)"
            self.active_alert_message = "HIGH UNCERTAINTY INJECTED: Epistemic ambiguity caps speed to 0.5 m/s"
            self.safety_action = "PROCEED_SAFE"
            return ("PROCEED_SAFE", 0.35, robot.rotation_y)
            
        self.safety_action = "PROCEED_SAFE"
        self.active_alert_message = "PATH CLEAR - ALL SAFETY RULES COMPLIANT"
        return ("PROCEED_SAFE", 1.6, robot.rotation_y)
