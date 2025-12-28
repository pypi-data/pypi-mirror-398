import time
import os
import re
import paho.mqtt.client as mqtt
import serial
import serial.tools.list_ports
from certificate.cert_mqtt import *
from certificate.cert_defines import *
from certificate.cert_prints import *
import certificate.cert_common as cert_common
from certificate.cert_data_sim import PIXEL_SIM_INDICATOR, write_to_data_sim_log_file
import certificate.cert_utils as cert_utils

# Generic Defines
SERIAL_TIMEOUT =                                    0.05 # TODO decide about the right value
STOP_ADVERTISING =                                  '!stop_advertising'
RESET_GW =                                          '!reset'
DEDUPLICATION_PKTS =                                '!deduplication_pkts'
GW_CERT_TESTER =                                    '!gw_cert_tester'
SET_RX_CHANNEL =                                    '!set_rx_channel'
VERSION =                                           '!version'
CONNECTIVITY_STATUS =                               '!connectivity_status'
BLE_SIM_INIT =                                      '!ble_sim_init'
BLE_SIM =                                           '!ble_sim'
BLE_SIM_EXT_ADV =                                   '!ble_sim_ext_adv'

# Received RX uarts
RX_NORDIC_RECOVER_RESET =                           "NORDIC_RECOVER 1"
RX_NORDIC_RECOVER_NORESET =                         "NORDIC_RECOVER 0"
RX_RESET =                                          "reset"

GW_SIM_RESET_TS = None

# Slip related
SLIP_END =                                          0xC0
UART_PKT_PREFIX_BYTE =                              0x70

# Interference Analysis Defines
DEFAULT_LOOKOUT_TIME =                              2
GET_LOGGER_COUNTERS =                               '!get_logger_counters'
CHANNELS_TO_ANALYZE =                               [(37, 2402), (38, 2426), (39, 2480)]
CNTRS_LISTEN_TIME_SEC =                             30
MAX_UNSIGNED_32_BIT =                               0xFFFFFFFF
INCONCLUSIVE_MINIMUM =                              70
NON_WLT_RX =                                        'non_wlt_rx'
WLT_RX =                                            'wlt_rx'
BAD_CRC =                                           'bad_crc'
CNTRS_KEYS =                                        [NON_WLT_RX, WLT_RX, BAD_CRC]

GW_STATUS_MESSAGES = []


##############################################
# UART PKT TYPES
##############################################
class UplinkPkt(): # p6
    def __init__(self, gw, seq_id, raw):
        self.gw = gw
        self.seq_id = seq_id
        self.alias_brg_id = raw[2:14]
        self.payload = raw[14:76]
        self.rssi = int(raw[0:2], 16)
    def dump(self):
        return {
            GW_ID: self.gw, TIMESTAMP: time.time()*1000,
            "packets": [{ALIAS_BRIDGE_ID: self.alias_brg_id,
                         TIMESTAMP: time.time()*1000,
                         SEQUENCE_ID: self.seq_id,
                         RSSI: self.rssi,
                         PAYLOAD: self.payload}]
        }

class UplinkExtendedPkt(): # p7
    def __init__(self, gw, seq_id, raw):
        self.gw = gw
        self.seq_id = seq_id
        self.alias_brg_id = raw[2:14]
        self.payload = raw[14:98] # 39 payload + 3 side info
        self.rssi = int(raw[0:2], 16)
    def dump(self):
        return {
            GW_ID: self.gw, TIMESTAMP: time.time()*1000,
            "packets": [{ALIAS_BRIDGE_ID: self.alias_brg_id,
                         TIMESTAMP: time.time()*1000,
                         SEQUENCE_ID: self.seq_id,
                         RSSI: self.rssi,
                         PAYLOAD: self.payload}]
        }

