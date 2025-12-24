import time
import threading
from mqtt_leds.core.color import Color
import logging
import json

logger = logging.getLogger(__name__)

class Hopscotch:
    def __init__(self, strip, mqtt_client, config_name):
        self.strip = strip
        self.mqtt = mqtt_client
        self.config_name = config_name.lower().replace(" ", "_")

        self.enabled = False
        self.colors = [Color(255, 0, 0), Color(0, 255, 0), Color(0, 0, 255)]
        self.position = 0

        self.thread = threading.Thread(target=self.run_loop)
        self.thread.daemon = True
        self.thread.start()

        self.subscribe_topics()
        self.publish_discovery()

    def subscribe_topics(self):
        self.mqtt.subscribe(f"switch/{self.config_name}_effect/set")
        for i in range(3):
            self.mqtt.subscribe(f"light/{self.config_name}_effect_color_{i}/set")
        self.mqtt.register_handler(self.handle_message)

    def publish_discovery(self):
        base = f"{self.mqtt.topic_prefix}"

        self.mqtt.client.publish(
            f"{base}/switch/{self.config_name}_effect/config",
            json.dumps({
                "name": f"{self.config_name} Effect",
                "unique_id": f"{self.config_name}_effect",
                "command_topic": f"{base}/switch/{self.config_name}_effect/set",
                "state_topic": f"{base}/switch/{self.config_name}_effect/state",
                "platform": "mqtt"
            }), retain=True
        )

        for i in range(3):
            self.mqtt.client.publish(
                f"{base}/light/{self.config_name}_effect_color_{i}/config",
                json.dumps({
                    "name": f"{self.config_name} Effect Color {i+1}",
                    "unique_id": f"{self.config_name}_effect_color_{i}",
                    "command_topic": f"{base}/light/{self.config_name}_effect_color_{i}/set",
                    "state_topic": f"{base}/light/{self.config_name}_effect_color_{i}/state",
                    "schema": "json",
                    "rgb": True,
                    "platform": "mqtt"
                }), retain=True
            )

    def handle_message(self, topic, payload):
        if topic.endswith("/set"):
            if topic.endswith("_effect/set"):
                self.enabled = payload.get("state", "off").lower() == "on"
                self.mqtt.client.publish(f"{self.mqtt.topic_prefix}/switch/{self.config_name}_effect/state",
                                         json.dumps({"state": "ON" if self.enabled else "OFF"}), retain=True)
            elif any(topic.endswith(f"_effect_color_{i}/set") for i in range(3)):
                for i in range(3):
                    if topic.endswith(f"_effect_color_{i}/set") and "color" in payload:
                        c = payload["color"]
                        self.colors[i] = Color(c.get("r", 0), c.get("g", 0), c.get("b", 0))
                        self.mqtt.client.publish(
                            f"{self.mqtt.topic_prefix}/light/{self.config_name}_effect_color_{i}/state",
                            json.dumps({"state": "ON", "color": c}), retain=True
                        )

    def run_loop(self):
        while True:
            if self.enabled:
                for i in range(self.strip.pixel_count):
                    idx = (i - self.position) % 3
                    self.strip.pixels[i] = self.colors[idx].as_tuple()
                self.strip.pixels.show()
                self.position = (self.position + 3) % self.strip.pixel_count
            time.sleep(0.1)