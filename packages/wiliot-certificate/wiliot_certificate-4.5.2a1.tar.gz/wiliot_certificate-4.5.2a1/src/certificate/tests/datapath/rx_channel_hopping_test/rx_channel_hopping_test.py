from certificate.cert_prints import *
from certificate.cert_defines import *
from certificate.wlt_types import *
import certificate.cert_mqtt as cert_mqtt
import certificate.cert_data_sim as cert_data_sim
import certificate.cert_common as cert_common
import certificate.cert_config as cert_config

SCAN_TIME_PER_CH = 60   # in seconds


def run(test):

    fields = [BRG_RX_CHANNEL, BRG_PACER_INTERVAL]

    datapath_module = test.active_brg.datapath
    pacer_interval = 1

    test = cert_common.test_prolog(test)
    if test.rc == TEST_FAILED:
        return cert_common.test_epilog(test)

    if not (test.data == DATA_SIMULATION):
        test.rc = TEST_FAILED
        warning_txt = "WARNING: This test should be ran with data simulator!"
        utPrint(warning_txt, "RED")
        test.add_reason(warning_txt)
        return cert_common.test_epilog(test)

    test = cert_config.brg_configure(test, fields=fields, values=[ag.RX_CHANNEL_HOPPING_37_10, pacer_interval], module=datapath_module)[0]

    num_of_pixels = 5
    # For bridge with cloud connectivity, each ble5 sent as is and not split to 2 packets
    split_pkt_mult = 1 if test.dut_is_combo() else 2

    # Simulating tag packets on channel 37
    utPrint("Scanning packets on channel 37", "BLUE")
    pixel_sim_thread_ch_37 = cert_data_sim.DataSimThread(test=test, num_of_pixels=num_of_pixels, duplicates=1,
                                                         delay=0, pkt_types=[0])
    pixel_sim_thread_ch_37.start()
    df_37 = cert_common.data_scan(test, scan_time=SCAN_TIME_PER_CH, brg_data=(not test.internal_brg), gw_data=test.internal_brg)
    pixel_sim_thread_ch_37.stop()
    time.sleep(5)

    # Simulating packets on ch 10
    utPrint("Scanning packets on channel 10", "BLUE")
    pixel_sim_thread_ch_10 = cert_data_sim.DataSimThread(test=test, num_of_pixels=num_of_pixels, duplicates=1,
                                                         delay=0, pkt_types=[2],
                                                         pixels_type=GEN3_EXTENDED)
    pixel_sim_thread_ch_10.start()
    df_10 = cert_common.data_scan(test, scan_time=SCAN_TIME_PER_CH, brg_data=(not test.internal_brg), gw_data=test.internal_brg)
    pixel_sim_thread_ch_10.stop()

    cert_mqtt.dump_pkts(test, log=test.module_name)

    # Analyze packet count per channel
    df_37_counts = df_37['tag_id'].value_counts().rename('pkt_count').reset_index().rename(columns={'index': 'tag_id'})
    df_10_counts = df_10['tag_id'].value_counts().rename('pkt_count').reset_index().rename(columns={'index': 'tag_id'})
    print(df_37_counts)
    print(f"Channel 37 avg pkt count: {df_37_counts['pkt_count'].mean()}")
    print(df_10_counts)
    print(f"Channel 10 avg pkt count: {df_10_counts['pkt_count'].mean()}")

    if not (0.9 * df_10_counts['pkt_count'].mean() <=
            split_pkt_mult * df_37_counts['pkt_count'].mean() <=
            1.1 * df_10_counts['pkt_count'].mean()):
        print("Packet count on both channels doesn't match!")
        test.rc = TEST_FAILED
        test.add_reason("Packet count on both channels doesn't match!")
    else:
        utPrint("Packet count match!")

    # param epilog
    cert_mqtt.generate_log_file(test, test.module_name)
    field_functionality_pass_fail_print(test, fields[0], value=test.module_name)

    return cert_common.test_epilog(test, revert_brgs=True, modules=[datapath_module])
