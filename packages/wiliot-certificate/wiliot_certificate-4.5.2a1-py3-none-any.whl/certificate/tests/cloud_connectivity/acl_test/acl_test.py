from certificate.cert_prints import *
from certificate.cert_defines import *
from certificate.wlt_types import *
import certificate.cert_mqtt as cert_mqtt
import certificate.cert_common as cert_common
import certificate.cert_config as cert_config
import certificate.cert_data_sim as cert_data_sim
from certificate.ag.wlt_types_ag import *

SCAN_TIMEOUT = 30
NUM_OF_BRGS = 4
# DEFINES
test_indicator = cert_data_sim.PIXEL_SIM_INDICATOR


def run(test):

    test = cert_common.test_prolog(test)
    if test.rc == TEST_FAILED:
        return cert_common.test_epilog(test)

    # Generate management and data packets
    bridge_ids = [cert_common.hex2alias_id_get(get_random_hex_str(12)) for _ in range(NUM_OF_BRGS)]
    pixels_pkts, _ = cert_data_sim.brg_pkt_gen(num_of_pkts_per_brg=20, num_of_brgs=NUM_OF_BRGS, brgs_list=bridge_ids,
                                               pkt_type=PIXELS_PKT, indicator=test_indicator)

    mgmt_pkts, _ = cert_data_sim.brg_pkt_gen(num_of_pkts_per_brg=10, num_of_brgs=NUM_OF_BRGS, brgs_list=bridge_ids,
                                             pkt_type=MGMT_PKT, indicator=test_indicator)
    # Use first 3 bridges for ACL, 4th bridge is not in ACL
    acl_bridge_ids = bridge_ids[:3]
    non_acl_bridge_id = bridge_ids[3]
    pkts = pixels_pkts + mgmt_pkts

    sim_thread = cert_data_sim.GenericSimThread(test=test, pkts=pkts)
    sim_thread.start()

    for param in test.params:
        phase_run_print(f"ACL Test - Mode: {param.value}")
        test.flush_all_mqtt_packets()

        cfg = cert_config.get_default_gw_dict(test)
        cfg[ACL][ACL_BRIDGE_IDS] = acl_bridge_ids
        cfg[ACL][ACL_MODE] = param.value
        test, _ = cert_config.gw_configure(test, cfg=cfg, wait=True)
        print_update_wait(1)

        test.get_mqttc_by_target(DUT).flush_pkts()
        mqtt_scan_wait(test, SCAN_TIMEOUT)
        cert_mqtt.dump_pkts(test, log=param.name)

        # Analyze pass/fail
        # Get all received packets with the test indicator and filter packets by bridge IDs in ACL list
        received_pkts = cert_mqtt.get_unified_data_pkts(test, only_active_brg=False, indicator=test_indicator)
        acl_bridge_pkts = [pkt for pkt in received_pkts if any([id in pkt[PAYLOAD] for id in acl_bridge_ids])]
        non_acl_bridge_pkts = [pkt for pkt in received_pkts if non_acl_bridge_id in pkt[PAYLOAD]]

        # In deny mode - we want to make sure bridges in ACL list are filtered
        if param.value == ACL_DENY:
            if len(non_acl_bridge_pkts) == 0:
                test.rc = TEST_FAILED
                test.add_reason(f"Phase failed! Bridge {non_acl_bridge_id} was not in the deny list "
                                f"and packets were not found from it")
            if len(acl_bridge_pkts) != 0:
                test.rc = TEST_FAILED
                test.add_reason("Phase failed! Received packets from bridges that were on the deny list")

        # In allow mode - we want to make sure only bridges in ACL list are not filtered
        if param.value == ACL_ALLOW:
            if len(non_acl_bridge_pkts) != 0:
                test.rc = TEST_FAILED
                test.add_reason(f"Phase failed! Bridge {non_acl_bridge_id} was not on the allow list "
                                f"and {len(non_acl_bridge_pkts)} packets were found from it")
            # Check that we received packets from all expected bridges
            received_alias_bridge_ids = set([pkt[ALIAS_BRIDGE_ID] for pkt in acl_bridge_pkts])
            if len(received_alias_bridge_ids) != len(acl_bridge_ids):
                test.rc = TEST_FAILED
                test.add_reason("Phase failed! Didn't receive packets from all bridges that were on the allow list")

        # Check that management packets are received from all bridges (ACL doesn't filter mgmt packets)
        all_mgmt_pkts = cert_mqtt.get_all_mgmt_pkts(test.get_mqttc_by_target(DUT), indicator=test_indicator)
        mgmt_alias_bridge_ids = set([pkt[ALIAS_BRIDGE_ID] for pkt in all_mgmt_pkts])

        if len(mgmt_alias_bridge_ids) != NUM_OF_BRGS:
            test.rc = TEST_FAILED
            test.add_reason("Phase failed! Didn't receive management packets from all bridges")

        field_functionality_pass_fail_print(test, "ACL", value=param.value)
        test.set_phase_rc(param.name, test.rc)
        test.add_phase_reason(param.name, test.reason)
        if test.rc == TEST_FAILED and test.exit_on_param_failure:
            break
        else:
            test.reset_result()

    sim_thread.stop()
    return cert_common.test_epilog(test, revert_gws=True, modules=[])
