from certificate.cert_prints import *
from certificate.cert_defines import *
from certificate.wlt_types import *
import certificate.cert_data_sim as cert_data_sim
import certificate.cert_mqtt as cert_mqtt
import certificate.cert_common as cert_common
import certificate.cert_config as cert_config


def run(test):

    fields = [BRG_PATTERN]
    calib_module = test.active_brg.calibration
    datapath_module = test.active_brg.datapath

    test = cert_common.test_prolog(test)
    if test.rc == TEST_FAILED:
        return cert_common.test_epilog(test)

    for param in test.params:
        # A special verification for 38_38_39, which is irrelevant for bridge with cloud connectivity
        if param.value == ag.CALIBRATION_PATTERN_38_38_39 and not test.dut_is_combo():
            utPrint("\nCALIBRATION_PATTERN_38_38_39 was configured - checking the GW doesn't receive tag packets", "BLUE")
            # Config tester's rx_channel to CHANNEL_37
            test = cert_config.brg_configure(test, fields=[BRG_RX_CHANNEL],
                                             values=[ag.RX_CHANNEL_37],
                                             module=test.tester.internal_brg.datapath,
                                             target=TESTER)[0]
            if test.rc != TEST_FAILED:
                # Configure the BRG, wait=False
                test = cert_config.brg_configure(test, fields=[BRG_PATTERN, BRG_CALIB_INTERVAL],
                                                 values=[param.value, 1], module=calib_module, wait=False)[0]
                if test.rc == TEST_FAILED:
                    if test.exit_on_param_failure:
                        break  # break the whole for loop and keep the test as failed
                    else:
                        test.reset_result()  # reset result
                        continue  # skip the current phase and continue to next param
                wait_time_n_print(CLEAR_DATA_PATH_TIMEOUT)
                # MQTT scan
                if test.data == DATA_SIMULATION:
                    # start generating pkts and send them using data simulator
                    pixel_sim_thread = cert_data_sim.DataSimThread(test=test, num_of_pixels=10, duplicates=1, delay=100, pkt_types=[0])
                    pixel_sim_thread.start()
                df = cert_common.data_scan(test, gw_data=True, brg_data=True, scan_time=(40))
                if test.data == DATA_SIMULATION:
                    # stop generating pkts with data simulator and wait a few seconds for full flush
                    pixel_sim_thread.stop()
                    time.sleep(5)

                # Analyze pass/fail
                gw_tags_pkts = len(df.query(f'src_id == {GW_ID}'))
                brg_tags_pkts = len(df.query(f'src_id != {GW_ID}'))
                print(f"Found gw_tags_pkts={gw_tags_pkts}, brg_tags_pkts={brg_tags_pkts}")
                if (gw_tags_pkts == 0 and test.data == DATA_REAL_TAGS) or brg_tags_pkts != 0:
                    test.rc = TEST_FAILED
                    test.add_reason(f"gw_tags_pkts={gw_tags_pkts} brg_tags_pkts={brg_tags_pkts} for BRG 38,38,39 calibration, "
                                    "and GW scanning on ch 37")
            # Revert tester
            test = cert_config.brg_configure(test, module=test.tester.internal_brg.datapath, target=TESTER)[0]
            cert_mqtt.generate_log_file(test, param.name)
            field_functionality_pass_fail_print(test, fields[0], value=param.name)
            test.set_phase_rc(param.name, test.rc)
            test.add_phase_reason(param.name, test.reason)
            if test.rc == TEST_FAILED:
                if test.exit_on_param_failure:
                    break  # break the whole for loop and keep the test as failed
            test.reset_result()  # reset result and continue to next param
        else:
            test = cert_config.brg_configure(test, fields=fields, values=[param.value], module=calib_module)[0]
            cert_mqtt.generate_log_file(test, param.name)
            field_functionality_pass_fail_print(test, fields[0], value=param.name)
            test.set_phase_rc(param.name, test.rc)
            test.add_phase_reason(param.name, test.reason)
            if test.rc == TEST_FAILED:
                if test.exit_on_param_failure:
                    break  # break the whole for loop and keep the test as failed
            test.reset_result()  # reset result and continue to next param

    return cert_common.test_epilog(test, revert_brgs=True, modules=[calib_module, datapath_module])
