from certificate.cert_prints import *
from certificate.cert_defines import *
from certificate.wlt_types import *
import certificate.cert_mqtt as cert_mqtt
import certificate.cert_common as cert_common
import certificate.cert_config as cert_config


def run(test):

    fields = [BRG_OUTPUT_POWER]
    datapath_module = test.active_brg.datapath

    test = cert_common.test_prolog(test)
    if test.rc == TEST_FAILED:
        return cert_common.test_epilog(test)

    for param in test.params:
        if not cert_common.output_power_supported(test.active_brg.board_type, param.value):
            # Skip this parameter if its value isn't supported by the board
            test.rc = TEST_SKIPPED
            cert_mqtt.generate_log_file(test, param.name)
            field_functionality_pass_fail_print(test, fields[0], value=param.name)
            test.set_phase_rc(param.name, test.rc)
            test.add_phase_reason(param.name, test.reason)
            test.reset_result()  # reset result and continue to next param
            continue

        test = cert_config.brg_configure(test, fields=fields, values=[param.value], module=datapath_module)[0]
        cert_mqtt.generate_log_file(test, param.name)
        field_functionality_pass_fail_print(test, fields[0], value=param.name)
        test.set_phase_rc(param.name, test.rc)
        test.add_phase_reason(param.name, test.reason)
        if test.rc == TEST_FAILED:
            if test.exit_on_param_failure:
                break  # break the whole for loop and keep the test as failed
        test.reset_result()  # reset result and continue to next param

    return cert_common.test_epilog(test, revert_brgs=True, modules=[datapath_module])
