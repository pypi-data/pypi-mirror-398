from certificate.cert_prints import *
from certificate.cert_defines import *
from certificate.wlt_types import *
import certificate.cert_mqtt as cert_mqtt
import certificate.cert_common as cert_common
import certificate.cert_config as cert_config

# Test MACROS #
NUM_OF_SCANNING_CYCLE = 5
SCAN_DELAY_TIME = 3


def test_ext_adv_rx37(test):

    dut = cert_config.get_brg_by_target(test, DUT)
    tester = cert_config.get_brg_by_target(test, TESTER)
    cycle, rep = 8, 4

    # Configuring DUT #
    # configuring transmitter #
    utPrint(f"Configuring DUT BRG {dut.id_str} as Signal Indicator Transmitter (cycle={cycle}, repetition={rep})", "BLUE")
    test = cert_config.brg_configure(test=test, module=dut.energy2400,
                                     fields=[BRG_SIGNAL_INDICATOR_CYCLE, BRG_SIGNAL_INDICATOR_REP],
                                     values=[cycle, rep])[0]
    if test.rc == TEST_FAILED:
        test.add_reason(f"DUT BRG {dut.id_str}: didn't receive signal indicator transmitter configuration!")
        return test
    # configuring extended advertising and rx channel #
    utPrint(f"Configuring DUT BRG {dut.id_str} with extended advertising and rx channel 37", "BLUE")
    test = cert_config.brg_configure(test=test, module=dut.datapath,
                                     fields=[BRG_RX_CHANNEL, BRG_PATTERN],
                                     values=[ag.RX_CHANNEL_37, ag.DATAPATH_PATTERN_EXTENDED_ADV])[0]
    if test.rc == TEST_FAILED:
        test.add_reason(f"DUT BRG {dut.id_str}: didn't receive extended advertising and rx channel configuration!")
        return test

    # configuring TESTER #
    utPrint(f"Configuring TESTER BRG {tester.id_str} as Signal Indicator Receiver", "BLUE")
    test = cert_config.brg_configure(test=test, module=tester.sensors, fields=[BRG_SENSOR0],
                                     values=[ag.EXTERNAL_SENSORS_SIGNAL_INDICATOR], target=TESTER)[0]
    if test.rc == TEST_FAILED:
        test.add_reason(f"TESTER BRG {tester.id_str}: didn't receive signal indicator receiver configuration!")
        return test
    utPrint(f"Configuring TESTER BRG {tester.id_str} with rx channel 37", "BLUE")
    test = cert_config.brg_configure(test=test, module=tester.datapath, fields=[BRG_RX_CHANNEL],
                                     values=[ag.RX_CHANNEL_37], target=TESTER)[0]
    if test.rc == TEST_FAILED:
        test.add_reason(f"TESTER BRG {tester.id_str}: didn't receive rx channel configuration!")
        return test

    # phase analysis #
    cert_mqtt.mqtt_scan_n_create_log_file(test, (NUM_OF_SCANNING_CYCLE * cycle) + SCAN_DELAY_TIME,
                                          f"tx_{cycle}_{rep}")
    rec_sig_ind_pkts = cert_common.get_all_sig_ind_pkts(test=test, rx_brg=tester, tx_brg=dut)
    if cert_common.sig_ind_pkts_fail_analysis(tx_brg=dut, rx_brg=tester, cycles=NUM_OF_SCANNING_CYCLE, received_pkts=rec_sig_ind_pkts):
        test.rc = TEST_FAILED
        expected_signal_ind_pkts = cert_common.exp_sig_ind_pkts2(tester, dut, NUM_OF_SCANNING_CYCLE)
        test.add_reason(f"tx phase failed - BRG {dut.id_str} received wrong number of "
                        f"signal indicator packets\nreceived {len(rec_sig_ind_pkts)} packets, "
                        f"expected {expected_signal_ind_pkts} packets")
        print(rec_sig_ind_pkts)  # TODO: logging print(debug)
        print([[p[TIMESTAMP], p[UNIFIED_SENSOR_PKT].pkt.signal_indicator_payload.rx_antenna] for p in rec_sig_ind_pkts])
        return test

    test = cert_common.rx_tx_antenna_check(test, rec_sig_ind_pkts, dut, tester, NUM_OF_SCANNING_CYCLE)
    test = cert_common.output_power_check(test, rec_sig_ind_pkts, dut)
    test = cert_common.rssi_check(test, rec_sig_ind_pkts)

    return test


