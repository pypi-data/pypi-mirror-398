from certificate.cert_prints import *
from certificate.cert_defines import *
from certificate.wlt_types import *
import certificate.cert_mqtt as cert_mqtt
import certificate.cert_common as cert_common
import certificate.cert_config as cert_config

# Test Description:
#   This test is to verify the functionality of both signal indicator tx (tx_brg) and rx (rx_brg) at BRG level.
#   We will configure several signal indicator params during the test, and check the functionality of the signal indicator logic
#   for each of them.
#   It is important to execute the test with several setups: 2 Fanstel BRG's, 2 Minew BRG's and 1 Fanstel and 1 Minew BRG.
#   At first, we will configure several tx signal indicator params and check for ack's, to verify all indicated params were
#   received at the cloud.
#   Then, we will examine the signal indicator end-2-end logic with both transmitter and receiver:
#   phase 1 - One BRG will be configured as signal indicator tx, and the other as signal indicator rx, and we expect to see
#   signal indicator packets only from the tx BRG, and according to the tx params (to check the repetition and cycle params).
#   phase 2 - Same as phase 1, but with different tx params configured.
#   phase 3 - One rx BRG without any tx BRG. We don't expect to see any signal indicator packets. This phase is to verify the
#   brg module logic is working properly, and no tag packet is accidentally being treated as signal indicator packet.
#   phase 4 - Both BRG's will be configured to be transmitters and receivers, with different tx params for each one. we expect
#   to see signal indicator packets from both BRG's, according to the tx params.
#   phase 5 - One BRG will be configured as signal indicator tx, but no rx, so we don't expect to receive signal indicatopr packets.
#   that way we can assure the logic within the receiver is not confused by the signal indicator uuid as external sensor.


# Test MACROS #
NUM_OF_SCANNING_CYCLE = 5
DEFAULT_SCAN_TIME = 30
SCAN_DELAY_TIME = 3


def test_rssi_threshold(test):
    cycle, rep = 5, 4
    dut = cert_config.get_brg_by_target(test, DUT)
    tester = cert_config.get_brg_by_target(test, TESTER)
    rssi_threshold = -25

    # configuring receiver #
    utPrint(f"Configuring DUT BRG {dut.id_str} as Signal Indicator Receiver with RSSI Threshold of {rssi_threshold}", "BOLD")
    test = cert_config.brg_configure(test=test, module=dut.sensors,
                                     fields=[BRG_SENSOR0, BRG_RSSI_THRESHOLD],
                                     values=[ag.EXTERNAL_SENSORS_SIGNAL_INDICATOR, rssi_threshold])[0]
    if test.rc == TEST_FAILED:
        test.add_reason(f"BRG {dut.id_str}: didn't receive signal indicator receiver configuration!")
        return test
    # configuring tester as a transmitter #
    utPrint(f"Configuring TESTER BRG {tester.id_str} as Signal Indicator Transmitter", "BOLD")
    test = cert_config.brg_configure(test=test, module=tester.energy2400, fields=[BRG_SIGNAL_INDICATOR_CYCLE, BRG_SIGNAL_INDICATOR_REP],
                                     values=[cycle, rep], target=TESTER)[0]
    if test.rc == TEST_FAILED:
        test.add_reason(f"BRG {tester.id_str}: didn't receive signal indicator transmitter configuration!")
        return test
    utPrint(f"BRG {tester.id_str} configured to be transmitter - cycle = {cycle} repetition = {rep}", "BOLD")
    # phase analysis #
    cert_mqtt.mqtt_scan_n_create_log_file(test, (NUM_OF_SCANNING_CYCLE * cycle) + SCAN_DELAY_TIME, "rssi_threshold")
    rec_sig_ind_pkts = cert_common.get_all_sig_ind_pkts(test=test, rx_brg=dut, tx_brg=tester)
    for p in rec_sig_ind_pkts:
        print(f"rssi value: {p[UNIFIED_SENSOR_PKT].pkt.rssi}")
    rssi_threshold_viloation_pkts = [p for p in rec_sig_ind_pkts if p[UNIFIED_SENSOR_PKT].pkt.rssi >= -1 * rssi_threshold]
    if rssi_threshold_viloation_pkts:
        test.rc = TEST_FAILED
        test.add_reason(f"rssi_threshold phase failed - BRG {dut.id_str} echoed"
                        f" {len(rssi_threshold_viloation_pkts)} signal indicator packets\n with RSSI weaker than {rssi_threshold}")
    return test


