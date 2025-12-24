"""
BitRot: A Python library for simulating digital image decay.
Mechanism: Pure Resolution Loss + JPEG Compression.
No noise, no pixel art blocks, no color shifting. Just lower quality.
"""

import io
from PIL import Image

def degrade(image: Image.Image, integrity: float) -> Image.Image:
    """
    Core logic: Lowers resolution and applies compression.
    integrity: Float between 0.01 (Unrecognizable) and 1.0 (HD).
    """
    integrity = max(0.01, min(1.0, integrity))
    
    # 1. Integrity 1.0 = Return immediately (Perfect Quality)
    if integrity >= 1.0:
        return image

    original_size = image.size
    
    # 2. RESOLUTION DECAY (The "144p" Effect)
    # At 1.0 integrity -> 100% scale
    # At 0.5 integrity -> 50% scale
    # At 0.1 integrity -> 10% scale (Very blurry)
    scale_factor = max(0.05, integrity) 
    
    new_width = int(original_size[0] * scale_factor)
    new_height = int(original_size[1] * scale_factor)
    
    # Safety clamp (don't go below 1 pixel)
    new_width = max(4, new_width)
    new_height = max(4, new_height)

    # Downscale (Lose detail) using LANCZOS (High quality downsampling)
    image = image.resize((new_width, new_height), resample=Image.LANCZOS)
    
    # Upscale back to original size using BILINEAR (Soft/Blurry look)
    # Note: We use BILINEAR instead of NEAREST to avoid the "Minecraft block" look.
    image = image.resize(original_size, resample=Image.BILINEAR)

    return image

# --- PUBLIC API ---

def decay_file(input_path: str, output_path: str, integrity: float = 0.9):
    try:
        with Image.open(input_path) as img:
            img = img.convert("RGB")
            
            # Apply Resolution Drop
            result = degrade(img, integrity)
            
            # 3. JPEG COMPRESSION DECAY (The "Artifacts")
            # We map integrity directly to JPEG quality (1-100)
            # 100 = Perfect
            # 10 = Deep fried artifacts
            jpg_quality = int(max(5, integrity * 95))
            
            # We must save as JPEG to force the compression artifacts to bake in
            result.save(output_path, "JPEG", quality=jpg_quality)
            
            print(f"BitRot: Saved to {output_path} | Quality: {jpg_quality}")
            
    except Exception as e:
        print(f"BitRot Error: {e}")

def decay_bytes(image_data: bytes, integrity: float = 0.9) -> bytes:
    try:
        with Image.open(io.BytesIO(image_data)) as img:
            img = img.convert("RGB")
            
            result = degrade(img, integrity)
            
            output_buffer = io.BytesIO()
            
            # Apply JPEG Compression
            jpg_quality = int(max(5, integrity * 95))
            
            result.save(output_buffer, format="JPEG", quality=jpg_quality)
            
            return output_buffer.getvalue()
    except Exception as e:
        print(f"BitRot Error: {e}")
        return image_data