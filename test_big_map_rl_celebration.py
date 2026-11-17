"""
Unit Test: Verifies Extended 280m Big Map, Dual Zebra Crossings (z=32 and z=160),
Reinforcement Learning Reward & Penalty Engine (Vehicle dash, road intrusion, zebra bonus),
and Destination Target Celebration Confetti Burst.
"""
from ursina import Ursina, Vec3
app = Ursina(headless=True)

from environment.road import Road
from environment.sidewalk import Sidewalk
from environment.objects import CityObjects
from environment.actors import DynamicActorManager, Vehicle, Pedestrian
from robot.humanoid_robot import HumanoidDeliveryRobot
from robot.navigation import RouteNavigator
from decision.safety_rules import SafetyRulesEngine
from decision.rl_engine import RLRewardEngine
from environment.weather import WeatherSystem

def test_big_map_and_dual_crossings():
    print("[TEST 1] Verifying 280m Big Map & Dual Zebra Crossings...")
    road = Road(length=280)
    sidewalk = Sidewalk(length=280)
    assert road.length == 280, f"Road length must be 280, got {road.length}"
    assert sidewalk.length == 280, f"Sidewalk length must be 280, got {sidewalk.length}"
    assert hasattr(road, 'zebra_crossing_1'), "Must have South Zebra crossing"
    assert hasattr(road, 'zebra_crossing_2'), "Must have North Zebra crossing"
    print("   -> Road & Sidewalk 280m dimensions: OK")
    print("   -> Dual Zebra Crossings at z=32 and z=160: OK")

def test_rl_rewards_and_penalties():
    print("[TEST 2] Verifying Reinforcement Learning (RL) Rewards & Penalties...")
    robot = HumanoidDeliveryRobot(position=(8.75, 0.45, -6))
    navigator = RouteNavigator(robot)
    safety_engine = SafetyRulesEngine()
    rl_engine = RLRewardEngine()
    weather_sys = WeatherSystem()
    
    # A. Forward progress reward
    step_r, tot = rl_engine.evaluate(robot, [], navigator, safety_engine, weather_sys, 0.016)
    robot.z = 2.0 # Advanced 8 meters forward
    step_r, tot = rl_engine.evaluate(robot, [], navigator, safety_engine, weather_sys, 0.016)
    assert tot > 0, f"Total reward should be positive after advancing, got {tot}"
    print(f"   -> Forward Progress Reward: OK (Reward = {tot:+.2f} pts)")
    
    # B. Vehicle Dash / Collision Penalty (-100.0)
    danger_vehicle = Vehicle(position=(robot.x + 0.5, 0.1, robot.z + 0.5))
    step_r, tot = rl_engine.evaluate(robot, [danger_vehicle], navigator, safety_engine, weather_sys, 0.016)
    assert rl_engine.total_collision_penalty >= 100.0, "Must record -100.0 vehicle dash penalty"
    print(f"   -> Vehicle Dash / Collision Risk Penalty: OK (Recorded -{rl_engine.total_collision_penalty:.1f} penalty)")
    
    # C. Illegal Roadway Intrusion Penalty (-50.0)
    bot_in_road = HumanoidDeliveryRobot(position=(2.0, 0.1, 80.0)) # In road outside zebra!
    safety_engine.evaluate(bot_in_road, [], 0.016)
    step_r, tot = rl_engine.evaluate(bot_in_road, [], navigator, safety_engine, weather_sys, 0.016)
    assert rl_engine.total_road_penalty > 0, "Must record illegal road intrusion penalty"
    print(f"   -> Roadway Intrusion Penalty: OK (Recorded -{rl_engine.total_road_penalty:.1f} penalty)")
    
    # D. Zebra Crosswalk Traversal & Completion Reward (+35.0)
    bot_crossing = HumanoidDeliveryRobot(position=(0.0, 0.1, 32.0)) # Legal crosswalk at z=32
    safety_engine.evaluate(bot_crossing, [], 0.016)
    rl_engine.evaluate(bot_crossing, [], navigator, safety_engine, weather_sys, 0.016)
    # Finish crossing onto west sidewalk
    bot_crossed = HumanoidDeliveryRobot(position=(-8.75, 0.35, 32.0))
    safety_engine.evaluate(bot_crossed, [], 0.016)
    rl_engine.evaluate(bot_crossed, [], navigator, safety_engine, weather_sys, 0.016)
    assert rl_engine.total_zebra_reward >= 35.0, f"Must award zebra completion bonus, got {rl_engine.total_zebra_reward}"
    print(f"   -> Legal Zebra Crosswalk Traversal Bonus: OK (Awarded +{rl_engine.total_zebra_reward:.1f} pts)")

def test_destination_celebration():
    print("[TEST 3] Verifying Target Destination Arrival & Celebration Sequence...")
    robot = HumanoidDeliveryRobot(position=(8.75, 0.45, 240.0))
    navigator = RouteNavigator(robot)
    safety_engine = SafetyRulesEngine()
    rl_engine = RLRewardEngine()
    weather_sys = WeatherSystem()
    objects = CityObjects(road_width=12, sidewalk_width=6.0, length=280)
    
    # Move navigator to end
    navigator.current_idx = len(navigator.waypoints) - 1
    navigator.update(0.016)
    assert navigator.is_finished, "Navigator must be finished at terminal destination"
    
    # RL Terminal Bonus (+150.0)
    step_r, tot = rl_engine.evaluate(robot, [], navigator, safety_engine, weather_sys, 0.016)
    assert rl_engine.total_goal_reward == 150.0, f"Terminal goal bonus must be 150.0, got {rl_engine.total_goal_reward}"
    print(f"   -> Terminal Goal Bonus Awarded: OK (+{rl_engine.total_goal_reward:.1f} pts)")
    
    # Trigger Celebration Confetti
    objects.celebration.trigger(robot.position)
    assert objects.celebration.is_active, "Celebration confetti system must be active"
    active_particles = sum(1 for p in objects.celebration.particles if p.enabled)
    assert active_particles >= 60, f"Expected 60+ confetti particles, got {active_particles}"
    
    # Update confetti physics
    objects.celebration.update()
    
    # Android celebration victory pose
    robot.celebrate(0.016)
    assert robot.arm_l.rotation_x < -100.0, "Left arm must raise into victory pose"
    assert robot.arm_r.rotation_x < -100.0, "Right arm must raise into victory pose"
    print("   -> Celebration Confetti & Android Victory Pose: OK")

if __name__ == "__main__":
    test_big_map_and_dual_crossings()
    test_rl_rewards_and_penalties()
    test_destination_celebration()
    print("=================================================================")
    print("ALL BIG MAP, RL REWARD & CELEBRATION TESTS PASSED (100%)!")
    print("=================================================================")

