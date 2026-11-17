"""
Road Module: Creates the main roadway, lane markings, zebra crossing, curbs,
road stormwater drains, and manhole covers for a realistic urban scene.
"""
from ursina import Entity, color, Vec3, load_texture
from ursina.color import rgb32, rgba32
import os

TEXTURES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "textures")

class Road(Entity):
    def __init__(self, length=280, road_width=12, **kwargs):
        super().__init__(**kwargs)
        self.length = length
        self.road_width = road_width
        
        asphalt_tex = load_texture(os.path.join(TEXTURES_DIR, "asphalt.png"))
        curb_tex = load_texture(os.path.join(TEXTURES_DIR, "curb.png"))
        zebra_tex = load_texture(os.path.join(TEXTURES_DIR, "zebra_crossing.png"))
        manhole_tex = load_texture(os.path.join(TEXTURES_DIR, "manhole.png"))
        drain_tex = load_texture(os.path.join(TEXTURES_DIR, "drain_grate.png"))
        
        # 1. Main Asphalt Roadway Surface
        self.road_surface = Entity(
            parent=self,
            model='cube',
            texture=asphalt_tex,
            texture_scale=(4, int(length / 4)),
            scale=(road_width, 0.1, length),
            position=(0, 0, length / 2 - 20),
            color=rgb32(200, 200, 205),
            collider='box'
        )
        
        # 2. Road Lane Markings (Dashed Center Line)
        dash_len = 3.0
        gap_len = 3.0
        z_start = -15
        z_end = length - 25
        curr_z = z_start
        
        self.dashes = []
        while curr_z < z_end:
            # Avoid dashed lines inside Zebra crossing zones (z=32 and z=160)
            in_zebra1 = (26 <= curr_z <= 38)
            in_zebra2 = (154 <= curr_z <= 166)
            if not in_zebra1 and not in_zebra2:
                dash = Entity(
                    parent=self,
                    model='quad',
                    scale=(0.25, dash_len),
                    rotation_x=90,
                    position=(0, 0.06, curr_z + dash_len / 2),
                    color=rgb32(250, 210, 40)
                )
                self.dashes.append(dash)
            curr_z += dash_len + gap_len
            
        # 3. Solid White Road Edge Lines
        Entity(parent=self, model='quad', scale=(0.2, length), rotation_x=90, position=(-(road_width / 2 - 0.3), 0.06, length / 2 - 20), color=color.white)
        Entity(parent=self, model='quad', scale=(0.2, length), rotation_x=90, position=(road_width / 2 - 0.3, 0.06, length / 2 - 20), color=color.white)
        
        # 4. Zebra Crossing 1 (South Crosswalk at z=32)
        self.zebra_crossing_1 = Entity(
            parent=self,
            model='cube',
            texture=zebra_tex,
            texture_scale=(1, 3),
            scale=(road_width + 0.1, 0.12, 7.5),
            position=(0, 0.01, 32),
            color=rgb32(240, 240, 245)
        )
        # Stop Lines before Zebra Crossing 1
        Entity(parent=self, model='quad', scale=(road_width / 2 - 0.5, 0.6), rotation_x=90, position=(road_width / 4, 0.07, 26.5), color=color.white)
        Entity(parent=self, model='quad', scale=(road_width / 2 - 0.5, 0.6), rotation_x=90, position=(-road_width / 4, 0.07, 37.5), color=color.white)

        # Zebra Crossing 2 (North Crosswalk at z=160)
        self.zebra_crossing_2 = Entity(
            parent=self,
            model='cube',
            texture=zebra_tex,
            texture_scale=(1, 3),
            scale=(road_width + 0.1, 0.12, 7.5),
            position=(0, 0.01, 160),
            color=rgb32(240, 240, 245)
        )
        # Stop Lines before Zebra Crossing 2
        Entity(parent=self, model='quad', scale=(road_width / 2 - 0.5, 0.6), rotation_x=90, position=(road_width / 4, 0.07, 154.5), color=color.white)
        Entity(parent=self, model='quad', scale=(road_width / 2 - 0.5, 0.6), rotation_x=90, position=(-road_width / 4, 0.07, 165.5), color=color.white)
        
        # 5. Realistic Manhole Covers & Storm Drains across full 280m length
        for mz in [5, 48, 85, 125, 185, 225]:
            Entity(parent=self, model='quad', texture=manhole_tex, scale=(1.2, 1.2), rotation_x=90, position=(1.8, 0.065, mz))
            
        for dz in [-5, 20, 50, 80, 110, 145, 175, 205, 235]:
            Entity(parent=self, model='quad', texture=drain_tex, scale=(0.65, 1.1), rotation_x=90, position=(road_width / 2 - 0.45, 0.065, dz))
            Entity(parent=self, model='quad', texture=drain_tex, scale=(0.65, 1.1), rotation_x=90, position=(-(road_width / 2 - 0.45), 0.065, dz + 12))
            
        # 6. Granite Curbs separating Road and Sidewalk
        curb_w = 0.35
        curb_h = 0.35
        self.left_curb = Entity(
            parent=self,
            model='cube',
            texture=curb_tex,
            texture_scale=(1, int(length / 2)),
            scale=(curb_w, curb_h, length),
            position=(-(road_width / 2 + curb_w / 2), curb_h / 2, length / 2 - 20),
            color=rgb32(200, 200, 205)
        )
        self.right_curb = Entity(
            parent=self,
            model='cube',
            texture=curb_tex,
            texture_scale=(1, int(length / 2)),
            scale=(curb_w, curb_h, length),
            position=(road_width / 2 + curb_w / 2, curb_h / 2, length / 2 - 20),
            color=rgb32(200, 200, 205)
        )
