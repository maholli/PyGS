import wifi, socketpool, time, alarm
import adafruit_minimqtt.adafruit_minimqtt as MQTT
from radio_helpers import gs, mqtt_message, connected
from secrets import secrets
import storage,os

DEEP_SLEEP_TIME = 30
DATA_TOPIC = 'gs/testsub'
CTRL_TOPIC = 'gs/remote'

radios=[]
# if we haven't slept yet, init radios
if not alarm.wake_alarm:
    print('First boot')
    radios = gs.init_radios(gs.SATELLITE['VR3X'])
    # reset counters
    gs.counter = 0
    gs.msg_count = 0
    gs.msg_cache = 0
    gs.cache_pointer = gs.CACHE_START
else:
    radios={1:gs.R1_CS,2:gs.R2_CS,3:gs.R3_CS}


print('Loop: {}, Total Msgs: {}, Msgs in Cache: {}'.format(gs.counter,gs.msg_count,gs.msg_cache))

# try connecting to wifi
print('Connecting to WiFi...')
try:
    wifi.radio.connect(ssid='W6YX') # open network
    # wifi.radio.connect(ssid='S8hotspot') # open network

    # Create a socket pool
    pool = socketpool.SocketPool(wifi.radio)
    # sync out RTC from the web
    gs.synctime(pool)
except Exception as e:
    print('Unable to connect to WiFi: {}'.format(e))

# check radios
new_messages=[]
if alarm.wake_alarm:
    for r in radios:
        if gs.rx_done(radios[r]):
            gs.rgb[0]=(0,255,0)
            print(r,end=': ')
            for msg in gs.get_msg2(radios[r]):
                if msg is not None:
                    print('[{}] rssi:{}'.format(bytes(msg),gs.last_rssi), end=', ')
                    if msg is b'CRC ERROR':
                        msg_str = '{},{},{},{}'.format(time.time(),r,'CRC ERROR',gs.last_rssi)
                        new_messages.append(msg_str)
                    else:
                        msg_str = '{},{},{},{}'.format(time.time(),r,bytes(msg),gs.last_rssi)
                        new_messages.append(msg_str)
            print()
    radios = gs.init_radios(gs.SATELLITE['VR3X'])
else:
    for r in radios:
        if r.rx_done():
            gs.rgb[0]=(0,255,0)
            print(r.name,end=': ')
            for msg in gs.get_msg(r):
                if msg is not None:
                    print('[{}] rssi:{}'.format(bytes(msg),gs.last_rssi), end=', ')
                    if msg is b'CRC ERROR':
                        msg_str = '{},{},{},{}'.format(time.time(),r.name,'CRC ERROR',gs.last_rssi)
                        new_messages.append(msg_str)
                    else:
                        msg_str = '{},{},{},{}'.format(time.time(),r.name,bytes(msg),gs.last_rssi)
                        new_messages.append(msg_str)
            print()

if new_messages:
    gs.msg_count = gs.msg_count + 1

# if we have wifi, connect to mqtt broker
if wifi.radio.ap_info is not None:
    # try:
    # Set up a MiniMQTT Client
    mqtt_client = MQTT.MQTT(
        broker=secrets['broker'],
        port=secrets['port'],
        socket_pool=pool,
        is_ssl=False,
    )
    mqtt_client.on_connect = connected
    mqtt_client.on_message = mqtt_message

    mqtt_client.connect()
    mqtt_client.subscribe(CTRL_TOPIC)
    mqtt_client.publish(DATA_TOPIC,'[{}] Loop:{}, Msg Cnt:{}, Msg Cache:{}'.format(time.time(),gs.counter,gs.msg_count,gs.msg_cache))

    # send any cached messages
    if gs.msg_cache:
        with open('/data.txt','r') as f:
            l=f.readline()
            while l:
                mqtt_client.publish(DATA_TOPIC,'[cached] {}'.format(l.strip()))
                l=f.readline()
        os.remove('/data.txt')
        gs.msg_cache=0

    # send any new messages
    if new_messages:
        for msg in new_messages:
            mqtt_client.publish(DATA_TOPIC,'[new] {}'.format(msg))
    mqtt_client.disconnect()

# if we can't connect, cache message
else:
    for msg in new_messages:
        try:
            storage.remount('/',False)
            with open('/data.txt','a') as f:
                f.write(msg+'\n')
            storage.remount('/',True)
        except: pass
        gs.msg_cache=gs.msg_cache+1


print('Finished. Deep sleep for {} seconds.'.format(DEEP_SLEEP_TIME))
gs.counter = gs.counter + 1
time_alarm = alarm.time.TimeAlarm(monotonic_time=time.monotonic() + DEEP_SLEEP_TIME)
alarm.exit_and_deep_sleep_until_alarms(time_alarm)
