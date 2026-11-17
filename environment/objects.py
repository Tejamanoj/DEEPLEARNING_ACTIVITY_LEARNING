"""
Objects Module: Populates street furniture, trees, streetlights, traffic signs,
pedestrian traffic light signals, bus stop shelter, planters, and navigation depot markers.
"""
from ursina import Entity, color, Vec3, Text, load_texture, camera
from ursina.color import rgb32, rgba32
from environment.common_models import get_cylinder, get_cone
import math

class Tree(Entity):
    def __init__(self, position=(0, 0, 0), scale=1.0, **kwargs):
        super().__init__(position=position, **kwargs)
        cyl = get_cylinder()
        # Textured wooden trunk
        self.trunk = Entity(
            parent=self,
            model=cyl,
            scale=(0.38 * scale, 3.4 * scale, 0.38 * scale),
            position=(0, 1.7 * scale, 0),
            color=rgb32(95, 62, 38)
        )
        # Tree planter ring around base
        Entity(parent=self, model=cyl, scale=(1.4 * scale, 0.18 * scale, 1.4 * scale), position=(0, 0.09 * scale, 0), color=rgb32(65, 70, 78))
        
        # Layered organic foliage canopy
        foliage_colors = [
            rgb32(40, 115, 45),
            rgb32(52, 135, 55),
            rgb32(35, 98, 40)
        ]
        self.canopy1 = Entity(parent=self, model='sphere', scale=(2.8 * scale, 2.4 * scale, 2.8 * scale), position=(0, 3.9 * scale, 0), color=foliage_colors[0])
        self.canopy2 = Entity(parent=self, model='sphere', scale=(2.4 * scale, 2.1 * scale, 2.4 * scale), position=(0.25 * scale, 4.9 * scale, -0.2 * scale), color=foliage_colors[1])
        self.canopy3 = Entity(parent=self, model='sphere', scale=(1.8 * scale, 1.6 * scale, 1.8 * scale), position=(-0.15 * scale, 5.7 * scale, 0.15 * scale), color=foliage_colors[2])

class StreetLight(Entity):
    def __init__(self, position=(0, 0, 0), rotate_y=0, **kwargs):
        super().__init__(position=position, rotation_y=rotate_y, **kwargs)
        pole_color = rgb32(45, 50, 56)
        cyl = get_cylinder()
        
        Entity(parent=self, model=cyl, scale=(0.55, 0.22, 0.55), position=(0, 0.11, 0), color=pole_color)
        Entity(parent=self, model=cyl, scale=(0.18, 6.8, 0.18), position=(0, 3.4, 0), color=pole_color)
        Entity(parent=self, model='cube', scale=(0.14, 0.14, 1.9), position=(0, 6.6, 0.85), rotation_x=12, color=pole_color)
        Entity(parent=self, model='cube', scale=(0.38, 0.16, 0.65), position=(0, 6.3, 1.7), color=pole_color)
        self.lens = Entity(parent=self, model='quad', scale=(0.32, 0.55), rotation_x=90, position=(0, 6.21, 1.7), color=rgb32(255, 245, 210))
        # Warm ambient street illumination puddle on ground
        self.ground_pool = Entity(parent=self, model='quad', rotation_x=90, scale=(4.2, 5.2), position=(0, 0.02, 1.7), color=rgba32(255, 238, 175, 45))

class PedestrianTrafficSignal(Entity):
    def __init__(self, position=(0, 0, 0), rotate_y=0, **kwargs):
        super().__init__(position=position, rotation_y=rotate_y, **kwargs)
        cyl = get_cylinder()
        pole_color = rgb32(50, 55, 62)
        
        # Post
        Entity(parent=self, model=cyl, scale=(0.14, 3.8, 0.14), position=(0, 1.9, 0), color=pole_color)
        # Signal Box
        self.box = Entity(parent=self, model='cube', scale=(0.42, 0.85, 0.35), position=(0, 3.1, 0), color=rgb32(28, 30, 35))
        # Red Hand (Don't Walk) & White Walking Person lenses
        self.red_light = Entity(parent=self.box, model='sphere', scale=(0.22, 0.22, 0.12), position=(0, 0.22, 0.18), color=rgb32(255, 35, 35))
        self.green_light = Entity(parent=self.box, model='sphere', scale=(0.22, 0.22, 0.12), position=(0, -0.22, 0.18), color=rgb32(40, 220, 110))

