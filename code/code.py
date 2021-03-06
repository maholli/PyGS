import wifi, socketpool, time, alarm
import adafruit_minimqtt.adafruit_minimqtt as MQTT
from radio_helpers import gs, mqtt_message, connected
from secrets import secrets
import storage,os,board

gs.ID = 'B'
DATA_TOPIC = 'gs/testsub'
CTRL_TOPIC = 'gs/remote'+gs.ID

SAT = gs.SATELLITE['VR3X']

radios=[]
# if we haven't slept yet, init radios
if not alarm.wake_alarm:
    print('First boot')
    radios = gs.init_radios(SAT)
    # reset counters
    gs.counter = 0
    gs.msg_count = 0
    gs.msg_cache = 0
    gs.deep_sleep = 600
else:
    radios={1:gs.R1_CS,2:gs.R2_CS,3:gs.R3_CS}


print('Loop: {}, Total Msgs: {}, Msgs in Cache: {}, Vbatt: {:.1f}'.format(gs.counter,gs.msg_count,gs.msg_cache,gs.battery_voltage))

# try connecting to wifi
print('Connecting to WiFi...')
try:
    wifi.radio.connect(ssid='W6YX') # open network
    # wifi.radio.connect(ssid='S8hotspot') # open network

    print('Signal: {}'.format(wifi.radio.ap_info.rssi))
    # Create a socket pool
    pool = socketpool.SocketPool(wifi.radio)
    # sync out RTC from the web
    gs.synctime(pool)
except Exception as e:
    print('Unable to connect to WiFi: {}'.format(e))

# check radios
new_messages=[]
if alarm.wake_alarm:
    # hacky way of checking the radios without initalizing the hardware
    for r in radios:
        if gs.rx_done(radios[r]):
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
    radios = gs.init_radios(SAT)
else:
    for r in radios:
        if r.rx_done():
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
    mqtt_client.publish(DATA_TOPIC,'[{}] [{}] {}, Msgs:{}, Cache:{}, Vbatt: {:.1f}, Wifi: {}'.format(
        time.time(),gs.ID,gs.counter,gs.msg_count,gs.msg_cache,
        gs.battery_voltage, wifi.radio.ap_info.rssi))

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
    # check for mqtt remote messages
    mqtt_client.loop()
    # break mqtt connection
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

gs.counter = gs.counter + 1

print('Finished. Deep sleep until packet or {}s timeout...'.format(gs.deep_sleep))
# wake up on IRQ or after deep sleep time
pin_alarm1 = alarm.pin.PinAlarm(pin=board.IO7, value=True, pull=False)
pin_alarm2 = alarm.pin.PinAlarm(pin=board.IO5, value=True, pull=False)
pin_alarm3 = alarm.pin.PinAlarm(pin=board.IO6, value=True, pull=False)
time_alarm = alarm.time.TimeAlarm(monotonic_time=time.monotonic() + gs.deep_sleep)
alarm.exit_and_deep_sleep_until_alarms(time_alarm,pin_alarm1,pin_alarm2,pin_alarm3)
