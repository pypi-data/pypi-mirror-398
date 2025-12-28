from certificate.cert_prints import *
from certificate.cert_defines import *
from certificate.wlt_types import *
import certificate.cert_mqtt as cert_mqtt
import certificate.cert_common as cert_common
import certificate.cert_config as cert_config
import certificate.cert_data_sim as cert_data_sim
import csv

# test MACROS definitions #
DEFAULT_ADVA0 = "112233445566"
DEFAULT_ADVA1 = "778899AABBCC"
DEFAULT_ADVA2 = "DDEEFF112233"
DEFAULT_ADVA3 = "123456123456"
TESTING_SENSOR_INDICATOR = "2222222222"
DEFAULT_SENSOR_PAYLOAD_DATA = "0200002929B0FFF98DB1" + TESTING_SENSOR_INDICATOR + "91456B55CC18AADB"
ERM_SMART_MS_PAYLOAD = "0201060303374C17FFAE04" + TESTING_SENSOR_INDICATOR + "E7AE7C5EB13B744D401CC6CFCF0107"
ZEBRA_PRINTER_PAYLOAD = "0201020F" + TESTING_SENSOR_INDICATOR + "4A323331363038333435030279FEA5A5A5A5A5A5A5A5"
UNIFIED_PAYLOAD = "0201020611111111111103FF000505" + TESTING_SENSOR_INDICATOR + "0000000000000000000000"
DEFAULT_PACKET_LENGTH = "1E"

SCAN_TIMEOUT = 60

# UUID defines for logs review #
ZEBRA_PRINTER_UUID = ag.EXTERNAL_SENSORS_ZEBRA_PRINTER >> 8  # Scrambling
MINEW_S1_UUID = ag.EXTERNAL_SENSORS_MINEWS1 >> 8  # Scrambling
ERM_SMART_MS_UUID = ag.EXTERNAL_SENSORS_ERM_SMART_MS >> 8  # No scrambling
SIGNAL_INDICATOR_UUID = ag.EXTERNAL_SENSORS_SIGNAL_INDICATOR >> 8  # Unified Sensor

SCRAMBLE_ON = 0x01
UNIFIED_SCRAMBLE_OFF = 0x00
UNIFIED_ON = 0x02


def unscramble(packet):
    unscrambled_packet_id = int(hex(packet[RSSI])[2:] + packet[SENSOR_ID][-6:], 16)  # transforming parameters string to hex format
    for idx in range(6, 60, 8):
        current_word = int(packet[PAYLOAD][idx: idx + 8], 16)
        unscrambled_packet_id ^= current_word
    return packet[PAYLOAD][8:-8] + f"{unscrambled_packet_id:08x}"


def find_packet_in_csv(unscrambled_payload):
    base_path = os.path.dirname(os.path.abspath(__file__))
    with open(f'{base_path}/out_sensor_data.csv', 'r') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        next(csv_reader)                        # stepping over the header line
        for line in csv_reader:
            raw_data_payload = line['raw packet'][20:]
            if raw_data_payload[:-8] == unscrambled_payload[:-8]:
                return True
        return False


def find_unified_packet_in_csv(pkt):
    unified_pkt = ag.UnifiedSensorPkt(pkt)
    base_path = os.path.dirname(os.path.abspath(__file__))
    with open(f'{base_path}/out_sensor_data.csv', 'r') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        next(csv_reader)                        # stepping over the header line
        for line in csv_reader:
            raw_data_pkt = ag.UnifiedSensorPkt(line['raw packet'][20:])
            if raw_data_pkt.sensor_payload == unified_pkt.sensor_payload:
                return True
        return False


