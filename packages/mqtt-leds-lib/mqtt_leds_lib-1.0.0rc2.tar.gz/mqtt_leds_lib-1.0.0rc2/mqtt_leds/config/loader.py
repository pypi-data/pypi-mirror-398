import yaml
import os
from pathlib import Path
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class LEDStripConfig:
    type: str
    name: str
    gpio_pin: int | None = None
    gpio_pins: dict | None = None
    individually_addressable: bool = False
    length: int = 1
    color_order: str = "RGB"
    autowrite: bool = False
    brightness: int = 255
    frequency: int = 1000
    description: str = ""
    # WS281x-specific fields
    led_freq_hz: int = 800000
    led_dma: int = 10
    led_invert: bool = False
    display_width: int | None = None
    display_height: int | None = None

def load_config(name: str) -> LEDStripConfig:
    path = Path(os.path.dirname(__file__)) / "../../configs" / f"{name}.yaml"
    data = None

    with open(path, 'r') as f:
        data = yaml.safe_load(f)
    logger.info(f"Loaded config for {name} at path {path}")
    logger.debug(data)
    return LEDStripConfig(**data)


def generate_device_config(config: LEDStripConfig) -> dict:
    return {
        "name": config.name,
        "unique_id": config.name.lower().replace(" ", "_"),
        "command_topic": f"homeassistant/light/{config.name.lower().replace(' ', '_')}/set",
        "state_topic": f"homeassistant/light/{config.name.lower().replace(' ', '_')}/state",
        "schema": "json",
        "brightness": True,
        "rgb": True,
        "qos": 0,
        "platform": "mqtt",
        "device": {
            "identifiers": [config.name.lower().replace(" ", "_")],
            "manufacturer": "mqtt-leds-lib",
            "model": config.type,
            "name": config.name
        }
    }


def publish_device_config(config: LEDStripConfig, mqtt_client):
    topic = f"homeassistant/light/{config.name.lower().replace(' ', '_')}/config"
    payload = generate_device_config(config)
    import json
    mqtt_client.client.publish(topic, json.dumps(payload), retain=True)
    logger.info(f"Published Home Assistant device config to {topic}")
