"""
Reinforcement Learning (RL) Reward & Penalty Engine:
Computes mathematical reward signals and penalty feedback for autonomous navigation,
crosswalk compliance, vehicle collision avoidance, and goal arrival.
Implements Markov Decision Process (MDP) reward function:
R_t = R_progress + R_zebra + R_alignment + R_goal - P_road - P_collision - P_ped - P_weather - P_step
"""
import math
from ursina import Vec3

class RLRewardEngine:
    def __init__(self):
        self.cumulative_reward = 0.0
        self.last_step_reward = 0.0
        self.step_count = 0
        self.episode_num = 1
        
        # Positive Reward accumulators
        self.total_progress_reward = 0.0
        self.total_zebra_reward = 0.0
        self.total_goal_reward = 0.0
        self.total_positive_rewards = 0.0
        
        # Penalty accumulators (Violations)
        self.total_penalties = 0.0
        self.total_road_penalty = 0.0
        self.total_collision_penalty = 0.0
        self.total_obstacle_penalty = 0.0
        self.total_pedestrian_penalty = 0.0
        self.total_overspeed_penalty = 0.0
        
        # Violation cooldown timers
        self.road_violation_cooldown = 0.0
        self.vehicle_cooldown = 0.0
        self.obstacle_cooldown = 0.0
        self.pedestrian_cooldown = 0.0
        
        # State tracking
        self.prev_distance_to_target = None
        self.prev_waypoint_idx = 0
        self.was_in_zebra = False
        self.goal_awarded = False
        self.recent_events = ["EPISODE READY: AWAITING START"]
        
    def reset(self):
        self.cumulative_reward = 0.0
        self.last_step_reward = 0.0
        self.step_count = 0
        self.episode_num += 1
        self.total_progress_reward = 0.0
        self.total_zebra_reward = 0.0
        self.total_goal_reward = 0.0
        self.total_positive_rewards = 0.0
        self.total_penalties = 0.0
        self.total_road_penalty = 0.0
        self.total_collision_penalty = 0.0
        self.total_obstacle_penalty = 0.0
        self.total_pedestrian_penalty = 0.0
        self.total_overspeed_penalty = 0.0
        self.road_violation_cooldown = 0.0
        self.vehicle_cooldown = 0.0
        self.obstacle_cooldown = 0.0
        self.pedestrian_cooldown = 0.0
        self.prev_distance_to_target = None
        self.prev_waypoint_idx = 0
        self.was_in_zebra = False
        self.goal_awarded = False
        self.recent_events = ["EPISODE RESET: READY"]
        
    def evaluate(self, robot, actors, navigator, safety_engine, weather_sys, dt):
        """Computes step reward and updates RL episode telemetry with active penalty enforcement."""
        self.step_count += 1
        step_reward = 0.0
        step_penalty = 0.0
        active_event = None
        
        # Update cooldown timers
        if self.road_violation_cooldown > 0:
            self.road_violation_cooldown -= dt
        if self.vehicle_cooldown > 0:
            self.vehicle_cooldown -= dt
        if self.obstacle_cooldown > 0:
            self.obstacle_cooldown -= dt
        if self.pedestrian_cooldown > 0:
            self.pedestrian_cooldown -= dt
            
        # ══════════════════════════════════════════════════════════════
        # A. POSITIVE REWARDS (DESIRABLE BEHAVIORS)
        # ══════════════════════════════════════════════════════════════
        
        # 1. Target Waypoint Distance Progress Reward (+R_progress)
        if navigator and not navigator.is_finished and navigator.current_idx < len(navigator.waypoints):
            target_pt = navigator.waypoints[navigator.current_idx]
            dist_to_target = math.sqrt((target_pt.x - robot.x)**2 + (target_pt.z - robot.z)**2)
            
            if self.prev_waypoint_idx != navigator.current_idx:
                self.prev_waypoint_idx = navigator.current_idx
                self.prev_distance_to_target = dist_to_target
            
            if self.prev_distance_to_target is not None:
                delta_progress = self.prev_distance_to_target - dist_to_target
                if 0.0005 < delta_progress < 1.0:
                    r_prog = delta_progress * 0.75
                    step_reward += r_prog
                    self.total_progress_reward += r_prog
            self.prev_distance_to_target = dist_to_target
        else:
            self.prev_distance_to_target = None
            
        # 2. Sidewalk Centerline Lane Alignment Reward (+R_alignment)
        if abs(robot.x) >= 6.35: # On sidewalk
            center_x = 8.75 if robot.x > 0 else -8.75
            lateral_offset = abs(robot.x - center_x)
            if lateral_offset < 0.45:
                r_align = 0.03
                step_reward += r_align
                
        # 3. Zebra Crossing Traversal Reward (+R_zebra)
        is_in_zebra = getattr(safety_engine, 'is_crossing_zebra', False)
        if is_in_zebra:
            r_zstep = 0.25
            step_reward += r_zstep
            self.total_zebra_reward += r_zstep
            if not self.was_in_zebra:
                # Entering crosswalk bonus
                step_reward += 5.0
                self.total_zebra_reward += 5.0
                active_event = "REWARD: +5.0 (ENTERED ZEBRA CROSSWALK)"
            self.was_in_zebra = True
        else:
            if self.was_in_zebra and (abs(robot.x) >= 6.35):
                # Completed crosswalk successfully!
                step_reward += 35.0
                self.total_zebra_reward += 35.0
                active_event = "REWARD: +35.0 (LEGAL ZEBRA CROSSING COMPLETED!)"
            self.was_in_zebra = False
            
        # 4. Terminal Destination Target Arrival (+R_goal)
        if navigator and navigator.is_finished and not self.goal_awarded:
            self.goal_awarded = True
            step_reward += 150.0
            self.total_goal_reward += 150.0
            active_event = "GOAL REACHED! +150.0 TERMINAL DELIVERY BONUS! 🎉"
            
        # ══════════════════════════════════════════════════════════════
        # B. PENALTIES (VIOLATIONS & WRONG ACTIONS)
        # ══════════════════════════════════════════════════════════════
        
        # 1. Illegal Roadway Intrusion Penalty (-P_road: -50.0 instant + continuous)
        roadway_breach = getattr(safety_engine, 'roadway_breach_active', False)
        if roadway_breach:
            if self.road_violation_cooldown <= 0:
                self.road_violation_cooldown = 1.8 # 1.8s cooldown
                p_road_instant = 50.0
                step_penalty += p_road_instant
                self.total_road_penalty += p_road_instant
                active_event = "CRITICAL PENALTY: -50.0 (ILLEGAL ROADWAY ENTRY OUTSIDE ZEBRA!)"
            p_road_cont = 20.0 * dt
            step_penalty += p_road_cont
            self.total_road_penalty += p_road_cont
            
        # 2. Vehicle & Bicycle Collision / Hazard Penalty (-P_collision: -100.0 / -50.0)
        for actor in actors:
            a_type = getattr(actor, 'actor_type', '')
            if a_type == 'VEHICLE':
                dx = actor.x - robot.x
                dz = actor.z - robot.z
                dist_veh = math.sqrt(dx**2 + dz**2)
                # Vehicle collision hazard range
                if dist_veh < 2.4 and self.vehicle_cooldown <= 0:
                    self.vehicle_cooldown = 2.0 # 2.0s cooldown
                    p_col = 100.0
                    step_penalty += p_col
                    self.total_collision_penalty += p_col
                    active_event = "CRITICAL PENALTY: -100.0 (VEHICLE DASH / COLLISION HAZARD!)"
                    break
            elif a_type == 'BICYCLE':
                dx = actor.x - robot.x
                dz = actor.z - robot.z
                dist_bike = math.sqrt(dx**2 + dz**2)
                if dist_bike < 1.8 and self.vehicle_cooldown <= 0:
                    self.vehicle_cooldown = 2.0
                    p_bike = 50.0
                    step_penalty += p_bike
                    self.total_collision_penalty += p_bike
                    active_event = "CRITICAL PENALTY: -50.0 (BICYCLE COLLISION HAZARD!)"
                    break
                    
        # 3. Obstacle Collision Penalty (-P_obstacle: -35.0 for hitting barrel / crate)
        for actor in actors:
            if getattr(actor, 'actor_type', '') == 'OBSTACLE':
                dx = actor.x - robot.x
                dz = actor.z - robot.z
                dist_obs = math.sqrt(dx**2 + dz**2)
                if dist_obs < 1.05 and self.obstacle_cooldown <= 0:
                    self.obstacle_cooldown = 1.5 # 1.5s cooldown
                    p_obs = 35.0
                    step_penalty += p_obs
                    self.total_obstacle_penalty += p_obs
                    active_event = "PENALTY: -35.0 (COLLISION WITH SIDEWALK OBSTACLE / BARREL!)"
                    break
                    
        # 4. Pedestrian Collision / Contact Penalty (-P_ped: -25.0 instant for bumping)
        for actor in actors:
            if getattr(actor, 'actor_type', '') == 'PEDESTRIAN':
                dx = actor.x - robot.x
                dz = actor.z - robot.z
                dist_ped = math.sqrt(dx**2 + dz**2)
                if dist_ped < 1.10 and robot.speed > 0.15 and self.pedestrian_cooldown <= 0:
                    self.pedestrian_cooldown = 1.5
                    p_ped_bump = 25.0
                    step_penalty += p_ped_bump
                    self.total_pedestrian_penalty += p_ped_bump
                    active_event = "PENALTY: -25.0 (PEDESTRIAN COLLISION / PHYSICAL INTRUSION!)"
                    break
                    
        # 5. Pedestrian Safe Buffer Encroachment (Moving towards pedestrian < 1.4m)
        if safety_engine and getattr(safety_engine, 'blocking_actor_name', '') == 'PEDESTRIAN':
            ped_dist = getattr(safety_engine, 'obstacle_ahead_distance', 999.0)
            if ped_dist < 1.4 and robot.speed > 0.25:
                p_ped = 25.0 * dt
                step_penalty += p_ped
                self.total_pedestrian_penalty += p_ped
                if not active_event:
                    active_event = "PENALTY: PEDESTRIAN BUFFER ENCROACHMENT (<1.4m)"
            elif ped_dist < 2.5 and robot.speed <= 0.15:
                # Courteous yielding bonus
                r_yield = 0.08 * dt
                step_reward += r_yield
                
        # 6. Weather Overspeed Penalty (-P_weather)
        if weather_sys:
            max_spd = weather_sys.get_speed_limit()
            if robot.speed > max_spd + 0.20:
                p_wspd = 12.0 * dt
                step_penalty += p_wspd
                self.total_overspeed_penalty += p_wspd
                if not active_event:
                    active_event = f"PENALTY: OVERSPEED IN {weather_sys.current_preset.upper()} (MAX {max_spd:.1f} m/s)"
                
        # 7. Step Time Penalty (-P_step)
        step_penalty += 0.005 * dt
        
        # ══════════════════════════════════════════════════════════════
        # C. TOTALS & TELEMETRY
        # ══════════════════════════════════════════════════════════════
        self.total_positive_rewards = self.total_progress_reward + self.total_zebra_reward + self.total_goal_reward
        self.total_penalties = (
            self.total_road_penalty + 
            self.total_collision_penalty + 
            self.total_obstacle_penalty + 
            self.total_pedestrian_penalty + 
            self.total_overspeed_penalty
        )
        
        # Net step reward & cumulative reward
        net_step = step_reward - step_penalty
        self.last_step_reward = net_step
        self.cumulative_reward += net_step
        
        if active_event:
            self.recent_events.append(active_event)
            if len(self.recent_events) > 5:
                self.recent_events.pop(0)
                
        return net_step, self.cumulative_reward
        
    def get_reward_summary(self):
        return {
            "total": self.cumulative_reward,
            "positive_rewards": self.total_positive_rewards,
            "total_penalties": self.total_penalties,
            "progress": self.total_progress_reward,
            "zebra": self.total_zebra_reward,
            "goal": self.total_goal_reward,
            "road_penalty": self.total_road_penalty,
            "collision_penalty": self.total_collision_penalty,
            "obstacle_penalty": self.total_obstacle_penalty,
            "ped_penalty": self.total_pedestrian_penalty,
            "overspeed_penalty": self.total_overspeed_penalty,
        }