def create_csv_file_in(test, length=500):
    if test.data != DATA_SIMULATION:
        return []
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    pkts = []
    with open(f"{base_path}/in_sensor_data.csv", "w+") as f:
        f.write("raw packet,output power,delay,duplicates,channel,COM\n")
        for i in range(length):
            # Create pkts
            pkt_0 = cert_data_sim.GenericPkt(adva=DEFAULT_ADVA0, payload=ZEBRA_PRINTER_PAYLOAD)
            pkt_1 = cert_data_sim.GenericPkt(adva=DEFAULT_ADVA1, payload=(DEFAULT_PACKET_LENGTH +
                                                                          cert_common.int2mac_get(MINEW_S1_UUID)[6:] +
                                                                          DEFAULT_SENSOR_PAYLOAD_DATA +
                                                                          f"{i:08X}"))
            pkt_2 = cert_data_sim.GenericPkt(adva=DEFAULT_ADVA2, payload=ERM_SMART_MS_PAYLOAD)
            pkt_unified = cert_data_sim.GenericPkt(adva=DEFAULT_ADVA3, payload=UNIFIED_PAYLOAD)
            # Write to csv
            f.write(pkt_0.get_pkt() + ",8,200,6,37,COM3\n")
            f.write(pkt_1.get_pkt() + ",8,200,6,37,COM3\n")
            f.write(pkt_2.get_pkt() + ",8,200,6,37,COM3\n")
            f.write(pkt_unified.get_pkt() + ",8,200,6,37,COM3\n")
            # Add to pkts list to be sent
            pkts.append(pkt_0)
            pkts.append(pkt_1)
            pkts.append(pkt_2)
            pkts.append(pkt_unified)
    return pkts


def create_csv_file_out(test):
    if test.data != DATA_SIMULATION:
        return
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    uuid_0 = cert_common.int2mac_get(ZEBRA_PRINTER_UUID)[6:]
    uuid_2 = cert_common.int2mac_get(ERM_SMART_MS_UUID)[6:]
    uuid_unified = cert_common.int2mac_get(SIGNAL_INDICATOR_UUID)[6:]
    with (open(f"{base_path}/in_sensor_data.csv", "r") as csv_in,
          open(f"{base_path}/out_sensor_data.csv", "w") as csv_out):
        csv_out.write("raw packet,output power,delay,duplicates,channel,COM\n")
        csv_in = csv.DictReader(csv_in)
        next(csv_in)                        # stepping over the header line
        for line in csv_in:
            input_payload = line['raw packet'][12:]
            if uuid_0 in input_payload:
                csv_out.write(DEFAULT_ADVA0 + process_sensor_payload(input_payload, uuid_0) + ",8,200,6,37,COM3\n")
            elif uuid_2 in input_payload:
                csv_out.write(DEFAULT_ADVA2 + process_sensor_payload(input_payload, uuid_2) + ",8,200,6,37,COM3\n")
            elif uuid_unified in input_payload:
                csv_out.write(DEFAULT_ADVA3 + process_sensor_payload(input_payload, uuid_unified) + ",8,200,6,37,COM3\n")
            else:
                csv_out.write(line['raw packet'] + ",8,200,6,37,COM3\n")


def process_sensor_payload(payload, uuid):
    uuid_idx = payload.find(uuid)
    if uuid_idx == -1:
        raise ValueError(f"Pattern {uuid_idx} not found in the packet")

    len = int(payload[uuid_idx - 2:uuid_idx], 16)
    segment_start_idx = uuid_idx - 2
    segment_end_idx = uuid_idx + len * 2
    segment = payload[segment_start_idx:segment_end_idx]
    output = segment + payload[:segment_start_idx] + payload[segment_end_idx:]
    return output


def pkts_get(test, phase, is_unified=False, target=DUT):
    test.get_mqttc_by_target(target).flush_pkts()
    mqtt_scan_wait(test, duration=SCAN_TIMEOUT)
    sensor_pkts = cert_mqtt.get_all_sensor_pkts(test, is_unified, remove_embedded=True)
    # protection against real sensors interfering with the test
    sensor_pkts = [p for p in sensor_pkts if TESTING_SENSOR_INDICATOR in p[PAYLOAD]]
    cert_mqtt.generate_log_file(test, phase)

    if len(sensor_pkts) == 0:
        if phase != "tag_data_only" and phase != "rssi_threshold":
            test.rc = TEST_FAILED
            test.add_reason(f"Phase {phase} failed - didn't find any sensor packets")

    return sensor_pkts


def test_tag_data_only(test, phase, _):
    sensor_pkts = pkts_get(test, phase)
    if len(sensor_pkts) > 0:
        test.rc = TEST_FAILED
        test.add_reason(f"Phase {phase} failed - found sensor packets")
    return test


