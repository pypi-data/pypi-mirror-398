"""WS281x LED strip implementation using rpi_ws281x library."""

from mqtt_leds.core.led_strip import LEDStrip
from mqtt_leds.utils.coordinates import xy_to_led_index
from rpi_ws281x import PixelStrip, Color
import logging

logger = logging.getLogger(__name__)


class WS281xStrip(LEDStrip):
    """WS281x LED strip controller using rpi_ws281x library.
    
    This implementation provides direct control over WS281x LED strips
    with support for individual pixel addressing and 2D coordinate mapping.
    """
    
    def __init__(self, config):
        """Initialize the WS281x strip with configuration.
        
        Args:
            config: LEDStripConfig object with strip parameters
        """
        super().__init__(config)
        
        # Initialize the PixelStrip with configuration parameters
        self.strip = PixelStrip(
            config.length,              # Number of LED pixels
            config.gpio_pin,            # GPIO pin connected to the pixels
            config.led_freq_hz,         # LED signal frequency in hertz
            config.led_dma,             # DMA channel to use for generating signal
            config.led_invert,          # True to invert the signal
            config.brightness           # Set to 0 for darkest and 255 for brightest
        )
        
        # Initialize the library (must be called once before other functions)
        self.strip.begin()
        
        logger.info(
            f"Initialized WS281x LED strip with {config.length} pixels on GPIO {config.gpio_pin}, "
            f"freq={config.led_freq_hz}Hz, dma={config.led_dma}, brightness={config.brightness}"
        )
    
    def set_color(self, r: int, g: int, b: int):
        """Set all pixels to the same color.
        
        Args:
            r: Red value (0-255)
            g: Green value (0-255)
            b: Blue value (0-255)
        """
        logger.debug(f"WS281x set_color: ({r}, {g}, {b})")
        color = Color(r, g, b)
        for i in range(self.strip.numPixels()):
            self.strip.setPixelColor(i, color)
    
    def turn_off(self):
        """Turn off all LEDs."""
        logger.info("WS281x turning off")
        self.set_color(0, 0, 0)
        self.update()
    
    def update(self):
        """Update the strip to show the current LED states."""
        logger.debug("WS281x update called")
        self.strip.show()
    
    # Advanced features for individual pixel control
    
    def set_pixel(self, index: int, r: int, g: int, b: int):
        """Set individual pixel by index.
        
        Args:
            index: LED index (0 to length-1)
            r: Red value (0-255)
            g: Green value (0-255)
            b: Blue value (0-255)
        """
        if 0 <= index < self.strip.numPixels():
            self.strip.setPixelColor(index, Color(r, g, b))
        else:
            logger.warning(f"Pixel index {index} out of range (0-{self.strip.numPixels()-1})")
    
    def set_pixel_xy(self, x: int, y: int, r: int, g: int, b: int):
        """Set pixel by 2D coordinates.
        
        Requires display_width and display_height to be configured.
        
        Args:
            x: X coordinate
            y: Y coordinate
            r: Red value (0-255)
            g: Green value (0-255)
            b: Blue value (0-255)
        """
        if self.config.display_width is None or self.config.display_height is None:
            logger.error("Cannot use set_pixel_xy: display_width and display_height not configured")
            return
        
        led_index = xy_to_led_index(x, y, self.config.display_width, self.config.display_height)
        if led_index is not None:
            self.strip.setPixelColor(led_index, Color(r, g, b))
        else:
            logger.warning(f"Coordinates ({x}, {y}) out of bounds")
    
    def get_brightness(self) -> int:
        """Get current brightness level.
        
        Returns:
            Brightness level (0-255)
        """
        return self.strip.getBrightness()
    
    def set_brightness(self, brightness: int):
        """Set brightness level.
        
        Args:
            brightness: Brightness level (0-255)
        """
        if 0 <= brightness <= 255:
            self.strip.setBrightness(brightness)
            logger.debug(f"Set brightness to {brightness}")
        else:
            logger.warning(f"Brightness {brightness} out of range (0-255)")
    
    def clear(self):
        """Clear all LEDs (same as turn_off but without calling update)."""
        for i in range(self.strip.numPixels()):
            self.strip.setPixelColor(i, Color(0, 0, 0))
    
    @property
    def num_pixels(self) -> int:
        """Get total number of pixels.
        
        Returns:
            Number of pixels in the strip
        """
        return self.strip.numPixels()
    
    @property
    def width(self) -> int | None:
        """Get display width if configured.
        
        Returns:
            Display width or None
        """
        return self.config.display_width
    
    @property
    def height(self) -> int | None:
        """Get display height if configured.
        
        Returns:
            Display height or None
        """
        return self.config.display_height
