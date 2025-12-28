
from certificate.cert_prints import *
from certificate.cert_defines import *
from certificate.wlt_types import *
from certificate.cert_utils import TESTER_FW_VERSIONS
import certificate.cert_gw_sim as cert_gw_sim
import certificate.cert_common as cert_common
import certificate.cert_config as cert_config
import certificate.cert_mqtt as cert_mqtt

BRG_OTA_HIGH_TIMEOUT = (60 * 10)


def run(test):
    test = cert_common.test_prolog(test)
    if test.rc == TEST_FAILED:
        return cert_common.test_epilog(test)

    phase_run_print("BRG OTA started")
    utPrint("Important: For the gateway to be able to download the file, it must use a valid token in the HTTP GET request.", "WARNING")
    utPrint("Meaning It must be registered under an owner, and the certificate '-env' should correspond to that owner.", "WARNING")
    test.flush_all_mqtt_packets()
    target_brg = test.tester.internal_brg
    desired_ver = TESTER_FW_VERSIONS[0] if target_brg.version != TESTER_FW_VERSIONS[0] else TESTER_FW_VERSIONS[1]

    # Initiate action
    utPrint(f"Publishing OTA action to DUT: {test.dut.mqttc.update_topic}. Awaiting OTA.. (timeout is {BRG_OTA_HIGH_TIMEOUT} seconds)")
    # Set active_brg to be the tester, for reboot_config_analysis within brg_ota
    test.active_brg = target_brg
    test = cert_config.brg_ota(test, ble_version=desired_ver, search_ack=True, target=TESTER, upgrader=DUT, timeout=BRG_OTA_HIGH_TIMEOUT)

    # Stop advertising on tester in case it just rebooted after getting OTA. So it is ready for next tests
    cert_config.gw_action(test, cert_gw_sim.STOP_ADVERTISING, target=TESTER)

    cert_mqtt.generate_log_file(test, "brg_ota")

    if test.rc == TEST_PASSED and cert_gw_sim.GW_SIM_RESET_TS is not None:
        reboot_pkt_time = int((cert_gw_sim.GW_SIM_RESET_TS - test.start_time).total_seconds())
        test.reason = f"Reboot pkt received after {reboot_pkt_time} seconds"

    return cert_common.test_epilog(test)
