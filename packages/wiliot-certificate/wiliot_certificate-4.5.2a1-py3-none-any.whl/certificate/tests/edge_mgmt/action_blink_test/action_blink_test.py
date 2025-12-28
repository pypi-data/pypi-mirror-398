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

    functionality_run_print("action_blink")

    # send action
    cert_config.send_brg_action(test, ag.ACTION_BLINK)
    # analysis
    test = cert_common.search_action_ack(test, ag.ACTION_BLINK)

    cert_mqtt.generate_log_file(test, "action_blink")
    field_functionality_pass_fail_print(test, "action_blink")

    return cert_common.test_epilog(test)
