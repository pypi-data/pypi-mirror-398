
from certificate.cert_prints import *
from certificate.cert_defines import *
from certificate.wlt_types import *
import certificate.cert_mqtt as cert_mqtt
import certificate.cert_common as cert_common
import certificate.cert_config as cert_config
import certificate.cert_data_sim as cert_data_sim
import time


# input address value and return the TBC value in s
def address2tbc(address):
    if address == 0:
        return 0
    result = 64 / (256 - address)
    return result


def cal_scan_time(test, delay, pacer_interval):
    # Calculate the scan time to ensure enough packets are captured in data scan
    # define the num of packet that you want to get
    num_of_cycles = 5
    delay = delay / 1000
    if delay < pacer_interval:
        scan_time = (pacer_interval * num_of_cycles) + 10
    else:  # pacer_interval <= delay
        scan_time = (delay * num_of_cycles) + 10
    return test, scan_time


def scan_and_compare(test, pacer_interval, delay, expected_TBC_value):

    pixel_sim_thread = cert_data_sim.DataSimThread(test=test, num_of_pixels=1, duplicates=3, delay=delay, pkt_types=[0], pixels_type=GEN3)
    pixel_sim_thread.start()
    test, scan_time = cal_scan_time(test, delay, pacer_interval)
    df = cert_common.data_scan(test, scan_time=scan_time, brg_data=(not test.internal_brg), gw_data=test.internal_brg)
    pixel_sim_thread.stop()
    cert_mqtt.dump_pkts(test, log="rx_rate")
    cert_common.display_data(df, tbc=True, rssi=True, dir=test.dir)
    # check if the dataframe is empty or not
    if len(df) <= 1:
        print("Df is empty")
        test.rc = TEST_FAILED
        test.add_reason("Df is empty")
        return test
    else:
        # Divided the dataframe by tag_id and continue with df's tag that has the highest number of rows.
        tag_counts = df[TAG_ID].value_counts()
        print(f"Tag counts:\n{tag_counts.to_string(header=False)}")
        most_common_tag = tag_counts.idxmax()
        print(f"Most common tag: {most_common_tag}")
        df = df[df[TAG_ID] == most_common_tag]
        df = df[[TAG_ID, TBC, PACKET_TYPE, DATETIME]]
        length = len(df)
        mid_index = int(length // 2)
        if mid_index == 0:
            mid_index = 1
        print(f"Length of df: {length}, mid index: {mid_index}")
        # TODO: Logging print
        # print(f"Df:\n {df}")
        df[TBC] = df[TBC].apply(address2tbc)
        print(f"Df after invert tbc:\n {df}")
        tag = df.iloc[0][TAG_ID]

        actual_tbc_value = round(df.iloc[mid_index:][TBC].mean(), 3)
        expected_tbc_value = round(expected_TBC_value, 3)
        threshold = 0.1 * expected_tbc_value
        print(f"Actual TBC value: {actual_tbc_value}")
        print(f"Expected TBC value: {expected_tbc_value} range: [{expected_tbc_value - threshold}, {expected_tbc_value + threshold}]")

        # Validate the received value is in 10% of the expected value
        if not ((expected_tbc_value - threshold) <= actual_tbc_value <= (expected_tbc_value + threshold)):
            test.rc = TEST_FAILED
            test.add_reason(f"TBC value for tag {tag}: got: {actual_tbc_value}, expected: {expected_tbc_value}!\n")
            if actual_tbc_value < expected_tbc_value:
                print(f" Actual TBC value: {actual_tbc_value} is less than expected TBC value: {expected_tbc_value}!\n")
            if actual_tbc_value > (expected_tbc_value + threshold):
                print(f" TBC value is higher than expected TBC value: {expected_tbc_value}!\n")
        if test.params == [mid_values] and delay == 1000:
            # checking 0 value in the first packet.
            first_row = df.iloc[0][TBC]
            second_row = df.iloc[1][TBC]
            if first_row != 0 and second_row != 0:
                test.rc = TEST_FAILED
                test.add_reason("first tbc value is not 0 as supposed to be while sanity checking")
    return test


def mid_values(test, _):
    # Mid_values - Sanity check: Generate packets with delays of 1, 5, and 0.5 seconds.
    # Verify that the correct TBC values are received and that the first packet's TBC is zero.

    SANITY_DELAY_VALUES = [1000, 5000, 500]
    for delay in SANITY_DELAY_VALUES:
        pacer_interval = 1
        test = scan_and_compare(test, pacer_interval=pacer_interval, delay=delay, expected_TBC_value=(delay / 1000))
    time.sleep(10)
    return test


def diff_pacer(test, datapath_module):
    # Diff_pacer - Generate packets with a 1-second delay and pacer intervals of 30 and 60.
    # Ensure that the TBC value remains unchanged.

    PACER_INTERVAL_LIST = [30, 60]
    delay = 1000  # 1 sec
    for pacer_interval in PACER_INTERVAL_LIST:
        test = cert_config.brg_configure(test, fields=[BRG_PACER_INTERVAL], values=[pacer_interval], module=datapath_module)[0]
        if test.rc == TEST_FAILED:
            test.add_reason(f"Didn't succeed to config pacer interval {pacer_interval}")
            return test
        test = scan_and_compare(test, pacer_interval=pacer_interval, delay=delay, expected_TBC_value=(delay / 1000))
    time.sleep(10)
    return test


def min_value(test, datapath_module):
    # Min_value - Minimum value: Generate packets with a 0.1-second delay.
    # Verify the correct TBC value is received.
    # NOTE: The min TBC value is 0.25 seconds.
    MIN_ADDRESS_VALUE = 0.25
    pacer_interval = 1
    test = cert_config.brg_configure(test, fields=[BRG_PACER_INTERVAL], values=[pacer_interval], module=datapath_module)[0]
    if test.rc == TEST_FAILED:
        test.add_reason(f"Didn't succeed to config pacer interval {pacer_interval}")
        return test
    delay = 100
    test = scan_and_compare(test, pacer_interval=pacer_interval, delay=delay, expected_TBC_value=MIN_ADDRESS_VALUE)
    time.sleep(10)
    return test


def max_value(test, datapath_module):
    # Max_value - Maximum value: Generate packets with a 70-second delay and a pacer interval of 80.
    # Verify the correct TBC value is received.
    # NOTE: The max TBC value is 64 seconds.
    MAX_TBC_VALUE = 64
    pacer_interval = 80
    test = cert_config.brg_configure(test, fields=[BRG_PACER_INTERVAL], values=[pacer_interval], module=datapath_module)[0]
    if test.rc == TEST_FAILED:
        test.add_reason(f"Didn't succeed to config pacer interval {pacer_interval}")
        return test
    delay = 70000
    test = scan_and_compare(test, pacer_interval=pacer_interval, delay=delay, expected_TBC_value=MAX_TBC_VALUE)
    time.sleep(10)
    return test


def diff_rate(test, datapath_module):
    # Diff_rate - alpha filter: Generate packets with delay 0.5 second and change to 3 seconds.
    # Verify that the TBC value changes according to the delay, within the expected tolerance.
    pacer_interval = 1
    delay_duration = [[500, 5], [3000, 3]]
    first_delay = delay_duration[0][0]
    first_duration = delay_duration[0][1]
    second_delay = delay_duration[1][0]
    test = cert_config.brg_configure(test, fields=[BRG_PACER_INTERVAL], values=[pacer_interval], module=datapath_module)[0]
    if test.rc == TEST_FAILED:
        test.add_reason(f"Didn't succeed to config pacer interval {pacer_interval}")
        return test
    pixel_sim_thread = cert_data_sim.DataSimThread(test=test, num_of_pixels=1, duplicates=2,
                                                   delay=first_delay, pkt_types=[0], pixels_type=GEN3)
    pixel_sim_thread.start()
    time_sleep = first_duration - ((first_delay / 1000) / 2)
    print(f"sleep for {time_sleep} sec\n")
    time.sleep(time_sleep)
    pixel_sim_thread.delay = second_delay
    scan_time = sum(duration for _, duration in delay_duration) + 40
    df = cert_common.data_scan(test, scan_time=scan_time, brg_data=(not test.internal_brg), gw_data=test.internal_brg)
    pixel_sim_thread.stop()
    df = df[[TAG_ID, TBC]]
    # TODO: logging print
    # print(f"df:\n {df}")
    df[TBC] = df[TBC].apply(address2tbc)
    if len(df) <= 1:
        test.add_reason("Df is empty")
        test.rc = TEST_FAILED
        return test
    else:
        print(f"Df:\n {df}")
    # NOTE: all next rows are specific for the values: delay 0.5 and 3 sec.
    # check if the last tbc value is as we expected  for delay 3 sec we need to get 235 according to LUT table
    # we define tolerance of +-10 units for address value
    expected_second_tbc_value = second_delay / 1000
    print(f"expected second tbc value: {expected_second_tbc_value}")
    # Most important check, verify it converges to the correct value
    average_of_last_5_tbc_value = round(df.iloc[-5:][TBC].mean(), 3)
    print(f"last tbc value: {average_of_last_5_tbc_value}")
    THRESHOLD_MIN = 0.95
    # NOTE: assume that there is time difference between SIM and GW
    if test.tester.is_simulated():
        THRESHOLD_MAX = 1.1
    else:
        THRESHOLD_MAX = 1.15
    min_expected_tbc_value = round(expected_second_tbc_value * THRESHOLD_MIN, 3)
    max_expected_tbc_value = round(expected_second_tbc_value * THRESHOLD_MAX, 3)

    print(f"TBC value: {average_of_last_5_tbc_value}")
    print(f"expected value [{min_expected_tbc_value},{max_expected_tbc_value}] according to delay:{second_delay / 1000} sec")
    if not (min_expected_tbc_value <= average_of_last_5_tbc_value <= max_expected_tbc_value):
        test.rc = TEST_FAILED
        test.add_reason(f"TBC value: {average_of_last_5_tbc_value}, expected value {expected_second_tbc_value}")
        return test

    # # TODO: we skip that part until we decide if there is a need to check the gap between the first and second tbc values
    # # for loop that skip the first row and check if somewhere there is the expected gap 0.5 to 3 sec
    # result = False
    # expected_first_tbc_value = first_delay / 1000
    # print(f"expected first tbc value: {expected_first_tbc_value}")
    # expected_first_gap_tbc_value = round(address_2_tbc(200), 3)
    # print(f"expected second tbc value: {expected_first_gap_tbc_value}")
    # for i in range(0, length - 1):
    #     prev = round(df.iloc[i][TBC],3)
    #     current = round(df.iloc[i + 1][TBC],3)
    #     print(f"prev: {prev}, current: {current}")
    #     if expected_first_tbc_value*0.9 <= prev <= expected_first_tbc_value*1.1:
    #       if expected_first_gap_tbc_value*0.9 <= current <= expected_first_gap_tbc_value*1.1:
    #         print(f"Found the gap between {prev} and {current}")
    #         print(f"row {i}: {df.iloc[i][TBC]}")
    #         print(f"row {i + 1}: {df.iloc[i + 1][TBC]}")
    #         result = True
    # if not result:
    #     test.rc = TEST_FAILED
    #     test.add_reason("Didn't find the correct gap according to alpha filter calculation")
    return test


def run(test):

    # "Test prolog"
    datapath_module = test.active_brg.datapath

    test = cert_common.test_prolog(test)
    pacer_interval = 1
    test = cert_config.brg_configure(test, fields=[BRG_PACER_INTERVAL], values=[pacer_interval], module=datapath_module)[0]
    if test.rc == TEST_FAILED:
        test.add_reason(f"Didn't succeed to config pacer interval {pacer_interval}")
    name = test.phases[0].name
    test.set_phase_rc(name, test.rc)
    test.add_phase_reason(name, test.reason)

    if test.rc == TEST_FAILED:
        return cert_common.test_epilog(test)

    RX_RATE_TEST_MAP = {"mid_values": mid_values, "diff_pacer": diff_pacer, "min_value": min_value,
                        "max_value": max_value, "diff_rate": diff_rate}
    for param in test.params:
        functionality_run_print(param.name)
        test = RX_RATE_TEST_MAP[param.value](test, datapath_module)
        cert_mqtt.generate_log_file(test, param.name)
        field_functionality_pass_fail_print(test, param.name)
        test.set_phase_rc(param.name, test.rc)
        test.add_phase_reason(param.name, test.reason)
        if test.rc == TEST_FAILED:
            if test.exit_on_param_failure:
                break  # break the whole for loop and keep the test as failed
        test.reset_result()  # reset result and continue to next param

    return cert_common.test_epilog(test)
