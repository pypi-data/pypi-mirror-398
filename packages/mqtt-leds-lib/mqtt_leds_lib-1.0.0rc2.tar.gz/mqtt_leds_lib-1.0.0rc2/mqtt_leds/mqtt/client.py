import paho.mqtt.client as mqtt
import logging
import os
import json
from mqtt_leds.core.color import Color

logger = logging.getLogger(__name__)

class MQTTClient:
    def __init__(self, broker=None, topic_prefix="homeassistant"):
        self.broker = broker or os.getenv("MQTT_BROKER", "localhost")
        self.port = int(os.getenv("MQTT_PORT", 1883))
        self.username = os.getenv("MQTT_USER")
        self.password = os.getenv("MQTT_PASS")
        self.topic_prefix = topic_prefix

        self.client = mqtt.Client()
        self.client.on_message = self.on_message

        if self.username and self.password:
            self.client.username_pw_set(self.username, self.password)

        self._message_handlers = []
        self._topic_map = {}
        self._last_colors = {}  # Track last known color per controller

    def connect(self, host=None, port=None):
        host = host or self.broker
        port = port or self.port
        self.client.connect(host, port)
        self.client.loop_start()
        logger.info(f"Connected to MQTT broker at {host}:{port}")

    def subscribe(self, topic):
        full_topic = f"{self.topic_prefix}/{topic}"
        self.client.subscribe(full_topic)
        logger.debug(f"Subscribed to topic: {full_topic}")

    def publish_state(self, config_name, color):
        topic = f"{self.topic_prefix}/light/{config_name.lower().replace(' ', '_')}/state"
        payload = {
            "state": "ON" if any((color.r, color.g, color.b)) else "OFF",
            "color": {"r": color.r, "g": color.g, "b": color.b},
            "brightness": max(color.r, color.g, color.b)
        }
        self.client.publish(topic, json.dumps(payload), retain=True)
        logger.debug(f"Published state to {topic}: {payload}")

    def subscribe_controller(self, config_name, controller):
        topic = f"light/{config_name.lower().replace(' ', '_')}/set"
        self.subscribe(topic)
        full_topic = f"{self.topic_prefix}/{topic}"
        self._topic_map[full_topic] = controller
        self._last_colors[config_name] = Color(255, 255, 255)  # Default fallback color
        logger.info(f"Subscribed to control topic for {config_name}: {full_topic}")

    def subscribe_controllers(self, controllers):
        for controller in controllers:
            self.subscribe_controller(controller.config.name, controller)

    def register_handler(self, handler):
        self._message_handlers.append(handler)
        logger.debug("Registered new MQTT message handler")

    def on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON payload received on topic {msg.topic}")
            return

        logger.info(f"Received message: {msg.topic} => {payload}")

        if msg.topic in self._topic_map:
            controller = self._topic_map[msg.topic]
            name = controller.config.name

            if "state" in payload:
                if payload["state"].lower() == "off":
                    controller.turn_off()
                    self.publish_state(name, self._last_colors[name])
                    return
                elif payload["state"].lower() == "on" and "color" not in payload:
                    controller.set_color(self._last_colors[name])
                    self.publish_state(name, self._last_colors[name])
                    return

            if "color" in payload:
                c = payload["color"]
                color = Color(c.get("r", 0), c.get("g", 0), c.get("b", 0))
                self._last_colors[name] = color
                controller.set_color(color)
                self.publish_state(name, color)

        for handler in self._message_handlers:
            try:
                handler(msg.topic, payload)
            except Exception as e:
                logger.error(f"Error in MQTT message handler: {e}")
