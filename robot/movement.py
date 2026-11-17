"""
Movement Module: Handles robot physics, acceleration, braking,
steering smoothing, reverse gear, and omnidirectional manual control.
"""
from ursina import time, held_keys, Vec3
import math

class RobotController:
    def __init__(self, robot):
        self.robot = robot
        self.mode = "AUTO" # "AUTO" or "MANUAL"
        
        # Dynamics parameters
        self.max_forward_speed = 2.4 # m/s (~8.6 km/h)
        self.max_reverse_speed = 1.4 # m/s
        self.accel_rate = 3.5
        self.brake_rate = 6.0
        self.turn_speed = 140.0 # deg/sec
        
        # Telemetry
        self.current_speed = 0.0
        self.target_speed = 1.6
        self.heading = 0.0
        
    def set_mode(self, mode):
        self.mode = mode
        
    def update(self, dt):
        if self.mode == "MANUAL":
            self._handle_manual_input(dt)
            
        # Apply displacement along current heading
        if abs(self.current_speed) > 0.001:
            rad = math.radians(self.robot.rotation_y)
            dx = math.sin(rad) * self.current_speed * dt
            dz = math.cos(rad) * self.current_speed * dt
            
            self.robot.x += dx
            self.robot.z += dz
            
            dist = self.current_speed * dt
            if hasattr(self.robot, 'roll_wheels'):
                self.robot.roll_wheels(dist)
                
        self.robot.speed = self.current_speed
        self.heading = self.robot.rotation_y % 360
        
    def _handle_manual_input(self, dt):
        # 1. Forward / Reverse Throttle
        throttle_input = 0
        if held_keys['w'] or held_keys['up arrow']:
            throttle_input += 1
        if held_keys['s'] or held_keys['down arrow']:
            throttle_input -= 1
            
        if throttle_input > 0:
            # Accelerate forward
            self.current_speed = min(self.max_forward_speed, self.current_speed + self.accel_rate * dt)
        elif throttle_input < 0:
            # Reverse gear
            self.current_speed = max(-self.max_reverse_speed, self.current_speed - self.brake_rate * dt)
        else:
            # Natural friction braking when no throttle is held
            if self.current_speed > 0:
                self.current_speed = max(0.0, self.current_speed - self.accel_rate * 1.5 * dt)
            elif self.current_speed < 0:
                self.current_speed = min(0.0, self.current_speed + self.accel_rate * 1.5 * dt)
                
        # 2. Steering & Turning (A / D or Left / Right Arrows)
        steer_input = 0
        if held_keys['a'] or held_keys['left arrow']:
            steer_input -= 1
        if held_keys['d'] or held_keys['right arrow']:
            steer_input += 1
            
        if steer_input != 0:
            # Can pivot on spot when standing, or turn while driving
            self.robot.rotation_y += steer_input * self.turn_speed * dt
            
    def drive_autonomous(self, target_heading, desired_speed, dt):
        """Called by navigation planner & safety supervisor in AUTO mode.
        Features coordinated angular steering and linear speed throttling
        to prevent corner overshoots and erratic drift.
        """
        # 1. Compute angle difference (-180 to +180)
        angle_diff = (target_heading - self.robot.rotation_y + 180) % 360 - 180
        
        # 2. Smoothly rotate towards target heading
        max_turn = self.turn_speed * dt
        if abs(angle_diff) > 0.4:
            turn_step = max(-max_turn, min(max_turn, angle_diff * 8.5 * dt))
            self.robot.rotation_y += turn_step
            
        # 3. Coordinate linear speed with heading alignment:
        # If robot needs to turn significantly (>50 deg), slow or pivot in place to face waypoint accurately!
        abs_diff = abs(angle_diff)
        if abs_diff > 50.0:
            effective_target_speed = 0.0 # Pivot cleanly on spot
        elif abs_diff > 20.0:
            alignment = max(0.1, math.cos(math.radians(abs_diff)))
            effective_target_speed = desired_speed * alignment
        else:
            effective_target_speed = desired_speed
            
        # 4. Smoothly accelerate / decelerate towards effective target speed
        if self.current_speed < effective_target_speed:
            self.current_speed = min(effective_target_speed, self.current_speed + self.accel_rate * dt)
        elif self.current_speed > effective_target_speed:
            self.current_speed = max(effective_target_speed, self.current_speed - self.brake_rate * dt)
            
        # 5. Apply displacement along actual current heading
        if abs(self.current_speed) > 0.001:
            rad = math.radians(self.robot.rotation_y)
            dx = math.sin(rad) * self.current_speed * dt
            dz = math.cos(rad) * self.current_speed * dt
            self.robot.x += dx
            self.robot.z += dz
            
            dist = self.current_speed * dt
            if hasattr(self.robot, 'roll_wheels'):
                self.robot.roll_wheels(dist)
                
        self.robot.speed = self.current_speed
        self.heading = self.robot.rotation_y % 360

MovementController = RobotController