def test_rssi_threshold(test, phase, ext_sensors_module):
    rssi_threshold = -25
    # Config
    utPrint(f"EXTERNAL_SENSORS_ZEBRA_PRINTER, RSSI Threshold = {rssi_threshold}\n", "BLUE")
    test = cert_config.brg_configure(test=test, module=ext_sensors_module,
                                     fields=[BRG_SENSOR0, BRG_RSSI_THRESHOLD],
                                     values=[ag.EXTERNAL_SENSORS_ZEBRA_PRINTER, rssi_threshold])[0]
    # Analyze
    sensor_pkts = pkts_get(test, phase)
    if test.rc == TEST_FAILED:
        return test
    rssi_threshold_violation_pkts = [p for p in sensor_pkts if p[RSSI] >= -1 * rssi_threshold]
    if rssi_threshold_violation_pkts:
        test.rc = TEST_FAILED
        test.add_reason("rssi_threshold phase failed - received"
                        f" {len(rssi_threshold_violation_pkts)} sensor packets\n with RSSI weaker than {rssi_threshold}")
        return test
    return test


def test_snsr2_unified(test, phase, ext_sensors_module):
    # Config
    utPrint(f"SIGNAL_INDICATOR_UUID is 0x{SIGNAL_INDICATOR_UUID:06X}", "BLUE")
    test = cert_config.brg_configure(test=test, module=ext_sensors_module,
                                     fields=[BRG_SENSOR2],
                                     values=[ag.EXTERNAL_SENSORS_SIGNAL_INDICATOR])[0]
    if test.rc == TEST_FAILED:
        test.add_reason(f"Configuration for phase {phase} failed")
        return test
    # Analyze
    sensor_pkts = pkts_get(test, phase, is_unified=True)
    if test.rc == TEST_FAILED:
        return test
    for p in sensor_pkts:
        sensor_id = (f"{p[UNIFIED_SENSOR_PKT].pkt.sensor_ad_type:02X}"
                     f"{p[UNIFIED_SENSOR_PKT].pkt.sensor_uuid_msb:02X}"
                     f"{p[UNIFIED_SENSOR_PKT].pkt.sensor_uuid_lsb:02X}")
        if sensor_id != f"{SIGNAL_INDICATOR_UUID:06X}":
            test.rc = TEST_FAILED
            test.add_reason(f"Phase {phase} failed - received packets from an un-registered sensor: {sensor_id}")
            return test
        unified_payload = p[PAYLOAD][8:]
        if find_unified_packet_in_csv(unified_payload) is False:
            test.rc = TEST_FAILED
            test.add_reason(f"Phase {phase} failed - couldn't find payload for {SIGNAL_INDICATOR_UUID:06X}")
            return test
    return test


def test_snsr0_no_scrmbl(test, phase, ext_sensors_module):
    # Config
    utPrint(f"ERM_SMART_MS_UUID only without scrambling - UUID is 0x{ERM_SMART_MS_UUID:06X}", "BLUE")
    test = cert_config.brg_configure(test=test, module=ext_sensors_module,
                                     fields=[BRG_SENSOR0],
                                     values=[ag.EXTERNAL_SENSORS_ERM_SMART_MS])[0]
    if test.rc == TEST_FAILED:
        test.add_reason(f"Configuration for phase {phase} failed")
        return test
    # Analyze
    sensor_pkts = pkts_get(test, phase)
    if test.rc == TEST_FAILED:
        return test
    # verify packets exists
    sensor0_pkts = [p[SENSOR_UUID] == f"{ERM_SMART_MS_UUID:06X}" for p in sensor_pkts if SENSOR_UUID in p]
    if not any(sensor0_pkts):
        test.rc = TEST_FAILED
        test.add_reason(f"Phase {phase} failed - didn't find any sensor0 packets")
        return test
    # verify packets structure
    for p in sensor_pkts:
        if p[SENSOR_UUID] != f"{ERM_SMART_MS_UUID:06X}":
            test.rc = TEST_FAILED
            test.add_reason(f"Phase {phase} failed - received packets from an un-registered sensor: {p[SENSOR_UUID]}")
            return test
        payload = p[PAYLOAD][8:]
        if find_packet_in_csv(payload) is False:
            test.rc = TEST_FAILED
            test.add_reason(f"Phase {phase} failed - couldn't find payload for {ERM_SMART_MS_UUID:06X}")
            return test
    return test