def test_ext_adv_rx10(test):

    dut = cert_config.get_brg_by_target(test, DUT)
    tester = cert_config.get_brg_by_target(test, TESTER)
    cycle, rep = 8, 4

    # Configuring DUT #
    # configuring transmitter #
    utPrint(f"Configuring DUT BRG {dut.id_str} as Signal Indicator Transmitter (cycle={cycle}, repetition={rep})", "BLUE")
    test = cert_config.brg_configure(test=test, module=dut.energy2400,
                                     fields=[BRG_SIGNAL_INDICATOR_CYCLE, BRG_SIGNAL_INDICATOR_REP],
                                     values=[cycle, rep])[0]
    if test.rc == TEST_FAILED:
        test.add_reason(f"DUT BRG {dut.id_str}: didn't receive signal indicator transmitter configuration!")
        return test
    # configuring extended advertising and rx channel #
    utPrint(f"Configuring DUT BRG {dut.id_str} with extended advertising and rx channel 10", "BLUE")
    test = cert_config.brg_configure(test=test, module=dut.datapath,
                                     fields=[BRG_RX_CHANNEL, BRG_PATTERN],
                                     values=[ag.RX_CHANNEL_10_500K, ag.DATAPATH_PATTERN_EXTENDED_ADV],
                                     ble5=test.dut_is_bridge(), wait=test.dut_is_combo())[0]
    if test.rc == TEST_FAILED:
        test.add_reason(f"DUT BRG {dut.id_str}: didn't receive extended advertising and rx channel configuration!")
        return test
    if test.dut_is_bridge():
        wait_time_n_print(BLE5_MAX_DURATION_SEC)  # BLE5 configuration can take up to BLE5_MAX_DURATION_SEC

    # configuring TESTER #
    utPrint(f"Configuring TESTER BRG {tester.id_str} as Signal Indicator Receiver", "BLUE")
    test = cert_config.brg_configure(test=test, module=tester.sensors, fields=[BRG_SENSOR0],
                                     values=[ag.EXTERNAL_SENSORS_SIGNAL_INDICATOR], target=TESTER)[0]
    if test.rc == TEST_FAILED:
        test.add_reason(f"TESTER BRG {tester.id_str}: didn't receive signal indicator receiver configuration!")
        return test
    utPrint(f"Configuring TESTER BRG {tester.id_str} with rx channel 10", "BLUE")
    test = cert_config.brg_configure(test=test, module=tester.datapath, fields=[BRG_RX_CHANNEL],
                                     values=[ag.RX_CHANNEL_10_500K], target=TESTER)[0]
    if test.rc == TEST_FAILED:
        test.add_reason(f"TESTER BRG {tester.id_str}: didn't receive rx channel configuration!")
        return test

    # phase analysis #
    cert_mqtt.mqtt_scan_n_create_log_file(test, (NUM_OF_SCANNING_CYCLE * cycle) + SCAN_DELAY_TIME,
                                          f"tx_{cycle}_{rep}")
    rec_sig_ind_pkts = cert_common.get_all_sig_ind_pkts(test=test, rx_brg=tester, tx_brg=dut)
    if cert_common.sig_ind_pkts_fail_analysis(tx_brg=dut, rx_brg=tester, cycles=NUM_OF_SCANNING_CYCLE, received_pkts=rec_sig_ind_pkts):
        test.rc = TEST_FAILED
        expected_signal_ind_pkts = cert_common.exp_sig_ind_pkts2(tester, dut, NUM_OF_SCANNING_CYCLE)
        test.add_reason(f"tx phase failed - BRG {dut.id_str} received wrong number of "
                        f"signal indicator packets\nreceived {len(rec_sig_ind_pkts)} packets, "
                        f"expected {expected_signal_ind_pkts} packets")
        print(rec_sig_ind_pkts)  # TODO: logging print(debug)
        print([[p[TIMESTAMP], p[UNIFIED_SENSOR_PKT].pkt.signal_indicator_payload.rx_antenna] for p in rec_sig_ind_pkts])
        return test

    test = cert_common.rx_tx_antenna_check(test, rec_sig_ind_pkts, dut, tester, NUM_OF_SCANNING_CYCLE)
    test = cert_common.output_power_check(test, rec_sig_ind_pkts, dut)
    test = cert_common.rssi_check(test, rec_sig_ind_pkts)

    return test


SIGNAL_INDICATOR_TEST_MAP = {"ext_adv_rx37": test_ext_adv_rx37, "ext_adv_rx10": test_ext_adv_rx10}


def run(test):
    # Test prolog
    test = cert_common.test_prolog(test)

    # Configure to rx channel and extended advertising pattern
    dut = cert_config.get_brg_by_target(test, DUT)
    tester = cert_config.get_brg_by_target(test, TESTER)

    for param in test.params:
        phase_run_print(param.name)
        test = SIGNAL_INDICATOR_TEST_MAP[param.value](test)
        cert_mqtt.generate_log_file(test, param.name)
        field_functionality_pass_fail_print(test, param.name)
        test.set_phase_rc(param.name, test.rc)
        test.add_phase_reason(param.name, test.reason)

        if test.rc == TEST_FAILED:
            test.set_phase_rc(param.name, test.rc)
            test.add_phase_reason(param.name, test.reason)
            if test.exit_on_param_failure:
                break
        else:
            test.reset_result()

    # Revert DUT and TESTER to defaults here and not in epilog
    test = cert_config.config_brg_defaults(test, modules=[dut.datapath, dut.energy2400],
                                           ble5=test.dut_is_bridge(), wait=test.dut_is_combo())[0]
    if test.dut_is_bridge():
        wait_time_n_print(2 * BLE5_MAX_DURATION_SEC)  # BLE5 configuration can take up to 2 * BLE5_MAX_DURATION_SEC
    if test.rc == TEST_FAILED:
        test.add_reason("Failed to revert dut to defaults")
    else:
        test = cert_config.config_brg_defaults(test, modules=[tester.datapath, tester.sensors], target=TESTER)[0]
        if test.rc == TEST_FAILED:
            test.add_reason("Failed to revert tester to defaults")

    return cert_common.test_epilog(test, revert_brgs=False)