class UplinkAggregatedPkt(): # p8
    def __init__(self, gw, seq_id, raw):
        self.gw = gw
        self.seq_id = seq_id
        self.alias_brg_id = raw[2:14]
        self.payload = raw[14:]
        self.rssi = int(raw[0:2], 16)
    def dump(self):
        return {
            GW_ID: self.gw, TIMESTAMP: time.time()*1000,
            "packets": [{ALIAS_BRIDGE_ID: self.alias_brg_id,
                         TIMESTAMP: time.time()*1000,
                         SEQUENCE_ID: self.seq_id,
                         RSSI: self.rssi,
                         PAYLOAD: self.payload}]
        }

##############################################
# UT HELPER FUNCTIONS
##############################################

def slip_decode(data: bytes) -> bytes:
    SLIP_ESC = 0xDB
    SLIP_ESC_END = 0xDC
    SLIP_ESC_ESC = 0xDD

    decoded = bytearray()
    i = 0
    while i < len(data):
        byte = data[i]
        if byte == SLIP_END:
            i += 1
            continue
        elif byte == SLIP_ESC:
            i += 1
            if i < len(data):
                if data[i] == SLIP_ESC_END:
                    decoded.append(SLIP_END)
                elif data[i] == SLIP_ESC_ESC:
                    decoded.append(SLIP_ESC)
        else:
            decoded.append(byte)
        i += 1
    return bytes(decoded)

##############################################
# UART FUNCTIONS
##############################################
def write_to_ble(ble_serial, txt, print_enable=True, sleep=0):
    # if print_enable:
    #     print('\n' + txt)
    ble_serial.write(bytes(txt, encoding='utf-8') + b'\r\n')
    if sleep:
        wait_time_n_print(sleep)

def read_frame(ble_serial: serial.Serial, frame_max_read_attempts: int = 5):
    """
    Read either [0xC0][data][0xC0] uart messages, or [data] message (for !version reply)

    :return str/None: ascii string if read successfully. None otherwise
    """
    opening_delim_received = False
    closing_delim_received = False
    read_attempts = 0

    input = ble_serial.read_until(expected=bytes([SLIP_END]))
    # We got the opening SLIP_END delimiter, read the message.
    # It's in a while loop to skip empty frames.
    while len(input) == 1 and input[0] == SLIP_END:
        opening_delim_received = True
        if read_attempts > frame_max_read_attempts:
            return None
        input = ble_serial.read_until(expected=bytes([SLIP_END]))
        read_attempts += 1
    
    while opening_delim_received and not closing_delim_received:
        # Keep reading until we get the closing delimiter
        if input[-1] == SLIP_END:
            closing_delim_received = True
            break
        if read_attempts > frame_max_read_attempts:
            print(f'WARNING: Dropped pkt with partial frame: {input}')
            return None
        chunk = ble_serial.read_until(expected=bytes([SLIP_END]))
        if not chunk:
            read_attempts += 1
            continue
        input += chunk
    
    return input

def read_from_ble(ble_serial: serial.Serial):
    input = read_frame(ble_serial)
    if input == None or len(input) == 0:
        return None
    
    input = slip_decode(input)
    input_len = len(input)
    if input_len > 3 and input[0] == UART_PKT_PREFIX_BYTE:
        input = input[0:3].decode("utf-8", "ignore") + input[3:].hex().upper()
    else:
        input = input.decode("utf-8", "ignore").strip()
    # if input:
    #     print(input)
    return input

def gw_app_reponse(ble_serial):
    write_to_ble(ble_serial, txt=VERSION, print_enable=True)
    start_time = datetime.datetime.now()
    while (datetime.datetime.now() - start_time).seconds < 2:
        input = read_from_ble(ble_serial)
        if input is not None and GW_APP_VERSION_HEADER in input:
            print(input)
            ble_chip_sw_ver = re.search(r'WILIOT_GW_BLE_CHIP_SW_VER=(\d+\.\d+\.\d+)', input).group(1)
            ble_mac_address = re.search(r'WILIOT_GW_BLE_CHIP_MAC_ADDRESS=([0-9A-F]{12})', input).group(1)
            print("success!")
            return TEST_PASSED, ble_mac_address, ble_chip_sw_ver
    print("failure!")
    return TEST_FAILED, ''

