from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)

class LEDStrip(ABC):
    def __init__(self, config):
        self.config = config
        logger.debug(f"Initialized LEDStrip with config: {config}")

    @abstractmethod
    def set_color(self, r: int, g: int, b: int):
        pass

    @abstractmethod
    def turn_off(self):
        pass

    @abstractmethod
    def update(self):
        pass

    def available_features(self):
        return {
            "individually_addressable": self.config.individually_addressable,
            "length": self.config.length,
            "supports_effects": self.config.individually_addressable
        }