class BusStopShelter(Entity):
    def __init__(self, position=(0, 0, 0), rotate_y=0, **kwargs):
        super().__init__(position=position, rotation_y=rotate_y, **kwargs)
        frame_c = rgb32(45, 52, 60)
        glass_c = rgba32(140, 185, 215, 90)
        
        # Roof Canopy
        Entity(parent=self, model='cube', scale=(3.6, 0.12, 1.8), position=(0, 2.7, 0), color=frame_c)
        # Back glass panel
        Entity(parent=self, model='cube', scale=(3.4, 2.4, 0.06), position=(0, 1.35, -0.8), color=glass_c)
        # Side glass panel
        Entity(parent=self, model='cube', scale=(0.06, 2.4, 1.6), position=(1.7, 1.35, 0), color=glass_c)
        # Metal Support Pillars
        Entity(parent=self, model='cube', scale=(0.12, 2.7, 0.12), position=(-1.7, 1.35, 0.8), color=frame_c)
        Entity(parent=self, model='cube', scale=(0.12, 2.7, 0.12), position=(1.7, 1.35, 0.8), color=frame_c)
        # Interior Transit Bench
        Entity(parent=self, model='cube', scale=(2.6, 0.1, 0.45), position=(0, 0.52, -0.45), color=rgb32(145, 95, 55))

class PlanterBox(Entity):
    def __init__(self, position=(0, 0, 0), **kwargs):
        super().__init__(position=position, **kwargs)
        # Concrete planter container
        Entity(parent=self, model='cube', scale=(1.8, 0.65, 0.75), position=(0, 0.32, 0), color=rgb32(185, 188, 192))
        # Soil
        Entity(parent=self, model='cube', scale=(1.6, 0.1, 0.6), position=(0, 0.62, 0), color=rgb32(60, 42, 28))
        # Flowers and shrubs
        Entity(parent=self, model='sphere', scale=(0.6, 0.45, 0.5), position=(-0.45, 0.82, 0), color=rgb32(45, 135, 60))
        Entity(parent=self, model='sphere', scale=(0.55, 0.42, 0.5), position=(0.45, 0.82, 0), color=rgb32(45, 135, 60))
        # Blossoms
        Entity(parent=self, model='sphere', scale=(0.25, 0.25, 0.25), position=(-0.45, 1.0, 0), color=rgb32(235, 55, 95))
        Entity(parent=self, model='sphere', scale=(0.25, 0.25, 0.25), position=(0.45, 1.0, 0), color=rgb32(255, 205, 40))

class Bollard(Entity):
    def __init__(self, position=(0, 0, 0), **kwargs):
        super().__init__(position=position, **kwargs)
        cyl = get_cylinder()
        Entity(parent=self, model=cyl, scale=(0.22, 0.95, 0.22), position=(0, 0.47, 0), color=rgb32(40, 45, 52))
        # Reflective yellow collar
        Entity(parent=self, model=cyl, scale=(0.24, 0.14, 0.24), position=(0, 0.78, 0), color=rgb32(255, 215, 30))

class Bench(Entity):
    def __init__(self, position=(0, 0, 0), rotate_y=0, **kwargs):
        super().__init__(position=position, rotation_y=rotate_y, **kwargs)
        wood_c = rgb32(145, 90, 50)
        metal_c = rgb32(40, 45, 50)
        
        Entity(parent=self, model='cube', scale=(0.1, 0.65, 0.7), position=(-0.9, 0.32, 0), color=metal_c)
        Entity(parent=self, model='cube', scale=(0.1, 0.65, 0.7), position=(0.9, 0.32, 0), color=metal_c)
        for oz in [-0.2, 0.0, 0.2]:
            Entity(parent=self, model='cube', scale=(1.9, 0.06, 0.16), position=(0, 0.45, oz), color=wood_c)
        for oy in [0.7, 0.9]:
            Entity(parent=self, model='cube', scale=(1.9, 0.16, 0.06), position=(0, oy, -0.32), color=wood_c)

