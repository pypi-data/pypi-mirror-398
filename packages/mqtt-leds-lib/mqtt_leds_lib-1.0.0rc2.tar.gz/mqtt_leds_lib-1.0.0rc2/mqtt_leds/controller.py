from mqtt_leds.config.loader import load_config, publish_device_config
from mqtt_leds.types.ws2811 import WS2811Strip
from mqtt_leds.types.ws281x import WS281xStrip
from mqtt_leds.types.solarox_rgb import SolaroxRGBStrip
from mqtt_leds.mqtt.client import MQTTClient  # import your class
import logging

logger = logging.getLogger(__name__)

class Controller:
    def __init__(self, strip_type: str, mqtt_client: MQTTClient = None):
        self.config = load_config(strip_type)

        if self.config.type == "ws2811":
            self.strip = WS2811Strip(self.config)
        elif self.config.type == "ws281x":
            self.strip = WS281xStrip(self.config)
        elif self.config.type == "solarox_rgb":
            self.strip = SolaroxRGBStrip(self.config)
        else:
            raise NotImplementedError(f"Unknown strip type: {strip_type}")

        self.mqtt_client = mqtt_client
        if self.mqtt_client:
            publish_device_config(self.config, self.mqtt_client)

    def set_color(self, color):
        logger.debug(f"Controller set_color: {color}")
        self.strip.set_color(*color.as_tuple())
        self.strip.update()

    def turn_off(self):
        logger.info("Controller turning off strip")
        self.strip.turn_off()
        self.strip.update()
