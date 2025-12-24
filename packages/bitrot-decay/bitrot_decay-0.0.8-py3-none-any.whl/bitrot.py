"""
BitRot: A Python library for simulating digital image decay.
New Mechanism: Resolution Downscaling (Pixelation) + JPEG Compression Artifacts + Color Loss.

Usage:
    import bitrot
    bitrot.decay_file("input.jpg", "output.jpg", integrity=0.8)
"""

import io
from PIL import Image

def degrade(image: Image.Image, integrity: float) -> Image.Image:
    """
    Core logic: Takes a PIL Image and returns a decayed PIL Image.
    integrity: Float between 0.0 (Destroyed) and 1.0 (Perfect)
    """
    # Clamp integrity to 0.01 - 1.0 (prevent div by zero or total void)
    integrity = max(0.01, min(1.0, integrity))
    
    # If it's perfect, return early
    if integrity >= 1.0:
        return image

    original_size = image.size
    
    # --- STAGE 1: PIXELATION (Resolution Decay) ---
    # At 1.0 integrity -> Factor 1.0 (Original Size)
    # At 0.0 integrity -> Factor 0.02 (Tiny blob)
    scale_factor = max(0.02, integrity)
    
    new_width = int(original_size[0] * scale_factor)
    new_height = int(original_size[1] * scale_factor)
    
    # Ensure dimensions are at least 8x8 px so it doesn't crash
    new_width = max(8, new_width)
    new_height = max(8, new_height)

    # Downscale (Lose information)
    # Upscale using NEAREST (Creates the blocky/pixelated look)
    image = image.resize((new_width, new_height), resample=Image.BILINEAR)
    image = image.resize(original_size, resample=Image.NEAREST)

    # --- STAGE 2: COLOR BANDING (Bit Depth Decay) ---
    # Only kicks in when integrity drops below 60%
    if integrity < 0.6:
        # Reduces colors to simulate GIF/8-bit look
        # 0.6 integrity -> ~128 colors
        # 0.1 integrity -> ~4 colors
        colors = int(max(2, integrity * 256))
        
        # Quantize forces the image into a limited palette
        image = image.quantize(colors=colors).convert("RGB")

    return image

# --- PUBLIC API ---

def decay_file(input_path: str, output_path: str, integrity: float = 0.9):
    """
    Reads an image from disk, decays it, and saves it to disk.
    
    Args:
        input_path (str): Path to source image.
        output_path (str): Path to save result.
        integrity (float): 0.0 to 1.0 (1.0 = Original).
    """
    try:
        with Image.open(input_path) as img:
            # Ensure RGB
            img = img.convert("RGB")
            
            # Apply Decay Logic
            result = degrade(img, integrity)
            
            # --- STAGE 3: JPEG ARTIFACTING (Compression Decay) ---
            # We map integrity directly to JPEG quality (1-95)
            # Integrity 0.9 -> Quality 85 (Good)
            # Integrity 0.1 -> Quality 9 (Deep Fried)
            jpg_quality = int(max(1, integrity * 95))
            
            result.save(output_path, "JPEG", quality=jpg_quality)
            
            print(f"BitRot: Saved to {output_path} | Integrity: {int(integrity*100)}% | Q: {jpg_quality}")
            
    except Exception as e:
        print(f"BitRot Error: {e}")

def decay_bytes(image_data: bytes, integrity: float = 0.9) -> bytes:
    """
    Takes raw image bytes, decays them, and returns raw image bytes.
    Useful for web servers / APIs where no file is saved to disk.
    """
    try:
        with Image.open(io.BytesIO(image_data)) as img:
            img = img.convert("RGB")
            
            # Apply Decay Logic
            result = degrade(img, integrity)
            
            output_buffer = io.BytesIO()
            
            # Apply JPEG Compression
            jpg_quality = int(max(1, integrity * 95))
            
            result.save(output_buffer, format="JPEG", quality=jpg_quality)
            
            return output_buffer.getvalue()
    except Exception as e:
        print(f"BitRot Error: {e}")
        return image_data