def test_rx(test):

    dut = cert_config.get_brg_by_target(test, DUT)
    tester = cert_config.get_brg_by_target(test, TESTER)
    cycle, rep = 8, 4

    utPrint(f"TESTER BRG with cycle = {cycle}, repetition = {rep}\n", "BLUE")
    # configuring receiver #
    utPrint(f"Configuring DUT BRG {dut.id_str} as Signal Indicator Receiver", "BOLD")
    test = cert_config.brg_configure(test=test, module=dut.sensors, fields=[BRG_SENSOR0],
                                     values=[ag.EXTERNAL_SENSORS_SIGNAL_INDICATOR], target=DUT)[0]
    if test.rc == TEST_FAILED:
        test.add_reason(f"BRG {dut.id_str}: didn't receive signal indicator receiver configuration!")
        return test
    # configuring transmitter #
    utPrint(f"Configuring TESTER BRG {tester.id_str} as Signal Indicator Transmitter", "BOLD")
    test = cert_config.brg_configure(test=test, module=tester.energy2400,
                                     fields=[BRG_SIGNAL_INDICATOR_CYCLE, BRG_SIGNAL_INDICATOR_REP],
                                     values=[cycle, rep], target=TESTER)[0]
    if test.rc == TEST_FAILED:
        test.add_reason(f"BRG {tester.id_str}: didn't receive signal indicator transmitter configuration!")
        return test
    utPrint(f"TESTER {tester.id_str} configured to be transmitter - cycle={cycle}, repetition={rep}", "BOLD")

    # phase analysis #
    cert_mqtt.mqtt_scan_n_create_log_file(test, (NUM_OF_SCANNING_CYCLE * cycle) + SCAN_DELAY_TIME, f"rx_{cycle}_{rep}")
    rec_sig_ind_pkts = cert_common.get_all_sig_ind_pkts(test=test, rx_brg=dut, tx_brg=tester)
    if cert_common.sig_ind_pkts_fail_analysis(tx_brg=tester, rx_brg=dut, cycles=NUM_OF_SCANNING_CYCLE, received_pkts=rec_sig_ind_pkts):
        test.rc = TEST_FAILED
        expected_signal_ind_pkts = cert_common.exp_sig_ind_pkts2(tx_brg=tester, rx_brg=dut, cycles=NUM_OF_SCANNING_CYCLE)
        test.add_reason(f"rx phase failed - BRG {dut.id_str} received wrong number of "
                        f"signal indicator packets\nreceived {len(rec_sig_ind_pkts)} packets, "
                        f"expected {expected_signal_ind_pkts} packets")
        print(rec_sig_ind_pkts)  # TODO: logging print(debug)
        print([[p[TIMESTAMP], p[UNIFIED_SENSOR_PKT].pkt.signal_indicator_payload.rx_antenna] for p in rec_sig_ind_pkts])

    test = cert_common.rx_tx_antenna_check(test, rec_sig_ind_pkts, tester, dut, NUM_OF_SCANNING_CYCLE)
    test = cert_common.output_power_check(test, rec_sig_ind_pkts, tester)
    test = cert_common.rssi_check(test, rec_sig_ind_pkts)

    return test


