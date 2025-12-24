from mqtt_leds.core.led_strip import LEDStrip
from mqtt_leds.core.color import Color
import logging
import os
import board
import neopixel

logger = logging.getLogger(__name__)

class WS2811Strip(LEDStrip):
    def __init__(self, config):
        super().__init__(config)
        pin = getattr(board, f"D{config.gpio_pin}", board.D18)  # fallback
        self.pixel_count = int(os.getenv("NUM_LEDS", config.length))
        auto_write = os.getenv("AUTOWRITE", config.autowrite) == "True"
        brightness = config.brightness / 255.0

        self.pixels = neopixel.NeoPixel(
            pin,
            self.pixel_count,
            brightness=brightness,
            auto_write=auto_write,
            pixel_order=neopixel.GRB if config.color_order == "GRB" else neopixel.RGB
        )

        logger.info(f"Initialized WS2811 LED strip with {self.pixel_count} pixels on GPIO {config.gpio_pin}")

    def set_color(self, r, g, b):
        logger.debug(f"WS2811 set_color: ({r}, {g}, {b})")
        for i in range(self.pixel_count):
            self.pixels[i] = (r, g, b)

    def turn_off(self):
        logger.info("WS2811 turning off")
        self.set_color(0, 0, 0)
        self.update()

    def update(self):
        logger.debug("WS2811 update called")
        self.pixels.show()

