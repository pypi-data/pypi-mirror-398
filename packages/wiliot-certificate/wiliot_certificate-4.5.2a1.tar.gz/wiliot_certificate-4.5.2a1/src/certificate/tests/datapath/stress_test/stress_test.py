from certificate.cert_prints import *
from certificate.cert_defines import *
from certificate.wlt_types import *
import certificate.cert_mqtt as cert_mqtt
import certificate.cert_common as cert_common
import certificate.cert_config as cert_config
import certificate.cert_data_sim as cert_data_sim
from certificate.cert_gw_sim import DEDUPLICATION_PKTS
import statistics
import time


def metric_checking_HB(test, check, mgmt_type_list, tx_queue_expected, pacer_increment_expected):
    if not mgmt_type_list:
        if check:
            test.add_reason("\nDidn't find HB pkt, therefore skip all checks\n")
            print("Didn't find HB pkt, therefore will not check tx_queue and pacer increment")
        else:
            test.rc = TEST_PASSED  # skip the rc result if we didn't find HB pkt
            print("Didn't find HB pkt, therefore will not check tx_queue and pacer increment")
    else:
        # check tx queue
        watermarks = [pkt.tx_queue_watermark for pkt in mgmt_type_list]
        half_index = len(watermarks) // 2
        tx_queue_HB = statistics.mean(watermarks[half_index:])
        if not (tx_queue_expected[0] <= tx_queue_HB <= tx_queue_expected[1]):
            print(f"\ntx_queue: {tx_queue_HB} expected: {tx_queue_expected},")
        else:
            print(f"\ntx_queue from HB: {tx_queue_HB}\n")

        # check pacer increment
        pacer_increment_HB = [pkt.effective_pacer_increment for pkt in mgmt_type_list]
        average_pacer_increment_HB = statistics.mean(pacer_increment_HB)
        if not (pacer_increment_expected[0] <= average_pacer_increment_HB <= pacer_increment_expected[1]):
            print(f"\npacer_increment value is wrong\nexpected: {pacer_increment_expected}\ngot: {average_pacer_increment_HB}")
            if check:
                test.rc = TEST_FAILED
                test.add_reason(f"pacer_increment: {average_pacer_increment_HB} expected: {pacer_increment_expected}")
        else:
            print(f"\naverage pacer_increment from HB: {average_pacer_increment_HB}\n")
            if check:
                test.add_reason(f"pacer_increment: {average_pacer_increment_HB}")
    return test


def metric_checking_df(test, check, pacer_interval, df, repetition_value_expected, brg_latency_expected, num_of_pixels_expected):
    if df.empty:
        print("Df is empty, therefore will not check repetitions, brg latency and num of tags")
        test.rc = TEST_FAILED
        test.add_reason("Df is empty, therefore skip all checks")
    else:
        print(f"result of pacer interval: {pacer_interval}\n")
        # check repetition value
        payload_counts_per_tag = df.groupby(TAG_ID)[PAYLOAD].value_counts()
        average_payload_count = round(payload_counts_per_tag.mean(), 2)
        if not repetition_value_expected[0] <= average_payload_count <= repetition_value_expected[1]:
            print(f"Repetition value is wrong! \nexpected:{repetition_value_expected}\ngot: {average_payload_count}")
            if check:
                test.rc = TEST_FAILED
                test.add_reason(f"Repetition:{average_payload_count}, expected: {repetition_value_expected}")
        else:
            print(f"Repetition value is correct! got: {average_payload_count}")
            if check:
                test.add_reason(f"Repetition value: {average_payload_count}")

        # check num of tags, with tolerance of 5%
        num_of_tags = len(df[TAG_ID].unique())
        if not num_of_pixels_expected * 0.95 <= num_of_tags <= num_of_pixels_expected * 1.05:
            print(f"\nnum of tags is not as expected\nexpected: {num_of_pixels_expected}, got: {num_of_tags}")
            if check:
                test.add_reason(f"num of tags:  {num_of_tags}")
        else:
            print(f"\nnum of tags from df: {num_of_tags}\n")

        # check brg_latency
        brg_latency_avg = round(df[BRG_LATENCY].mean(), 2)
        if not (brg_latency_expected[0] <= brg_latency_avg <= brg_latency_expected[1]):
            print(f"Average brg_latency: {brg_latency_avg} , expected: {brg_latency_expected}")
        else:
            print(f"Average brg_latency: {brg_latency_avg}")
    return test