def cur_time():
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

# Packet Counters
def get_pkts_cntrs(ble_serial, channel, set_rx_ch=False):
    print(f'\n{cur_time()} | Getting pkt counters for CH{channel}')
    if set_rx_ch:
        write_to_ble(ble_serial, f"{SET_RX_CHANNEL} {channel}", sleep=1)
    pkt_cntrs = None
    write_to_ble(ble_serial, GET_LOGGER_COUNTERS)
    start_time = datetime.datetime.now()
    while (datetime.datetime.now() - start_time).seconds < DEFAULT_LOOKOUT_TIME:
        input = read_from_ble(ble_serial)
        if input and f"'{BAD_CRC}'" in input:
            start_of_cntr_index = input.find('{')
            pkt_cntrs = input[start_of_cntr_index:]
            print(f"pkt_cntrs: {pkt_cntrs}")
            return eval(pkt_cntrs)
    print(f"No counter received within the time limit of {DEFAULT_LOOKOUT_TIME} seconds")
    return pkt_cntrs

# Interference Analysis
def interference_analysis(ble_serial):
    """Analyze the interference level (PER) before the test begins"""
    
    def handle_wrap_around(a):
        "handle a wrap around of the counter"
        if a < 0:
            a = a + MAX_UNSIGNED_32_BIT
        return a

    for channel in CHANNELS_TO_ANALYZE:
        print('\n' + '#' * 30 + f'\nAnalyzing channel {channel[0]}\n' + '#' * 30)
        # Send the sniffer a command to retrieve the counters and convert them to dict
        start_cntrs = get_pkts_cntrs(ble_serial, channel[0], set_rx_ch=True)
        wait_time_n_print(CNTRS_LISTEN_TIME_SEC)
        end_cntrs = get_pkts_cntrs(ble_serial, channel[0])

        if start_cntrs is None or end_cntrs is None:
            print(color('RED', f'Channel {channel[0]} ({channel[1]} MHz) interference analysis was skipped because at least one counter is missing.'))
            print(color('RED', f'Channel {channel[0]} ({channel[1]} MHz) Ambient Interference was not calculated, missing at least one counter.'))
            continue

        # Calculate the bad CRC percentage
        diff_dict = dict()
        for key in CNTRS_KEYS:
            diff_dict[key] = handle_wrap_around(end_cntrs[key] - start_cntrs[key])
        bad_crc_percentage = round((diff_dict[BAD_CRC] / (diff_dict[WLT_RX] + diff_dict[NON_WLT_RX])) * 100)
        notes_file_path = os.path.join(ARTIFACTS_DIR, RESULT_NOTES_FILE)
        with open(notes_file_path, "a") as f:
            f.write(f'Channel {channel[0]} ({channel[1]} MHz) Ambient Interference (bad CRC percentage): {bad_crc_percentage}%\n')
        print(color('WARNING', f'Channel {channel[0]} ({channel[1]} MHz) Ambient Interference (bad CRC percentage) is: {bad_crc_percentage}%'))
        print(f'Good CRC packets = {diff_dict[NON_WLT_RX] + diff_dict[WLT_RX] - diff_dict[BAD_CRC]}, bad CRC packets: {diff_dict[BAD_CRC]}')

##############################################
# MQTT FUNCTIONS
##############################################

def on_connect(mqttc, userdata, flags, rc):
    print("python_gw_sim_connect, rc: " + str(rc))

def on_disconnect(mqttc, userdata, rc):
    txt = f"ERROR: python_gw_sim_disconnect, rc: {rc} {mqtt.error_string(rc)}"
    print(txt)
    write_to_mqtt_log_file(txt)
    write_to_data_sim_log_file(txt)

def on_subscribe(mqttc, userdata, mid, granted_qos):
    print("python_gw_sim_subscribe, " + str(mid) + " " + str(granted_qos))

def on_unsubscribe(mqttc, userdata, mid):
    print("ERROR: python_gw_sim_unsubscribe, " + str(mid))