class TrashBin(Entity):
    def __init__(self, position=(0, 0, 0), **kwargs):
        super().__init__(position=position, **kwargs)
        cyl = get_cylinder()
        Entity(parent=self, model=cyl, scale=(0.55, 1.1, 0.55), position=(0, 0.55, 0), color=rgb32(40, 110, 80))
        Entity(parent=self, model=cyl, scale=(0.6, 0.15, 0.6), position=(0, 1.15, 0), color=rgb32(30, 35, 40))

class TrafficSign(Entity):
    def __init__(self, position=(0, 0, 0), sign_type="crosswalk", rotate_y=0, **kwargs):
        super().__init__(position=position, rotation_y=rotate_y, **kwargs)
        cyl = get_cylinder()
        Entity(parent=self, model=cyl, scale=(0.08, 3.4, 0.08), position=(0, 1.7, 0), color=rgb32(180, 185, 190))
        
        if sign_type == "crosswalk":
            self.board = Entity(parent=self, model='cube', scale=(0.7, 0.7, 0.04), position=(0, 3.1, 0), color=rgb32(30, 110, 220))
            Entity(parent=self, model='quad', scale=(0.45, 0.45), rotation_z=45, position=(0, 3.1, 0.025), color=color.white)
            Entity(parent=self, model='sphere', scale=(0.08, 0.08, 0.01), position=(0, 3.22, 0.03), color=color.black)
            Entity(parent=self, model='quad', scale=(0.07, 0.18), position=(0, 3.08, 0.03), color=color.black)
        elif sign_type == "stop":
            self.board = Entity(parent=self, model=cyl, scale=(0.75, 0.04, 0.75), rotation_x=90, position=(0, 3.1, 0), color=rgb32(215, 35, 35))
            Entity(parent=self, model='quad', scale=(0.6, 0.6), position=(0, 3.1, 0.025), color=color.white)
            Entity(parent=self, model='quad', scale=(0.54, 0.54), position=(0, 3.1, 0.026), color=rgb32(215, 35, 35))
        elif sign_type == "speed_15":
            self.board = Entity(parent=self, model='cube', scale=(0.6, 0.8, 0.04), position=(0, 3.1, 0), color=color.white)
            Entity(parent=self, model='quad', scale=(0.52, 0.72), position=(0, 3.1, 0.025), color=rgb32(245, 245, 245))

class WaypointMarker(Entity):
    def __init__(self, position=(0, 0, 0), label="DELIVERY TARGET #04", marker_color=None, **kwargs):
        super().__init__(position=position, **kwargs)
        self.label_str = label
        cyl = get_cylinder()
        cone = get_cone()
        marker_c = marker_color if marker_color else rgb32(255, 185, 20)
        
        # 1. Concentric Target Rings on ground
        self.outer_ring = Entity(parent=self, model=cyl, scale=(3.4, 0.05, 3.4), position=(0, 0.02, 0), color=rgba32(255, 195, 30, 180))
        self.mid_ring = Entity(parent=self, model=cyl, scale=(2.4, 0.07, 2.4), position=(0, 0.03, 0), color=rgb32(25, 30, 40))
        self.inner_ring = Entity(parent=self, model=cyl, scale=(1.4, 0.09, 1.4), position=(0, 0.04, 0), color=rgb32(255, 225, 50))
        self.center_bullseye = Entity(parent=self, model='sphere', scale=(0.55, 0.25, 0.55), position=(0, 0.12, 0), color=rgb32(0, 255, 180))
        
        # 2. Vertical Target Sky Beacon (Pillar of light)
        self.sky_beam = Entity(
            parent=self,
            model=cyl,
            scale=(1.2, 18.0, 1.2),
            position=(0, 9.0, 0),
            color=rgba32(255, 215, 0, 32)
        )
        
        # 3. Rotating Holographic Diamond / Trophy
        self.beacon = Entity(parent=self, model='cube', scale=(0.95, 0.95, 0.95), rotation=(45, 45, 45), position=(0, 2.6, 0), color=rgb32(255, 205, 30))
        self.inner_core = Entity(parent=self.beacon, model='sphere', scale=(0.6, 0.6, 0.6), position=(0, 0, 0), color=rgb32(0, 255, 220))
        
        # 4. Floating 3D Target Text Billboard
        self.tag = Text(
            text="★ TARGET HUB #04: CENTRAL TERMINAL ★",
            parent=self,
            position=(0, 4.2, 0),
            scale=8.0,
            color=rgb32(255, 225, 40),
            origin=(0, 0)
        )
        
    def update(self):
        dt = 0.016
        if hasattr(self, 'beacon'):
            self.beacon.rotation_y += 75 * dt
            self.beacon.y = 2.6 + 0.22 * math.sin(self.beacon.rotation_y * 0.05)
            self.tag.look_at(camera.world_position)
            self.tag.rotation_y += 180