def combination_func(test, param, datapath_module, pacer_interval, num_of_sim_tags, repetition_value_expected,
                     tx_queue_expected, pacer_increment_expected, brg_latency_expected):
    test = cert_config.brg_configure(test, fields=[BRG_PACER_INTERVAL], values=[pacer_interval], module=datapath_module)[0]
    if test.rc == TEST_FAILED:
        print("Failed to configure pacer interval")
        test.add_reason("Failed to configure pacer interval")
        return test
    if param.name == "rep1_adaptive_pacer":
        print(f"run phase: {param.name}")
        df = cert_common.data_scan(test, scan_time=30, brg_data=(not test.internal_brg), gw_data=test.internal_brg)
        cert_common.display_data(df, tbc=True, name_prefix=f"stress_{pacer_interval}_", dir=test.dir)
        test, hbs = cert_common.scan_for_mgmt_pkts(test, [eval_pkt(f'Brg2GwHbV{test.active_brg.api_version}')])
        hbs = [p[MGMT_PKT].pkt for p in hbs]

        check = True
        test = metric_checking_df(test, check, pacer_interval, df, repetition_value_expected, brg_latency_expected, num_of_sim_tags)
        if not test.rc == TEST_FAILED:
            test = metric_checking_HB(test, check, hbs, tx_queue_expected, pacer_increment_expected)
            return test
        else:
            # in case it failed because the repetition value. the reason has been added in the metric_checking_df function
            return test

    time.sleep(30)
    # first df
    df = cert_common.data_scan(test, scan_time=30, brg_data=(not test.internal_brg), gw_data=test.internal_brg)
    cert_common.display_data(df, tbc=True, name_prefix=f"stress_{pacer_interval}_", dir=test.dir)
    test, hbs = cert_common.scan_for_mgmt_pkts(test, [eval_pkt(f'Brg2GwHbV{test.active_brg.api_version}')])
    hbs = [p[MGMT_PKT].pkt for p in hbs]
    print("result of first df\n")
    check = False
    test = metric_checking_df(test, check, pacer_interval, df, repetition_value_expected, brg_latency_expected, num_of_sim_tags)
    test = metric_checking_HB(test, check, hbs, tx_queue_expected, pacer_increment_expected)
    time.sleep(30)
    # second df
    df = cert_common.data_scan(test, scan_time=60, brg_data=(not test.internal_brg), gw_data=test.internal_brg)
    cert_common.display_data(df, tbc=True, name_prefix=f"stress_{pacer_interval}_", dir=test.dir)
    test, hbs = cert_common.scan_for_mgmt_pkts(test, [eval_pkt(f'Brg2GwHbV{test.active_brg.api_version}')])
    hbs = [p[MGMT_PKT].pkt for p in hbs]
    print("result of second df\n")
    check = True
    test = metric_checking_df(test, check, pacer_interval, df, repetition_value_expected, brg_latency_expected, num_of_sim_tags)
    if param.name != "rep1":
        check = False
    test = metric_checking_HB(test, check, hbs, tx_queue_expected, pacer_increment_expected)
    return test


