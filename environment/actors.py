"""
Actors Module: Creates dynamic moving pedestrians with walking animations
and collision-aware mutual avoidance so they never walk through the robot,
plus roadway vehicles, bicycles, and sidewalk obstacles.
"""
from ursina import Entity, color, Vec3, Text
from ursina.color import rgb32, rgba32
from environment.common_models import get_cylinder, get_cone
import math
import random

class Pedestrian(Entity):
    def __init__(self, position=(8.75, 0.28, 15), path_start=15, path_end=45, speed=1.2, 
                 crosses_street=False, crossing_y_range=(-5, 12), shirt_color=None, **kwargs):
        super().__init__(position=position, **kwargs)
        self.actor_type = "PEDESTRIAN"
        self.speed = speed
        self.path_start = path_start
        self.path_end = path_end
        self.direction = 1
        self.crosses_street = crosses_street
        self.crossing_y_range = crossing_y_range
        self.walk_time = random.uniform(0, 10)
        self.is_yielding = False
        
        cyl = get_cylinder()
        skin_c = rgb32(235, 195, 165)
        shirt_c = shirt_color if shirt_color else rgb32(40, 110, 200)
        pants_c = rgb32(45, 50, 60)
        hair_c = rgb32(60, 40, 25)
        
        # 1. Torso
        self.torso = Entity(parent=self, model='cube', scale=(0.55, 0.70, 0.32), position=(0, 1.25, 0), color=shirt_c)
        
        # 2. Head & Hair
        self.head = Entity(parent=self, model='sphere', scale=(0.32, 0.36, 0.32), position=(0, 1.82, 0), color=skin_c)
        self.hair = Entity(parent=self.head, model='sphere', scale=(1.05, 0.65, 1.05), position=(0, 0.25, -0.05), color=hair_c)
        
        # 3. Arms
        self.arm_left = Entity(parent=self, model=cyl, scale=(0.14, 0.65, 0.14), position=(-0.36, 1.15, 0), color=shirt_c)
        self.arm_right = Entity(parent=self, model=cyl, scale=(0.14, 0.65, 0.14), position=(0.36, 1.15, 0), color=shirt_c)
        
        # 4. Legs
        self.leg_left = Entity(parent=self, model=cyl, scale=(0.18, 0.85, 0.18), position=(-0.16, 0.45, 0), color=pants_c)
        self.leg_right = Entity(parent=self, model=cyl, scale=(0.18, 0.85, 0.18), position=(0.16, 0.45, 0), color=pants_c)
        
        # 5. Shoes
        Entity(parent=self.leg_left, model='cube', scale=(1.2, 0.2, 1.8), position=(0, -0.45, 0.3), color=rgb32(20, 20, 25))
        Entity(parent=self.leg_right, model='cube', scale=(1.2, 0.2, 1.8), position=(0, -0.45, 0.3), color=rgb32(20, 20, 25))
        
        self.radius = 0.55
        self.height = 1.9
        
    def update_walk(self, dt, robot_pos=None):
        # Check proximity to robot: wait politely if face-to-face to prevent clipping
        self.is_yielding = False
        if robot_pos:
            dx = robot_pos.x - self.x
            dz = robot_pos.z - self.z
            dist_to_robot = math.sqrt(dx**2 + dz**2)
            # Yield when robot is directly ahead to prevent clipping
            if dist_to_robot < 1.8 and abs(dx) < 0.85:
                self.is_yielding = True
                
        if self.is_yielding:
            # Stand and wait politely without walking through robot
            self.leg_left.rotation_x *= 0.85
            self.leg_right.rotation_x *= 0.85
            self.arm_left.rotation_x *= 0.85
            self.arm_right.rotation_x *= 0.85
            return
            
        self.walk_time += dt * (self.speed * 4.5)
        
        swing_angle = math.sin(self.walk_time) * 32.0
        self.leg_left.rotation_x = swing_angle
        self.leg_right.rotation_x = -swing_angle
        self.arm_left.rotation_x = -swing_angle * 0.75
        self.arm_right.rotation_x = swing_angle * 0.75
        self.torso.y = 1.25 + abs(math.sin(self.walk_time * 2.0)) * 0.04
        self.head.y = 1.82 + abs(math.sin(self.walk_time * 2.0)) * 0.04
        
        if not self.crosses_street:
            self.z += self.direction * self.speed * dt
            if self.direction > 0:
                self.rotation_y = 0
                if self.z > self.path_end:
                    self.direction = -1
            else:
                self.rotation_y = 180
                if self.z < self.path_start:
                    self.direction = 1
        else:
            self.x += self.direction * self.speed * dt
            if self.direction > 0:
                self.rotation_y = 90
                if self.x > self.crossing_y_range[1]:
                    self.direction = -1
            else:
                self.rotation_y = -90
                if self.x < self.crossing_y_range[0]:
                    self.direction = 1

