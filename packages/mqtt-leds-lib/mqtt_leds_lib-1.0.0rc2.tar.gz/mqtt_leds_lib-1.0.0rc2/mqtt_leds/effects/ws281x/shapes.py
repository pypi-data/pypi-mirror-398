"""Shape drawing effects for WS281x LED displays."""

import math
from rpi_ws281x import Color


def draw_circle(strip, center_x, center_y, radius, r, g, b, fill=False):
    """
    Draw a circle on the LED display using Bresenham's circle algorithm.
    
    Requires the strip to have display_width and display_height configured.
    
    Args:
        strip: WS281xStrip object to draw on
        center_x: X coordinate of circle center
        center_y: Y coordinate of circle center
        radius: Radius of the circle in pixels
        r: Red value (0-255)
        g: Green value (0-255)
        b: Blue value (0-255)
        fill: If True, fill the circle; if False, draw only the outline
    """
    if strip.width is None or strip.height is None:
        raise ValueError("Strip must have display_width and display_height configured for shape drawing")
    
    if fill:
        # Fill the circle by drawing all pixels within the radius
        for y in range(strip.height):
            for x in range(strip.width):
                # Calculate distance from center
                dx = x - center_x
                dy = y - center_y
                distance = math.sqrt(dx * dx + dy * dy)
                
                if distance <= radius:
                    strip.set_pixel_xy(x, y, r, g, b)
    else:
        # Draw circle outline using Bresenham's circle algorithm
        x = 0
        y = radius
        d = 3 - 2 * radius
        
        def draw_circle_points(cx, cy, x, y):
            """Draw 8 symmetric points of the circle."""
            points = [
                (cx + x, cy + y),
                (cx - x, cy + y),
                (cx + x, cy - y),
                (cx - x, cy - y),
                (cx + y, cy + x),
                (cx - y, cy + x),
                (cx + y, cy - x),
                (cx - y, cy - x)
            ]
            for px, py in points:
                if 0 <= px < strip.width and 0 <= py < strip.height:
                    strip.set_pixel_xy(px, py, r, g, b)
        
        draw_circle_points(center_x, center_y, x, y)
        
        while y >= x:
            x += 1
            
            if d > 0:
                y -= 1
                d = d + 4 * (x - y) + 10
            else:
                d = d + 4 * x + 6
            
            draw_circle_points(center_x, center_y, x, y)
