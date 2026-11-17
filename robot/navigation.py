"""
Navigation Module: Predefined sidewalk waypoint route follower,
path geometry tracker, and progress calculation.
"""
from ursina import Vec3
import math

class RouteNavigator:
    def __init__(self, robot, waypoints=None):
        self.robot = robot
        
        self.MISSIONS = [
            {
                "name": "GRAND ZEBRA CROSSWALK MISSION -> TERMINAL #04",
                "waypoints": [
                    Vec3(8.75, 0.45, -6.0),   # Start Depot
                    Vec3(8.75, 0.45, 18.0),   # East sidewalk approach
                    Vec3(8.75, 0.35, 29.5),   # Approach South Zebra ramp
                    Vec3(8.75, 0.35, 32.0),   # Turn into South Zebra Crosswalk
                    Vec3(2.5, 0.12, 32.0),    # Crossing East road lane on zebra stripes
                    Vec3(-2.5, 0.12, 32.0),   # Crossing West road lane on zebra stripes
                    Vec3(-8.75, 0.35, 32.0),  # Arrive at West curb tactile ramp
                    Vec3(-8.75, 0.45, 75.0),  # Cruise along West Sidewalk Tech District
                    Vec3(-8.75, 0.45, 120.0), # Passing West Central Park
                    Vec3(-8.75, 0.35, 156.5), # Approach North Zebra ramp
                    Vec3(-8.75, 0.35, 160.0), # Turn into North Zebra Crosswalk
                    Vec3(-2.5, 0.12, 160.0),  # Crossing West road lane on zebra stripes
                    Vec3(2.5, 0.12, 160.0),   # Crossing East road lane on zebra stripes
                    Vec3(8.75, 0.35, 160.0),  # Arrive at East curb tactile ramp
                    Vec3(8.75, 0.45, 200.0),  # Approach Terminal
                    Vec3(8.75, 0.45, 240.0),  # DELIVERY TARGET HUB #04 (CELEBRATION!)
                ]
            },
            {
                "name": "EAST SIDEWALK DIRECT EXPRESS -> TERMINAL #04",
                "waypoints": [
                    Vec3(8.75, 0.45, -6.0),
                    Vec3(8.75, 0.45, 32.0),
                    Vec3(8.75, 0.45, 80.0),
                    Vec3(8.75, 0.45, 160.0),
                    Vec3(8.75, 0.45, 200.0),
                    Vec3(8.75, 0.45, 240.0), # Destination Terminal #04
                ]
            }
        ]
        
        self.current_mission_idx = 0
        if waypoints is not None:
            self.waypoints = waypoints
        else:
            self.waypoints = self.MISSIONS[self.current_mission_idx]["waypoints"]
            
        self.current_idx = 0
        self.is_active = True
        self.is_finished = False
        self.total_path_length = self._calc_total_length()
        self.base_speed = 1.6 # m/s
        self.target_speed = 1.6 # m/s
        
    def toggle_mission(self):
        """Cycles between Sidewalk Patrol and Zebra Crosswalk mission."""
        self.current_mission_idx = (self.current_mission_idx + 1) % len(self.MISSIONS)
        self.waypoints = self.MISSIONS[self.current_mission_idx]["waypoints"]
        self.reset()
        return self.get_mission_name()
        
    def get_mission_name(self):
        return self.MISSIONS[self.current_mission_idx]["name"]
        
    def _calc_total_length(self):
        total = 0.0
        for i in range(len(self.waypoints) - 1):
            total += (self.waypoints[i+1] - self.waypoints[i]).length()
        return max(1.0, total)
        
    def reset(self):
        self.current_idx = 0
        self.is_active = True
        self.is_finished = False
        self.target_speed = self.base_speed
        if len(self.waypoints) > 0:
            start_pos = self.waypoints[0]
            self.robot.position = (start_pos.x, start_pos.y, start_pos.z)
            self.robot.rotation_y = 0.0
            self.robot.speed = 0.0
            
    def get_progress_percent(self):
        if self.is_finished:
            return 100.0
        pct = (self.current_idx / max(1, len(self.waypoints) - 1)) * 100.0
        return max(0.0, min(99.0, pct))
        
    def update(self, dt):
        """Returns (target_heading, recommended_speed, reached_destination)"""
        if not self.is_active or self.is_finished:
            return (self.robot.rotation_y, 0.0, self.is_finished)
            
        target_pt = self.waypoints[self.current_idx]
        diff_x = target_pt.x - self.robot.x
        diff_z = target_pt.z - self.robot.z
        dist_to_target = math.sqrt(diff_x**2 + diff_z**2)
        
        # Waypoint arrival threshold: tighter on sharp turns to prevent corner cutting
        threshold = 0.55
        if self.current_idx < len(self.waypoints) - 1:
            next_pt = self.waypoints[self.current_idx + 1]
            seg1_angle = math.degrees(math.atan2(diff_x, diff_z))
            seg2_angle = math.degrees(math.atan2(next_pt.x - target_pt.x, next_pt.z - target_pt.z))
            turn_angle = abs((seg2_angle - seg1_angle + 180) % 360 - 180)
            threshold = 0.50 if turn_angle > 25.0 else 0.85
        
        if dist_to_target < threshold:
            if self.current_idx < len(self.waypoints) - 1:
                self.current_idx += 1
                target_pt = self.waypoints[self.current_idx]
                diff_x = target_pt.x - self.robot.x
                diff_z = target_pt.z - self.robot.z
            else:
                self.is_finished = True
                self.robot.status = "DESTINATION REACHED"
                return (self.robot.rotation_y, 0.0, True)
                
        # Calculate target heading (0 deg is along +Z axis)
        target_heading = math.degrees(math.atan2(diff_x, diff_z))
        
        return (target_heading, self.base_speed, False)