def test_snsr1_scrmbl(test, phase, ext_sensors_module):
    # Config
    utPrint(f"MINEW_S1_UUID only with scrambling - UUID is 0x{MINEW_S1_UUID:06X}", "BLUE")
    test = cert_config.brg_configure(test=test, module=ext_sensors_module,
                                     fields=[BRG_SENSOR1],
                                     values=[ag.EXTERNAL_SENSORS_MINEWS1])[0]
    if test.rc == TEST_FAILED:
        test.add_reason(f"Configuration for phase {phase} failed")
        return test
    # Analyze
    sensor_pkts = pkts_get(test, phase)
    if test.rc == TEST_FAILED:
        return test
    # verify packets exists
    sensor1_pkts = [p[SENSOR_UUID] == f"{MINEW_S1_UUID:06X}" for p in sensor_pkts if SENSOR_UUID in p]
    if not any(sensor1_pkts):
        test.rc = TEST_FAILED
        test.add_reason(f"Phase {phase} failed - didn't find any sensor1 packets")
        return test
    # verify packets structure
    for p in sensor_pkts:
        if p[SENSOR_UUID] != f"{MINEW_S1_UUID:06X}":
            test.rc = TEST_FAILED
            test.add_reason(f"Phase {phase} failed - received packets from an un-registered sensor: {p[SENSOR_UUID]}")
            return test
        unscrambled_payload = unscramble(p)
        if find_packet_in_csv(unscrambled_payload) is False:
            test.rc = TEST_FAILED
            test.add_reason(f"Phase {phase} failed - couldn't find unscrambled payload")
            return test
    return test


def test_snsr0_no_scrmbl_snsr1_scrmbl_snsr2_scrmbl(test, phase, ext_sensors_module):
    # Config
    utPrint(f"ERM_SMART_MS without scrambling, ZEBRA_PRINTER with scrambling, MINEW_S1 with scrambling,"
            f"{SCAN_TIMEOUT} sec\n", "BLUE")
    test = cert_config.brg_configure(test=test, module=ext_sensors_module,
                                     fields=[BRG_SENSOR0, BRG_SENSOR1, BRG_SENSOR2],
                                     values=[ag.EXTERNAL_SENSORS_ERM_SMART_MS,
                                             ag.EXTERNAL_SENSORS_ZEBRA_PRINTER,
                                             ag.EXTERNAL_SENSORS_MINEWS1])[0]
    if test.rc == TEST_FAILED:
        return test
    # Analyze
    sensor_pkts = pkts_get(test, phase)
    if test.rc == TEST_FAILED:
        return test
    # verify packets exists
    sensor0_pkts = [p[SENSOR_UUID] == f"{ERM_SMART_MS_UUID:06X}" for p in sensor_pkts if SENSOR_UUID in p]
    if not any(sensor0_pkts):
        test.rc = TEST_FAILED
        test.add_reason(f"Phase {phase} failed - didn't find any sensor0 packets")
        return test
    sensor1_pkts = [p[SENSOR_UUID] == f"{ZEBRA_PRINTER_UUID:06X}" for p in sensor_pkts if SENSOR_UUID in p]
    if not any(sensor1_pkts):
        test.rc = TEST_FAILED
        test.add_reason(f"Phase {phase} failed - didn't find any sensor1 packets")
        return test
    sensor2_pkts = [p[SENSOR_UUID] == f"{MINEW_S1_UUID:06X}" for p in sensor_pkts if SENSOR_UUID in p]
    if not any(sensor2_pkts):
        test.rc = TEST_FAILED
        test.add_reason(f"Phase {phase} failed - didn't find any sensor2 packets")
        return test
    # verify packets structure
    for p in sensor_pkts:
        if not (p[SENSOR_UUID] == f"{ZEBRA_PRINTER_UUID:06X}" or p[SENSOR_UUID] == f"{MINEW_S1_UUID:06X}" or
                p[SENSOR_UUID] == f"{ERM_SMART_MS_UUID:06X}"):
            test.rc = TEST_FAILED
            test.add_reason(f"Phase {phase} failed - received packets from an un-registered sensor: {p[SENSOR_UUID]}")
            return test
        if p[SENSOR_UUID] == f"{ERM_SMART_MS_UUID:06X}":
            payload = p[PAYLOAD][8:]
            if find_packet_in_csv(payload) is False:
                test.rc = TEST_FAILED
                test.add_reason(f"Phase {phase} failed - couldn't find payload for {ERM_SMART_MS_UUID:06X}")
                return test
        if p[SENSOR_UUID] == f"{MINEW_S1_UUID:06X}":
            unscrambled_payload = unscramble(p)
            if find_packet_in_csv(unscrambled_payload) is False:
                test.rc = TEST_FAILED
                test.add_reason(f"Phase {phase} failed - couldn't find payload for {MINEW_S1_UUID:06X}")
                return test
        if p[SENSOR_UUID] == f"{ZEBRA_PRINTER_UUID:06X}":
            unscrambled_payload = unscramble(p)
            if find_packet_in_csv(unscrambled_payload) is False:
                test.rc = TEST_FAILED
                test.add_reason(f"Phase {phase} failed - couldn't find unscrambled payload for {ZEBRA_PRINTER_UUID:06X}")
                return test
    return test