def test_tx_eu_pattern(test):

    dut = cert_config.get_brg_by_target(test, DUT)
    tester = cert_config.get_brg_by_target(test, TESTER)
    cycle, rep = 8, 4

    utPrint(f"TESTER BRG - cycle = {cycle}, repetition = {rep}, Using EU pattern\n", "BLUE")
    # configuring EU Pattern #
    utPrint(f"Configuring DUT BRG {dut.id_str} to EU pattern", "BOLD")
    test = cert_config.brg_configure(test=test, module=dut.datapath,
                                     fields=[BRG_PATTERN],
                                     values=[ag.DATAPATH_PATTERN_EU_PATTERN], target=DUT)[0]
    if test.rc == TEST_FAILED:
        test.add_reason(f"DUT BRG {dut.id_str}: didn't receive signal indicator receiver configuration!")
        return test
    # configuring transmitter #
    utPrint(f"Configuring DUT BRG {dut.id_str} as Signal Indicator Transmitter", "BOLD")
    test = cert_config.brg_configure(test=test, module=dut.energy2400,
                                     fields=[BRG_SIGNAL_INDICATOR_CYCLE, BRG_SIGNAL_INDICATOR_REP],
                                     values=[cycle, rep], target=DUT)[0]
    if test.rc == TEST_FAILED:
        test.add_reason(f"DUT BRG {dut.id_str}: didn't receive signal indicator transmitter configuration!")
        return test
    utPrint(f"DUT BRG {dut.id_str} configured to be transmitter - cycle = {cycle},repetition = {rep}", "BOLD")
    # configuring receiver #
    utPrint(f"Configuring TESTER BRG {tester.id_str} as Signal Indicator Receiver", "BOLD")
    test = cert_config.brg_configure(test=test, module=tester.sensors, fields=[BRG_SENSOR0],
                                     values=[ag.EXTERNAL_SENSORS_SIGNAL_INDICATOR], target=TESTER)[0]
    if test.rc == TEST_FAILED:
        test.add_reason(f"TESTER BRG {tester.id_str}: didn't receive signal indicator receiver configuration!")
        return test
    # configuring receiver to rx channel 37 #
    utPrint(f"Configuring TESTER BRG {tester.id_str} to scan channel 37", "BOLD")
    test = cert_config.brg_configure(test=test, module=tester.datapath, fields=[BRG_RX_CHANNEL],
                                     values=[ag.RX_CHANNEL_37], target=TESTER)[0]
    if test.rc == TEST_FAILED:
        test.add_reason(f"TESTER BRG {tester.id_str}: didn't receive rx channel 37 configuration!")
        return test

    # phase analysis #
    cert_mqtt.mqtt_scan_n_create_log_file(test, (NUM_OF_SCANNING_CYCLE * cycle) + SCAN_DELAY_TIME,
                                          f"tx_eu_pattern_{cycle}_{rep}")
    rec_sig_ind_pkts = cert_common.get_all_sig_ind_pkts(test=test, rx_brg=tester, tx_brg=dut)
    if cert_common.sig_ind_pkts_fail_analysis(tx_brg=dut, rx_brg=tester, cycles=NUM_OF_SCANNING_CYCLE, received_pkts=rec_sig_ind_pkts):
        test.rc = TEST_FAILED
        expected_signal_ind_pkts = cert_common.exp_sig_ind_pkts2(tester, dut, NUM_OF_SCANNING_CYCLE)
        test.add_reason(f"tx_eu_pattern phase failed - BRG {dut.id_str} received wrong number of "
                        f"signal indicator packets\nreceived {len(rec_sig_ind_pkts)} packets, "
                        f"expected {expected_signal_ind_pkts} packets")
        print(rec_sig_ind_pkts)  # TODO: logging print(debug)
        print([[p[TIMESTAMP], p[UNIFIED_SENSOR_PKT].pkt.signal_indicator_payload.rx_antenna] for p in rec_sig_ind_pkts])

    test = cert_config.config_brg_defaults(test, modules=[tester.datapath], target=TESTER)[0]
    if test.rc == TEST_FAILED:
        test.add_reason("Failed to restore tester to defaults for module Datapath")

    test = cert_common.rx_tx_antenna_check(test, rec_sig_ind_pkts, dut, tester, NUM_OF_SCANNING_CYCLE)
    test = cert_common.output_power_check(test, rec_sig_ind_pkts, dut)
    test = cert_common.rssi_check(test, rec_sig_ind_pkts)

    return test