class Vehicle(Entity):
    def __init__(self, position=(3.0, 0.1, 0), direction=1, speed=5.5, car_color=None, **kwargs):
        super().__init__(position=position, **kwargs)
        self.actor_type = "VEHICLE"
        self.speed = speed
        self.direction = direction
        self.rotation_y = 0 if direction > 0 else 180
        
        cyl = get_cylinder()
        body_c = car_color if car_color else rgb32(210, 45, 45)
        glass_c = rgb32(40, 50, 65)
        tire_c = rgb32(25, 25, 28)
        rim_c = rgb32(180, 185, 190)
        
        self.chassis = Entity(parent=self, model='cube', scale=(2.1, 0.65, 4.4), position=(0, 0.55, 0), color=body_c)
        self.cabin = Entity(parent=self, model='cube', scale=(1.8, 0.55, 2.3), position=(0, 1.10, -0.2), color=glass_c)
        self.roof = Entity(parent=self, model='cube', scale=(1.75, 0.08, 2.1), position=(0, 1.40, -0.2), color=body_c)
        
        Entity(parent=self, model='quad', scale=(0.4, 0.2), position=(-0.75, 0.65, 2.21), color=rgb32(255, 255, 220))
        Entity(parent=self, model='quad', scale=(0.4, 0.2), position=(0.75, 0.65, 2.21), color=rgb32(255, 255, 220))
        Entity(parent=self, model='quad', rotation_y=180, scale=(0.4, 0.2), position=(-0.75, 0.65, -2.21), color=rgb32(240, 25, 25))
        Entity(parent=self, model='quad', rotation_y=180, scale=(0.4, 0.2), position=(0.75, 0.65, -2.21), color=rgb32(240, 25, 25))
        
        self.wheels = []
        wheel_r = 0.38
        wheel_w = 0.24
        wheel_coords = [(-1.05, wheel_r, 1.35), (1.05, wheel_r, 1.35), (-1.05, wheel_r, -1.35), (1.05, wheel_r, -1.35)]
        for wpos in wheel_coords:
            wh = Entity(parent=self, position=wpos)
            Entity(parent=wh, model=cyl, rotation_z=90, scale=(wheel_r*2, wheel_w, wheel_r*2), color=tire_c)
            Entity(parent=wh, model=cyl, rotation_z=90, scale=(wheel_r*1.3, wheel_w+0.02, wheel_r*1.3), color=rim_c)
            self.wheels.append(wh)
            
        self.radius = 1.4
        self.height = 1.6
        
    def update_drive(self, dt, min_z=-20, max_z=270, robot_pos=None):
        # Crosswalk yield check: vehicles must stop for pedestrians/robots on zebra crossings!
        should_stop = False
        if robot_pos:
            # Check if robot is crossing the roadway
            if abs(robot_pos.x) < 6.4:
                # Zebra Crossing 1 at z=32 (stop lines at 26.5 and 37.5)
                if 28.0 <= robot_pos.z <= 36.0:
                    if self.direction > 0 and 19.5 <= self.z <= 26.5:
                        should_stop = True
                    elif self.direction < 0 and 37.5 <= self.z <= 44.5:
                        should_stop = True
                # Zebra Crossing 2 at z=160 (stop lines at 154.5 and 165.5)
                elif 156.0 <= robot_pos.z <= 164.0:
                    if self.direction > 0 and 147.5 <= self.z <= 154.5:
                        should_stop = True
                    elif self.direction < 0 and 165.5 <= self.z <= 172.5:
                        should_stop = True
            
            # Direct safety bumper: stop if robot is within braking distance in vehicle lane
            dx = robot_pos.x - self.x
            dz = (robot_pos.z - self.z) * self.direction
            if abs(dx) < 1.8 and 0.5 < dz < 4.5:
                should_stop = True

        if should_stop:
            return # Vehicle yields at stop line
            
        self.z += self.direction * self.speed * dt
        deg = (self.speed * dt / 0.38) * (180.0 / math.pi) * self.direction
        for w in self.wheels:
            w.rotation_x += deg
            
        if self.direction > 0 and self.z > max_z:
            self.z = min_z
        elif self.direction < 0 and self.z < min_z:
            self.z = max_z

