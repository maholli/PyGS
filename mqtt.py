from sam32lib import sam32
import adafruit_esp32spi.adafruit_esp32spi_socket as socket
from adafruit_minimqtt import MQTT
from secrets import secrets
import time
sam32.esp_init()
sam32.wifi(enterprise=2)
sam32.WIFI.debug=True
sam32.WIFI.connect()

sam32.synctime()

mqtt_client = MQTT(
    socket=socket,
    broker=secrets['broker'],
    port=1883,
    network_manager=sam32.WIFI,
    is_ssl=False
)
mqtt_client.connect()

mqtt_client.publish('testsub',str(time.time())+' sam32 connected')
