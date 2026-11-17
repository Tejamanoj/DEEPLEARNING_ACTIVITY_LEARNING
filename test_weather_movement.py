"""
Unit Test: Verifies that changing weather across all presets
does NOT cause speed decay or stop the robot from moving.
"""
from ursina import Ursina, Vec3
app = Ursina(headless=True)

from robot.humanoid_robot import HumanoidDeliveryRobot
from robot.navigation import RouteNavigator
from robot.movement import MovementController
from decision.safety_rules import SafetyRulesEngine
from environment.weather import WeatherSystem, WEATHER_PRESETS

def test_weather_speed_no_decay():
    print("[TEST] Verifying robot movement across all weather changes...")
    
    robot = HumanoidDeliveryRobot(position=(8.75, 0.45, -6))
    navigator = RouteNavigator(robot)
    controller = MovementController(robot)
    safety_engine = SafetyRulesEngine()
    weather_sys = WeatherSystem()
    
    dt = 0.016 # ~60 FPS
    
    weather_presets = ['CLEAR', 'LIGHT_RAIN', 'HEAVY_RAIN', 'DENSE_FOG', 'NIGHT', 'SNOWFALL']
    
    for weather_name in weather_presets:
        weather_sys.set_weather(weather_name)
        expected_speed_limit = weather_sys.get_speed_limit()
        weather_speed_mult = expected_speed_limit / 1.6
        
        # Simulate 120 frames (2 seconds) in this weather
        for frame in range(120):
            safety_action, speed_mult, target_heading = safety_engine.evaluate(robot, [], dt)
            assert safety_action == "PROCEED_SAFE", f"Action should be PROCEED_SAFE, got {safety_action}"
            
            nav_heading, nav_speed, is_done = navigator.update(dt)
            assert nav_speed == 1.6, f"navigator.update() must maintain base speed 1.6, got {nav_speed}"
            
            target_drive_speed = nav_speed * weather_speed_mult
            controller.drive_autonomous(nav_heading, target_drive_speed, dt)
            robot.update_walk(dt)
            
        print(f"   -> Weather '{weather_name}': Speed={robot.speed:.2f} m/s (Expected: {expected_speed_limit:.2f} m/s), Position z={robot.z:.2f}m")
        assert robot.speed > 0.4, f"Robot speed must not decay! Current speed: {robot.speed}"
        assert abs(robot.speed - expected_speed_limit) < 0.1, f"Robot speed should match weather limit: {robot.speed} vs {expected_speed_limit}"

    print("=================================================================")
    print("ALL WEATHER MOVEMENT TESTS PASSED! NO SPEED DECAY OCCURRED!")
    print("=================================================================")

if __name__ == "__main__":
    test_weather_speed_no_decay()