def on_message(client, userdata, message):
    data = json.loads(message.payload.decode("utf-8"))
    print_enable = True if not PIXEL_SIM_INDICATOR in str(message.payload.decode("utf-8")) else False
    # Send packet to UART
    if TX_PKT in data:
        # Downlink packet
        cmd = f"!sp {data[TX_PKT]} {data[TX_MAX_RETRIES]}"
        write_to_ble(userdata['serial'], cmd, print_enable=print_enable)
    if GW_CONF in data:
        # GW configuration
        cfg = data[GW_CONF][ADDITIONAL]
        GW_STATUS_MESSAGES.append(data)
    if ACTION in data and len(data) == 1:
        # GW actions
        if data[ACTION].startswith("!"):
            write_to_ble(userdata['serial'], data[ACTION], print_enable=print_enable)

##############################################
# GW SIMULATOR
##############################################
def parse_uart_pkts(input, mqttc, custom_broker, gw_id, seq_id):
    # 3 for p6, 2 for rssi, 12 for alias_brg_id, 62 for payload
    if input.startswith("p6 ") and len(input) == (3 + 12 + 62 + 2):
        # p6 301234567898761E16C6FC0000EE02093E3C71BF6DFA3C006648001CB8003A730160000E0100
        pkt = UplinkPkt(gw_id, seq_id, input.split()[1])
        mqttc.publish(custom_broker[CUSTOM_BROKER_DATA_TOPIC], payload=json.dumps(pkt.dump(), indent=4))
        return True
    # 3 for p7, 2 for rssi, 12 for alias_brg_id, 78 for payload, 6 for side info
    elif input.startswith("p7 ") and len(input) == (3 + 12 + 78 + 6 + 2):
        # p7 301234567898762616C6FC05000002093E3C71BF6DFA3C006648001CB8003A730160000E01001122334455667788
        pkt = UplinkExtendedPkt(gw_id, seq_id, input.split()[1])
        mqttc.publish(custom_broker[CUSTOM_BROKER_DATA_TOPIC], payload=json.dumps(pkt.dump(), indent=4))
        return True
    # 3 for p8, 2 for rssi, 12 for alias_brg_id, the rest for payload of multiple packets
    elif input.startswith("p8 "):
        # p8 301234567898762616C6FC05000002093E3C71BF6DFA3C006648001CB8003A730160000E01001122334455667788....
        pkt = UplinkAggregatedPkt(gw_id, seq_id, input.split()[1])
        mqttc.publish(custom_broker[CUSTOM_BROKER_DATA_TOPIC], payload=json.dumps(pkt.dump(), indent=4))
        return True
    elif GW_STATUS_MESSAGES:
        pkt = GW_STATUS_MESSAGES.pop(0)
        mqttc.publish(custom_broker[CUSTOM_BROKER_STATUS_TOPIC], payload=json.dumps(pkt, indent=4))
    return False

def handle_cmds(input, ble_serial):
    if input.startswith(RX_NORDIC_RECOVER_RESET):
        utPrint(f"Simulator received reboot packet", "CYAN")
        global GW_SIM_RESET_TS
        GW_SIM_RESET_TS = datetime.datetime.now()
        write_to_ble(ble_serial, RESET_GW, sleep=0)
    if input.startswith(RX_NORDIC_RECOVER_NORESET):
        utPrint(f"COM tester recovered", "CYAN")
        write_to_ble(ble_serial, f"{CONNECTIVITY_STATUS} 1 1")

def validate_port(port):
    try:
        with serial.serial_for_url(url=port, baudrate=921600, timeout=SERIAL_TIMEOUT,
                                   write_timeout=SERIAL_TIMEOUT * 10) as ser:
            ser.flushInput()
            write_to_ble(ser, txt=VERSION, print_enable=True)
            start_time = datetime.datetime.now()
            while (datetime.datetime.now() - start_time).seconds < 2:
                input = read_from_ble(ser)
                if input is not None and GW_APP_VERSION_HEADER in input:
                    return True
            return False
    except Exception as e:
        utPrint(f"Failed to open serial: {e}", "RED")
        return False


