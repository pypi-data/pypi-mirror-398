from certificate.cert_prints import *
from certificate.cert_defines import *
from certificate.wlt_types import *
import certificate.cert_mqtt as cert_mqtt
import certificate.cert_common as cert_common
import certificate.cert_config as cert_config
import random


def run(test):
    test = cert_common.test_prolog(test)
    if test.rc == TEST_FAILED:
        return cert_common.test_epilog(test)

    functionality_run_print("action_gw_hb")

    # Create randomized 13 bytes hex to send as the gw
    randomized_gw = ''.join(f'{b:02X}' for b in bytes([random.randint(0, 255) for _ in range(13)]))
    randomized_gw = hex_str2int(randomized_gw)
    # send action
    cert_config.send_brg_action(test, ag.ACTION_GW_HB, gw_id=randomized_gw)
    # analysis
    gw_hb_pkt = eval_pkt(f'ActionGwHbV{test.active_brg.api_version}')
    test, mgmt_pkts = cert_common.scan_for_mgmt_pkts(test, [gw_hb_pkt])
    if not mgmt_pkts:
        test.add_reason("Didn't find ACTION GW HB ACK pkts")
        test.rc = TEST_FAILED
    else:
        for p in mgmt_pkts:
            if p[MGMT_PKT].pkt.rssi == 0 or randomized_gw != p[MGMT_PKT].pkt.gw_id:
                if p[MGMT_PKT].pkt.rssi == 0:
                    print("ERROR: PKT RSSI is zero!")
                    test.add_reason("RSSI is zero on the ACTION GW HB ACK pkt")
                else:
                    print(f"ERROR: GW ID does not match!\nGW_ID: {p[MGMT_PKT].pkt.gw_id}\nrandomized_gw: {randomized_gw}")
                    test.add_reason("GW ID not found on the ACTION GW HB ACK pkt")
                test.rc = TEST_FAILED

    cert_mqtt.generate_log_file(test, "action_gw_hb")
    field_functionality_pass_fail_print(test, "action_gw_hb")

    return cert_common.test_epilog(test)
