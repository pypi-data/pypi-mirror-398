from certificate.cert_prints import *
from certificate.cert_defines import *
from certificate.wlt_types import *
import certificate.cert_mqtt as cert_mqtt
import certificate.cert_common as cert_common
import certificate.cert_config as cert_config


def run(test):

    fields = [BRG_PATTERN]
    datapath_module = test.active_brg.datapath

    test = cert_common.test_prolog(test)
    if test.rc == TEST_FAILED:
        return cert_common.test_epilog(test)

    # configure tester to listen to ch39 so we can receive 38-38-39 and euro pattern packets
    test = cert_config.brg_configure(test, fields=[BRG_RX_CHANNEL], values=[ag.RX_CHANNEL_39],
                                     module=test.tester.internal_brg.datapath,
                                     target=TESTER)[0]
    if test.rc == TEST_FAILED:
        return cert_common.test_epilog(test)

    for param in test.params:
        # Set brg cfg
        test = cert_config.brg_configure(test, fields=fields, values=[param.value], module=datapath_module)[0]
        cert_mqtt.generate_log_file(test, param.name)
        field_functionality_pass_fail_print(test, fields[0], value=param.name)
        test.set_phase_rc(param.name, test.rc)
        test.add_phase_reason(param.name, test.reason)
        if test.rc == TEST_FAILED:
            if test.exit_on_param_failure:
                break  # break the whole for loop and keep the test as failed
        test.reset_result()  # reset result and continue to next param

    # configure tester to listen to default channel again
    test = cert_config.brg_configure(test, module=test.tester.internal_brg.datapath, target=TESTER)[0]

    return cert_common.test_epilog(test, revert_brgs=True, modules=[datapath_module])
