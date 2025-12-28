from certificate.cert_prints import *
from certificate.cert_defines import *
from certificate.wlt_types import *
import certificate.cert_mqtt as cert_mqtt
import certificate.cert_common as cert_common
import certificate.cert_config as cert_config
import certificate.cert_data_sim as cert_data_sim

DEFAULT_NUM_OF_PIXELS = 300
DEFAULT_DUPLICATES = 4
DEFAULT_DELAY = 0
HIGH_PACER_VALUE = 300
LOW_PACER_VALUE = 15
TAGS_CTR_UNDER_THRESHOLD = 0.9
TAGS_CTR_OVER_THRESHOLD = 1.1
TIME_OFFSET = 15


def get_hb_pkt(test):
    test.get_mqttc_by_target(DUT).flush_pkts()
    cert_config.send_brg_action(test, ag.ACTION_SEND_HB)
    test, hb_pkts = cert_common.scan_for_mgmt_pkts(test, [eval_pkt(f'Brg2GwHbV{test.active_brg.api_version}')])
    tags_ctr = hb_pkts[-1][MGMT_PKT].pkt.tags_ctr if hb_pkts else 0
    return test, tags_ctr


def wait_in_reference_to_start_time(start_time, wait_time):
    print(f"\nWaiting for {(wait_time - (time.time() - start_time)):.1f} seconds...")
    while (time.time() - start_time) < wait_time:
        print_update_wait()


def wait_for_zero_pixels(test, wait_time=60):
    for i in range(int(wait_time / 10)):
        print(f"\nWaiting {wait_time - (i * 10)} more seconds for pixels table to clear")
        wait_in_reference_to_start_time(time.time(), 10)
        test, tags_ctr = get_hb_pkt(test)
        # tags_ctr will be 0 if the tags table cleared OR if no hb was received - return in both cases
        if tags_ctr > 0:
            print(f"\nPixels count: {tags_ctr}")
            continue
        return test, tags_ctr
    test.rc = TEST_FAILED
    test.add_reason("Floor pixel count value is not zero, make sure there are no pixels (or other energizing devices) around!")
    return test, tags_ctr