class CelebrationConfetti(Entity):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.is_active = False
        self.particles = []
        
        # Pre-allocate colorful celebration confetti flakes
        confetti_colors = [
            rgb32(255, 215, 0),   # Gold
            rgb32(0, 255, 180),   # Emerald
            rgb32(255, 45, 110),  # Ruby Magenta
            rgb32(0, 220, 255),   # Cyan
            rgb32(180, 70, 255),  # Violet
            rgb32(255, 255, 255), # White sparkle
        ]
        
        for i in range(75):
            c = confetti_colors[i % len(confetti_colors)]
            p = Entity(
                parent=self,
                model='cube',
                scale=(0.14, 0.14, 0.03),
                position=(0, -10, 0),
                color=c,
                enabled=False
            )
            p.vx = 0.0
            p.vy = 0.0
            p.vz = 0.0
            p.rot_speed = 0.0
            self.particles.append(p)
            
    def trigger(self, spawn_pos):
        """Spawns an energetic firework/confetti explosion celebration!"""
        import random
        self.is_active = True
        for p in self.particles:
            p.enabled = True
            p.position = Vec3(spawn_pos.x + random.uniform(-0.5, 0.5), spawn_pos.y + 0.8, spawn_pos.z + random.uniform(-0.5, 0.5))
            speed = random.uniform(4.5, 9.5)
            angle = random.uniform(0, math.pi * 2)
            elevation = random.uniform(0.4, 0.95)
            p.vx = math.cos(angle) * speed * (1.0 - elevation)
            p.vy = speed * elevation
            p.vz = math.sin(angle) * speed * (1.0 - elevation)
            p.rot_speed = random.uniform(120, 480)
            
    def update(self):
        if not self.is_active:
            return
        dt = 0.016
        for p in self.particles:
            if not p.enabled:
                continue
            p.x += p.vx * dt
            p.y += p.vy * dt
            p.z += p.vz * dt
            p.vy -= 9.8 * dt * 0.45 # Gentle gravity
            p.vx *= 0.98 # Air friction
            p.vz *= 0.98
            p.rotation_x += p.rot_speed * dt
            p.rotation_y += p.rot_speed * dt
            # Reached ground
            if p.y <= 0.05:
                p.y = 0.05
                p.vy = 0
                p.vx = 0
                p.vz = 0

