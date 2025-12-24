import time
import logging
import os
from dotenv import load_dotenv

load_dotenv(os.getenv("MQTT_LEDS_ENVFILE_PATH", ".env"))

from mqtt_leds.controller import Controller
from mqtt_leds.core.color import Color
from mqtt_leds.mqtt.client import MQTTClient

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def main():
    mqtt = MQTTClient()
    mqtt.connect()

    # solarox = Controller("solarox_rgb", mqtt_client=mqtt)
    # ws2811 = Controller("ws2811", mqtt_client=mqtt)
    ws2812 = Controller("ws281x", mqtt_client=mqtt)

    mqtt.subscribe_controllers([ws2812])

    logger.info("Waiting for MQTT messages. Press Ctrl+C to exit.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Exiting.")
        ws2812.turn_off()
        mqtt.publish_state(ws2812.config.name, Color(0, 0, 0))

if __name__ == "__main__":
    main()