# This test meant to show the GW performance when is put in a pkt stress generated from the BLE via the UART
from certificate.cert_prints import *
from certificate.cert_defines import *
from certificate.wlt_types import *
import certificate.cert_common as cert_common
import certificate.cert_mqtt as cert_mqtt
import certificate.cert_data_sim as cert_data_sim
import pandas as pd


# DEFINES
UPLINK_TEST_INDICATOR = get_random_hex_str(6)
NUM_OF_BRGS = 3


# HELPER FUNCTIONS
def duplication_analysis(test, sent_pkts, received_pkts):
    if len(received_pkts) == 0:
        test.rc = TEST_FAILED
        test.reason = "No packets were received!"
        return test

    _sent_pkts = [p.get_pkt()[12:] for p in sent_pkts]
    sent_df = pd.DataFrame(_sent_pkts, columns=[PACKETS])
    received_pkts = [p[PAYLOAD] for p in received_pkts]
    received_df = pd.DataFrame(received_pkts, columns=[PACKETS])

    merged_df = pd.merge(sent_df, received_df, on=PACKETS, how='inner')
    # Count total received packets (including duplicates) and unique packets
    pkts_received_total = len(merged_df)
    merged_df_unique = merged_df.drop_duplicates(subset=[PACKETS])
    pkts_duplicates = pkts_received_total - len(merged_df_unique)

    # Prints
    print(f'Number of packets sent: {len(sent_df)}')
    print(f'Number of packets received in total: {pkts_received_total}, out of them {pkts_duplicates} are duplicates')

    duplicate_percentage = (pkts_duplicates / pkts_received_total) * 100
    print(f'{duplicate_percentage:.2f}% of the received packets are duplicates')

    if duplicate_percentage > 5.0:
        test.rc = TEST_FAILED
        test.reason = f"{duplicate_percentage:.2f}% of the received packets are duplicates"
        return test

    return test


def run(test):
    test = cert_common.test_prolog(test)
    if test.rc == TEST_FAILED:
        return cert_common.test_epilog(test)

    dut_mqttc = test.get_mqttc_by_target(DUT)
    dut_mqttc.flush_pkts()
    pkts = []

    # generate pkts and send them using data simulator
    data_pkts, _ = cert_data_sim.brg_pkt_gen(num_of_pkts_per_brg=10, num_of_brgs=NUM_OF_BRGS,
                                             pkt_type=PIXELS_PKT, indicator=UPLINK_TEST_INDICATOR)

    mgmt_pkts, _ = cert_data_sim.brg_pkt_gen(num_of_pkts_per_brg=10, num_of_brgs=NUM_OF_BRGS,
                                             pkt_type=MGMT_PKT, indicator=UPLINK_TEST_INDICATOR)
    sensor_pkts, _ = cert_data_sim.brg_pkt_gen(num_of_pkts_per_brg=10, num_of_brgs=NUM_OF_BRGS,
                                               pkt_type=SENSOR_PKT, indicator=UPLINK_TEST_INDICATOR)
    si_pkts, _ = cert_data_sim.brg_pkt_gen(num_of_pkts_per_brg=10, num_of_brgs=NUM_OF_BRGS,
                                           pkt_type=SIDE_INFO_SENSOR_PKT, indicator=UPLINK_TEST_INDICATOR)
    pkts = data_pkts + mgmt_pkts + sensor_pkts + si_pkts

    pixel_sim_thread = cert_data_sim.GenericSimThread(test=test, pkts=pkts, send_single_cycle=True)
    pixel_sim_thread.start()

    mqtt_scan_wait(test, 12 + test.dut.upload_wait_time)
    cert_mqtt.dump_pkts(test, log="deduplication_test")
    recieved_pkts = cert_mqtt.get_all_data_pkts(dut_mqttc, indicator=UPLINK_TEST_INDICATOR)
    pixel_sim_thread.stop()

    test = duplication_analysis(test, pkts, recieved_pkts)

    return cert_common.test_epilog(test)
