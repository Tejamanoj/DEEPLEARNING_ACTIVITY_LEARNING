"""
Unit Test: Verifies Zebra-Crossing-Only Roadway Crossing Rule,
Weather System Vision Degradation & Particle Animation,
Robot Torch Spotlight, and Mission Route Toggling.
"""
from ursina import Ursina, Entity, Vec3, color
import math

app = Ursina(headless=True)

from decision.safety_rules import SafetyRulesEngine
from environment.weather import WeatherSystem, WEATHER_PRESETS
from robot.humanoid_robot import HumanoidDeliveryRobot
from robot.navigation import RouteNavigator

def test_zebra_crossing_rules():
    print("[TEST 1] Testing Zebra-Crossing-Only Roadway Crossing Rule...")
    engine = SafetyRulesEngine()
    
    # Mock robot entity
    class MockRobot:
        def __init__(self, x, y, z, rot_y=0):
            self.position = Vec3(x, y, z)
            self.rotation_y = rot_y
            self.x = x
            self.y = y
            self.z = z
            
    # Case A: Robot on sidewalk (x=8.75, z=15.0) -> COMPLIANT
    bot_sidewalk = MockRobot(8.75, 0.45, 15.0)
    action, spd, heading = engine.evaluate(bot_sidewalk, [], 0.016)
    assert not engine.roadway_breach_active, "Should not breach on sidewalk"
    assert "COMPLIANT" in engine.rule_statuses["RULE_1_SIDEWALK_BOUNDS"]
    print("   -> Case A (On Sidewalk): OK [COMPLIANT]")
    
    # Case B: Robot on road OUTSIDE zebra crossing (x=2.0, z=12.0) -> CRITICAL VIOLATION
    bot_illegal_road = MockRobot(2.0, 0.1, 12.0)
    action, spd, heading = engine.evaluate(bot_illegal_road, [], 0.016)
    assert engine.roadway_breach_active, "Should trigger roadway breach outside zebra crossing"
    assert action == "EMERGENCY_RETURN", f"Action should be EMERGENCY_RETURN, got {action}"
    assert "VIOLATION" in engine.rule_statuses["RULE_2_ZEBRA_CROSSING_ONLY"]
    print("   -> Case B (Illegal Road Crossing at z=12m): OK [CRITICAL VIOLATION INTERCEPTED -> EMERGENCY RETURN]")
    
    # Case C: Robot on road INSIDE zebra crossing (x=0.0, z=32.0) -> AUTHORIZED CROSSING
    bot_legal_zebra = MockRobot(0.0, 0.1, 32.0)
    action, spd, heading = engine.evaluate(bot_legal_zebra, [], 0.016)
    assert not engine.roadway_breach_active, "Should NOT trigger roadway breach inside zebra crossing"
    assert engine.is_crossing_zebra, "Should mark is_crossing_zebra as True"
    assert "AUTHORIZED" in engine.rule_statuses["RULE_2_ZEBRA_CROSSING_ONLY"]
    print("   -> Case C (Legal Road Crossing at Zebra Crosswalk z=32m): OK [AUTHORIZED - SAFE PASSAGE]")

def test_weather_system():
    print("[TEST 2] Testing Weather System & Vision Perception Degradation...")
    weather_sys = WeatherSystem()
    
    for w in ['CLEAR', 'LIGHT_RAIN', 'HEAVY_RAIN', 'DENSE_FOG', 'NIGHT', 'SNOWFALL']:
        weather_sys.set_weather(w)
        vis = weather_sys.get_visibility_range()
        conf = weather_sys.get_detection_confidence()
        spd = weather_sys.get_speed_limit()
        print(f"   -> Preset '{w}': Vision Range={vis:.1f}m, Confidence={conf}%, Speed Limit={spd:.2f}m/s")
        assert vis > 0 and conf > 0 and spd > 0
        
    # Verify particle animation tick
    weather_sys.set_weather('HEAVY_RAIN')
    initial_y = weather_sys.rain_particles[0].y
    weather_sys.update(0.05, robot_pos=Vec3(8.75, 0, 10))
    new_y = weather_sys.rain_particles[0].y
    assert new_y != initial_y, "Rain particle Y should advance during weather update"
    print("   -> Weather Particle System: Falling rain animation verified OK")

def test_torch_spotlight():
    print("[TEST 3] Testing Robot Torch Light Spotlight...")
    robot = HumanoidDeliveryRobot(position=(8.75, 0.28, -6))
    assert hasattr(robot, 'torch_beam'), "Robot should have volumetric torch_beam"
    assert hasattr(robot, 'torch_ground_spot'), "Robot should have torch_ground_spot"
    assert robot.torch_enabled, "Torch should be enabled by default"
    
    # Toggle torch
    robot.toggle_torch()
    assert not robot.torch_enabled, "Torch should be disabled after toggle"
    robot.toggle_torch()
    assert robot.torch_enabled, "Torch should be enabled after second toggle"
    
    # Test weather adaptation
    robot.set_torch_weather_mode('night')
    assert robot.torch_beam.color.a > 0.4, "Torch beam alpha should intensify at night"
    print("   -> Robot Torch Spotlight: Volumetric beam & weather adaptation OK")

def test_navigation_missions():
    print("[TEST 4] Testing Mission Route Toggling (Sidewalk Direct vs Zebra Crosswalk)...")
    robot = HumanoidDeliveryRobot(position=(8.75, 0.28, -6))
    nav = RouteNavigator(robot)
    
    mission1 = nav.get_mission_name()
    assert "ZEBRA" in mission1 or "GRAND" in mission1, f"Initial mission should be Grand Zebra Crosswalk, got {mission1}"
    print(f"   -> Mission 1 (Default): '{mission1}' OK")
    
    # Verify zebra mission waypoints cross through roadway at z=32
    cross_waypoints = [wp for wp in nav.waypoints if abs(wp.z - 32.0) < 0.1]
    assert len(cross_waypoints) >= 3, "Zebra mission must contain crossing waypoints along z=32"
    print(f"   -> Verified {len(cross_waypoints)} Zebra Crosswalk waypoints strictly along z=32 across roadway")
    
    mission2 = nav.toggle_mission()
    assert "SIDEWALK" in mission2 or "EXPRESS" in mission2, f"Toggled mission should be Sidewalk/Express, got {mission2}"
    print(f"   -> Mission 2 (Toggled): '{mission2}' OK")

if __name__ == "__main__":
    test_zebra_crossing_rules()
    test_weather_system()
    test_torch_spotlight()
    test_navigation_missions()
    print("=================================================================")
    print("ALL ZEBRA CROSSING, WEATHER & TORCH VERIFICATION TESTS PASSED (100%)!")
    print("=================================================================")