def gw_sim_run(port, gw_id, custom_broker, disable_interference_analyzer=False):

    # Init serial side
    if not port:
        print("\nNo COM port given. Scanning for available ports:")
        for port, desc, hwid in sorted(serial.tools.list_ports.comports()):
            print("{}: {} [{}]".format(port, desc, hwid))
            if validate_port(port):
                utPrint(f"Found the tester's port ({port})", "GREEN")
                break
    if not port:
        print("\nNo available COM port found! Please verify a tester is connected and set the correct --port parameter.")
        sys.exit(-1)
    print(f"###>>> GW SIM STARTED WITH PORT {port}")
    ble_serial = serial.serial_for_url(url=port, baudrate=921600, timeout=SERIAL_TIMEOUT)
    ble_serial.flushInput()

    # Init mqtt side
    custom_broker = load_custom_broker(custom_broker, gw_id)
    client_id = '{}-republish2'.format(gw_id)
    userdata = {'serial': ble_serial}
    mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, client_id, userdata=userdata)
    mqttc.username_pw_set(custom_broker[CUSTOM_BROKER_USERNAME], custom_broker[CUSTOM_BROKER_PASSWORD])
    mqttc.on_message = on_message
    mqttc.on_connect = on_connect
    mqttc.on_disconnect = on_disconnect
    mqttc.on_subscribe = on_subscribe
    mqttc.on_unsubscribe = on_unsubscribe
    if not 1883 == custom_broker[CUSTOM_BROKER_PORT]:
        mqttc.tls_set(tls_version=ssl.PROTOCOL_TLSv1_2)
    mqttc.connect(custom_broker[CUSTOM_BROKER_BROKER_URL].replace("mqtts://", ""), port=custom_broker[CUSTOM_BROKER_PORT], keepalive=60)
    mqttc.loop_start()

    mqttc.update_topic = custom_broker[CUSTOM_BROKER_UPDATE_TOPIC]
    mqttc.subscribe(mqttc.update_topic)

    # Run BLE
    write_to_ble(ble_serial, RESET_GW, sleep=5)
    gw_app_res = gw_app_reponse(ble_serial)
    if gw_app_res[0] == TEST_FAILED:
        utPrint("ERROR: didn't get version response! Please verify a tester is connected and set the correct --port parameter.", "RED")
        sys.exit(1)
    if gw_app_res[2] not in cert_utils.TESTER_FW_VERSIONS:
        utPrint(f"ERROR: Tester FW version={gw_app_res[2]} instead of versions={cert_utils.TESTER_FW_VERSIONS}!\n"
                f"Please run the command wlt-cert-tester-upgrade to upgrade the tester firmware!", "RED")
        sys.exit(1)
    os.environ[GW_SIM_BLE_MAC_ADDRESS] = gw_app_res[1]
    os.environ[GW_APP_VERSION_HEADER] = gw_app_res[2]
    write_to_ble(ble_serial, STOP_ADVERTISING, sleep=2)
    write_to_ble(ble_serial, f"{CONNECTIVITY_STATUS} 1 1")

    # Run interference analysis
    if not disable_interference_analyzer:
        print(color("BLUE", f"\nStarting interference analysis for channels {[ch[0] for ch in CHANNELS_TO_ANALYZE]}. This will take {30 * len(CHANNELS_TO_ANALYZE)} seconds (total)"))
        interference_analysis(ble_serial)

    # Run infinte loop reading from UART
    seq_id = 100
    while True:
        input = read_from_ble(ble_serial)
        if input and len(input) >= 3 and input[0] == "p" and input[2] == " ":
            seq_id += 1
        # input = ""
        if input and not parse_uart_pkts(input, mqttc, custom_broker, gw_id, seq_id):
            handle_cmds(input, ble_serial)
            # if input:
            if 0:
                print(f"###>>> IGNORED: {input}")