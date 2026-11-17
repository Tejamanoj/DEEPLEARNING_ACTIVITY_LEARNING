"""
Weather System Module: Comprehensive meteorological simulation with dynamic falling particles
(rain streaks, snowflakes, low-altitude fog mist), realistic sky/ambient lighting,
and sensor vision degradation modeling (optical range & detection confidence).
"""
from ursina import Entity, scene, color, DirectionalLight, AmbientLight, camera, Sky
from ursina.color import rgb32, rgba32
import random
import math

WEATHER_PRESETS = {
    "CLEAR": {
        "visibility_range": 16.0,
        "detection_confidence": 99,
        "speed_limit": 1.6,
        "camera_far": 380,
        "fog_range": (90, 350),
        "sky_color": rgb32(100, 158, 228),
        "fog_color": rgb32(185, 215, 245),
        "sun_color": rgb32(245, 240, 230),
        "ambient_color": color.Color(0.68, 0.68, 0.72, 1.0),
        "description": "CLEAR SUNLIGHT (Optimal Vision & Grip)"
    },
    "LIGHT_RAIN": {
        "visibility_range": 12.0,
        "detection_confidence": 80,
        "speed_limit": 1.3,
        "camera_far": 180,
        "fog_range": (35, 140),
        "sky_color": rgb32(95, 108, 128),
        "fog_color": rgb32(130, 140, 150),
        "sun_color": rgb32(145, 150, 155),
        "ambient_color": color.Color(0.42, 0.42, 0.46, 1.0),
        "description": "LIGHT DRIZZLE (Wet Road - Vision -20%)"
    },
    "HEAVY_RAIN": {
        "visibility_range": 8.0,
        "detection_confidence": 62,
        "speed_limit": 0.9,
        "camera_far": 95,
        "fog_range": (18, 75),
        "sky_color": rgb32(55, 60, 75),
        "fog_color": rgb32(90, 95, 105),
        "sun_color": rgb32(90, 95, 105),
        "ambient_color": color.Color(0.26, 0.26, 0.30, 1.0),
        "description": "HEAVY RAINSTORM (Water Spray - Vision -38%)"
    },
    "DENSE_FOG": {
        "visibility_range": 5.2,
        "detection_confidence": 38,
        "speed_limit": 0.65,
        "camera_far": 48,
        "fog_range": (8, 42),
        "sky_color": rgb32(170, 174, 184),
        "fog_color": rgb32(180, 184, 192),
        "sun_color": rgb32(130, 135, 140),
        "ambient_color": color.Color(0.50, 0.50, 0.52, 1.0),
        "description": "DENSE FOG WHITEOUT (Reduced Visibility -62%)"
    },
    "NIGHT": {
        "visibility_range": 6.8,
        "detection_confidence": 56,
        "speed_limit": 1.1,
        "camera_far": 120,
        "fog_range": (25, 95),
        "sky_color": rgb32(4, 6, 16),
        "fog_color": rgb32(12, 16, 26),
        "sun_color": rgb32(25, 30, 45),
        "ambient_color": color.Color(0.08, 0.08, 0.12, 1.0),
        "description": "NIGHTTIME (Torch Spotlight Illuminated)"
    },
    "SNOWFALL": {
        "visibility_range": 9.0,
        "detection_confidence": 70,
        "speed_limit": 1.0,
        "camera_far": 110,
        "fog_range": (28, 90),
        "sky_color": rgb32(178, 182, 198),
        "fog_color": rgb32(205, 212, 222),
        "sun_color": rgb32(195, 200, 210),
        "ambient_color": color.Color(0.58, 0.58, 0.62, 1.0),
        "description": "FALLING SNOW (Low Traction & Drift)"
    }
}

