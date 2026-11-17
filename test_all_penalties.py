"""
Test Suite: Comprehensive Verification of RL Penalties for Wrong Actions
========================================================================
Validates that ANY wrong action or safety violation immediately incurs
a steep, quantifiable penalty that reduces cumulative reward and displays
clear visual alert telemetry.
"""
import math
from ursina import Ursina, Vec3
from environment.actors import DynamicActorManager, Vehicle, Bicycle, RoadObstacle, Pedestrian
from robot.humanoid_robot import HumanoidDeliveryRobot
from robot.navigation import RouteNavigator
from decision.safety_rules import SafetyRulesEngine
from decision.rl_engine import RLRewardEngine
from environment.weather import WeatherSystem

app = Ursina(headless=True)

def test_all_penalties():
    print("=================================================================")
    print("TESTING REINFORCEMENT LEARNING PENALTIES FOR WRONG ACTIONS")
    print("=================================================================")
    
    robot = HumanoidDeliveryRobot(position=(8.75, 0.28, 10.0))
    nav = RouteNavigator(robot)
    safety = SafetyRulesEngine()
    rl = RLRewardEngine()
    weather = WeatherSystem()
    
    # ── Test 1: Illegal Roadway Intrusion Penalty (-50.0 instant + continuous) ──
    print("\n[TEST 1] Illegal Roadway Intrusion Outside Zebra Crosswalk...")
    bot_in_road = HumanoidDeliveryRobot(position=(2.0, 0.1, 75.0)) # Middle of road at z=75 (no zebra!)
    safety.evaluate(bot_in_road, [], 0.016)
    assert safety.roadway_breach_active, "Road breach flag must be active"
    
    step_r, cum_r = rl.evaluate(bot_in_road, [], nav, safety, weather, 0.016)
    assert rl.total_road_penalty >= 50.0, f"Expected at least -50.0 road penalty, got {rl.total_road_penalty}"
    assert "CRITICAL PENALTY" in rl.recent_events[-1] and "-50.0" in rl.recent_events[-1]
    print(f"   -> [PASS] Recorded Roadway Breach Penalty: -{rl.total_road_penalty:.1f} pts")
    print(f"   -> Alert: '{rl.recent_events[-1]}'")
    
    # ── Test 2: Vehicle Collision Hazard Penalty (-100.0) ──
    print("\n[TEST 2] Vehicle Collision Hazard Penalty (-100.0)...")
    rl.reset()
    danger_car = Vehicle(position=(robot.x + 0.3, 0.1, robot.z + 0.3)) # Car right next to robot!
    step_r, cum_r = rl.evaluate(robot, [danger_car], nav, safety, weather, 0.016)
    assert rl.total_collision_penalty >= 100.0, f"Expected -100.0 vehicle penalty, got {rl.total_collision_penalty}"
    assert "CRITICAL PENALTY" in rl.recent_events[-1] and "-100.0" in rl.recent_events[-1]
    print(f"   -> [PASS] Recorded Vehicle Hazard Penalty: -{rl.total_collision_penalty:.1f} pts")
    print(f"   -> Alert: '{rl.recent_events[-1]}'")
    
    # ── Test 3: Sidewalk Obstacle / Barrel Collision Penalty (-35.0) ──
    print("\n[TEST 3] Sidewalk Obstacle / Construction Barrel Collision (-35.0)...")
    rl.reset()
    barrel = RoadObstacle(position=(robot.x + 0.2, 0.28, robot.z + 0.2)) # Barrel right against robot!
    step_r, cum_r = rl.evaluate(robot, [barrel], nav, safety, weather, 0.016)
    assert rl.total_obstacle_penalty >= 35.0, f"Expected -35.0 obstacle penalty, got {rl.total_obstacle_penalty}"
    assert "PENALTY" in rl.recent_events[-1] and "-35.0" in rl.recent_events[-1]
    print(f"   -> [PASS] Recorded Obstacle Crash Penalty: -{rl.total_obstacle_penalty:.1f} pts")
    print(f"   -> Alert: '{rl.recent_events[-1]}'")
    
    # ── Test 4: Bicycle Collision Hazard Penalty (-50.0) ──
    print("\n[TEST 4] Bicycle Collision Hazard Penalty (-50.0)...")
    rl.reset()
    bike = Bicycle(position=(robot.x + 0.3, 0.1, robot.z + 0.3)) # Bicycle right next to robot!
    step_r, cum_r = rl.evaluate(robot, [bike], nav, safety, weather, 0.016)
    assert rl.total_collision_penalty >= 50.0, f"Expected -50.0 bicycle penalty, got {rl.total_collision_penalty}"
    assert "CRITICAL PENALTY" in rl.recent_events[-1] and "-50.0" in rl.recent_events[-1]
    print(f"   -> [PASS] Recorded Bicycle Hazard Penalty: -{rl.total_collision_penalty:.1f} pts")
    print(f"   -> Alert: '{rl.recent_events[-1]}'")
    
    # ── Test 5: Pedestrian Physical Contact / Bump Penalty (-25.0) ──
    print("\n[TEST 5] Pedestrian Physical Collision / Contact Penalty (-25.0)...")
    rl.reset()
    robot.speed = 1.2 # Robot moving forward
    ped = Pedestrian(position=(robot.x + 0.2, 0.28, robot.z + 0.4)) # Pedestrian 0.4m ahead
    step_r, cum_r = rl.evaluate(robot, [ped], nav, safety, weather, 0.016)
    assert rl.total_pedestrian_penalty >= 25.0, f"Expected -25.0 pedestrian penalty, got {rl.total_pedestrian_penalty}"
    assert "PENALTY" in rl.recent_events[-1] and "-25.0" in rl.recent_events[-1]
    print(f"   -> [PASS] Recorded Pedestrian Bump Penalty: -{rl.total_pedestrian_penalty:.1f} pts")
    print(f"   -> Alert: '{rl.recent_events[-1]}'")
    
    # ── Test 6: Weather Overspeeding Penalty in Fog / Rain ──
    print("\n[TEST 6] Weather Overspeeding in Dense Fog...")
    rl.reset()
    weather.set_weather('dense_fog') # Speed limit is 0.65 m/s
    robot.speed = 1.6 # Robot driving at 1.6 m/s (illegal overspeed in dense fog!)
    step_r, cum_r = rl.evaluate(robot, [], nav, safety, weather, 0.1) # 100ms
    assert rl.total_overspeed_penalty > 0, "Overspeed penalty must be recorded"
    print(f"   -> [PASS] Recorded Weather Overspeed Penalty: -{rl.total_overspeed_penalty:.2f} pts")
    
    # ── Test 7: Total Cumulative Negative Balance Check ──
    print("\n[TEST 7] Negative Cumulative Balance Verification...")
    rl.reset()
    # Trigger 2 major violations
    rl.evaluate(bot_in_road, [], nav, safety, weather, 0.016) # -50 road
    rl.evaluate(robot, [danger_car], nav, safety, weather, 0.016) # -100 car
    summary = rl.get_reward_summary()
    assert summary["total"] < -100.0, f"Total reward should be deeply negative, got {summary['total']}"
    assert summary["total_penalties"] >= 150.0, f"Total penalties should be at least 150.0, got {summary['total_penalties']}"
    print(f"   -> [PASS] Net Reward: {summary['total']:.1f} pts | Total Penalties Incurred: -{summary['total_penalties']:.1f} pts")
    
    print("\n=================================================================")
    print("ALL 7 RL PENALTY & VIOLATION TESTS PASSED (100%)!")
    print("=================================================================")

if __name__ == "__main__":
    test_all_penalties()

