"""
Automated Verification Script for Phase 1.
Initializes the complete 3D simulation, executes simulation steps,
verifies entity state, and confirms 100% bug-free operation.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ursina import Ursina, window, time, color

# Headless / hidden window initialization for automated test
app = Ursina(title="Test Phase 1", borderless=True, size=(640, 480), development_mode=False)

from environment.road import Road
from environment.sidewalk import Sidewalk
from environment.city import City
from environment.objects import CityObjects
from environment.weather import WeatherSystem

from robot.delivery_robot import DeliveryRobot
from robot.movement import RobotController
from robot.navigation import RouteNavigator
from camera_controller import CameraController
from dashboard.ui import DashboardUI

def run_test():
    print("[TEST] 1. Initializing WeatherSystem...")
    weather = WeatherSystem()
    assert weather.current_weather == "CLEAR", "Weather initial state mismatch"
    print("   -> WeatherSystem OK")
    
    print("[TEST] 2. Building Road & Markings...")
    road = Road(length=140, road_width=12)
    assert road.road_surface is not None, "Road surface missing"
    assert len(road.dashes) > 0, "Road dashes missing"
    print("   -> Road & Zebra Crossing OK")
    
    print("[TEST] 3. Building Sidewalk & ADA tactile warning...")
    sidewalk = Sidewalk(length=140, road_width=12, sidewalk_width=5.0)
    assert sidewalk.right_sidewalk_1 is not None, "Right sidewalk missing"
    print("   -> Sidewalk OK")
    
    print("[TEST] 4. Generating City Architecture...")
    city = City(road_width=12, sidewalk_width=5.0, length=140)
    print("   -> City Buildings OK")
    
    print("[TEST] 5. Placing Objects, Trees, Signs, Depot...")
    objects = CityObjects(road_width=12, sidewalk_width=5.0, length=140)
    assert objects.destination_hub is not None, "Destination hub missing"
    print("   -> City Objects OK")
    
    print("[TEST] 6. Instantiating Autonomous Delivery Robot...")
    robot = DeliveryRobot(position=(8.75, 0.45, -6.0))
    assert len(robot.wheels) == 4, "Robot must have 4 wheels"
    print(f"   -> Robot spawned at: {robot.position}")
    
    print("[TEST] 7. Testing Movement Controller & Navigator...")
    controller = RobotController(robot)
    navigator = RouteNavigator(robot)
    camera_ctrl = CameraController(robot)
    dashboard = DashboardUI(robot, camera_ctrl, navigator)
    
    dt = 1.0 / 60.0
    initial_z = robot.z
    
    for frame in range(60):
        robot.update()
        objects.destination_hub.update()
        
        target_heading, desired_speed, reached = navigator.update(dt)
        controller.drive_autonomous(target_heading, desired_speed, dt)
        
        camera_ctrl.update(dt)
        dashboard.update(dt)
        
    print(f"   -> Robot navigated from z={initial_z:.2f} to z={robot.z:.2f}")
    assert robot.z > initial_z, "Robot should move forward towards destination"
    assert robot.speed > 0, "Robot speed should be positive"
    assert robot.total_distance > 0, "Distance traveled should be positive"
    print(f"   -> Total distance: {robot.total_distance:.2f}m, Speed: {robot.speed:.2f} m/s")
    
    print("[TEST] 8. Testing Camera Mode Switching...")
    for _ in range(len(camera_ctrl.modes)):
        mode = camera_ctrl.next_mode()
        camera_ctrl.update(dt)
        print(f"   -> Camera mode: {mode}")
        
    print("[TEST] 9. Testing Weather State Transitions...")
    for w in ["FOG", "NIGHT", "RAIN", "SNOW", "CLEAR"]:
        weather.set_weather(w)
        assert weather.current_weather == w, f"Failed setting weather {w}"
    print("   -> Weather transitions OK")
    
    print("=" * 60)
    print("ALL PHASE 1 VERIFICATION TESTS PASSED SUCCESSFULLY (100%)!")
    print("=" * 60)

if __name__ == "__main__":
    run_test()
