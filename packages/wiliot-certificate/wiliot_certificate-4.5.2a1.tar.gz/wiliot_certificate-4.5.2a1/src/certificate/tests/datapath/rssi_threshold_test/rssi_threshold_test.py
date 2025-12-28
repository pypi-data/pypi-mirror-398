from certificate.cert_prints import *
from certificate.cert_defines import *
from certificate.wlt_types import *
import certificate.cert_mqtt as cert_mqtt
import certificate.cert_data_sim as cert_data_sim
import certificate.cert_common as cert_common
import certificate.cert_config as cert_config


def rssi_threshold_analysis(test, df, threshold):
    tags_count = len(list(df[TAG_ID].unique()))

    # Filter rows where RSSI is higher than threshold
    low_rssi_df = df[df[RSSI] >= (-1) * threshold]

    # Extract all tag IDs from those filtered rows
    low_rssi_tag_ids = low_rssi_df[TAG_ID].unique()
    failed_tags = len(low_rssi_tag_ids)

    if failed_tags:
        test.rc = TEST_FAILED
        print("Tag IDs with RSSI exceeding", (-1) * threshold, ":", low_rssi_tag_ids)

    if test.rc == TEST_FAILED:
        test.add_reason(f"{failed_tags}/{tags_count} tags rssi violating threshold of {(-1) * threshold}")
        print(test.reason)
    else:
        test.rc = TEST_PASSED
    return test


def run(test):

    fields = [BRG_RSSI_THRESHOLD]
    datapath_module = test.active_brg.datapath

    test = cert_common.test_prolog(test)
    if test.rc == TEST_FAILED:
        return cert_common.test_epilog(test)

    # Configure the BRG with RSSI threshold and check for packets violating the threshold
    for param in test.params:
        functionality_run_print(f"test for RSSI threshold of {param.value}")
        test = cert_config.brg_configure(test, fields=fields, values=[param.value], module=datapath_module)[0]
        test.set_phase_rc(param.name, test.rc)
        test.add_phase_reason(param.name, test.reason)
        if test.rc == TEST_FAILED:
            if test.exit_on_param_failure:
                break  # break the whole for loop and keep the test as failed
            else:
                test.reset_result()  # reset result and continue to next param
                continue
        wait_time_n_print(5, txt="Waiting datapath to clear")

        if test.data == DATA_SIMULATION:
            # start generating pkts and send them using data simulator
            num_of_pixels = 10
            pixel_sim_thread = cert_data_sim.DataSimThread(test=test, num_of_pixels=num_of_pixels, duplicates=3, delay=100, pkt_types=[0])
            pixel_sim_thread.start()
        df = cert_common.data_scan(test, brg_data=(not test.internal_brg), gw_data=test.internal_brg, scan_time=60)
        if test.data == DATA_SIMULATION:
            # stop generating pkts with data simulator and wait a few seconds for full flush
            pixel_sim_thread.stop()
            time.sleep(5)
        test = rssi_threshold_analysis(test, df, param.value)

        # param epilog
        cert_mqtt.generate_log_file(test, param.name)
        field_functionality_pass_fail_print(test, fields[0], value=param.name)
        test.set_phase_rc(param.name, test.rc)
        test.add_phase_reason(param.name, test.reason)
        if test.rc == TEST_FAILED:
            if test.exit_on_param_failure:
                break  # break the whole for loop and keep the test as failed
        test.reset_result()  # reset result and continue to next param

    return cert_common.test_epilog(test, revert_brgs=True, revert_gws=test.internal_brg, modules=[datapath_module])
