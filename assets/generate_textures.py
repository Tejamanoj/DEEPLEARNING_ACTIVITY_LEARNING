"""
High-Resolution Procedural Texture Generator for Ultra-Realistic Urban Simulator.
Generates realistic PBR-style textures optimized for Intel Iris Xe integrated graphics.
"""
import os
from PIL import Image, ImageDraw, ImageFilter
import numpy as np

TEXTURES_DIR = os.path.join(os.path.dirname(__file__), "textures")
os.makedirs(TEXTURES_DIR, exist_ok=True)

def generate_asphalt(path, size=512):
    # Dark charcoal asphalt with aggregate grain and road wear
    base = np.full((size, size, 3), [42, 45, 50], dtype=np.int16)
    noise = np.random.randint(-14, 14, base.shape, dtype=np.int16)
    arr = np.clip(base + noise, 0, 255).astype(np.uint8)
    img = Image.fromarray(arr)
    draw = ImageDraw.Draw(img)
    # Aggregate stone chips
    for _ in range(800):
        x = np.random.randint(0, size)
        y = np.random.randint(0, size)
        c = np.random.choice([30, 65, 80, 95])
        draw.point((x, y), fill=(c, c, c))
    img.save(path)
    print(f"Generated {path}")

def generate_granite_sidewalk(path, size=512):
    # Elegant light granite paving slabs with beveled mortar seams
    base = np.full((size, size, 3), [212, 215, 220], dtype=np.int16)
    noise = np.random.randint(-10, 10, base.shape, dtype=np.int16)
    arr = np.clip(base + noise, 0, 255).astype(np.uint8)
    img = Image.fromarray(arr)
    draw = ImageDraw.Draw(img)
    
    # 4x4 Large square stone flagstones
    step = size // 4
    seam_dark = (110, 115, 122)
    seam_light = (245, 248, 252)
    
    for i in range(1, 4):
        p = i * step
        # Mortar recessed groove
        draw.line([(p, 0), (p, size)], fill=seam_dark, width=3)
        draw.line([(0, p), (size, p)], fill=seam_dark, width=3)
        # Highlight bevel
        draw.line([(p + 2, 0), (p + 2, size)], fill=seam_light, width=1)
        draw.line([(0, p + 2), (size, p + 2)], fill=seam_light, width=1)
        
    draw.rectangle([(0, 0), (size-1, size-1)], outline=seam_dark, width=2)
    img.save(path)
    print(f"Generated {path}")

def generate_manhole(path, size=256):
    # Circular cast-iron city sewer cover
    img = Image.new("RGBA", (size, size), color=(0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    center = size // 2
    r = size // 2 - 8
    # Outer ring
    draw.ellipse([(center - r, center - r), (center + r, center + r)], fill=(55, 58, 64, 255), outline=(35, 38, 42, 255), width=4)
    # Inner waffle rings
    for cr in [r - 18, r - 36, r - 54, r - 72]:
        if cr > 0:
            draw.ellipse([(center - cr, center - cr), (center + cr, center + cr)], outline=(40, 42, 48, 255), width=3)
    # Radial grip spokes
    for deg in range(0, 360, 30):
        rad = np.radians(deg)
        x1 = center + int((r - 70) * np.cos(rad))
        y1 = center + int((r - 70) * np.sin(rad))
        x2 = center + int((r - 18) * np.cos(rad))
        y2 = center + int((r - 18) * np.sin(rad))
        draw.line([(x1, y1), (x2, y2)], fill=(40, 42, 48, 255), width=2)
    img.save(path)
    print(f"Generated {path}")

def generate_drain_grate(path, size=256):
    # Cast iron street drain grate with parallel slots
    img = Image.new("RGBA", (size, size), color=(45, 48, 54, 255))
    draw = ImageDraw.Draw(img)
    draw.rectangle([(6, 6), (size-7, size-7)], outline=(30, 32, 38, 255), width=5)
    slot_w = 12
    gap = 8
    curr_x = 22
    while curr_x < size - 26:
        draw.rectangle([(curr_x, 18), (curr_x + slot_w, size - 19)], fill=(15, 16, 20, 255), outline=(28, 30, 35, 255), width=2)
        curr_x += slot_w + gap
    img.save(path)
    print(f"Generated {path}")

def generate_facade_storefront(path, size=512):
    # Multi-story building: Glass storefront on ground floor, modern residential/office above
    img = Image.new("RGB", (size, size), color=(225, 222, 218))
    draw = ImageDraw.Draw(img)
    
    # Ground floor dark metallic storefront frame
    ground_h = 140
    draw.rectangle([(0, size - ground_h), (size, size)], fill=(45, 50, 58))
    # Glass showcase windows with indoor warm lighting
    for i in range(3):
        x0 = i * 165 + 16
        x1 = x0 + 140
        draw.rectangle([(x0, size - ground_h + 18), (x1, size - 14)], fill=(120, 165, 195))
        draw.rectangle([(x0, size - ground_h + 18), (x1, size - 14)], outline=(25, 28, 35), width=3)
        # Store sign banner
        draw.rectangle([(x0, size - ground_h + 4), (x1, size - ground_h + 16)], fill=(185, 45, 45))
        
    # Upper floors windows (4 rows x 4 columns)
    rows, cols = 4, 4
    cell_w = size // cols
    cell_h = (size - ground_h) // rows
    for r in range(rows):
        for c in range(cols):
            x0 = c * cell_w + 24
            y0 = r * cell_h + 16
            x1 = (c + 1) * cell_w - 24
            y1 = (r + 1) * cell_h - 16
            # Glass tint variation
            tint = (255, 240, 190) if (r + c*2) % 3 == 0 else (135, 175, 205)
            # Window frame & sill
            draw.rectangle([(x0 - 4, y0 - 4), (x1 + 4, y1 + 8)], fill=(180, 175, 170))
            draw.rectangle([(x0, y0), (x1, y1)], fill=tint)
            draw.line([( (x0+x1)//2, y0 ), ( (x0+x1)//2, y1 )], fill=(60, 65, 75), width=2)
            draw.line([( x0, (y0+y1)//2 ), ( x1, (y0+y1)//2 )], fill=(60, 65, 75), width=2)
            
    img.save(path)
    print(f"Generated {path}")

def generate_all():
    generate_asphalt(os.path.join(TEXTURES_DIR, "asphalt.png"))
    generate_granite_sidewalk(os.path.join(TEXTURES_DIR, "sidewalk.png"))
    generate_manhole(os.path.join(TEXTURES_DIR, "manhole.png"))
    generate_drain_grate(os.path.join(TEXTURES_DIR, "drain_grate.png"))
    generate_facade_storefront(os.path.join(TEXTURES_DIR, "facade_modern.png"))
    print("Realistic urban textures generated successfully!")

if __name__ == "__main__":
    generate_all()
