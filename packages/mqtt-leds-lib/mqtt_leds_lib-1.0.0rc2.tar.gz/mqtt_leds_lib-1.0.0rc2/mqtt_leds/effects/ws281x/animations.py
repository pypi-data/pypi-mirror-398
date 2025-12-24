"""Animation effects for WS281x LED displays."""

import time
from rpi_ws281x import Color
from mqtt_leds.utils.colors import wheel


def sequential_mode(strip, colors=None, delay=0.05, trail_length=0, fade=False, 
                   reverse=False, loops="infinite"):
    """
    Light up all LEDs sequentially with customizable parameters.
    
    Args:
        strip: WS281xStrip object to animate
        colors: List of RGB tuples to cycle through. Default: [(255,0,0), (0,255,0), (0,0,255)]
        delay: Time delay between lighting each LED (in seconds). Default: 0.05
        trail_length: Number of LEDs to keep lit behind the current one (0 = only current LED). Default: 0
        fade: If True, trailing LEDs fade out gradually. Default: False
        reverse: If True, light LEDs in reverse order. Default: False
        loops: Number of times to repeat the sequence or "infinite". Default: "infinite"
    """
    if colors is None:
        colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]  # Red, Green, Blue
    
    num_pixels = strip.num_pixels
    if loops != "infinite":
        loops = int(loops)
    
    while True:
        for i in range(num_pixels):
            # Determine actual pixel index based on reverse flag
            pixel_idx = (num_pixels - 1 - i) if reverse else i
            
            # Select color based on position
            color_idx = i % len(colors)
            r, g, b = colors[color_idx]
            
            # Set current pixel to full brightness
            strip.set_pixel(pixel_idx, r, g, b)
            
            # Handle trailing LEDs
            if trail_length > 0:
                for j in range(1, trail_length + 1):
                    if i - j >= 0:
                        trail_pixel_idx = (num_pixels - 1 - (i - j)) if reverse else (i - j)
                        trail_color_idx = (i - j) % len(colors)
                        tr, tg, tb = colors[trail_color_idx]
                        
                        if fade:
                            # Fade out trailing LEDs
                            fade_factor = 1.0 - (j / (trail_length + 1))
                            tr = int(tr * fade_factor)
                            tg = int(tg * fade_factor)
                            tb = int(tb * fade_factor)
                        
                        strip.set_pixel(trail_pixel_idx, tr, tg, tb)
            
            # Clear LEDs beyond the trail
            if trail_length < num_pixels:
                for j in range(trail_length + 1, i + 1):
                    if i - j >= 0:
                        clear_pixel_idx = (num_pixels - 1 - (i - j)) if reverse else (i - j)
                        strip.set_pixel(clear_pixel_idx, 0, 0, 0)
            
            strip.update()
            time.sleep(delay)
        
        # Clear all after each loop
        strip.clear()
        strip.update()
        if loops != "infinite":
            loops = loops - 1
            if loops <= 0:
                break


def wave_mode(strip, colors=None, delay=0.02, wave_length=10, loops="infinite"):
    """
    Create a wave effect across the LED strip.
    
    Args:
        strip: WS281xStrip object to animate
        colors: List of RGB tuples for the wave. Default: [(255,0,255), (0,255,255)]
        delay: Time delay between wave steps. Default: 0.02
        wave_length: Length of the wave in LEDs. Default: 10
        loops: Number of times to repeat the wave or "infinite". Default: "infinite"
    """
    if colors is None:
        colors = [(255, 0, 255), (0, 255, 255)]  # Magenta, Cyan
    
    num_pixels = strip.num_pixels
    if loops != "infinite":
        loops = int(loops)
        
    while True:
        for offset in range(num_pixels + wave_length):
            for i in range(num_pixels):
                # Calculate wave position
                wave_pos = (i - offset) % (num_pixels + wave_length)
                
                if 0 <= wave_pos < wave_length:
                    # LED is within the wave
                    color_idx = wave_pos % len(colors)
                    r, g, b = colors[color_idx]
                    
                    # Apply brightness gradient
                    brightness = 1.0 - abs(wave_pos - wave_length / 2) / (wave_length / 2)
                    r = int(r * brightness)
                    g = int(g * brightness)
                    b = int(b * brightness)
                    
                    strip.set_pixel(i, r, g, b)
                else:
                    strip.set_pixel(i, 0, 0, 0)
            
            strip.update()
            time.sleep(delay)
        
        strip.clear()
        strip.update()
        if loops != "infinite":
            loops = loops - 1
            if loops <= 0:
                break


def rainbow_mode(strip, delay=0.01, loops="infinite"):
    """
    Create a rainbow effect that cycles through all LEDs.
    
    Args:
        strip: WS281xStrip object to animate
        delay: Time delay between updates. Default: 0.01
        loops: Number of times to cycle through or "infinite". Default: "infinite"
    """
    num_pixels = strip.num_pixels
    if loops != "infinite":
        loops = int(loops)

    while True:
        for j in range(256):  # One full cycle through color wheel
            for i in range(num_pixels):
                # Calculate color based on position and time
                color_pos = (i * 256 // num_pixels + j) & 255
                r, g, b = wheel(color_pos)
                strip.set_pixel(i, r, g, b)
            
            strip.update()
            time.sleep(delay)
            
        if loops != "infinite":
            loops = loops - 1
            if loops <= 0:
                break
    
    strip.clear()
    strip.update()