class WeatherSystem:
    def __init__(self, sky_entity=None, sun_light=None, ambient_light=None):
        self.current_weather = "CLEAR"
        self.preset_data = WEATHER_PRESETS["CLEAR"]
        
        # Link or create lighting
        self.sky = sky_entity if sky_entity else Sky()
        self.sun = sun_light if sun_light else DirectionalLight(color=rgb32(245, 240, 230), direction=(0.55, -1.25, 0.65))
        self.ambient = ambient_light if ambient_light else AmbientLight(color=rgb32(115, 122, 135))
        
        # Dynamic falling particle pools (pre-allocated for 60 FPS performance)
        self.particle_count = 110
        self.rain_particles = []
        self.snow_particles = []
        self.fog_particles = []
        self._init_particles()
        
        # Apply clear preset
        self.set_weather("CLEAR")
        
    def _init_particles(self):
        # 1. Rain streaks
        for i in range(self.particle_count):
            p = Entity(
                model='cube',
                scale=(0.025, random.uniform(0.35, 0.65), 0.025),
                position=(random.uniform(-18, 18), random.uniform(0.5, 14), random.uniform(-18, 18)),
                color=rgba32(200, 225, 255, 140),
                enabled=False
            )
            self.rain_particles.append(p)
            
        # 2. Snowflakes
        for i in range(self.particle_count):
            p = Entity(
                model='sphere',
                scale=random.uniform(0.06, 0.12),
                position=(random.uniform(-18, 18), random.uniform(0.5, 14), random.uniform(-18, 18)),
                color=rgba32(245, 250, 255, 190),
                enabled=False
            )
            p.sway_seed = random.uniform(0, 100)
            self.snow_particles.append(p)
            
        # 3. Dense fog mist layers
        for i in range(12):
            p = Entity(
                model='quad',
                rotation_x=90,
                scale=(random.uniform(10, 16), random.uniform(10, 16)),
                position=(random.uniform(-20, 20), random.uniform(0.2, 1.8), random.uniform(-10, 80)),
                color=rgba32(215, 220, 228, 28),
                enabled=False
            )
            self.fog_particles.append(p)
            
    def set_weather(self, mode="CLEAR"):
        norm_mode = mode.upper()
        if norm_mode not in WEATHER_PRESETS:
            # Map aliases
            if "RAIN" in norm_mode:
                norm_mode = "HEAVY_RAIN" if "HEAVY" in norm_mode else "LIGHT_RAIN"
            elif "FOG" in norm_mode:
                norm_mode = "DENSE_FOG"
            elif "SNOW" in norm_mode:
                norm_mode = "SNOWFALL"
            elif "NIGHT" in norm_mode:
                norm_mode = "NIGHT"
            else:
                norm_mode = "CLEAR"
                
        self.current_weather = norm_mode
        self.preset_data = WEATHER_PRESETS[norm_mode]
        
        # Apply environment visual attributes
        if self.sky:
            self.sky.color = self.preset_data["sky_color"]
        if self.sun:
            self.sun.color = self.preset_data["sun_color"]
        if self.ambient:
            self.ambient.color = self.preset_data["ambient_color"]
            
        scene.fog_color = self.preset_data["fog_color"]
        scene.fog_density = self.preset_data["fog_range"]
        camera.clip_plane_far = self.preset_data["camera_far"]
        
        # Enable / disable particle systems
        is_rain = norm_mode in ["LIGHT_RAIN", "HEAVY_RAIN"]
        is_snow = norm_mode == "SNOWFALL"
        is_fog  = norm_mode == "DENSE_FOG"
        
        for p in self.rain_particles:
            p.enabled = is_rain
        for p in self.snow_particles:
            p.enabled = is_snow
        for p in self.fog_particles:
            p.enabled = is_fog
            
    def update(self, dt, robot_pos=None):
        """Advances falling rain, drifting snow, and low-altitude mist around the robot."""
        if not robot_pos:
            return
            
        rx, rz = robot_pos.x, robot_pos.z
        
        if self.current_weather in ["LIGHT_RAIN", "HEAVY_RAIN"]:
            fall_speed = 22.0 if self.current_weather == "HEAVY_RAIN" else 15.0
            for p in self.rain_particles:
                p.y -= fall_speed * dt
                if p.y <= 0.05:
                    p.y = random.uniform(10.0, 15.0)
                    p.x = rx + random.uniform(-16.0, 16.0)
                    p.z = rz + random.uniform(-16.0, 16.0)
                    
        elif self.current_weather == "SNOWFALL":
            for p in self.snow_particles:
                p.y -= 2.6 * dt
                p.x += math.sin(p.sway_seed + p.y * 1.5) * 0.8 * dt
                if p.y <= 0.05:
                    p.y = random.uniform(9.0, 14.0)
                    p.x = rx + random.uniform(-16.0, 16.0)
                    p.z = rz + random.uniform(-16.0, 16.0)
                    
        elif self.current_weather == "DENSE_FOG":
            for p in self.fog_particles:
                p.z += 0.8 * dt
                if p.z > rz + 30.0:
                    p.z = rz - 30.0
                    p.x = rx + random.uniform(-18.0, 18.0)
                    
    def get_visibility_range(self):
        return self.preset_data["visibility_range"]
        
    def get_detection_confidence(self):
        return self.preset_data["detection_confidence"]
        
    def get_speed_limit(self):
        return self.preset_data["speed_limit"]
        
    def get_description(self):
        return self.preset_data["description"]
