import os

import time
import logging
logger = logging.getLogger(__name__)
from dotenv import load_dotenv

if os.name == 'nt':
    os.system('color')

logger.info(os.getenv("MQTT_BROKER"))