def test_disable_tx(test):
    cycle, rep = ag.BRG_DEFAULT_SIGNAL_INDICATOR_CYCLE, ag.BRG_DEFAULT_SIGNAL_INDICATOR_REP
    tester = cert_config.get_brg_by_target(test, TESTER)
    dut = cert_config.get_brg_by_target(test, DUT)
    utPrint(f"DUT BRG with TX disabled - cycle = {cycle}, repetition = {rep}\n", "BLUE")
    # configuring tester as a receiver #
    utPrint(f"Configuring TESTER BRG {tester.id_str} as Signal Indicator Receiver", "BOLD")
    test = cert_config.brg_configure(test=test, module=tester.sensors,
                                     fields=[BRG_SENSOR0],
                                     values=[ag.EXTERNAL_SENSORS_SIGNAL_INDICATOR],
                                     target=TESTER)[0]
    if test.rc == TEST_FAILED:
        test.add_reason(f"BRG {tester.id_str}: didn't receive signal indicator receiver configuration!")
        return test
    utPrint(f"TESTER BRG {tester.id_str} successfully configured as Signal Indicator Receiver\n", "BOLD")

    # phase analysis #
    cert_mqtt.mqtt_scan_n_create_log_file(test, DEFAULT_SCAN_TIME, "disable_tx")
    expected_signal_ind_pkts = [0]
    rec_sig_ind_pkts = cert_common.get_all_sig_ind_pkts(test=test, rx_brg=tester, tx_brg=dut)
    if len(rec_sig_ind_pkts) not in expected_signal_ind_pkts:
        test.rc = TEST_FAILED
        test.add_reason(f"disable_tx phase failed - DUT BRG {dut.id_str} sent signal indicator packets\n"
                        f"received {len(rec_sig_ind_pkts)} packets, "
                        f"expected {expected_signal_ind_pkts} packets")

    return test


def test_disable_rx(test):
    # DUT BRG without rx. just waiting for packets to be sent from the transmitter and verify
    # The receiver does not receive any signal indicator packets.
    cycle, rep = 4, 3
    dut = cert_config.get_brg_by_target(test, DUT)
    tester = cert_config.get_brg_by_target(test, TESTER)
    utPrint("DUT BRG with RX disabled\n", "BLUE")
    # configuring transmitter #
    utPrint(f"Configuring TESTER BRG {tester.id_str} as Signal Indicator Transmitter", "BOLD")
    test = cert_config.brg_configure(test=test, module=tester.energy2400,
                                     fields=[BRG_SIGNAL_INDICATOR_CYCLE, BRG_SIGNAL_INDICATOR_REP],
                                     values=[cycle, rep], target=TESTER)[0]
    if test.rc == TEST_FAILED:
        test.add_reason(f"TESTER BRG {tester.id_str}: didn't receive signal indicator transmitter configuration!")
        return test

    # phase analysis #
    cert_mqtt.mqtt_scan_n_create_log_file(test, (NUM_OF_SCANNING_CYCLE * cycle) + SCAN_DELAY_TIME, "disable_rx")
    expected_signal_ind_pkts = [0]
    rec_sig_ind_pkts = cert_common.get_all_sig_ind_pkts(test=test, rx_brg=dut, tx_brg=tester)
    if len(rec_sig_ind_pkts) not in expected_signal_ind_pkts:
        test.rc = TEST_FAILED
        test.add_reason(f"disable_rx phase failed - DUT {dut.id_str} received signal indicator packets\n"
                        f"received {len(rec_sig_ind_pkts)} packets, expected 0 packets")

    return test


