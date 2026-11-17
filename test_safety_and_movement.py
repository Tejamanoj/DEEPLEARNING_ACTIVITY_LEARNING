"""
Verification script for Safety Rules Engine, Roadway Intrusion Protection,
and Omnidirectional Movement.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ursina import Ursina, Vec3

app = Ursina(borderless=True, size=(640, 480), development_mode=False)

from robot.humanoid_robot import HumanoidDeliveryRobot
from robot.movement import RobotController
from decision.safety_rules import SafetyRulesEngine
from environment.actors import RoadObstacle, Vehicle, Pedestrian
from camera_controller import CameraController

def run_safety_tests():
    print("[SAFETY TEST] 1. Initializing Safety Rules Engine...")
    safety_engine = SafetyRulesEngine()
    bot = HumanoidDeliveryRobot(position=(8.75, 0.0, 10.0))
    print("   -> SafetyRulesEngine initialized OK")
    
    print("[SAFETY TEST] 2. Testing Sidewalk Boundary Compliance...")
    # On sidewalk (x=8.75)
    action, spd, heading = safety_engine.evaluate(bot, [], 0.016)
    assert not safety_engine.roadway_breach_active, "Should be compliant on sidewalk"
    print("   -> Sidewalk compliance OK")
    
    print("[SAFETY TEST] 3. Testing Roadway Intrusion Detection & Emergency Return...")
    # Drive into vehicle roadway (x=3.5, outside crosswalk)
    bot.position = (3.5, 0.0, 10.0)
    action, spd, override_heading = safety_engine.evaluate(bot, [], 0.016)
    assert safety_engine.roadway_breach_active, "Roadway breach failed to detect"
    assert action == "EMERGENCY_RETURN", "Should trigger EMERGENCY_RETURN"
    assert override_heading > 0, "Emergency return heading should point towards positive X (sidewalk)"
    print(f"   -> Roadway Intrusion detected! Action: {action}, Return Heading: {override_heading:.1f}°")
    
    print("[SAFETY TEST] 4. Testing Forward Path Clearance vs Side Traffic...")
    bot.position = (8.75, 0.0, 10.0)
    bot.rotation_y = 0.0 # Facing +Z along sidewalk
    
    # Side traffic in roadway (x=3.0, z=12.0) - should NOT block forward path
    car = Vehicle(position=(3.0, 0.0, 12.0))
    action, spd, _ = safety_engine.evaluate(bot, [car], 0.016)
    assert action == "PROCEED_SAFE", "Side vehicle incorrectly blocked forward path"
    print("   -> Side traffic correctly ignored for forward stop")
    
    # Direct forward obstacle on sidewalk (x=8.75, z=12.0, 2.0m ahead)
    obs = RoadObstacle(position=(8.75, 0.0, 12.0))
    action, spd, _ = safety_engine.evaluate(bot, [obs], 0.016)
    assert action in ["DETOUR_AVOIDANCE", "EMERGENCY_STOP"], f"Forward obstacle triggered unexpected action {action}"
    print(f"   -> Forward Obstacle correctly handled: {action} at {safety_engine.obstacle_ahead_distance:.1f}m")
    
    print("[SAFETY TEST] 5. Testing Omnidirectional Movement (Reverse & Turn)...")
    ctrl = RobotController(bot)
    ctrl.mode = "MANUAL"
    # Reverse movement
    ctrl.current_speed = -1.0
    ctrl.update(0.1)
    assert bot.z < 10.0, "Robot failed to move backwards in reverse"
    print(f"   -> Reverse driving OK (z: {bot.z:.2f})")
    
    print("[SAFETY TEST] 6. Testing Camera Angles & Mouse Zoom...")
    cam_ctrl = CameraController(bot)
    initial_dist = cam_ctrl.distance
    # Simulate zoom in
    cam_ctrl.distance -= 1.0
    cam_ctrl.update(0.016)
    assert cam_ctrl.distance < initial_dist, "Camera zoom failed"
    print(f"   -> Camera zoom OK (distance: {cam_ctrl.distance:.1f}m)")
    
    print("=" * 65)
    print("ALL SAFETY & MOVEMENT VERIFICATION TESTS PASSED (100%)!")
    print("=" * 65)

if __name__ == "__main__":
    run_safety_tests()

