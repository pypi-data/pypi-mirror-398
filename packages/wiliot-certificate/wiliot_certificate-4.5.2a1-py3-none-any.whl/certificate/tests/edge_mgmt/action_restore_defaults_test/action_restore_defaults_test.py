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

    functionality_run_print("action_restore_defaults")

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
    if test.rc == TEST_FAILED:
        # revert to defaults without restore_defaults action if action failed
        test = cert_config.config_brg_defaults(test)[0]
        return cert_common.test_epilog(test)
    # send action
    cert_config.send_brg_action(test, ag.ACTION_RESTORE_DEFAULTS)
    # analysis
    expected_hash = test.active_brg.cfg_hash
    utPrint("Analyzing Restore Defaults", "BLUE")
    # First 30 for wlt app start + 10 sec extra for brg to settle to recieve its get module action
    wait_time_n_print(40, txt="Analyzing Restore Defaults")

    start_time = datetime.datetime.now()
    seq_ids = []
    cfg_once = True
    test.get_mqttc_by_target(DUT).flush_pkts()

    utPrint(f"Get Interface Module from BRG {test.active_brg.id_str}")
    cert_config.send_brg_action(test, ag.ACTION_GET_MODULE, interface=1)
    test = cert_common.search_action_ack(test, ag.ACTION_GET_MODULE, interface=1)
    if test.rc == TEST_FAILED:
        return cert_common.test_epilog(test)

    while True:
        # scan for ModuleIf pkt of all api versions to support api version change on update
        mgmt_types = [eval_pkt(f'ModuleIfV{test.active_brg.api_version}')]
        pkts = cert_mqtt.get_brg2gw_mgmt_pkts(test.get_mqttc_by_target(DUT), test.active_brg, mgmt_types=mgmt_types)
        for p in pkts:
            if (not seq_ids or p[SEQUENCE_ID] not in seq_ids):
                seq_ids.append(p[SEQUENCE_ID])
                interface = p[MGMT_PKT].pkt
                if interface:
                    test.active_brg.api_version = interface.api_version
                    print(f"\nGot pkt after {(datetime.datetime.now() - start_time).seconds} sec!")
                    print(interface)
                    received_hash = interface.cfg_hash
                    print(f"\nexpected cfg_hash: 0x{expected_hash:08X}\n"
                          f"received cfg_hash: 0x{received_hash:08X}\n"
                          f"non_default_hash: 0x{non_default_hash:08X}")
                    if received_hash == non_default_hash:
                        # test.rc = TEST_FAILED
                        test.add_reason("received_hash is equal to non_default_hash, ACTION_RESTORE_DEFAULTS was not received by the brg!")
                        # return test
                    elif received_hash == expected_hash:
                        return cert_common.test_epilog(test)
                    else:
                        # Default SUB1G EP in the BRG is 0 and in the UT is 9
                        # in order to allign BRG cfg to the one after ut.py start script
                        # we should configure sub1g ep individually once after reboot in case cfg hash dont match
                        if ag.MODULE_ENERGY_SUB1G in test.active_brg.sup_caps and cfg_once:
                            cfg_once = False
                            cfg_pkt = cert_config.get_default_brg_pkt(test,
                                                                      test.active_brg.energy_sub1g,
                                                                      **{BRG_PATTERN: ag.SUB1G_ENERGY_PATTERN_ISRAEL})
                            test = cert_config.brg_configure(test, cfg_pkt=cfg_pkt)[0]
                            if test.rc == TEST_FAILED:
                                return cert_common.test_epilog(test)
                            cert_config.send_brg_action(test, ag.ACTION_GET_MODULE, interface=1)
        print_update_wait()

        if (datetime.datetime.now() - start_time).seconds > DEFAULT_BRG_FIELD_UPDATE_TIMEOUT:
            test.rc = TEST_FAILED
            test.add_reason(f"Didn't receive expected ModuleIfV{test.active_brg.api_version} pkt "
                            f"after {DEFAULT_BRG_FIELD_UPDATE_TIMEOUT} seconds!")
            # revert to defaults without restore_defaults action if action failed
            test = cert_config.config_brg_defaults(test)[0]
            break

    # configure tester to listen to default channel again
    test = cert_config.brg_configure(test, module=test.tester.internal_brg.datapath, target=TESTER)[0]

    cert_mqtt.generate_log_file(test, "action_restore_defaults")
    field_functionality_pass_fail_print(test, "action_restore_defaults")

    return cert_common.test_epilog(test)