def test_rx_tx(test):
    tx_cycle, tx_rep = 5, 4
    rx_cycle, rx_rep = 5, 4
    dut = cert_config.get_brg_by_target(test, DUT)
    tester = cert_config.get_brg_by_target(test, TESTER)
    utPrint("Both TESTER and DUT are transmitters and receivers\n", "BLUE")
    # configuring dut brg as receiver
    utPrint(f"Configuring DUT BRG {dut.id_str} as Signal Indicator Receiver", "BOLD")
    test = cert_config.brg_configure(test=test, module=dut.sensors, fields=[BRG_SENSOR0],
                                     values=[ag.EXTERNAL_SENSORS_SIGNAL_INDICATOR])[0]
    if test.rc == TEST_FAILED and test.exit_on_param_failure:
        test.add_reason(f"BRG {dut.id_str}: didn't receive signal indicator receiver configuration!")
        return test
    utPrint(f"BRG {dut.id_str} successfully configured as Signal Indicator Receiver\n", "BOLD")
    # configuring dut brg as transmitter
    utPrint(f"Configuring DUT BRG {dut.id_str} as Signal Indicator Transmitter", "BOLD")
    test = cert_config.brg_configure(test=test, module=dut.energy2400, fields=[BRG_SIGNAL_INDICATOR_CYCLE, BRG_SIGNAL_INDICATOR_REP],
                                     values=[tx_cycle, tx_rep])[0]
    if test.rc == TEST_FAILED and test.exit_on_param_failure:
        test.add_reason(f"BRG {dut.id_str}: didn't receive signal indicator transmitter configuration!")
        return test
    utPrint(f"BRG {dut.id_str} configured to be transmitter - cycle={tx_cycle}, repetition={tx_rep}", "BOLD")

    # configuring tester brg as receiver
    utPrint(f"Configuring TESTER BRG {tester.id_str} as Signal Indicator Receiver", "BOLD")
    test = cert_config.brg_configure(test=test, module=tester.sensors,
                                     fields=[BRG_SENSOR0],
                                     values=[ag.EXTERNAL_SENSORS_SIGNAL_INDICATOR],
                                     target=TESTER)[0]
    if test.rc == TEST_FAILED and test.exit_on_param_failure:
        test.add_reason(f"BRG {tester.id_str}: didn't receive signal indicator receiver configuration!")
        return test
    utPrint(f"BRG {tester.id_str} successfully configured as Signal Indicator Receiver\n", "BOLD")

    # configuring tester brg as transmitter (already configured as rx)
    utPrint(f"Configuring TESTER BRG {tester.id_str} as Signal Indicator Transmitter", "BOLD")
    test = cert_config.brg_configure(test=test, module=tester.energy2400,
                                     fields=[BRG_SIGNAL_INDICATOR_CYCLE, BRG_SIGNAL_INDICATOR_REP],
                                     values=[rx_cycle, rx_rep],
                                     target=TESTER)[0]
    if test.rc == TEST_FAILED and test.exit_on_param_failure:
        test.add_reason(f"BRG {tester.id_str}: didn't receive signal indicator transmitter configuration!")
        return test
    utPrint(f"BRG {tester.id_str} configured to be transmitter - cycle={rx_cycle}, repetition={rx_rep}")

    # phase analysis #
    cert_mqtt.mqtt_scan_n_create_log_file(test, NUM_OF_SCANNING_CYCLE * max(tx_cycle, rx_cycle) + SCAN_DELAY_TIME, "rx_tx")

    # Analyzing dut performance as receiver
    utPrint(f"Analyzing DUT {dut.id_str} performance as a Receiver\n", "BOLD")
    rec_sig_ind_pkts = cert_common.get_all_sig_ind_pkts(test=test, rx_brg=dut, tx_brg=tester)
    if cert_common.sig_ind_pkts_fail_analysis(tx_brg=tester, rx_brg=dut, cycles=NUM_OF_SCANNING_CYCLE, received_pkts=rec_sig_ind_pkts):
        test.rc = TEST_FAILED
        expected_signal_ind_pkts = cert_common.exp_sig_ind_pkts2(dut, tester, NUM_OF_SCANNING_CYCLE)
        test.add_reason(f"rx_tx phase failed - BRG {dut.id_str} received wrong number of "
                        f"signal indicator packets\nreceived {len(rec_sig_ind_pkts)} packets, "
                        f"expected {expected_signal_ind_pkts} packets")
        print(rec_sig_ind_pkts)  # TODO: logging print(debug)

    # Analyzing tester performance as receiver
    utPrint(f"Analyzing DUT {dut.id_str} performance as a Transmitter\n", "BOLD")
    rec_sig_ind_pkts = cert_common.get_all_sig_ind_pkts(test=test, rx_brg=tester, tx_brg=dut)
    if cert_common.sig_ind_pkts_fail_analysis(tx_brg=dut, rx_brg=tester, cycles=NUM_OF_SCANNING_CYCLE, received_pkts=rec_sig_ind_pkts):
        test.rc = TEST_FAILED
        expected_signal_ind_pkts = cert_common.exp_sig_ind_pkts2(dut, tester, NUM_OF_SCANNING_CYCLE)
        test.add_reason(f"rx_tx phase failed - BRG {tester.id_str} received wrong number of "
                        f"signal indicator packets\n received {len(rec_sig_ind_pkts)} packets, "
                        f"expected {expected_signal_ind_pkts} packets")
        print(rec_sig_ind_pkts)  # TODO: logging print(debug)
    # NOTE: We skipped the antenna and output power checks for this phase
    return test


