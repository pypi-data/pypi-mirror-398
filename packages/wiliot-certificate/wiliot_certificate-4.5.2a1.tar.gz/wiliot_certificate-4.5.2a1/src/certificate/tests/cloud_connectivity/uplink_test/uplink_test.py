# This test meant to show the GW performance when is put in a pkt stress generated from the BLE via the UART
from certificate.cert_prints import *
from certificate.cert_defines import *
from certificate.wlt_types import *
from common.api_if.api_validation import api_validation
import certificate.cert_common as cert_common
import certificate.cert_mqtt as cert_mqtt
import certificate.cert_data_sim as cert_data_sim
import pandas as pd


# DEFINES

API_VALIDATION = "API Validation"
UPLINK_TEST_INDICATOR = get_random_hex_str(6)
NUM_OF_BRGS = 3


# HELPER FUNCTIONS
def uplink_analysis(test, sent_pkts, received_pkts, pkt_type):
    if len(received_pkts) == 0:
        test.set_phase_rc(pkt_type, TEST_FAILED)
        test.add_phase_reason(pkt_type, "No packets were received!")
        return test

    # Verify packets were received from NUM_OF_BRGS bridges
    received_brgs = set([p[ALIAS_BRIDGE_ID] for p in received_pkts])
    if len(received_brgs) != NUM_OF_BRGS:
        test.set_phase_rc(pkt_type, TEST_FAILED)
        test.add_phase_reason(pkt_type, f"Received packets from {len(received_brgs)} bridges instead of {NUM_OF_BRGS} bridges!")
        utPrint(f"Received packets from {received_brgs} bridges instead of {NUM_OF_BRGS} bridges!", "RED")
        return test

    _sent_pkts = [p.get_pkt()[12:] for p in sent_pkts]
    sent_df = pd.DataFrame(_sent_pkts, columns=[PACKETS])
    received_pkts = [p[PAYLOAD] for p in received_pkts]
    received_df = pd.DataFrame(received_pkts, columns=[PACKETS])

    merged_df = pd.merge(sent_df, received_df, on=PACKETS, how='inner')
    # Drop duplicates to count unique packets that were received
    merged_df_unique = merged_df.drop_duplicates(subset=[PACKETS])
    pkts_sent_count = len(sent_df)
    pkts_received_count = len(merged_df_unique)

    # Prints
    print(f'Number of {pkt_type} packets sent: {pkts_sent_count}')
    print(f'Number of {pkt_type} packets received: {pkts_received_count}')

    # Check for division by zero
    if pkts_sent_count == 0:
        test.set_phase_rc(pkt_type, TEST_FAILED)
        test.add_phase_reason(pkt_type, "No packets were sent!")
        return test

    percentage_received = round(pkts_received_count * 100 / pkts_sent_count)

    # PASS/FAIL logic
    if percentage_received < 80:
        test.set_phase_rc(pkt_type, TEST_FAILED)
        test.add_phase_reason(pkt_type, f'{percentage_received}% of {pkt_type} packets received')
    else:
        test.set_phase_rc(pkt_type, TEST_PASSED)
        test.add_phase_reason(pkt_type, f'{percentage_received}% of {pkt_type} packets received')

    return test


def geolocation(test, all_messages_in_test):
    phase_run_print(GEOLOCATION)
    locations_list = []
    locations_df = pd.DataFrame()
    for message in all_messages_in_test:
        message = message.body_ex
        timestamp = message[TIMESTAMP]
        if LOCATION in message.keys():
            loc = message[LOCATION]
            loc.update({TIMESTAMP: timestamp})
            locations_list.append(loc)
    num_unique_locs = 0
    if test.get_phase_rc(GEOLOCATION) == TEST_SKIPPED:
        pass
    elif len(locations_list) == 0:
        test.set_phase_rc(GEOLOCATION, TEST_FAILED)
        test.add_phase_reason(GEOLOCATION, 'No coordinates were uploaded')
    else:
        test.set_phase_rc(GEOLOCATION, TEST_PASSED)
        locations_df = pd.DataFrame(locations_list)
        num_unique_locs = locations_df[['lat', 'lng']].drop_duplicates().shape[0]
        print(f'Number of unique locations received: {num_unique_locs}')

    # Export all stage data
    csv_path = os.path.join(ARTIFACTS_DIR, test.dir, f'uplink_{GEOLOCATION}.csv')
    locations_df.to_csv(csv_path)
    print(f'\nLocations data saved - {csv_path}')
    field_functionality_pass_fail_print(test.get_phase_by_name(GEOLOCATION), GEOLOCATION)

    return test


