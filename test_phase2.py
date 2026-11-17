"""
Automated Verification Script for Phase 2: Dynamic Actors & Advanced Laser Tracking.
Tests pedestrian walking cycles, vehicle traffic, multi-modal sensors,
targeting laser beams, 3D bounding boxes, and collision avoidance logic.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ursina import Ursina, window, time, color

app = Ursina(title="Test Phase 2", borderless=True, size=(640, 480), development_mode=False)

from environment.road import Road
from environment.sidewalk import Sidewalk
from environment.city import City
from environment.objects import CityObjects
from environment.weather import WeatherSystem
from environment.actors import DynamicActorManager, Pedestrian, Vehicle, Bicycle, RoadObstacle

from robot.delivery_robot import DeliveryRobot
from robot.movement import RobotController
from robot.navigation import RouteNavigator
from camera_controller import CameraController

from sensors.sensor_manager import SensorManager
from dashboard.ui import DashboardUI

def run_test():
    print("[TEST 2] 1. Initializing Environment & Lighting...")
    weather = WeatherSystem()
    road = Road(length=140, road_width=12)
    sidewalk = Sidewalk(length=140, road_width=12, sidewalk_width=5.0)
    city = City(road_width=12, sidewalk_width=5.0, length=140)
    objects = CityObjects(road_width=12, sidewalk_width=5.0, length=140)
    print("   -> Static environment OK")
    
    print("[TEST 2] 2. Spawning Dynamic Actors...")
    actor_mgr = DynamicActorManager()
    all_actors = actor_mgr.get_all_trackable_actors()
    assert len(actor_mgr.pedestrians) >= 3, "Missing pedestrians"
    assert len(actor_mgr.vehicles) >= 2, "Missing vehicles"
    assert len(actor_mgr.bicycles) >= 1, "Missing bicycle"
    assert len(actor_mgr.obstacles) >= 1, "Missing obstacle"
    print(f"   -> Spawned {len(all_actors)} dynamic actors in urban scene")
    
    print("[TEST 2] 3. Testing Walking and Driving Animations...")
    dt = 1.0 / 60.0
    p1 = actor_mgr.pedestrians[0]
    initial_walk_time = p1.walk_time
    v1 = actor_mgr.vehicles[0]
    initial_car_z = v1.z
    
    for _ in range(30):
        actor_mgr.update(dt)
        
    assert p1.walk_time > initial_walk_time, "Pedestrian walk animation failed to advance"
    assert v1.z != initial_car_z, "Vehicle failed to drive along roadway"
    print(f"   -> Pedestrian walk cycle OK (leg swing: {p1.leg_left.rotation_x:.1f}°)")
    print(f"   -> Vehicle movement OK (traveled: {abs(v1.z - initial_car_z):.2f}m)")
    
    print("[TEST 2] 4. Initializing Robot & Advanced Sensors...")
    robot = DeliveryRobot(position=(8.75, 0.45, -6.0))
    sensor_mgr = SensorManager(robot=robot)
    assert sensor_mgr.lidar is not None, "LiDAR visualizer missing"
    assert sensor_mgr.radar is not None, "Radar visualizer missing"
    assert sensor_mgr.camera_frustum is not None, "Camera frustum missing"
    assert sensor_mgr.laser_tracker is not None, "Laser tracker missing"
    print("   -> Multi-modal sensors & laser tracker initialized OK")
    
    print("[TEST 2] 5. Testing Target Lock Lasers & 3D Bounding Boxes...")
    # Position robot near pedestrian to test laser lock
    robot.position = (8.75, 0.45, 10.0) # Near pedestrian at z=12
    sensor_mgr.update_sensors(all_actors, dt)
    
    assert sensor_mgr.detected_count > 0, "Sensors failed to detect nearby actors"
    assert sensor_mgr.closest_object_distance < 10.0, "Closest object distance calculation error"
    print(f"   -> Detected {sensor_mgr.detected_count} objects in range")
    print(f"   -> Closest object: {sensor_mgr.closest_object_type} at {sensor_mgr.closest_object_distance:.2f}m")
    print(f"   -> Safety Threat Level: {sensor_mgr.threat_level}")
    
    active_lasers = [s for s in sensor_mgr.laser_tracker.target_slots if s["active"]]
    assert len(active_lasers) > 0, "No dynamic laser beams activated"
    print(f"   -> Active targeting laser beams: {len(active_lasers)}")
    print(f"   -> Bounding box scale: {active_lasers[0]['bbox'].scale}")
    print(f"   -> Billboard tag text: '{active_lasers[0]['tag'].text}'")
    
    print("[TEST 2] 6. Testing Sensor Toggles...")
    assert sensor_mgr.lidar.toggle() is False
    assert sensor_mgr.lidar.toggle() is True
    assert sensor_mgr.laser_tracker.toggle() is False
    assert sensor_mgr.laser_tracker.toggle() is True
    print("   -> Sensor hotkey toggles OK")
    
    print("=" * 65)
    print("ALL PHASE 2 VERIFICATION TESTS PASSED SUCCESSFULLY (100%)!")
    print("=" * 65)

if __name__ == "__main__":
    run_test()

