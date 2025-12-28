
from certificate.cert_prints import *
from certificate.cert_defines import *
from certificate.wlt_types import *
from certificate.ag.wlt_types_ag import OUTPUT_POWER_2_4_MAX
import certificate.cert_common as cert_common
import certificate.cert_utils as cert_utils
import certificate.cert_mqtt as cert_mqtt
import certificate.cert_config as cert_config
import certificate.cert_gw_sim as cert_gw_sim
import math


# DEFINES
STRESS_TEST_INDICATOR = get_random_hex_str(6)

DUPLICATES = 1
ADVA_ASCII_LEN = 12

LOWEST_PPS = 20
ADV_DURATION_LOWEST_PPS = 70
ADV_DURATION_DEFAULT = 30


# HELPER FUNCTIONS

def generate_extended_adv_payloads_list(pkt, duplicates):
    """
    Should always stay synced to how cmd_ble_sim generate additional packets with unique_pkts_count
    """
    data_payload = pkt[12:]
    ext_adv_payload = data_payload * 7
    last_hex = pkt[-8:]
    last_int = int.from_bytes(bytes.fromhex(last_hex), byteorder='little', signed=False)

    pkts_list = []
    for i in range(duplicates):
        value = last_int + i
        # Convert back to 4 bytes in little-endian and then to hex
        new_hex = value.to_bytes(4, byteorder='little', signed=False).hex().upper()

        pkts_list.append(pkt[:12] + ext_adv_payload[:-8] + new_hex)

    return pkts_list


def run(test):
    test = cert_common.test_prolog(test)
    if test.rc == TEST_FAILED:
        return cert_common.test_epilog(test)

    cert_config.gw_action(test, f'{cert_gw_sim.BLE_SIM_INIT} 1', TESTER)

    ppses = [20, 40, 60, 80, 100, 120, 140, 160, 180, 200]
    test_pkts_received = []
    data_pkts_received = []
    results = []
    for pps in ppses:
        phase_run_print(f"PPS = {pps}")
        test.flush_all_mqtt_packets()
        # adv_duration is increased only for lowest pps to increase packets sample for reliable results
        adv_duration = ADV_DURATION_LOWEST_PPS if pps == LOWEST_PPS else ADV_DURATION_DEFAULT
        delay = math.floor(1000 / pps)  # This should be bigger than 2ms
        upload_wait_time = test.dut.upload_wait_time + 15

        # Generate pkts and get ready to advertise
        payload = cert_common.generate_adv_payload(STRESS_TEST_INDICATOR)
        generated_payloads = generate_extended_adv_payloads_list(payload, adv_duration * pps)

        # We provide the tester with the first pkt only. It then advertises in a loop pkts identical
        # to the ones we generated (by incrementing the last bytes).
        gw_action_cmd = (f'{cert_gw_sim.BLE_SIM_EXT_ADV} {payload} {DUPLICATES} '
                         f'{OUTPUT_POWER_2_4_MAX} {delay} {adv_duration * pps}')
        cert_config.gw_action(test, gw_action_cmd, TESTER)
        mqtt_scan_wait(test, adv_duration + upload_wait_time)

        cert_mqtt.dump_pkts(test, log=str(pps))
        phase_pkts_received = cert_mqtt.get_all_aggregated_data_pkts(test.get_mqttc_by_target(DUT), indicator=STRESS_TEST_INDICATOR)
        valid, reason = cert_common.validate_received_packets(phase_pkts_received)
        test.add_phase(cert_utils.Phase(pps))
        if valid is False:
            test.set_phase_rc(str(pps), TEST_FAILED)
            test.add_phase_reason(str(pps), reason)
            utPrint(f"Phase {pps} failed validation: {reason}", "RED")
            continue
        phase_pkts_received = [p[AGGREGATED_PAYLOAD] for p in phase_pkts_received]
        test, received_pps = cert_common.stress_analysis(test, pps, generated_payloads, phase_pkts_received)
        results.extend([pps, received_pps])
        cert_mqtt.generate_log_file(test, str(pps))

        if test.rc == TEST_FAILED and test.exit_on_param_failure:
            break  # break the whole for loop and keep the test as failed
        test.reset_result()  # reset result and continue to next param
        data_pkts_received.extend(cert_mqtt.get_all_data_pkts(test.get_mqttc_by_target(DUT)))
        test_pkts_received.extend(test.get_mqttc_by_target(DUT)._userdata[PKTS].data)
    cert_config.gw_action(test, f'{cert_gw_sim.BLE_SIM_INIT} 0', TESTER)

    # Generate stress test graphs
    if len(data_pkts_received) > 0:
        cert_common.generate_graph_stress_test(test, results, data_pkts_received)
    else:
        utPrint("No data packets received - skipping graph generation", "RED")

    return cert_common.test_epilog(test)
