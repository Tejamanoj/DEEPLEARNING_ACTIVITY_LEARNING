"""
Sidewalk Module: Creates realistic pedestrian sidewalks with paver tiles,
pedestrian plazas, ADA tactile warning paving, curb cuts, and distinct safety boundaries.
"""
from ursina import Entity, color, Vec3, load_texture
from ursina.color import rgb32, rgba32
import os

TEXTURES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "textures")

class Sidewalk(Entity):
    def __init__(self, length=280, road_width=12, sidewalk_width=6.0, **kwargs):
        super().__init__(**kwargs)
        self.length = length
        self.road_width = road_width
        self.sidewalk_width = sidewalk_width
        self.sidewalk_height = 0.28
        
        sidewalk_tex = load_texture(os.path.join(TEXTURES_DIR, "sidewalk.png"))
        tactile_tex = load_texture(os.path.join(TEXTURES_DIR, "tactile_paving.png"))
        curb_tex = load_texture(os.path.join(TEXTURES_DIR, "curb.png"))
        
        self.right_x = (road_width / 2 + 0.35) + sidewalk_width / 2
        self.left_x = -(road_width / 2 + 0.35) - sidewalk_width / 2
        center_z = length / 2 - 20
        
        cross_len = 7.0
        
        # 1. Right Sidewalk (Continuous paved promenade across 280m)
        self.right_sidewalk = Entity(
            parent=self,
            model='cube',
            texture=sidewalk_tex,
            texture_scale=(int(sidewalk_width), int(length / 2)),
            scale=(sidewalk_width, self.sidewalk_height, length),
            position=(self.right_x, self.sidewalk_height / 2, center_z),
            color=rgb32(230, 230, 235),
            collider='box'
        )
        
        # ADA Yellow Tactile Blister Paving & Curb cuts at both Zebra Crossings
        for cross_z in [32.0, 160.0]:
            # Right tactile paving
            Entity(
                parent=self,
                model='cube',
                texture=tactile_tex,
                scale=(1.4, 0.05, cross_len * 0.85),
                position=(self.right_x - sidewalk_width / 2 + 0.8, self.sidewalk_height + 0.02, cross_z),
                color=rgb32(255, 235, 70)
            )
            # Left tactile paving
            Entity(
                parent=self,
                model='cube',
                texture=tactile_tex,
                scale=(1.4, 0.05, cross_len * 0.85),
                position=(self.left_x + sidewalk_width / 2 - 0.8, self.sidewalk_height + 0.02, cross_z),
                color=rgb32(255, 235, 70)
            )
            # Right curb ramp
            Entity(
                parent=self,
                model='cube',
                texture=sidewalk_tex,
                scale=(sidewalk_width, self.sidewalk_height * 0.4, cross_len),
                position=(self.right_x, self.sidewalk_height * 0.2, cross_z),
                color=rgb32(215, 215, 220)
            )
            # Left curb ramp
            Entity(
                parent=self,
                model='cube',
                texture=sidewalk_tex,
                scale=(sidewalk_width, self.sidewalk_height * 0.4, cross_len),
                position=(self.left_x, self.sidewalk_height * 0.2, cross_z),
                color=rgb32(215, 215, 220)
            )
            
        # 2. Continuous Yellow Hazard Curb Warning Stripe along road edges
        Entity(
            parent=self,
            model='quad',
            scale=(0.15, length),
            rotation_x=90,
            position=(self.right_x - sidewalk_width / 2 + 0.08, self.sidewalk_height + 0.01, center_z),
            color=rgb32(255, 205, 30) # High-vis yellow curb warning line
        )
        Entity(
            parent=self,
            model='quad',
            scale=(0.15, length),
            rotation_x=90,
            position=(self.left_x + sidewalk_width / 2 - 0.08, self.sidewalk_height + 0.01, center_z),
            color=rgb32(255, 205, 30)
        )
        
        # 3. Left Sidewalk (Opposite Promenade)
        self.left_sidewalk = Entity(
            parent=self,
            model='cube',
            texture=sidewalk_tex,
            texture_scale=(int(sidewalk_width), int(length / 2)),
            scale=(sidewalk_width, self.sidewalk_height, length),
            position=(self.left_x, self.sidewalk_height / 2, center_z),
            color=rgb32(220, 220, 225),
            collider='box'
        )
        
        # 4. Outer Green Lawn & Plaza Buffer Strips
        grass_width = 10.0
        Entity(
            parent=self,
            model='cube',
            scale=(grass_width, 0.2, length),
            position=(self.right_x + sidewalk_width / 2 + grass_width / 2, 0.1, center_z),
            color=rgb32(65, 120, 55)
        )
        Entity(
            parent=self,
            model='cube',
            scale=(grass_width, 0.2, length),
            position=(self.left_x - sidewalk_width / 2 - grass_width / 2, 0.1, center_z),
            color=rgb32(65, 120, 55)
        )
        
        # 5. Safe Autonomous Walkable Corridor Guide (Glowing Cyan Safety Corridor)
        self.path_guide = Entity(
            parent=self,
            model='quad',
            scale=(2.6, length - 10),
            rotation_x=90,
            position=(self.right_x, self.sidewalk_height + 0.015, center_z),
            color=rgba32(0, 220, 255, 30),
            enabled=True
        )
