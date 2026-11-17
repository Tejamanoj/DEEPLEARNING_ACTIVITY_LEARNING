"""
City Module: Generates a realistic, deep urban metropolis with storefront facades,
awnings, signs, rooftop architecture, cafe terraces, and distant skyscraper skylines.
"""
from ursina import Entity, color, Vec3, Text, load_texture
from ursina.color import rgb32, rgba32
from environment.common_models import get_cylinder
import os

TEXTURES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "textures")

class City(Entity):
    def __init__(self, road_width=12, sidewalk_width=6.0, length=280, **kwargs):
        super().__init__(**kwargs)
        
        modern_tex = load_texture(os.path.join(TEXTURES_DIR, "facade_modern.png"))
        brick_tex = load_texture(os.path.join(TEXTURES_DIR, "facade_brick.png"))
        
        cyl = get_cylinder()
        
        # Ground foundation expansion: large asphalt city ground plane (400m x 400m)
        Entity(
            parent=self,
            model='cube',
            scale=(400, 0.05, 400),
            position=(0, -0.05, length / 2 - 20),
            color=rgb32(38, 40, 45) # Dark city asphalt ground plane
        )
        
        # 1. DISTANT METROPOLIS SKYLINE SILHOUETTE (Gives immense realistic depth to horizon)
        skyline_z = [-40, 0, 40, 80, 120, 160, 200, 240, 280]
        for idx, sz in enumerate(skyline_z):
            # Right distant skyscrapers
            h_r = 55 + (idx * 17) % 45
            w_r = 22 + (idx * 5) % 15
            Entity(
                parent=self,
                model='cube',
                texture=modern_tex,
                texture_scale=(int(w_r / 4), int(h_r / 4)),
                scale=(w_r, h_r, 22),
                position=(52 + (idx % 3) * 6, h_r / 2, sz),
                color=rgb32(190, 205, 225)
            )
            # Left distant skyscrapers
            h_l = 60 + ((idx + 2) * 19) % 50
            w_l = 24 + (idx * 7) % 14
            Entity(
                parent=self,
                model='cube',
                texture=modern_tex,
                texture_scale=(int(w_l / 4), int(h_l / 4)),
                scale=(w_l, h_l, 22),
                position=(-(52 + (idx % 3) * 6), h_l / 2, sz + 8),
                color=rgb32(185, 200, 220)
            )
            
        # 2. DETAILED FOREGROUND BUILDINGS WITH STOREFRONTS & CAFE TERRACES
        building_offset_x = (road_width / 2 + 0.35) + sidewalk_width + 3.8
        
        building_specs = [
            {"depth": 24, "height": 34, "style": "modern", "tint": rgb32(230, 238, 248), "name": "METRO TECH TOWER"},
            {"depth": 20, "height": 26, "style": "brick",  "tint": rgb32(235, 205, 195), "name": "PARK APARTMENTS"},
            {"depth": 22, "height": 38, "style": "modern", "tint": rgb32(215, 230, 245), "name": "INNOVATION HUB"},
            {"depth": 18, "height": 22, "style": "retail", "tint": rgb32(248, 244, 236), "name": "CITY CAFE & BAKERY"},
            {"depth": 22, "height": 30, "style": "brick",  "tint": rgb32(225, 200, 190), "name": "MADISON BOUTIQUE"},
            {"depth": 26, "height": 42, "style": "modern", "tint": rgb32(220, 235, 252), "name": "SKYLINE PLAZA"},
        ]
        
        # Build East City Block (Right Side)
        curr_z = -16
        idx = 0
        while curr_z < length - 15:
            spec = building_specs[idx % len(building_specs)]
            b_width = 18
            b_depth = spec["depth"]
            b_height = spec["height"]
            b_x = building_offset_x + b_width / 2
            b_z = curr_z + b_depth / 2
            
            tex = modern_tex if spec["style"] == "modern" else brick_tex
            
            # Main Building Tower
            Entity(
                parent=self,
                model='cube',
                texture=tex,
                texture_scale=(int(b_width / 4), int(b_height / 4)),
                scale=(b_width, b_height, b_depth),
                position=(b_x, b_height / 2, b_z),
                color=spec["tint"],
                collider='box'
            )
            
            # Ground floor glass storefront frame
            Entity(
                parent=self,
                model='cube',
                scale=(0.35, 4.2, b_depth - 1.5),
                position=(b_x - b_width / 2 - 0.18, 2.1, b_z),
                color=rgb32(38, 42, 50)
            )
            
            # Overhanging Storefront Awning
            if spec["style"] in ["retail", "brick"]:
                awning_c = rgb32(185, 42, 42) if (idx % 2 == 0) else rgb32(35, 95, 175)
                Entity(
                    parent=self,
                    model='cube',
                    scale=(2.2, 0.18, 9.5),
                    rotation_z=14,
                    position=(b_x - b_width / 2 - 1.1, 4.1, b_z),
                    color=awning_c
                )
                
            # Rooftop Mechanical Room & Antennas
            Entity(parent=self, model='cube', scale=(b_width * 0.55, 2.8, b_depth * 0.45), position=(b_x, b_height + 1.4, b_z), color=rgb32(85, 90, 100))
            # Rooftop communication mast antenna
            Entity(parent=self, model=cyl, scale=(0.12, 6.5, 0.12), position=(b_x, b_height + 4.5, b_z), color=rgb32(170, 175, 182))
            
            # Cross Street / Alleyway gap between buildings
            curr_z += b_depth + 4.5
            idx += 1
            
        # Build West City Block (Left Side)
        curr_z = -16
        idx = 2
        while curr_z < length - 15:
            spec = building_specs[idx % len(building_specs)]
            b_width = 18
            b_depth = spec["depth"]
            b_height = spec["height"]
            b_x = -(building_offset_x + b_width / 2)
            b_z = curr_z + b_depth / 2
            
            tex = modern_tex if spec["style"] == "modern" else brick_tex
            
            Entity(
                parent=self,
                model='cube',
                texture=tex,
                texture_scale=(int(b_width / 4), int(b_height / 4)),
                scale=(b_width, b_height, b_depth),
                position=(b_x, b_height / 2, b_z),
                color=spec["tint"],
                collider='box'
            )
            
            Entity(parent=self, model='cube', scale=(0.35, 4.2, b_depth - 1.5), position=(b_x + b_width / 2 + 0.18, 2.1, b_z), color=rgb32(38, 42, 50))
            Entity(parent=self, model='cube', scale=(b_width * 0.5, 2.6, b_depth * 0.4), position=(b_x, b_height + 1.3, b_z), color=rgb32(85, 90, 100))
            
            curr_z += b_depth + 5.0
            idx += 1