def rep3(test, param, datapath_module, num_of_sim_tags):
    # step 1 - config pacer interval=15 , then check repetition value = 3, tx_queue ~ 0, pacer increment ~ 0, brg latency ~ 0
    pacer_interval = 22
    test = combination_func(test, param, datapath_module, pacer_interval=pacer_interval, num_of_sim_tags=num_of_sim_tags,
                            repetition_value_expected=[2, 3], tx_queue_expected=[20, 40],
                            pacer_increment_expected=[0, 2], brg_latency_expected=[0, 10])
    time.sleep(5)
    return test


def rep2(test, param, datapath_module, num_of_sim_tags):
    # step 2 - config pacer interval 9, then check repetition value = 2, tx_queue = 20-40, pacer increment = 0, brg latency = 0-200
    pacer_interval = 12
    test = combination_func(test, param, datapath_module, pacer_interval=pacer_interval, num_of_sim_tags=num_of_sim_tags,
                            repetition_value_expected=[1.5, 2.5], tx_queue_expected=[20, 40],
                            pacer_increment_expected=[0, 2], brg_latency_expected=[10, 200])
    time.sleep(5)
    return test


def rep1(test, param, datapath_module, num_of_sim_tags):
    # "step 3 - config pacer interval 6 , then check repetition value = 1, tx_queue 40-60, pacer increment ~ 0, brg latency 200-300
    pacer_interval = 7
    test = combination_func(test, param, datapath_module, pacer_interval=pacer_interval, num_of_sim_tags=num_of_sim_tags,
                            repetition_value_expected=[1, 2], tx_queue_expected=[20, 40],
                            pacer_increment_expected=[0, 25], brg_latency_expected=[200, 300])
    time.sleep(5)
    return test


def rep1_adaptive_pacer(test, param, datapath_module, num_of_sim_tags):
    # step 4 - config pacer interval 1, then check repetition value = 1, tx_queue > 60, pacer increment = 3, brg latency > 300
    pacer_interval = 1

    test = combination_func(test, param, datapath_module, pacer_interval=pacer_interval, num_of_sim_tags=num_of_sim_tags,
                            repetition_value_expected=[1, 2], tx_queue_expected=[20, 40],
                            pacer_increment_expected=[2, 50], brg_latency_expected=[300, 1000])
    time.sleep(5)
    return test


def run(test):
    # Test prolog
    datapath_module = test.active_brg.datapath
    test = cert_common.test_prolog(test)
    if test.rc == TEST_FAILED:
        return cert_common.test_epilog(test, revert_brgs=True, modules=[datapath_module])
    # config GW deduplication pkts = 0
    print("Configuring GW with !deduplication_pkts 0")
    cert_config.gw_action(test, f"{DEDUPLICATION_PKTS} 0")
    STRESS_TEST_MAP = {"rep3": rep3, "rep2": rep2, "rep1": rep1}
    num_of_pixels = 300
    pixel_sim_thread = cert_data_sim.DataSimThread(test=test,
                                                   num_of_pixels=num_of_pixels,
                                                   duplicates=1,
                                                   delay=0,
                                                   pkt_types=[0],
                                                   pixels_type=GEN2)
    pixel_sim_thread.start()
    time.sleep(30)
    for param in test.params:
        functionality_run_print(param.name)
        test = STRESS_TEST_MAP[param.value](test, param, datapath_module, num_of_pixels)
        cert_mqtt.generate_log_file(test, param.name)
        field_functionality_pass_fail_print(test, param.name)
        test.set_phase_rc(param.name, test.rc)
        test.add_phase_reason(param.name, test.reason)
        if test.rc == TEST_FAILED:
            if test.exit_on_param_failure:
                break  # break the whole for loop and keep the test as failed
        test.reset_result()  # reset result and continue to next param

    pixel_sim_thread.stop()
    # Re-enable unified packets deduplication
    cert_config.gw_action(test, f"{DEDUPLICATION_PKTS} 1")

    # wait a few seconds to ensure bridge relaxed before next test
    wait_time_n_print(60)

    return cert_common.test_epilog(test, revert_brgs=True, modules=[datapath_module])
