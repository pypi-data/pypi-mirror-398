from mqtt_leds.core.led_strip import LEDStrip
from mqtt_leds.core.color import Color
import time
import logging

logger = logging.getLogger(__name__)

try:
    import RPi.GPIO as GPIO
except ImportError:
    GPIO = None

class SolaroxRGBStrip(LEDStrip):
    def __init__(self, config):
        super().__init__(config)
        if GPIO is None:
            raise RuntimeError("RPi.GPIO is not available. Must run on a Raspberry Pi.")

        self.red_pin = config.gpio_pins['red']
        self.green_pin = config.gpio_pins['green']
        self.blue_pin = config.gpio_pins['blue']
        self.frequency = config.frequency

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.red_pin, GPIO.OUT)
        GPIO.setup(self.green_pin, GPIO.OUT)
        GPIO.setup(self.blue_pin, GPIO.OUT)
        GPIO.output(self.red_pin, GPIO.LOW)
        GPIO.output(self.green_pin, GPIO.LOW)
        GPIO.output(self.blue_pin, GPIO.LOW)

        self.red_pwm = GPIO.PWM(self.red_pin, self.frequency)
        self.green_pwm = GPIO.PWM(self.green_pin, self.frequency)
        self.blue_pwm = GPIO.PWM(self.blue_pin, self.frequency)

        self.red_pwm.start(0)
        self.green_pwm.start(0)
        self.blue_pwm.start(0)

        logger.info("Initialized SolaroxRGB strip with pins R:%s G:%s B:%s and frequency %sHz",
                    self.red_pin, self.green_pin, self.blue_pin, self.frequency)

    def set_color(self, r, g, b):
        def scale(val):
            return max(0, min(100, round(val / 255 * 100)))
        self.red_pwm.ChangeDutyCycle(scale(r))
        self.green_pwm.ChangeDutyCycle(scale(g))
        self.blue_pwm.ChangeDutyCycle(scale(b))
        logger.debug(f"SolaroxRGB set_color: ({r}, {g}, {b})")

    def turn_off(self):
        logger.info("SolaroxRGB turning off")
        self.set_color(0, 0, 0)

    def update(self):
        logger.debug("SolaroxRGB update called")
        # Nothing required for basic analog RGB
        pass