def run(test):
    test = cert_common.test_prolog(test)
    if test.rc == TEST_FAILED:
        return cert_common.test_epilog(test)

    dut_mqttc = test.get_mqttc_by_target(DUT)
    all_data_messages_in_test = []
    all_data_pkts = []
    for param in test.params:
        phase_run_print(f"Tested packet type = {param}")
        dut_mqttc.flush_pkts()
        # generate pkts and send them using data simulator
        pkts = []
        bridge_ids = []
        if param.value == PIXELS_PKT:
            pkts, _ = cert_data_sim.brg_pkt_gen(num_of_pkts_per_brg=10, num_of_brgs=NUM_OF_BRGS,
                                                pkt_type=PIXELS_PKT, indicator=UPLINK_TEST_INDICATOR)
        elif param.value == MGMT_PKT:
            pkts, _ = cert_data_sim.brg_pkt_gen(num_of_pkts_per_brg=10, num_of_brgs=NUM_OF_BRGS,
                                                pkt_type=MGMT_PKT, indicator=UPLINK_TEST_INDICATOR)
        # Generate both sensor data and side info sensor packets
        elif param.value == SENSOR_PKT:
            sensor_pkts, bridge_ids = cert_data_sim.brg_pkt_gen(num_of_pkts_per_brg=10, num_of_brgs=NUM_OF_BRGS,
                                                                pkt_type=SENSOR_PKT, indicator=UPLINK_TEST_INDICATOR)
            si_pkts, _ = cert_data_sim.brg_pkt_gen(num_of_pkts_per_brg=10, num_of_brgs=NUM_OF_BRGS,
                                                   brgs_list=bridge_ids, pkt_type=SIDE_INFO_SENSOR_PKT, indicator=UPLINK_TEST_INDICATOR)
            pkts = sensor_pkts + si_pkts
        else:
            test.rc = TEST_FAILED
            test.reason = "Invalid test parameter!"
            break

        pixel_sim_thread = cert_data_sim.GenericSimThread(test=test, pkts=pkts, send_single_cycle=True)
        pixel_sim_thread.start()

        mqtt_scan_wait(test, 10 + test.dut.upload_wait_time)
        cert_mqtt.dump_pkts(test, log=param.name)
        pixel_sim_thread.stop()
        all_data_messages_in_test.extend(dut_mqttc._userdata[PKTS].data)
        all_data_pkts.extend(cert_mqtt.get_all_data_pkts(dut_mqttc))
        recieved_pkts = cert_mqtt.get_all_data_pkts(dut_mqttc, indicator=UPLINK_TEST_INDICATOR)
        valid, reason = cert_common.validate_received_packets(recieved_pkts)
        if valid is False:
            test.set_phase_rc(param.name, TEST_FAILED)
            test.add_phase_reason(param.name, reason)
            utPrint(f"Phase {param.name} failed validation: {reason}", "RED")
            continue

        test = uplink_analysis(test, pkts, recieved_pkts, param.name)

        cert_mqtt.generate_log_file(test, param.name)
        field_functionality_pass_fail_print(test.get_phase_by_name(param.name), 'pkt_type', value=param.name)
        if test.get_phase_by_name(param.name).rc == TEST_FAILED:
            if test.exit_on_param_failure:
                break  # break the whole for loop and keep the test as failed
        test.reset_result()  # reset result and continue to next param

    # Other Validations
    # Api Validation
    test = api_validation(test)
    test = cert_common.wiliot_pkts_validation(test, all_data_messages_in_test, all_data_pkts)

    # Geolocation phase
    if len(all_data_messages_in_test) == 0:
        test.set_phase_rc(param.name, TEST_FAILED)
        test.add_phase_reason(param.name, "No messages were received!")
        return cert_common.test_epilog(test)
    test = geolocation(test, all_data_messages_in_test)

    return cert_common.test_epilog(test)