class Bicycle(Entity):
    def __init__(self, position=(5.2, 0.1, 10), speed=3.2, **kwargs):
        super().__init__(position=position, **kwargs)
        self.actor_type = "BICYCLE"
        self.speed = speed
        self.direction = 1
        
        cyl = get_cylinder()
        frame_c = rgb32(30, 160, 240)
        tire_c = rgb32(25, 25, 28)
        rider_c = rgb32(230, 120, 30)
        
        self.wheel_front = Entity(parent=self, model=cyl, rotation_z=90, scale=(0.7, 0.08, 0.7), position=(0, 0.35, 0.75), color=tire_c)
        self.wheel_back = Entity(parent=self, model=cyl, rotation_z=90, scale=(0.7, 0.08, 0.7), position=(0, 0.35, -0.75), color=tire_c)
        Entity(parent=self, model='cube', scale=(0.06, 0.06, 1.4), position=(0, 0.45, 0), color=frame_c)
        Entity(parent=self, model='cube', scale=(0.06, 0.55, 0.06), position=(0, 0.65, 0.55), rotation_x=15, color=frame_c)
        Entity(parent=self, model='cube', scale=(0.06, 0.55, 0.06), position=(0, 0.65, -0.35), rotation_x=-15, color=frame_c)
        Entity(parent=self, model='cube', scale=(0.65, 0.05, 0.05), position=(0, 0.95, 0.65), color=rgb32(40, 45, 50))
        
        self.rider_torso = Entity(parent=self, model='cube', scale=(0.4, 0.55, 0.28), position=(0, 1.15, -0.15), rotation_x=18, color=rider_c)
        self.rider_head = Entity(parent=self, model='sphere', scale=(0.28, 0.30, 0.28), position=(0, 1.62, 0.05), color=rgb32(235, 195, 165))
        Entity(parent=self.rider_head, model='sphere', scale=(1.1, 0.7, 1.1), position=(0, 0.15, 0), color=rgb32(255, 220, 20))
        
        self.radius = 0.8
        self.height = 1.7
        
    def update_ride(self, dt, min_z=-20, max_z=120):
        self.z += self.direction * self.speed * dt
        deg = (self.speed * dt / 0.35) * (180.0 / math.pi)
        self.wheel_front.rotation_x += deg
        self.wheel_back.rotation_x += deg
        if self.z > max_z:
            self.z = min_z

class RoadObstacle(Entity):
    def __init__(self, position=(8.75, 0.28, 54), obstacle_type="construction_barrel", **kwargs):
        super().__init__(position=position, **kwargs)
        self.actor_type = "OBSTACLE"
        cyl = get_cylinder()
        
        if obstacle_type == "construction_barrel":
            Entity(parent=self, model=cyl, scale=(0.7, 1.1, 0.7), position=(0, 0.55, 0), color=rgb32(255, 95, 15))
            Entity(parent=self, model=cyl, scale=(0.72, 0.22, 0.72), position=(0, 0.55, 0), color=rgb32(245, 245, 250))
            Entity(parent=self, model=cyl, scale=(0.72, 0.18, 0.72), position=(0, 0.85, 0), color=rgb32(245, 245, 250))
            Entity(parent=self, model=cyl, scale=(0.85, 0.12, 0.85), position=(0, 0.06, 0), color=rgb32(30, 30, 35))
            
        self.radius = 0.55
        self.height = 1.1

