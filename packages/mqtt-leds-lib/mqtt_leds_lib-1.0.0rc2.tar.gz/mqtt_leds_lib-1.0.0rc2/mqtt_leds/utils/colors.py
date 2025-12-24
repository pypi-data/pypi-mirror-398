"""Color utilities for LED displays."""


def wheel(pos):
    """
    Generate rainbow colors across 0-255 positions.
    
    This function generates colors that smoothly transition through the rainbow
    spectrum, useful for creating rainbow effects.
    
    Args:
        pos: Position in color wheel (0-255)
    
    Returns:
        RGB tuple (r, g, b) where each value is 0-255
    """
    if pos < 85:
        return (pos * 3, 255 - pos * 3, 0)
    elif pos < 170:
        pos -= 85
        return (255 - pos * 3, 0, pos * 3)
    else:
        pos -= 170
        return (0, pos * 3, 255 - pos * 3)


def rgb_to_color(r, g, b):
    """
    Convert RGB values to a 24-bit color value.
    
    Args:
        r: Red value (0-255)
        g: Green value (0-255)
        b: Blue value (0-255)
    
    Returns:
        24-bit color value (compatible with rpi_ws281x.Color)
    """
    return (r << 16) | (g << 8) | b


def parse_color_string(color_str):
    """
    Parse a color string in R,G,B format.
    
    Args:
        color_str: String in format "R,G,B" (e.g., "255,0,0")
    
    Returns:
        Tuple of (r, g, b) integers
    
    Raises:
        ValueError: If the color string is invalid
    """
    try:
        r, g, b = map(int, color_str.split(','))
        if not all(0 <= val <= 255 for val in (r, g, b)):
            raise ValueError("Color values must be between 0 and 255")
        return (r, g, b)
    except (ValueError, AttributeError) as e:
        raise ValueError(f"Invalid color format '{color_str}'. Use R,G,B format (e.g., 255,0,0)") from e