SIGNAL_INDICATOR_TEST_MAP = {"rssi_threshold": test_rssi_threshold, "rx": test_rx,
                             "tx_eu_pattern": test_tx_eu_pattern,
                             "disable_tx": test_disable_tx, "rx_tx": test_rx_tx,
                             "disable_rx": test_disable_rx}


def run(test):
    # Test prolog
    test = cert_common.test_prolog(test)
    brg_dut = cert_config.get_brg_by_target(test, DUT)
    brg_tester = cert_config.get_brg_by_target(test, TESTER)

    for param in test.params:
        phase_run_print(param.name)
        test = SIGNAL_INDICATOR_TEST_MAP[param.value](test)
        cert_mqtt.generate_log_file(test, param.name)
        field_functionality_pass_fail_print(test, param.name)
        test.set_phase_rc(param.name, test.rc)
        test.add_phase_reason(param.name, test.reason)
        if test.rc == TEST_FAILED:
            if test.exit_on_param_failure:
                break  # break the whole for loop and keep the test as failed
            else:
                test.reset_result()  # reset result and continue to next param
                continue

        # Reset to defaults after every phase (don't fail the phase on that)
        test = cert_config.config_brg_defaults(test, modules=[brg_dut.energy2400, brg_dut.sensors], target=DUT)[0]
        if test.rc == TEST_FAILED:
            test.add_reason("Failed to restore brg0 to defaults")
        else:
            test = cert_config.config_brg_defaults(test,
                                                   modules=[brg_tester.energy2400, brg_tester.sensors],
                                                   target=TESTER)[0]
            if test.rc == TEST_FAILED:
                test.add_reason("Failed to restore brg1 to defaults")
        if test.rc == TEST_FAILED:
            test.set_phase_rc(param.name, test.rc)
            test.add_phase_reason(param.name, test.reason)
            if test.exit_on_param_failure:
                break
        else:
            test.reset_result()

    return cert_common.test_epilog(test, revert_brgs=True,
                                   modules=[brg_dut.energy2400, brg_dut.sensors],
                                   brg1_modules=[brg_tester.energy2400, brg_tester.sensors])
