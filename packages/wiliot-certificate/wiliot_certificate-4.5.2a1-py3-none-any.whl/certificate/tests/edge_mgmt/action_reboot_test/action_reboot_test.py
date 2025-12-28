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

    functionality_run_print("action_reboot")

    # configure tester to listen to ch39 so we can receieve euro pattern packets
    test = cert_config.brg_configure(test, fields=[BRG_RX_CHANNEL], values=[ag.RX_CHANNEL_39],
                                     module=test.tester.internal_brg.datapath,
                                     target=TESTER)[0]
    if test.rc == TEST_FAILED:
        return cert_common.test_epilog(test)
    # non-default cfg
    test = cert_common.brg_non_default_modules_cfg(test)
    if test.rc == TEST_FAILED and test.exit_on_param_failure:
        return cert_common.test_epilog(test, revert_brgs=True)
    # sample non-default cfg_hash
    test, non_default_hash = cert_common.get_cfg_hash(test)
    if test.active_brg.cfg_hash == non_default_hash:
        test.rc = TEST_FAILED
        test.add_reason(f"Config failed default_hash==non_default==0x{non_default_hash:08X}")
    if test.rc == TEST_FAILED:
        return cert_common.test_epilog(test)
    print(f"\nnon_default_hash: 0x{non_default_hash:08X}\n")
    # send action
    cert_config.send_brg_action(test, ag.ACTION_REBOOT)
    # analysis
    test = cert_common.reboot_config_analysis(test, expected_hash=non_default_hash, timeout=40)
    # epilog
    test = cert_config.config_brg_defaults(test)[0]
    if test.rc == TEST_FAILED:
        return cert_common.test_epilog(test)

    # configure tester to listen to default channel again
    test = cert_config.brg_configure(test, module=test.tester.internal_brg.datapath, target=TESTER)[0]

    cert_mqtt.generate_log_file(test, "action_reboot")
    field_functionality_pass_fail_print(test, "action_reboot")

    return cert_common.test_epilog(test)
