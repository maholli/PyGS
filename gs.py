import time
from radio_helpers import init_radios, get_msg, mqtt_message
import adafruit_esp32spi.adafruit_esp32spi_socket as socket
from adafruit_minimqtt import MQTT
from secrets import secrets
from sam32lib import sam32


# SATELLITE = {
#     'NAME':'VR3X',
#     'FREQ':915.6,
#     'SF':7,'BW':62500,'CR':8,
# }

SATELLITE = {
    'NAME':'NORBI',
    'FREQ':436.703,
    'SF':10,'BW':250000,'CR':8,
}

radios = init_radios(SATELLITE)

sam32.esp_init()
sam32.wifi(enterprise=2)
sam32.WIFI.debug=True
sam32.WIFI.connect()
sam32.synctime()


mqtt_client = MQTT(
    socket=socket,
    broker=secrets['broker'],
    port=1884,
    network_manager=sam32.WIFI,
    is_ssl=False
)

mqtt_client.on_message=mqtt_message

mqtt_client.connect()
mqtt_client.subscribe('gs/remote')
mqtt_client.publish('gs/testsub','[{}] sam32 connected'.format(time.time()))
mqtt_client.publish('gs/testsub','Radio Config: {}'.format(SATELLITE))

while True:
    mqtt_client.loop()
    # time.sleep(1)
    for r in radios:
        if r.rx_done():
            print(r.name,end=': ')
            for msg in get_msg(r):
                if msg is not None:
                    print(bytes(msg), end=', ')
                    mqtt_client.publish('gs/testsub',str(time.time().to_bytes(5,'big')+msg))
            print()