def test_snsr0_no_scrmbl_snsr1_scrmbl_snsr2_unified(test, phase, ext_sensors_module):
    # Config
    utPrint(f"ERM_SMART_MS without scrambling, ZEBRA_PRINTER scrambling, SIGNAL_INDICATOR unified, {SCAN_TIMEOUT} sec\n", "BLUE")
    test = cert_config.brg_configure(test=test, module=ext_sensors_module, fields=[BRG_SENSOR0, BRG_SENSOR1, BRG_SENSOR2],
                                     values=[ag.EXTERNAL_SENSORS_ERM_SMART_MS,
                                             ag.EXTERNAL_SENSORS_ZEBRA_PRINTER,
                                             ag.EXTERNAL_SENSORS_SIGNAL_INDICATOR])[0]
    if test.rc == TEST_FAILED:
        return test
    # Analyze
    sensor_pkts = pkts_get(test, phase, is_unified=True)
    if test.rc == TEST_FAILED:
        return test
    # verify packets exists
    sensor0_pkts = [p[SENSOR_UUID] == f"{ERM_SMART_MS_UUID:06X}" for p in sensor_pkts if SENSOR_UUID in p]
    if not any(sensor0_pkts):
        test.rc = TEST_FAILED
        test.add_reason(f"Phase {phase} failed - didn't find any sensor0 packets")
        return test
    sensor1_pkts = [p[SENSOR_UUID] == f"{ZEBRA_PRINTER_UUID:06X}" for p in sensor_pkts if SENSOR_UUID in p]
    if not any(sensor1_pkts):
        test.rc = TEST_FAILED
        test.add_reason(f"Phase {phase} failed - didn't find any sensor1 packets")
        return test
    sensor2_pkts = []
    for p in sensor_pkts:
        if UNIFIED_SENSOR_PKT in p:
            unified_sensor_uuid = (f"{p[UNIFIED_SENSOR_PKT].pkt.sensor_ad_type:02X}"
                                   f"{p[UNIFIED_SENSOR_PKT].pkt.sensor_uuid_msb:02X}"
                                   f"{p[UNIFIED_SENSOR_PKT].pkt.sensor_uuid_lsb:02X}")
            if unified_sensor_uuid == f"{SIGNAL_INDICATOR_UUID:06X}":
                sensor2_pkts.append(p)
    if not any(sensor2_pkts):
        test.rc = TEST_FAILED
        test.add_reason(f"Phase {phase} failed - didn't find any sensor2 packets")
        return test
    # verify packets structure
    for p in sensor_pkts:
        if SENSOR_UUID in p:
            if not (p[SENSOR_UUID] == f"{ERM_SMART_MS_UUID:06X}" or
                    p[SENSOR_UUID] == f"{ZEBRA_PRINTER_UUID:06X}" or
                    p[SENSOR_UUID] == f"{SIGNAL_INDICATOR_UUID:06X}"):
                test.rc = TEST_FAILED
                test.add_reason(f"Phase {phase} failed - received packets from an un-registered sensor: {p[SENSOR_UUID]}")
                return test
            payload = p[PAYLOAD][8:]
            if p[SENSOR_UUID] == f"{ERM_SMART_MS_UUID:06X}":
                if find_packet_in_csv(payload) is False:
                    test.rc = TEST_FAILED
                    test.add_reason(f"Phase {phase} failed - couldn't find payload for {ERM_SMART_MS_UUID:06X}")
                    return test
            if p[SENSOR_UUID] == f"{ZEBRA_PRINTER_UUID:06X}":
                if find_packet_in_csv(payload) is False:
                    test.rc = TEST_FAILED
                    test.add_reason(f"Phase {phase} failed - couldn't find payload for {ZEBRA_PRINTER_UUID:06X}")
                    return test
        elif UNIFIED_SENSOR_PKT in p:
            unified_sensor_uuid = (f"{p[UNIFIED_SENSOR_PKT].pkt.sensor_ad_type:02X}"
                                   f"{p[UNIFIED_SENSOR_PKT].pkt.sensor_uuid_msb:02X}"
                                   f"{p[UNIFIED_SENSOR_PKT].pkt.sensor_uuid_lsb:02X}")
            if unified_sensor_uuid != f"{SIGNAL_INDICATOR_UUID:06X}":
                test.rc = TEST_FAILED
                test.add_reason(f"Phase {phase} failed - received packets from an un-registered sensor: {unified_sensor_uuid}")
                return test
            payload = p[PAYLOAD][8:]
            if find_unified_packet_in_csv(payload) is False:
                test.rc = TEST_FAILED
                test.add_reason(f"Phase {phase} failed - couldn't find unified payload for {SIGNAL_INDICATOR_UUID}")
                return test
    return test


