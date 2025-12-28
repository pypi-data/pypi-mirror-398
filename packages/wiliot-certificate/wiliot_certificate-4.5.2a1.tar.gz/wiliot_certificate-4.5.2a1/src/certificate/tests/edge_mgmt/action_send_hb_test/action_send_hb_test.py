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

    functionality_run_print("action_send_hb")

    # send action
    cert_config.send_brg_action(test, ag.ACTION_SEND_HB)
    # analysis
    test, mgmt_pkts = cert_common.scan_for_mgmt_pkts(test, [eval_pkt(f'Brg2GwHbV{test.active_brg.api_version}')])
    if not mgmt_pkts:
        test.add_reason("Didn't find ACTION HB pkt")
        test.rc = TEST_FAILED
    elif test.active_brg.api_version >= ag.API_VERSION_V13:
        utPrint("Got HB pkt", "GREEN")
        algo_tx_rep_val = []
        for p in mgmt_pkts:
            algo_tx_rep_val.append(p[MGMT_PKT].pkt.algo_tx_rep)
        if test.dut_is_combo() and any(val != 0 for val in algo_tx_rep_val):
            invalid_vals = [val for val in algo_tx_rep_val if val != 0]
            print(f"ERROR: tx_rep_algo yielded invalid value(s) {invalid_vals} instead of '0' for internal brg!")
            test.add_reason("Internal's BRG tx_rep_algo isn't working as expected!")
            test.rc = TEST_FAILED
        elif test.dut_is_bridge() and any((val < 1 or val > 3) for val in algo_tx_rep_val):
            invalid_vals = [val for val in algo_tx_rep_val if val < 1 or val > 3]
            print(f"ERROR: tx_rep_algo yielded invalid value(s) {invalid_vals}!")
            test.add_reason("BRG's tx_rep_algo isn't working as expected!")
            test.rc = TEST_FAILED
        print(f"tx_rep_algo yielded valid value(s) of - {algo_tx_rep_val}")
    else:
        utPrint("Got HB pkt, Skipping tx_rep_algo hb field check - API version < V13", "GREEN")

    cert_mqtt.generate_log_file(test, "action_send_hb")
    field_functionality_pass_fail_print(test, "action_send_hb")

    return cert_common.test_epilog(test)