class CityObjects(Entity):
    def __init__(self, road_width=12, sidewalk_width=6.0, length=280, **kwargs):
        super().__init__(**kwargs)
        
        curb_right_x = road_width / 2 + 0.35
        curb_left_x = -(road_width / 2 + 0.35)
        sidewalk_outer_right = curb_right_x + sidewalk_width
        sidewalk_outer_left = curb_left_x - sidewalk_width
        
        # 1. Streetlights along curbs across full 280m map
        for z in [-10, 20, 50, 80, 110, 140, 175, 205, 235, 260]:
            StreetLight(parent=self, position=(curb_right_x + 0.35, 0.28, z), rotate_y=180)
            StreetLight(parent=self, position=(curb_left_x - 0.35, 0.28, z), rotate_y=0)
            
        # 2. Pedestrian Traffic Signals at BOTH Zebra Crossings (z=32 and z=160)
        # Zebra Crossing 1 (z=32)
        PedestrianTrafficSignal(parent=self, position=(curb_right_x + 0.5, 0.28, 27.5), rotate_y=180)
        PedestrianTrafficSignal(parent=self, position=(curb_left_x - 0.5, 0.28, 36.5), rotate_y=0)
        # Zebra Crossing 2 (z=160)
        PedestrianTrafficSignal(parent=self, position=(curb_right_x + 0.5, 0.28, 155.5), rotate_y=180)
        PedestrianTrafficSignal(parent=self, position=(curb_left_x - 0.5, 0.28, 164.5), rotate_y=0)
        
        # 3. Modern Bus Stop Shelters
        BusStopShelter(parent=self, position=(sidewalk_outer_right - 1.2, 0.28, 70), rotate_y=-90)
        BusStopShelter(parent=self, position=(sidewalk_outer_left + 1.2, 0.28, 195), rotate_y=90)
        
        # 4. Safety Bollards along curb ramps at both crosswalks
        for bz in [24, 26, 38, 40, 152, 154, 166, 168]:
            Bollard(parent=self, position=(curb_right_x + 0.15, 0.28, bz))
            Bollard(parent=self, position=(curb_left_x - 0.15, 0.28, bz))
            
        # 5. Planter Boxes with flowers
        for pz in [2, 42, 90, 135, 180, 220]:
            PlanterBox(parent=self, position=(sidewalk_outer_right - 0.9, 0.28, pz))
            PlanterBox(parent=self, position=(sidewalk_outer_left + 0.9, 0.28, pz + 12))
        
        # 6. Trees
        for z in [-12, 10, 22, 52, 85, 110, 145, 175, 210, 245]:
            Tree(parent=self, position=(sidewalk_outer_right + 1.8, 0, z), scale=1.1)
            Tree(parent=self, position=(sidewalk_outer_left - 1.8, 0, z + 6), scale=1.0)
            
        # 7. Park Benches
        for bnz in [18, 58, 105, 148, 200]:
            Bench(parent=self, position=(sidewalk_outer_right - 0.8, 0.28, bnz), rotate_y=-90)
            Bench(parent=self, position=(sidewalk_outer_left + 0.8, 0.28, bnz + 8), rotate_y=90)
        
        # 8. Traffic & Pedestrian Crossing Signs
        TrafficSign(parent=self, position=(curb_right_x + 0.4, 0.28, 25), sign_type="crosswalk", rotate_y=180)
        TrafficSign(parent=self, position=(curb_left_x - 0.4, 0.28, 39), sign_type="crosswalk", rotate_y=0)
        TrafficSign(parent=self, position=(curb_right_x + 0.4, 0.28, 153), sign_type="crosswalk", rotate_y=180)
        TrafficSign(parent=self, position=(curb_left_x - 0.4, 0.28, 167), sign_type="crosswalk", rotate_y=0)
        TrafficSign(parent=self, position=(curb_right_x + 0.4, 0.28, -5), sign_type="speed_15", rotate_y=180)
        TrafficSign(parent=self, position=(curb_right_x + 0.4, 0.28, 255), sign_type="stop", rotate_y=180)
        
        # 9. Start Depot & Destination Target Hub (at z=240 on East Sidewalk)
        self.start_depot = Entity(parent=self, model='cube', scale=(2.6, 0.05, 2.6), position=(curb_right_x + sidewalk_width / 2, 0.29, -6), color=rgb32(40, 180, 110))
        Entity(parent=self.start_depot, model='quad', scale=(1.0, 1.0), rotation_x=90, position=(0, 0.55, 0), color=color.white)
        
        # Grand Delivery Destination Target Hub at z=240
        self.destination_hub = WaypointMarker(parent=self, position=(curb_right_x + sidewalk_width / 2, 0.28, 240), label="TARGET HUB #04: CENTRAL TERMINAL", marker_color=rgb32(255, 185, 20))
        
        # Celebration Confetti & Fireworks System
        self.celebration = CelebrationConfetti(parent=self)
