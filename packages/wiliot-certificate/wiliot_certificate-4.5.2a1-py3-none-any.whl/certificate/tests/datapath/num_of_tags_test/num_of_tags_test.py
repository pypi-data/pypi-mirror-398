
from certificate.cert_prints import *
from certificate.cert_defines import *
from certificate.wlt_types import *
import certificate.cert_mqtt as cert_mqtt
import certificate.cert_common as cert_common
import certificate.cert_config as cert_config
import certificate.cert_data_sim as cert_data_sim

GW_CYCLE_TIME = 0.02  # GW sends BLE packet every 20 nsec


def run(test):

    datapath_module = test.active_brg.datapath
    print(f"values: {[param.value for param in test.params]}")

    test = cert_common.test_prolog(test)
    if test.rc == TEST_FAILED:
        return cert_common.test_epilog(test)

    duplicates = 3

    for param in test.params:

        # The time it takes to send two cycles from the GW/DataSimThread
        time_of_sending_pkts = duplicates * param.value * GW_CYCLE_TIME * 2

        test = cert_config.brg_configure(test, fields=[BRG_PACER_INTERVAL], values=[time_of_sending_pkts], module=datapath_module)[0]
        if test.rc == TEST_FAILED:
            return cert_common.test_epilog(test)

        if test.data == DATA_SIMULATION:
            # start generating pkts and send them using data simulator
            pixel_sim_thread = cert_data_sim.DataSimThread(test=test, num_of_pixels=param.value, duplicates=duplicates,
                                                           delay=0, pkt_types=[0])
            pixel_sim_thread.start()

        df = cert_common.data_scan(test, scan_time=time_of_sending_pkts + 5, brg_data=(not test.internal_brg), gw_data=test.internal_brg)

        if test.data == DATA_SIMULATION:
            # stop generating pkts with data simulator and wait a few seconds for full flush
            pixel_sim_thread.stop()
            time.sleep(10)

        cert_common.display_data(df, tbc=True, name_prefix=f"num_of_tags_{param.name}_", dir=test.dir)

        num_of_tags = len(df[TAG_ID].unique())
        print(f"Tags from DF: {num_of_tags}")

        cert_config.send_brg_action(test, ag.ACTION_SEND_HB)
        test, mgmt_pkts = cert_common.scan_for_mgmt_pkts(test, [eval_pkt(f'Brg2GwHbV{test.active_brg.api_version}')])
        if not mgmt_pkts:
            reason = "Didn't find ACTION HB pkt"
            utPrint(reason, "RED")
            test.set_phase_rc(param.name, TEST_FAILED)
            test.add_phase_reason(param.name, "Didn't find ACTION HB pkt")
            continue

        num_of_tags_HB = mgmt_pkts[0][MGMT_PKT].pkt.tags_ctr
        print(f"Tags from HB: {num_of_tags_HB}\n ")

        cert_common.display_data(df, tbc=True, name_prefix=f"num_of_tags_{param.name}_", dir=test.dir)

        # compare the numbers of tags that come from the brg, success in 95% from number of tags (value) or more.
        if num_of_tags < (param.value * 0.95):
            test.add_reason(f"Received {num_of_tags} different pixels, expected: {param.name} pixels!")
            test.rc = TEST_FAILED

        # compare the counter tags in the HB packet
        if num_of_tags_HB < 0.95 * param.value or num_of_tags_HB > (param.value + 100):
            test.add_reason(f"HB counter num_of_tags: {num_of_tags_HB}, expected: {param.name}!")
            test.rc = TEST_FAILED
        # param epilog
        time.sleep(10)
        cert_mqtt.generate_log_file(test, param.name)
        field_functionality_pass_fail_print(test, "num_of_tags", value=param.name)
        test.set_phase_rc(param.name, test.rc)
        test.add_phase_reason(param.name, test.reason)
        if test.rc == TEST_FAILED:
            if test.exit_on_param_failure:
                break  # break the whole for loop and keep the test as failed
        test.reset_result()  # reset result and continue to next param

    return cert_common.test_epilog(test)
