from certificate.cert_prints import *
from certificate.cert_defines import *
from certificate.wlt_types import *
import certificate.cert_mqtt as cert_mqtt
import certificate.cert_common as cert_common
import certificate.cert_config as cert_config
import certificate.cert_data_sim as cert_data_sim
from certificate.ag.wlt_types_ag import *
import certificate.cert_gw_sim as cert_gw_sim


# DEFINES
DUPLICATES = 5
DELAY = 20
test_indicator = cert_data_sim.PIXEL_SIM_INDICATOR


def generate_expected_pkts(acl_bridge_ids, non_acl_bridge_id, pixels_pkts, mgmt_pkts):
    expected_pkts_allow, expected_pkts_deny = [], []
    # This payload is hardcoded in !ble_sim_ext_adv when adding extra data packets after mgmt packets
    extra_data_payload = "1E16C6FC000039019F8BB88B5EE6CB0F5760B70AA55C87A494776400000000" * 5

    for pkt in pixels_pkts:
        brg_id = cert_common.change_endianness(pkt.adva)
        (expected_pkts_allow if brg_id in acl_bridge_ids else expected_pkts_deny).append(brg_id + pkt.payload * 7)
    for pkt in mgmt_pkts:
        brg_id = cert_common.change_endianness(pkt.adva)
        if brg_id in acl_bridge_ids:
            expected_pkts_allow.append(brg_id + pkt.payload * 2 + extra_data_payload)
            expected_pkts_deny.append(brg_id + pkt.payload * 2)
        elif brg_id == non_acl_bridge_id:
            expected_pkts_allow.append(brg_id + pkt.payload * 2)
            expected_pkts_deny.append(brg_id + pkt.payload * 2 + extra_data_payload)
    return expected_pkts_allow, expected_pkts_deny


def run(test):

    test = cert_common.test_prolog(test)
    if test.rc == TEST_FAILED:
        return cert_common.test_epilog(test)

    cert_config.gw_action(test, f'{cert_gw_sim.BLE_SIM_INIT} 1', TESTER)

    # Generate management and data packets
    pixels_pkts, bridge_ids = cert_data_sim.brg_pkt_gen(num_of_pkts_per_brg=100, num_of_brgs=4,
                                                        pkt_type=PIXELS_PKT, indicator=test_indicator)
    mgmt_pkts, _ = cert_data_sim.brg_pkt_gen(num_of_pkts_per_brg=100, num_of_brgs=4, brgs_list=bridge_ids,
                                             pkt_type=MGMT_PKT, indicator=test_indicator)

    # Use first 3 bridges for ACL, 4th bridge is not in ACL
    acl_bridge_ids = bridge_ids[:3]
    non_acl_bridge_id = bridge_ids[3]

    expected_pkts_allow, expected_pkts_deny = generate_expected_pkts(acl_bridge_ids, non_acl_bridge_id, pixels_pkts, mgmt_pkts)

    for param in test.params:
        phase_run_print(f"ACL Extended Advertising Test - Mode: {param.value}")

        cfg = cert_config.get_default_gw_dict(test)
        cfg[ACL][ACL_BRIDGE_IDS] = acl_bridge_ids
        cfg[ACL][ACL_MODE] = param.value
        test, ret = cert_config.gw_configure(test, cfg=cfg, wait=True)
        print_update_wait(1)

        test.get_mqttc_by_target(DUT).flush_pkts()

        # We provide the tester with the first pkt only. It concatenates the packets to an aggregated packet.
        for pkt in mgmt_pkts:
            # Here the aggregated packet is 2 mgmt pkts and 5 hardcoded data pkts
            cert_config.gw_action(test, f'{cert_gw_sim.BLE_SIM_EXT_ADV} {pkt.get_pkt()} {DUPLICATES} '
                                        f'{OUTPUT_POWER_2_4_MAX} {DELAY} {1} {1}', TESTER)
            print_update_wait(0.1)
        for pkt in pixels_pkts:
            cert_config.gw_action(test, f'{cert_gw_sim.BLE_SIM_EXT_ADV} {pkt.get_pkt()} {DUPLICATES} '
                                        f'{OUTPUT_POWER_2_4_MAX} {DELAY}', TESTER)
            print_update_wait(0.1)
        print_update_wait(1)

        cert_mqtt.dump_pkts(test, log=param.name)

        # Analyze pass/fail
        # Get all received aggregated packets with the test indicator
        received_pkts = cert_mqtt.get_all_aggregated_data_pkts(test.get_mqttc_by_target(DUT), indicator=test_indicator)

        # Validate that received packets match expected packets
        expected_pkts = set(expected_pkts_deny if param.value == ACL_DENY else expected_pkts_allow)
        for p in received_pkts:
            pkt = p[ALIAS_BRIDGE_ID] + p[AGGREGATED_PAYLOAD]
            if pkt not in expected_pkts:
                test.rc = TEST_FAILED
                test.add_reason(f"Phase failed! Received unexpected packet from brg {p[ALIAS_BRIDGE_ID]} in {param.value} mode")
                break

        # Filter packets by bridge IDs in ACL list
        received_data_pkts = [pkt for pkt in received_pkts if MGMT_PKT not in pkt]
        acl_bridge_pkts = [pkt for pkt in received_data_pkts if pkt[ALIAS_BRIDGE_ID] in acl_bridge_ids]
        non_acl_bridge_pkts = [pkt for pkt in received_data_pkts if pkt[ALIAS_BRIDGE_ID] == non_acl_bridge_id]

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
            received_bridge_ids = set([pkt[ALIAS_BRIDGE_ID] for pkt in acl_bridge_pkts])
            if received_bridge_ids != set(acl_bridge_ids):
                test.rc = TEST_FAILED
                test.add_reason("Phase failed! Didn't receive packets from all bridges that were on the allow list")

        # Check that management packets are received from all bridges (ACL doesn't filter mgmt packets)
        all_mgmt_pkts = cert_mqtt.get_all_mgmt_pkts(test.get_mqttc_by_target(DUT), indicator=test_indicator)
        mgmt_bridge_ids = set([pkt[ALIAS_BRIDGE_ID] for pkt in all_mgmt_pkts])
        if not set(bridge_ids).issubset(mgmt_bridge_ids):
            test.rc = TEST_FAILED
            missing_bridges = set(bridge_ids) - mgmt_bridge_ids
            test.add_reason(f"Phase failed! Expected management packets from all bridges, "
                            f"whether they are on the ACL or not, but missing from BRG {missing_bridges}")

        field_functionality_pass_fail_print(test, "ACL", value=param.value)
        test.set_phase_rc(param.name, test.rc)
        test.add_phase_reason(param.name, test.reason)
        if test.rc == TEST_FAILED and test.exit_on_param_failure:
            break
        else:
            test.reset_result()

    cert_config.gw_action(test, f'{cert_gw_sim.BLE_SIM_INIT} 0', TESTER)
    return cert_common.test_epilog(test, revert_gws=True)
