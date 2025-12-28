import datetime

from certificate.cert_prints import *
from certificate.cert_defines import *
from certificate.wlt_types import *
import certificate.cert_common as cert_common
import certificate.cert_config as cert_config
import certificate.cert_mqtt as cert_mqtt
from common.api_if.api_validation import api_validation


# DEFINES
TIMEOUT_IN_MINUTES = 3


def run(test):
    test = cert_common.test_prolog(test)
    if test.rc == TEST_FAILED:
        return cert_common.test_epilog(test)

    # Stage setup
    phase_run_print("Reboot started")

    # Initiate action
    dut_mqttc = test.get_mqttc_by_target(DUT)
    utPrint(f"Publishing reboot action to {dut_mqttc.update_topic}. Awaiting reboot.. (timeout is {TIMEOUT_IN_MINUTES} minutes)")
    cert_config.gw_action(test, f"{REBOOT_GW_ACTION}", target=DUT)
    dut_mqttc.flush_pkts()

    # Wait for response
    gw_type = None
    utPrint(f'Waiting for GW to connect... (Timeout {TIMEOUT_IN_MINUTES} minutes)')
    timeout = datetime.datetime.now() + datetime.timedelta(minutes=TIMEOUT_IN_MINUTES)
    while datetime.datetime.now() < timeout:
        gw_type, msg = cert_common.get_gw_type(dut_mqttc)
        gw_api_version = cert_common.get_gw_api_version(dut_mqttc)
        if gw_type is not None:
            break
        print_update_wait(5)
    test.dut.gw_api_version = gw_api_version

    # generate logs
    cert_mqtt.generate_log_file(test, "reboot")

    # Analyze results
    if gw_type is None:
        test.rc = TEST_FAILED
        test.reason = "The gateway did not reboot properly, status message was not received"
    elif gw_type == "other":
        test.rc = TEST_FAILED
        test.reason = f"gatewayType must be defined in the status message {msg}"
    else:
        utPrint("Gateway rebooted and uploaded a configuration message as expected.", "GREEN")
        utPrint(f"The configuration message received:\n {msg}")

    utPrint("Checking the status message matches API format...")
    test = api_validation(test)

    return cert_common.test_epilog(test)
