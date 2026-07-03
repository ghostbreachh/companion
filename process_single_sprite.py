#!/usr/bin/env python3
import os
import sys
import collections
import argparse
from PIL import Image

def remove_background_robust(image_path, output_path, threshold=20, feather_range=5):
    img = Image.open(image_path).convert("RGBA")
    pixels = img.load()
    w, h = img.size
    
    # Calculate average color of the top row to represent background color
    temp_rgb = img.convert("RGB")
    temp_pixels = temp_rgb.load()
    top_pixels = [temp_pixels[x, 0] for x in range(w)]
    avg_r = sum(c[0] for c in top_pixels) // w
    avg_g = sum(c[1] for c in top_pixels) // w
    avg_b = sum(c[2] for c in top_pixels) // w
    bg_color = (avg_r, avg_g, avg_b)
    
    visited = set()
    queue = collections.deque()
    
    # Add top border to start BFS
    for x in range(w):
        queue.append((x, 0))
        visited.add((x, 0))
        
    # Add left and right borders (excluding the bottom 10% where the body is)
    for y in range(1, int(h * 0.9)):
        queue.append((0, y))
        queue.append((w-1, y))
        visited.add((0, y))
        visited.add((w-1, y))
        
    background_pixels = set()
    
    # BFS
    while queue:
        cx, cy = queue.popleft()
        r, g, b, a = pixels[cx, cy]
        dist = ((r - bg_color[0])**2 + (g - bg_color[1])**2 + (b - bg_color[2])**2)**0.5
        
        if dist < threshold:
            background_pixels.add((cx, cy))
            for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
                nx, ny = cx + dx, cy + dy
                if 0 <= nx < w and 0 <= ny < h:
                    if (nx, ny) not in visited:
                        visited.add((nx, ny))
                        queue.append((nx, ny))
                        
    # Apply transparency to background pixels
    for x, y in background_pixels:
        r, g, b, a = pixels[x, y]
        dist = ((r - bg_color[0])**2 + (g - bg_color[1])**2 + (b - bg_color[2])**2)**0.5
        if dist < (threshold - feather_range):
            pixels[x, y] = (r, g, b, 0)
        else:
            alpha = int(255 * (dist - (threshold - feather_range)) / feather_range)
            pixels[x, y] = (r, g, b, min(255, max(0, alpha)))
            
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img.save(output_path, "PNG")
    print(f"Processed {os.path.basename(image_path)} -> {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Remove background transparently.")
    parser.add_argument("--input", required=True, help="Input image path (.jpg or .png)")
    parser.add_argument("--output", required=True, help="Output PNG path")
    parser.add_argument("--threshold", type=int, default=20, help="Distance threshold")
    args = parser.parse_args()
    
    if os.path.exists(args.input):
        remove_background_robust(args.input, args.output, threshold=args.threshold)
    else:
        print(f"Error: input file {args.input} does not exist.")
        sys.exit(1)
