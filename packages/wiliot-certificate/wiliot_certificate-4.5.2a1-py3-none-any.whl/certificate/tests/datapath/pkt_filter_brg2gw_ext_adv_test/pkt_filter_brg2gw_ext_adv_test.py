from certificate.cert_prints import *
from certificate.cert_defines import *
from certificate.ag.wlt_types_ag import *
import certificate.cert_mqtt as cert_mqtt
import certificate.cert_data_sim as cert_data_sim
import certificate.cert_common as cert_common
import certificate.cert_config as cert_config

PKT_FILTER_TEST_PACER_INTERVAL = 4


def run(test):

    fields = [BRG_PKT_FILTER, BRG_RX_CHANNEL, BRG_PACER_INTERVAL, BRG_PATTERN]
    dut = cert_config.get_brg_by_target(test, DUT)

    test = cert_common.test_prolog(test)
    if test.rc == TEST_FAILED:
        return cert_common.test_epilog(test)

    test = cert_config.brg_configure(test, fields=fields,
                                     values=[PKT_FILTER_TEMP_AND_ADVANCED_PKTS, RX_CHANNEL_10_500K,
                                             PKT_FILTER_TEST_PACER_INTERVAL, DATAPATH_PATTERN_EXTENDED_ADV],
                                     module=dut.datapath, ble5=test.dut_is_bridge())[0]
    if test.rc == TEST_FAILED:
        return cert_common.test_epilog(test)

    for param in test.params:
        # Configure tester's rx channel
        test = cert_config.brg_configure(test, fields=[BRG_RX_CHANNEL],
                                         values=[param.value],
                                         module=test.tester.internal_brg.datapath,
                                         target=TESTER)[0]
        test.set_phase_rc(param.name, test.rc)
        test.add_phase_reason(param.name, test.reason)
        if test.rc == TEST_FAILED:
            if test.exit_on_param_failure:
                break  # break the whole for loop and keep the test as failed
            else:
                test.reset_result()  # reset result and continue to next param
                continue

        # Configure the BRG to DATAPATH_PATTERN_EXTENDED_ADV_CH_10 if the GW listens to channel 10
        if param.value == RX_CHANNEL_10_500K:
            test = cert_config.brg_configure(test, fields=fields,
                                             values=[PKT_FILTER_TEMP_AND_ADVANCED_PKTS, RX_CHANNEL_10_500K,
                                                     PKT_FILTER_TEST_PACER_INTERVAL, DATAPATH_PATTERN_EXTENDED_ADV_CH_10],
                                             module=dut.datapath, ble5=test.dut_is_bridge())[0]
            if test.rc == TEST_FAILED:
                if test.exit_on_param_failure:
                    break  # break the whole for loop and keep the test as failed
            test.reset_result()  # reset result and continue to next param

        wait_time_n_print(5, txt="Waiting datapath to clear")
        num_of_pixels = 0
        if test.data == DATA_SIMULATION:
            # start generating pkts and send them using data simulator
            num_of_pixels = 50
            pixel_sim_thread = cert_data_sim.DataSimThread(test=test, num_of_pixels=num_of_pixels, duplicates=2,
                                                           delay=0, pkt_types=[2], pixels_type=GEN3_EXTENDED)
            pixel_sim_thread.start()
        df = cert_common.data_scan(test, brg_data=(not test.internal_brg), gw_data=test.internal_brg,
                                   scan_time=PKT_FILTER_TEST_PACER_INTERVAL * 8, per_pkt_type=True,
                                   pkt_filter_cfg=PKT_FILTER_TEMP_AND_ADVANCED_PKTS, flush_pkts=True)
        if test.data == DATA_SIMULATION:
            # stop generating pkts with data simulator and wait a few seconds for full flush
            pixel_sim_thread.stop()
            time.sleep(5)
        cert_common.display_data(df, tbc=True, name_prefix=f"{param.name}_", dir=test.dir)
        test = cert_common.pacing_analysis(test, pacer_interval=PKT_FILTER_TEST_PACER_INTERVAL, df=df,
                                           pkt_filter_cfg=PKT_FILTER_TEMP_AND_ADVANCED_PKTS,
                                           num_of_pixels=num_of_pixels, is_ble5_test=True, ext_adv_brg2gw=True)
        cert_mqtt.generate_log_file(test, param.name)
        field_functionality_pass_fail_print(test, fields[0], value=param.name)
        test.set_phase_rc(param.name, test.rc)
        test.add_phase_reason(param.name, test.reason)
        if test.rc == TEST_FAILED:
            if test.exit_on_param_failure:
                break  # break the whole for loop and keep the test as failed
        test.reset_result()  # reset result and continue to next param

        # Revert tester's rx channel
        test = cert_config.brg_configure(test, module=test.tester.internal_brg.datapath, target=TESTER)[0]

    return cert_common.test_epilog(test, revert_brgs=True, modules=[dut.datapath], ble5=test.dut_is_bridge())
