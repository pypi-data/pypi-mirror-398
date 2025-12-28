from certificate.cert_prints import *
from certificate.cert_defines import *
from certificate.wlt_types import *
import certificate.cert_mqtt as cert_mqtt
import certificate.cert_common as cert_common

BRG_PER_MSGS_SCAN_TIMEOUT = 65


def scan_for_brg_periodic_msgs(test, timeout=BRG_PER_MSGS_SCAN_TIMEOUT, only_hb=False):
    # In case we want to look for HB pkts only - set all modules to be True --> as if there are alredy found
    found = {HB: False, MODULE_IF: False}
    if only_hb is True:
        for pkt_type in found:
            if pkt_type != HB:
                found[pkt_type] = True
    else:  # flush pkts if only_hb=False
        test.get_mqttc_by_target(DUT).flush_pkts()

    start_time = datetime.datetime.now()
    # Search for packets
    while not all(found.values()):
        mgmt_types = [eval_pkt(f'Brg2GwHbV{test.active_brg.api_version}')]
        hb_pkts = cert_mqtt.get_brg2gw_mgmt_pkts(
            test.get_mqttc_by_target(DUT),
            test.active_brg,
            mgmt_types=mgmt_types,
        )
        if hb_pkts and not found[HB]:
            found[HB] = True
            print(f"Got HB packet after {(datetime.datetime.now() - start_time).seconds} sec!")
        mgmt_types = [eval_pkt(f'ModuleIfV{test.active_brg.api_version}')]
        module_if_pkts = cert_mqtt.get_brg2gw_mgmt_pkts(
            test.get_mqttc_by_target(DUT),
            test.active_brg,
            mgmt_types=mgmt_types,
        )
        if module_if_pkts and not found[MODULE_IF]:
            found[MODULE_IF] = True
            print(f"Got interface module packet after {(datetime.datetime.now() - start_time).seconds} sec!")
        print_update_wait()
        if (datetime.datetime.now() - start_time).seconds > timeout:
            test.rc = TEST_FAILED
            err_print = f"{'HB' if not found[HB] else ''} {'MODULE_IF' if not found[MODULE_IF] else ''}"
            test.add_reason(f"Didn't receive {err_print} pkt after {timeout} seconds!")
            break
    return test


def run(test):

    test = cert_common.test_prolog(test)
    if test.rc == TEST_FAILED:
        return cert_common.test_epilog(test)

    test = scan_for_brg_periodic_msgs(test)
    cert_mqtt.generate_log_file(test, "periodic_msgs")

    return cert_common.test_epilog(test)
