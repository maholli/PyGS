import time
from radio_helpers import init_radios, get_msg
import adafruit_esp32spi.adafruit_esp32spi_socket as socket
from adafruit_minimqtt import MQTT
from secrets import secrets
from sam32lib import sam32

radios = init_radios()

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

# mqtt_client.publish('testsub',str(time.time())+' sam32 connected')

while True:
    for r in radios:
        if r.rx_done():
            print(r.name,end=': ')
            for msg in get_msg(r):
                if msg is not None:
                    print(bytes(msg), end=', ')
                    mqtt_client.publish('testsub',str(time.time().to_bytes(5,'big')+msg))
            print()
