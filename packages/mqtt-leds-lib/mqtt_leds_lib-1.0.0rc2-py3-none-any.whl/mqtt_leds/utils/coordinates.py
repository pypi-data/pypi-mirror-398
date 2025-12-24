"""Coordinate mapping utilities for LED displays."""


def xy_to_led_index(x, y, display_width=32, display_height=16):
    """
    Convert logical (x, y) coordinates to physical LED index.
    
    The display is 16x32 (16 rows, 32 columns) composed of two 8x32 arrays stacked vertically.
    The sheets are facing outward, so we mirror the entire display left-to-right.
    
    Layout (after mirroring):
    - Bottom array (y=8-15): LEDs 0-255, starts at bottom-left (x=0, y=15), serpentine right
    - Top array (y=0-7): LEDs 256-511, starts at top-right (x=31, y=0), serpentine left
    
    Each row is 8 LEDs tall (the short axis), 32 LEDs wide (the long axis).
    Serpentine pattern alternates direction with each column.
    
    Args:
        x: X coordinate (0 to display_width-1)
        y: Y coordinate (0 to display_height-1)
        display_width: Width of the display (default: 32)
        display_height: Height of the display (default: 16)
    
    Returns:
        LED index (0-511), or None if coordinates are out of bounds
    """
    # Validate coordinates
    if x < 0 or x >= display_width or y < 0 or y >= display_height:
        return None
    
    # Determine which 8x32 array we're in (top or bottom)
    if y < 8:
        # Bottom array (y=8-15): LEDs 0-255
        # This array starts at bottom-left corner (x=0, y=15)
        # Serpentine pattern going right across x-axis
        local_x = x  # 0-31 across the width
        local_y = 7 - y  # 0-7 within the 8-pixel height, mirrored
        
        # Each column is 8 LEDs tall
        col_start = local_x * 8
        
        # Serpentine: even columns go up, odd columns go down
        if local_x % 2 == 0:
            # Even columns: bottom to top
            local_pos = local_y
        else:
            # Odd columns: top to bottom
            local_pos = 7 - local_y
        
        led_index = col_start + local_pos
    else:
        # Top array (y=0-7): LEDs 256-511
        # This array starts at top-right corner (x=31, y=0)
        # Serpentine pattern going left across x-axis
        local_x = x  # 0-31 across the width
        local_y = y - 8  # 0-7 within the 8-pixel height
        
        # Each column is 8 LEDs tall
        col_start = local_x * 8
        
        # Serpentine: even columns go down, odd columns go up
        if local_x % 2 == 0:
            # Even columns: top to bottom
            local_pos = local_y
        else:
            # Odd columns: bottom to top
            local_pos = 7 - local_y
        
        led_index = 256 + col_start + local_pos
    
    return led_index
