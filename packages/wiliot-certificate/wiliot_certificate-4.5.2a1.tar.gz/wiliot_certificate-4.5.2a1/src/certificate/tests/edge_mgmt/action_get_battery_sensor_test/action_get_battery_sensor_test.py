from certificate.cert_prints import *
from certificate.cert_defines import *
from certificate.wlt_types import *
import certificate.cert_mqtt as cert_mqtt
import certificate.cert_common as cert_common
import certificate.cert_config as cert_config


def run(test):
    test = cert_common.test_prolog(test)
    if test.rc == TEST_FAILED:
        return cert_common.test_epilog(test)

    if test.active_brg.board_type not in BATTERY_SENSOR_SUPPORTING_BOARD_TYPES:
        test.rc = TEST_SKIPPED
        return cert_common.test_epilog(test)
    # prolog
    functionality_run_print("action_get_battery_sensor")
    # send action
    cert_config.send_brg_action(test, ag.ACTION_GET_BATTERY_SENSOR)
    # analysis
    test = cert_common.search_action_ack(test, ag.ACTION_GET_BATTERY_SENSOR)
    if test.rc == TEST_FAILED:
        return cert_common.test_epilog(test)

    found_packet = False
    custom_pkts = cert_mqtt.get_all_custom_pkts(test)
    for p in custom_pkts:
        if ("{:02X}{:02X}{:02X}".format(p[UNIFIED_SENSOR_PKT].pkt.sensor_ad_type,
                                        p[UNIFIED_SENSOR_PKT].pkt.sensor_uuid_msb,
                                        p[UNIFIED_SENSOR_PKT].pkt.sensor_uuid_lsb) ==
                f"{ag.SENSOR_SERVICE_ID_BATTERY_SENSOR:06X}"):
            print_pkt(p)
            found_packet = True
            break
    if found_packet is False:
        test.rc = TEST_FAILED
        test.add_reason("Didn't find battery sensor data packet")

    cert_mqtt.generate_log_file(test, "action_get_battery_sensor")
    field_functionality_pass_fail_print(test, "action_get_battery_sensor")

    return cert_common.test_epilog(test)
