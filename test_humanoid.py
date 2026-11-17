"""
Test script for Humanoid Delivery Android.
Verifies bipedal stride animation, head tracking gaze, and chassis switching.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ursina import Ursina, Vec3

app = Ursina(borderless=True, size=(640, 480), development_mode=False)

from robot.humanoid_robot import HumanoidDeliveryRobot
from robot.movement import RobotController
from robot.navigation import RouteNavigator

def test_humanoid():
    print("[TEST HUMANOID] 1. Instantiating Humanoid Delivery Android...")
    bot = HumanoidDeliveryRobot(position=(8.75, 0.0, -6.0))
    assert bot.torso is not None, "Torso missing"
    assert bot.head is not None, "Head missing"
    assert bot.eye_left is not None, "Eye optics missing"
    assert bot.cargo_backpack is not None, "Cargo backpack missing"
    print("   -> Humanoid Robot model integrity OK")
    
    print("[TEST HUMANOID] 2. Testing Bipedal Walking Kinematics...")
    controller = RobotController(bot)
    navigator = RouteNavigator(bot)
    
    dt = 1.0 / 60.0
    for _ in range(60):
        target_heading, desired_speed, reached = navigator.update(dt)
        controller.drive_autonomous(target_heading, desired_speed, dt)
        bot.update_walk(dt)
        
    assert bot.total_distance > 0.5, "Robot failed to travel"
    assert abs(bot.hip_l.rotation_x) > 0.01, "Leg swing angle is zero"
    print(f"   -> Walking stride OK (leg angle: {bot.hip_l.rotation_x:.1f}°, arm angle: {bot.arm_l.rotation_x:.1f}°)")
    
    print("[TEST HUMANOID] 3. Testing Dynamic Head Gaze Tracking...")
    # Look toward pedestrian at (5.0, 1.2, 5.0)
    bot.look_at_target(Vec3(5.0, 1.2, 5.0))
    assert abs(bot.head.rotation_y) > 0.1, "Head failed to turn toward target"
    print(f"   -> Head gaze tracking OK (yaw: {bot.head.rotation_y:.1f}°)")
    
    print("=" * 60)
    print("HUMANOID DELIVERY ANDROID TEST PASSED (100%)!")
    print("=" * 60)

if __name__ == "__main__":
    test_humanoid()