EXT_SENSOR_TEST_MAP = {"tag_data_only": test_tag_data_only,
                       "rssi_threshold": test_rssi_threshold,
                       "snsr2_unified": test_snsr2_unified,
                       "snsr0_no_scrmbl": test_snsr0_no_scrmbl,
                       "snsr1_scrmbl": test_snsr1_scrmbl,
                       "snsr0_no_scrmbl_snsr1_scrmbl_snsr2_scrmbl": test_snsr0_no_scrmbl_snsr1_scrmbl_snsr2_scrmbl,
                       "snsr0_no_scrmbl_snsr1_scrmbl_snsr2_unified": test_snsr0_no_scrmbl_snsr1_scrmbl_snsr2_unified}


def run(test):

    test = cert_common.test_prolog(test)
    # check for problems in prolog
    if test.rc == TEST_FAILED:
        test = cert_common.test_epilog(test)
        return test

    dut = cert_config.get_brg_by_target(test, DUT)

    # create csv file for the test
    in_pkts = create_csv_file_in(test)
    create_csv_file_out(test)

    if test.data == DATA_SIMULATION:
        # start generating sensor pkts and send them using data simulator
        pixel_sim_thread = cert_data_sim.GenericSimThread(test=test, duplicates=6, delay=200, pkts=in_pkts)
        pixel_sim_thread.start()
        ble_sim_thread = pixel_sim_thread

    for param in test.params:
        phase_run_print(param.name)
        test = EXT_SENSOR_TEST_MAP[param.value](test, param.name, dut.sensors)
        field_functionality_pass_fail_print(test, param.name)
        test.set_phase_rc(param.name, test.rc)
        test.add_phase_reason(param.name, test.reason)
        if test.rc == TEST_FAILED:
            if test.exit_on_param_failure:
                break  # break the whole for loop and keep the test as failed
        test.reset_result()  # reset result and continue to next param

    # Kill the ble simulator
    if test.data == DATA_SIMULATION:
        ble_sim_thread.stop()

    return cert_common.test_epilog(test, revert_brgs=True, modules=[dut.sensors, dut.datapath])
