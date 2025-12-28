from certificate.cert_prints import *
from certificate.cert_defines import *
from certificate.wlt_types import *
import certificate.cert_mqtt as cert_mqtt
import certificate.cert_common as cert_common
import certificate.cert_config as cert_config


def is_primary_channel(channel):
    if channel == ag.RX_CHANNEL_37 or channel == ag.RX_CHANNEL_38 or channel == ag.RX_CHANNEL_39:
        return True
    else:
        return False


def run(test):

    fields = [BRG_RX_CHANNEL]
    print(test.params)
    datapath_module = test.active_brg.datapath

    # We use this flag to know whether the BRG is currently in BLE5 mode and needs special configuration next time it is configured
    ble5_state = False

    test = cert_common.test_prolog(test)
    if test.rc == TEST_FAILED:
        return cert_common.test_epilog(test)

    for param in test.params:
        if ble5_state:
            test = cert_config.brg_configure_ble5(test, fields=fields, values=[param.value], module=datapath_module)[0]
        else:
            test = cert_config.brg_configure(test, fields=fields, values=[param.value], module=datapath_module)[0]
        # param epilog
        ble5_state = not is_primary_channel(param.value)
        cert_mqtt.generate_log_file(test, param.name)
        field_functionality_pass_fail_print(test, fields[0], value=param.name)
        test.set_phase_rc(param.name, test.rc)
        test.add_phase_reason(param.name, test.reason)
        if test.rc == TEST_FAILED:
            if test.exit_on_param_failure:
                break  # break the whole for loop and keep the test as failed
        test.reset_result()  # reset result and continue to next param

    return cert_common.test_epilog(test, revert_brgs=True, modules=[datapath_module], ble5=ble5_state)
