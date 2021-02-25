import digitalio,board, time
import pycubed_rfm9x
from sam32lib import sam32

FIFO = bytearray(256)
fifo_view = memoryview(FIFO)

def init_radios(config):
    # define radio pins
    # 1 - RST:B(D61) CS:C(DAC0)
    R1_RST = digitalio.DigitalInOut(board.D64)
    R1_CS  = digitalio.DigitalInOut(board.DAC0)
    R1_RST.switch_to_output(True)
    R1_CS.switch_to_output(True)
    # 2 - RST:D(A7)  CS:E(A8)
    R2_RST = digitalio.DigitalInOut(board.A7)
    R2_CS  = digitalio.DigitalInOut(board.A8)
    R2_RST.switch_to_output(True)
    R2_CS.switch_to_output(True)
    # 3 - RST:D59    CS:DAC1
    R3_RST = digitalio.DigitalInOut(board.DAC1)
    R3_CS  = digitalio.DigitalInOut(board.D59)
    R3_RST.switch_to_output(True)
    R3_CS.switch_to_output(True)

    # initialize radios
    radio1 = pycubed_rfm9x.RFM9x(sam32._spi,R1_CS,R1_RST,config['FREQ'],code_rate=config['CR'],baudrate=1320000)
    radio2 = pycubed_rfm9x.RFM9x(sam32._spi,R2_CS,R2_RST,config['FREQ'],code_rate=config['CR'],baudrate=1320000)
    radio3 = pycubed_rfm9x.RFM9x(sam32._spi,R3_CS,R3_RST,config['FREQ'],code_rate=config['CR'],baudrate=1320000)
    radio1.name='R1'
    radio2.name='R2'
    radio3.name='R3'
    # configure radios
    for r in (radio1,radio2,radio3):
        r.node = 0x33 # ground station ID
        r.idle()
        r.spreading_factor=config['SF']
        r.signal_bandwidth=config['BW']
        r.coding_rate=config['CR']
        r.preamble_length = 8
        r.enable_crc=True
        r.low_datarate_optimize = True
        r.ack_wait=2
        r.ack_delay=0.2
        r.ack_retries=0
        r.listen()
    return (radio1,radio2,radio3)


def get_msg(r):
    tout = time.monotonic()+2
    while time.monotonic() < tout:
        if not r.rx_done():
            pass
        else:
            packet=None
            error=1
            r.idle()
            if not r.crc_error():
                l=r._read_u8(0x13) # fifo length
                # print(l)
                if l:
                    pos = r._read_u8(0x10)
                    r._write_u8(0x0D, pos)
                    packet = fifo_view[:l]
                    r._read_into(0,packet)
                error=0
            else:
                print('crc error')
            # clear IRQ flags
            r._write_u8(0x12, 0xFF)
            # start listening again
            r.operation_mode = 5
            tout = time.monotonic() + 2
            yield packet

def mqtt_message(client, feed_id, payload):
    print("[{0}] {1}".format(feed_id, payload))
    try:
        if payload[:2]=='EV':
            client.publish('remote/response',str(eval(payload[2:])))
        elif payload[:2]=='EX':
            exec(payload[2:].encode())
    except Exception as e:
        print('error: {}'.format(e))
        print(type(payload))
        client.publish('remote/response',str(e))
