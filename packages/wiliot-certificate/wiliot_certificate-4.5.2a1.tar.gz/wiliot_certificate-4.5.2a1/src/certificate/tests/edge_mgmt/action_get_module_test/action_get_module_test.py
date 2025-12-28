from certificate.cert_prints import *
from certificate.cert_defines import *
from certificate.wlt_types import *
import certificate.cert_mqtt as cert_mqtt
import certificate.cert_common as cert_common
import certificate.cert_config as cert_config


def run(test):
    test = cert_common.test_prolog(test)
    if test.rc == TEST_FAILED:
        return cert_common.test_epilog(test)

    if test.active_brg.board_type in POF_NOT_SUPPORTING_BOARD_TYPES:
        test.rc = TEST_SKIPPED
        return cert_common.test_epilog(test)
    functionality_run_print("action_get_module")

    # CHECK ONLY FOR ONE MODULE (ModuleDatapath) #
    # send action
    print("\nCHECK ONLY FOR ModuleDatapath\n")
    cert_config.send_brg_action(test, ag.ACTION_GET_MODULE, datapath=1)
    # analysis
    test = cert_common.search_action_ack(test, ag.ACTION_GET_MODULE, datapath=1)
    test = cert_common.scan_for_modules(test, [test.active_brg.datapath])
    if test.rc == TEST_FAILED:
        return cert_common.test_epilog(test)

    # CHECK FOR ALL MODULES AT ONCE #
    # send action
    print("\nCHECK FOR ALL MODULES AT ONCE\n")
    cert_config.send_brg_action(test, ag.ACTION_GET_MODULE, interface=1, datapath=1, energy2400=1,
                                energy_sub1g=1, calibration=1, pwr_mgmt=1, ext_sensors=1, custom=1)
    # analysis
    test = cert_common.search_action_ack(test, ag.ACTION_GET_MODULE, interface=1, datapath=1, energy2400=1,
                                         energy_sub1g=1, calibration=1, pwr_mgmt=1, ext_sensors=1, custom=1)
    test = cert_common.scan_for_modules(test)

    cert_mqtt.generate_log_file(test, "action_get_module")
    field_functionality_pass_fail_print(test, "action_get_module")

    return cert_common.test_epilog(test)
