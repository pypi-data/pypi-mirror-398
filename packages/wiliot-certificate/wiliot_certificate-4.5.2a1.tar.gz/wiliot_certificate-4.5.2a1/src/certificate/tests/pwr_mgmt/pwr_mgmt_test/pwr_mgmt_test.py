from certificate.cert_prints import *
from certificate.cert_defines import *
from certificate.wlt_types import *
import certificate.cert_common as cert_common
import certificate.cert_mqtt as cert_mqtt

# Test MACROS #
SEC_TO_MS = 1000
LOW_VALUE_IDX = 0
HIGH_VALUE_IDX = -1
STATIC_MODE = 0


# Test Functions #
def num_to_str(id):
    return str(id).zfill(2)


def get_expected_hb_sleep_msgs_count(pkt):
    # sent cfg is static_sleep_duration = 60, static_keep_alive_period = 20
    periods_ratio = int(pkt.static_sleep_duration / pkt.static_keep_alive_period)
    if not (pkt.static_sleep_duration % pkt.static_keep_alive_period):
        return [periods_ratio - 1, periods_ratio]
    else:
        return [periods_ratio, periods_ratio + 1]


def get_hb_sleep_pkts(test, start_ts, end_ts, target=DUT):
    mgmt_pkts_found = cert_mqtt.get_brg2gw_mgmt_pkts(test.get_mqttc_by_target(target), test.active_brg)
    # Screen pkts according to ts
    mgmt_pkts = [p for p in mgmt_pkts_found if (start_ts <= p[TIMESTAMP] and p[TIMESTAMP] <= end_ts)]
    # return count of HbSleep pkts
    return len([p for p in mgmt_pkts if isinstance(p[MGMT_PKT].pkt, eval_pkt(f'Brg2GwHbSleepV{test.active_brg.api_version}'))])


def brg_pwr_mgmt_sleep_state_analysis(test, wltpkt, start_ts, end_ts):
    utPrint("Analyzing HB Sleep pkts count", "HEADER")
    hb_sleep_pkts = get_hb_sleep_pkts(test, start_ts, end_ts)
    exp_hb_sleep_msgs = get_expected_hb_sleep_msgs_count(wltpkt.pkt)

    if (not hb_sleep_pkts or
            hb_sleep_pkts < exp_hb_sleep_msgs[LOW_VALUE_IDX] or
            hb_sleep_pkts > exp_hb_sleep_msgs[HIGH_VALUE_IDX]):
        test.rc = TEST_FAILED
        test.add_reason(f"Didn't received expected number of HB_SLEEP pkts during sleep state, "
                        f"Found {hb_sleep_pkts} Expected {exp_hb_sleep_msgs[LOW_VALUE_IDX]}-{exp_hb_sleep_msgs[HIGH_VALUE_IDX]}")
    else:
        utPrint(f"Success! found {hb_sleep_pkts} HB_SLEEP pkts "
                f"(expected {exp_hb_sleep_msgs[LOW_VALUE_IDX]}-{exp_hb_sleep_msgs[HIGH_VALUE_IDX]})", "BLUE")

    return test


def run(test):

    test = cert_common.test_prolog(test)
    if test.rc == TEST_FAILED:
        return cert_common.test_epilog(test)

    # Turn on pwr mgmt static mode - 30 sec on, 60 sec sleep
    test, wltpkt = cert_common.brg_pwr_mgmt_turn_on(test)
    if test.rc == TEST_FAILED:
        # Need to turn off just in case the ON was successful but didn't receive the ack packet
        test = cert_common.brg_pwr_mgmt_turn_off(test)
        cert_mqtt.dump_pkts(test, log=test.module_name)
        return cert_common.test_epilog(test, revert_brgs=True, modules=[test.active_brg.pwr_mgmt])

    # On duration starts
    utPrint(f"On duration started - Waiting for {int(wltpkt.pkt.static_on_duration)} seconds!", "WARNING")
    wait_time_n_print(wltpkt.pkt.static_on_duration)
    utPrint(f"On duration expired - Entering sleep state for {int(wltpkt.pkt.static_sleep_duration)} seconds!", "BLUE")
    # Sleep duration starts
    sleep_state_start_ts = int(datetime.datetime.now().timestamp() * SEC_TO_MS)
    test.get_mqttc_by_target(DUT).flush_pkts()
    wait_time_n_print(wltpkt.pkt.static_sleep_duration)
    sleep_state_end_ts = int(datetime.datetime.now().timestamp() * SEC_TO_MS)
    utPrint(f"Sleep duration expired - Returning to on state for {int(wltpkt.pkt.static_on_duration)} seconds!", "BLUE")

    # Sleep state analysis - check for SLEEP_HB packet
    test = brg_pwr_mgmt_sleep_state_analysis(test, wltpkt, sleep_state_start_ts, sleep_state_end_ts)
    test = cert_common.brg_pwr_mgmt_turn_off(test)

    cert_mqtt.dump_pkts(test, log=test.module_name)
    return cert_common.test_epilog(test, revert_brgs=True, modules=[test.active_brg.pwr_mgmt])
