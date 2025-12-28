from certificate.cert_prints import *
from certificate.cert_defines import *
from certificate.wlt_types import *
import certificate.cert_mqtt as cert_mqtt
import certificate.cert_common as cert_common
import certificate.cert_config as cert_config

NEW_TAG_EVENT_SCAN_TIME = 100             # in seconds
TAG_EVENT_SCAN_TIME = 60                 # in seconds
RSSI_MOVEMENT_THRESHOLD = 15


def test_new_tag_event_minutes(test, phase, datapath_module):
    values = [ag.EVENT_TIME_UNIT_MINUTES, TEST_EVENT_WINDOW_MIN_CFG, ag.RX_CHANNEL_37, ag.EVENT_TRIGGER_NEW_TAG, 0]
    return cert_common.run_event_test_phase(test, phase, datapath_module, values, NEW_TAG_EVENT_SCAN_TIME, ag.EVENT_TIME_UNIT_MINUTES)


# In seconds phase we also test the dynamic pacer interval
def test_new_tag_event_seconds(test, phase, datapath_module):
    values = [ag.EVENT_TIME_UNIT_SECONDS, TEST_EVENT_WINDOW_SEC_CFG, ag.RX_CHANNEL_37, ag.EVENT_TRIGGER_NEW_TAG,
              DATA_SIM_EVENT_PACER_INTERVAL_TESTING]
    return cert_common.run_event_test_phase(test, phase, datapath_module, values, NEW_TAG_EVENT_SCAN_TIME, ag.EVENT_TIME_UNIT_SECONDS)


def test_temp_event(test, phase, datapath_module):
    values = [ag.EVENT_TIME_UNIT_SECONDS, TEST_TAG_EVENT_WINDOW_CFG, ag.RX_CHANNEL_37, ag.EVENT_TRIGGER_TEMP_CHANGE, 0]
    return cert_common.run_event_test_phase(test, phase, datapath_module, values, TAG_EVENT_SCAN_TIME, ag.EVENT_TIME_UNIT_SECONDS)


def test_tx_rate_event(test, phase, datapath_module):
    values = [ag.EVENT_TIME_UNIT_SECONDS, TEST_TAG_EVENT_WINDOW_CFG, ag.RX_CHANNEL_37, ag.EVENT_TRIGGER_TX_RATE_CHANGE, 0]
    return cert_common.run_event_test_phase(test, phase, datapath_module, values, TAG_EVENT_SCAN_TIME, ag.EVENT_TIME_UNIT_SECONDS)


def test_rssi_event(test, phase, datapath_module):
    values = [ag.EVENT_TIME_UNIT_SECONDS, TEST_TAG_EVENT_WINDOW_CFG, ag.RX_CHANNEL_37, ag.EVENT_TRIGGER_RSSI_CHANGE, 0,
              RSSI_MOVEMENT_THRESHOLD]
    return cert_common.run_event_test_phase(test, phase, datapath_module, values, TAG_EVENT_SCAN_TIME, ag.EVENT_TIME_UNIT_SECONDS)


EVENT_TEST_MAP = {"rssi_event": test_rssi_event, "new_tag_event_seconds": test_new_tag_event_seconds,
                  "new_tag_event_minutes": test_new_tag_event_minutes,
                  "temp_event": test_temp_event, "tx_rate_event": test_tx_rate_event}


def run(test):
    # Test prolog
    test = cert_common.test_prolog(test)
    if test.rc == TEST_FAILED:
        return cert_common.test_epilog(test)
    dut = cert_config.get_brg_by_target(test, DUT)

    for param in test.params:
        phase_run_print(param.name)
        test = EVENT_TEST_MAP[param.value](test, param.name, dut.datapath)
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
        test = cert_config.config_brg_defaults(test, modules=[dut.datapath])[0]
        if test.rc == TEST_FAILED:
            test.add_reason("Failed to restore brg to defaults")

        if test.rc == TEST_FAILED:
            test.set_phase_rc(param.name, test.rc)
            test.add_phase_reason(param.name, test.reason)
            if test.exit_on_param_failure:
                break
        else:
            test.reset_result()

    return cert_common.test_epilog(test, revert_brgs=True, modules=[dut.datapath])