def aging_analysis(test, datapath_module, pacer_interval, num_of_sim_tags):
    # Get tags counter floor
    test, first_floor_tags_ctr = get_hb_pkt(test)
    if test.sterile_run and first_floor_tags_ctr > 0:
        test, first_floor_tags_ctr = wait_for_zero_pixels(test)
    if test.rc == TEST_FAILED:
        return test
    utPrint(f"\nPhase start pixels count: {first_floor_tags_ctr}\n", "BLUE")
    # Configure bridge pacer interval
    test = cert_config.brg_configure(test, fields=[BRG_PACER_INTERVAL], values=[pacer_interval], module=datapath_module)[0]
    if test.rc == TEST_FAILED:
        return test
    # Simualtor pixel packets generation
    cycle_time = DEFAULT_DUPLICATES * (cert_data_sim.PIXEL_SIM_MIN_CYCLE / 1000) * num_of_sim_tags
    pixel_sim_thread = cert_data_sim.DataSimThread(test=test, num_of_pixels=num_of_sim_tags, duplicates=DEFAULT_DUPLICATES,
                                                   delay=DEFAULT_DELAY, pkt_types=[0], pixels_type=GEN2)
    sending_time = cycle_time  # Send one cycle of pixel pkts
    print(f"Simulator starts sending pixel packets for {sending_time} sec")
    pixel_sim_thread.start()
    start_time = time.time()
    wait_in_reference_to_start_time(start_time, wait_time=sending_time)
    pixel_sim_thread.stop()
    print("\nSimulator stopped sending pixel packets\n")
    print(f"\nWaiting for a {TIME_OFFSET} seconds time offset\n")
    time.sleep(TIME_OFFSET)
    # Get tags counter peak
    test, first_peak_tags_ctr = get_hb_pkt(test)
    if test.rc == TEST_FAILED:
        return test
    utPrint(f"\nEnd of pixel simulation pixels count: {first_peak_tags_ctr}\n", "BLUE")
    if first_peak_tags_ctr - first_floor_tags_ctr < TAGS_CTR_UNDER_THRESHOLD * DEFAULT_NUM_OF_PIXELS:
        test.rc = TEST_FAILED
        test.add_reason("Didn't count sufficient amount of pixels.\n"
                        f"tags_ctr value: {first_peak_tags_ctr}\nNumber of simulated pixels: {DEFAULT_NUM_OF_PIXELS}")
        return test

    # Waiting the aging time
    # Throuout the aging time until deletion starts we expect to get the tags_ctr equal to the number of pixels
    aging_time = max(60, pacer_interval)
    print(f"Waiting the aging time of {aging_time} seconds")

    # (sending_time - cycle_time + aging_time) is the expected deletion time of the first simulated pixel
    wait_in_reference_to_start_time(start_time, wait_time=(sending_time - cycle_time + aging_time) - TIME_OFFSET)
    test, second_peak_tags_ctr = get_hb_pkt(test)
    if test.rc == TEST_FAILED:
        return test
    utPrint(f"\nBefore deletion start pixels count: {second_peak_tags_ctr}\n", "BLUE")
    if second_peak_tags_ctr < TAGS_CTR_UNDER_THRESHOLD * first_peak_tags_ctr:
        test.rc = TEST_FAILED
        test.add_reason("Pixel count is lower than expected. Looks like aging time is too short.\n"
                        f"Found {second_peak_tags_ctr} tags in hb ctr, Previously got {first_peak_tags_ctr},\n"
                        f"only {(100 * second_peak_tags_ctr / first_peak_tags_ctr):.1f}% of expected\n")
        return test

    # (sending_time + aging_time) is the expected deletion time of all simulated pixels
    wait_in_reference_to_start_time(start_time, wait_time=(sending_time + aging_time) + TIME_OFFSET)
    test, second_floor_tags_ctr = get_hb_pkt(test)
    if test.rc == TEST_FAILED:
        return test
    utPrint(f"\nEnd of aging time pixels count: {second_floor_tags_ctr}\n", "BLUE")
    if test.sterile_run and second_floor_tags_ctr != 0:
        test.rc = TEST_FAILED
        test.add_reason("Pixel count is higher than expected. Looks like aging time is too long.\n"
                        f"Number of pixels after aging time: {second_floor_tags_ctr}")
    elif not test.sterile_run and (second_floor_tags_ctr > TAGS_CTR_OVER_THRESHOLD * first_floor_tags_ctr):
        test.rc = TEST_FAILED
        test.add_reason("Pixel count is higher than expected. Looks like aging time is too long.\n"
                        f"Number of pixels after aging time: {second_floor_tags_ctr},"
                        f" before tags simulation was: {second_peak_tags_ctr}\n")
    return test


def run(test):
    # Test prolog
    datapath_module = test.active_brg.datapath
    test = cert_common.test_prolog(test)
    if test.rc == TEST_FAILED:
        return cert_common.test_epilog(test)

    AGING_TEST_MAP = {"low_pacer": LOW_PACER_VALUE, "high_pacer": HIGH_PACER_VALUE}

    for param in test.params:
        phase_run_print(param.name)
        test = aging_analysis(test, datapath_module, pacer_interval=AGING_TEST_MAP[param.value],
                              num_of_sim_tags=DEFAULT_NUM_OF_PIXELS)
        cert_mqtt.generate_log_file(test, param.name)
        field_functionality_pass_fail_print(test, param.name)
        test.set_phase_rc(param.name, test.rc)
        test.add_phase_reason(param.name, test.reason)
        if test.rc == TEST_FAILED:
            if test.exit_on_param_failure:
                break  # break the whole for loop and keep the test as failed
        test.reset_result()  # reset result and continue to next param

    return cert_common.test_epilog(test, revert_brgs=True, modules=[datapath_module])
