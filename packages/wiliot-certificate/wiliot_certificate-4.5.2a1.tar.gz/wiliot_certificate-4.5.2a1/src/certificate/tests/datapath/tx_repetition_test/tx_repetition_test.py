# This test will run on "params" mode when it gets parameters in its call - check config only
# Otherwise it will run on "auto" mode - collect packets and analyze packets actual repetitions

from certificate.cert_prints import *
from certificate.cert_defines import *
from certificate.wlt_types import *
import certificate.cert_mqtt as cert_mqtt
import certificate.cert_common as cert_common
import certificate.cert_config as cert_config
import certificate.cert_data_sim as cert_data_sim
from certificate.cert_gw_sim import DEDUPLICATION_PKTS
import statistics

TX_REPETITION_THRESHOLD = 0.5


def tx_repetitions_analysis(test, repetitions):
    wait_time_n_print(CLEAR_DATA_PATH_TIMEOUT)
    test.get_mqttc_by_target(DUT).flush_pkts()
    if test.data == DATA_SIMULATION:
        pixel_sim_thread = cert_data_sim.DataSimThread(test=test, num_of_pixels=15, duplicates=1, delay=100, pkt_types=[0])
        pixel_sim_thread.start()
    mqtt_scan_wait(test, 60)
    if test.data == DATA_SIMULATION:
        pixel_sim_thread.stop()  # stop generating pkts on data simulator
        wait_time_n_print(CLEAR_DATA_PATH_TIMEOUT)  # Wait for sim queue to free
    pkts = cert_mqtt.get_unified_data_pkts(test)
    print(f"Found {len(pkts)} packets")
    if len(pkts) == 0:
        test.rc = TEST_FAILED
        test.add_reason(f"For repetitions {repetitions} found 0 pkts!")
        cert_mqtt.generate_log_file(test, repetitions)
        return test
    pkt_payload_counter = {}
    for p in pkts:
        cur_pkt = p[PAYLOAD]
        if cur_pkt in pkt_payload_counter:
            pkt_payload_counter[cur_pkt] += 1
        else:
            pkt_payload_counter[cur_pkt] = 1
    cert_mqtt.generate_log_file(test, repetitions)
    avg = statistics.mean([pkt_payload_counter[p] for p in pkt_payload_counter])
    txt = f"For TX repetition = {repetitions}, average {round(avg, 3)} repetitions"
    print(txt)
    if (avg / float(repetitions)) <= TX_REPETITION_THRESHOLD or (avg / float(repetitions)) > 1:
        test.rc = TEST_FAILED
        test.add_reason(txt)
    return test


def run(test):

    fields = [BRG_TX_REPETITION, BRG_PKT_FILTER, BRG_RX_CHANNEL]
    datapath_module = test.active_brg.datapath

    test = cert_common.test_prolog(test)
    if test.rc == TEST_FAILED:
        return cert_common.test_epilog(test)

    print("Configuring GW with !deduplication_pkts 0")
    cert_config.gw_action(test, f"{DEDUPLICATION_PKTS} 0")

    for param in test.params:
        test = cert_config.brg_configure(test, fields=fields,
                                         values=[param.value, ag.PKT_FILTER_RANDOM_FIRST_ARRIVING_PKT, ag.RX_CHANNEL_37],
                                         module=datapath_module)[0]
        if test.rc == TEST_FAILED:
            if test.exit_on_param_failure:
                break  # break the whole for loop and keep the test as failed
            else:
                test.reset_result()   # reset result and continue to next param
                continue
        tx_repetitions_analysis(test, param.name)
        field_functionality_pass_fail_print(test, fields[0], value=param.name)
        test.set_phase_rc(param.name, test.rc)
        test.add_phase_reason(param.name, test.reason)
        if test.rc == TEST_FAILED:
            if test.exit_on_param_failure:
                break  # break the whole for loop and keep the test as failed
        test.reset_result()  # reset result and continue to next param

    # Re-enable unified packets deduplication
    cert_config.gw_action(test, f"{DEDUPLICATION_PKTS} 1")
    return cert_common.test_epilog(test, revert_brgs=True, modules=[datapath_module])