class DynamicActorManager:
    def __init__(self):
        self.pedestrians = []
        self.vehicles = []
        self.bicycles = []
        self.obstacles = []
        
        # Pedestrian 1: Walking ahead along east sidewalk
        p1 = Pedestrian(position=(8.75, 0.28, 12), path_start=8, path_end=24, speed=1.1, shirt_color=rgb32(40, 110, 200))
        self.pedestrians.append(p1)
        
        # Pedestrian 2: Crossing street at South Zebra Crossing (z=34.0, upper lane of 7.5m crosswalk)
        p2 = Pedestrian(position=(-7.0, 0.05, 34.0), path_start=0, path_end=0, speed=1.3, 
                        crosses_street=True, crossing_y_range=(-7.5, 9.5), shirt_color=rgb32(220, 50, 50))
        self.pedestrians.append(p2)
        
        # Pedestrian 3: Walking along west sidewalk in tech district
        p3 = Pedestrian(position=(-9.4, 0.28, 80), path_start=60, path_end=110, speed=1.4, shirt_color=rgb32(40, 180, 110))
        self.pedestrians.append(p3)

        # Pedestrian 4: Crossing street at North Zebra Crossing (z=162.0, upper lane of 7.5m crosswalk)
        p4 = Pedestrian(position=(7.5, 0.05, 162.0), path_start=0, path_end=0, speed=1.2,
                        crosses_street=True, crossing_y_range=(-7.5, 9.5), shirt_color=rgb32(230, 140, 30))
        self.pedestrians.append(p4)

        # Pedestrian 5: Jogger near Central Terminal
        p5 = Pedestrian(position=(9.4, 0.28, 200), path_start=185, path_end=225, speed=1.6, shirt_color=rgb32(180, 60, 210))
        self.pedestrians.append(p5)
        self.pedestrians.append(p5)
        
        # Roadway Vehicles across 280m roadway
        v1 = Vehicle(position=(3.2, 0.06, -5), direction=1, speed=6.2, car_color=rgb32(215, 45, 45))
        self.vehicles.append(v1)
        v2 = Vehicle(position=(-3.2, 0.06, 75), direction=-1, speed=6.8, car_color=rgb32(45, 115, 215))
        self.vehicles.append(v2)
        v3 = Vehicle(position=(3.2, 0.06, 130), direction=1, speed=5.8, car_color=rgb32(240, 200, 35))
        self.vehicles.append(v3)
        v4 = Vehicle(position=(-3.2, 0.06, 210), direction=-1, speed=6.4, car_color=rgb32(40, 190, 120))
        self.vehicles.append(v4)
        
        # Bicycles on Road Shoulders
        b1 = Bicycle(position=(5.6, 0.06, -10), speed=3.6)
        self.bicycles.append(b1)
        b2 = Bicycle(position=(-5.6, 0.06, 120), speed=3.4)
        self.bicycles.append(b2)
        
        # Sidewalk Obstacles (Construction barrels)
        # Barrel 1 on East sidewalk at z=54
        obs1 = RoadObstacle(position=(8.75, 0.28, 54), obstacle_type="construction_barrel")
        self.obstacles.append(obs1)
        # Barrel 2 on West sidewalk at z=115
        obs2 = RoadObstacle(position=(-8.75, 0.28, 115), obstacle_type="construction_barrel")
        self.obstacles.append(obs2)
        
    def get_all_trackable_actors(self):
        return self.pedestrians + self.vehicles + self.bicycles + self.obstacles
        
    def update(self, dt, robot_pos=None):
        for p in self.pedestrians:
            p.update_walk(dt, robot_pos=robot_pos)
        for v in self.vehicles:
            v.update_drive(dt, min_z=-20, max_z=270, robot_pos=robot_pos)
        for b in self.bicycles:
            b.update_ride(dt, min_z=-20, max_z=270)
