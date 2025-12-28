from certificate.cert_prints import *
from certificate.cert_defines import *
from certificate.wlt_types import *
import certificate.cert_utils as cert_utils
import certificate.cert_config as cert_config
import certificate.cert_mqtt as cert_mqtt
import certificate.cert_data_sim as cert_data_sim
import datetime
# from ut_te import ut_rtsa
import pandas as pd
import os
import plotly.express as px
import math, random

DEFAULT_HDR = ag.Hdr(group_id=ag.GROUP_ID_GW2BRG)

# Returns a 12 chars long hex string
int2mac_get = lambda int_val: f"{int_val:012X}"

# Returns a 12 chars long masked alias_id from hex string
STATIC_RANDOM_ADDR_MASK = 0xC00000000000
hex2alias_id_get = lambda id_str: int2mac_get(int(id_str, 16) | STATIC_RANDOM_ADDR_MASK)

# Returns True if running from PyPi package, else False
is_cert_running = lambda : not (CERT_VERSION == LOCAL_DEV)


def name_to_val(name):
    return globals()[name]


def test_prolog(test, flush_mqtt=True):
    """
    kicks off the test:
    - sets test start time
    - checks to see if brg is DB for DB-only tests
    - setups spectrum analyzer configuration if needed

    :param WltTest test: test to be started
    :return test: returns the test
    """
    test.start_time = datetime.datetime.now()

    test_run_print(test)

    # Clean all exsisting mqtt's before starting
    if flush_mqtt:
        test.flush_all_mqtt_packets()

    #TODO - remove/check status later on in the test
    test.set_phase_rc(PRE_CONFIG, rc=test.rc) 
    test.add_phase_reason(PRE_CONFIG, reason=test.reason)
    #

    return test

def test_epilog(test, revert_brgs=False, revert_gws=False, modules=[], brg1_modules=[], ble5=False,
                flush_mqtt=True):
    """
    closes off the test:
    - sets test end time and duration
    - reverts gw/brgs/both to defaults
    - prints test results

    :param WltTest test: test to be finished
    :param bool revert_brgs: reverts brgs to defaults (default ep and config), defaults to False
    :param bool revert_gws: reverts gws to defaults (default config), defaults to False
    :return test: returns the test
    """
    # TODO - REMOVE when rc is re-designed
    if test.get_phase_by_name(TEST_BODY):
        test.set_phase_rc(TEST_BODY, test.rc)
        test.add_phase_reason(TEST_BODY, test.reason)

    test.reset_result()
    test.set_phase_rc(RESTORE_CONFIG, TEST_PASSED)

    if revert_brgs:
        res2 = DONE
        test, res = cert_config.config_brg_defaults(test, modules=modules, ble5=ble5)
        # TODO - REMOVE when rc is re-designed
        test.set_phase_rc(RESTORE_CONFIG, test.rc)
        test.reset_result()
        #
        if test.brg1 and test.multi_brg:
            brg1_modules = modules if not brg1_modules else brg1_modules
            test, res2 = cert_config.config_brg_defaults(test, modules=brg1_modules, ble5=ble5, target=BRG1)
            # TODO - REMOVE when rc is re-designed
            test.set_phase_rc(RESTORE_CONFIG, test.rc)
            test.reset_result()
            #
        if res == NO_RESPONSE or res2 == NO_RESPONSE:
            txt = "Failed: Revert BRGs to defaults"
            utPrint(txt, "RED")
            test.add_phase_reason(RESTORE_CONFIG, txt)

    if revert_gws:
        test, res = cert_config.config_gw_defaults(test)
        # TODO - REMOVE when rc is re-designed
        test.set_phase_rc(RESTORE_CONFIG, test.rc)
        test.reset_result()
        #
        if res == NO_RESPONSE:
            txt = "Failed: Revert GW to defaults"
            utPrint(txt, "RED")
            test.add_phase_reason(RESTORE_CONFIG, txt)
    if flush_mqtt:
        test.flush_all_mqtt_packets()
    test.end_time = datetime.datetime.now()
    test.duration = str(test.end_time - test.start_time).split(".")[0]

    # patch for nightly pipeline - as long as brg ver is updated, continue
    if ("ota_test" in test.module_name and not "brg2brg" in test.module_name and
        (BRG_VER_SUCCESS in test.get_phase_reason(TEST_BODY) or WANTED_VER_SAME in test.get_phase_reason(TEST_BODY))
        and test.get_phase_rc(TEST_BODY) == TEST_FAILED):
        print("Setting rc to TEST_PASSED for pipeline after BRG OTA succeeded")
        test.set_phase_rc(TEST_BODY, TEST_PASSED)
        test.set_phase_rc(RESTORE_CONFIG, TEST_PASSED)

    test_epilog_print(test)
    return test

def get_gw_versions(test, target=DUT):
    """
    returns gw ble and wifi versions

    :param WltTest test: test (with gw) to be checked
    :return dict[str, str]: dictionary with BLE_VERSION and WIFI_VERSION
    """
    mqttc = test.get_mqttc_by_target(target)
    mqttc.flush_pkts()
    cert_config.gw_info_action(test)
    found = False
    gw_ble_version, gw_wifi_version = "", ""
    start_time = datetime.datetime.now()
    while not found:
        for p in cert_mqtt.get_all_status_pkts(mqttc):
            if GW_INFO in p:
                print("Config pkts:")
                print_pkt(p)
                if test.tester.protobuf:
                    gw_ble_version = p[GW_INFO][ENTRIES][BLE_VERSION][STR_VAL]
                    gw_wifi_version = p[GW_INFO][ENTRIES][WIFI_VERSION][STR_VAL]
                else:
                    gw_ble_version = p[GW_INFO][BLE_VERSION]
                    gw_wifi_version = p[GW_INFO][WIFI_VERSION]
                print(f"current versions: wifi {gw_wifi_version} ble {gw_ble_version}")
                found = True
        print_update_wait()
        if (datetime.datetime.now() - start_time).seconds > DEFAULT_GW_FIELD_UPDATE_TIMEOUT:
            test.rc = TEST_FAILED
            test.add_reason(f"{GW_INFO} not found after {DEFAULT_BRG_FIELD_UPDATE_TIMEOUT} seconds!")
            break
    return {BLE_VERSION:gw_ble_version, WIFI_VERSION:gw_wifi_version}

def get_gw_geolocation(test, target=DUT):
    """
    returns gw latitude and longitude from a gw_info action

    :param WltTest test: test (with gw) to be checked
    :return dict[str, float]: dictionary with GW_LATITUDE and GW_LONGITUDE
    """
    mqttc = test.get_mqttc_by_target(target)
    mqttc.flush_pkts()
    cert_config.gw_info_action(test)
    found = False
    gw_lat, gw_lng = 0.0, 0.0
    start_time = datetime.datetime.now()
    while not found:
        for p in cert_mqtt.get_all_status_pkts(mqttc):
            if GW_INFO in p:
                print_pkt(p)
                if test.protobuf:
                    gw_lat = p[GW_INFO][ENTRIES][GW_LATITUDE][NUM_VAL]
                    gw_lng = p[GW_INFO][ENTRIES][GW_LONGITUDE][NUM_VAL]
                else:
                    gw_lat = p[GW_INFO][GW_LATITUDE]
                    gw_lng = p[GW_INFO][GW_LONGITUDE]
                print(f"gw_lat:{gw_lat} \ngw_lng:{gw_lng}")
                found = True
        print_update_wait()
        if (datetime.datetime.now() - start_time).seconds > DEFAULT_GW_FIELD_UPDATE_TIMEOUT:
            test.rc = TEST_FAILED
            test.add_reason(f"{GW_INFO} not found after {DEFAULT_BRG_FIELD_UPDATE_TIMEOUT} seconds!")
            break
    return test, {GW_LATITUDE:gw_lat, GW_LONGITUDE:gw_lng}

def get_gw_info(test, print=True, target=DUT):
    """
    gets gw info json dict from a gw_info action

    :param WltTest test: test with gw that it's info will be retreived
    :return str/dict[str, str]: json info dict from an info pkt OR a NO_RESPONSE str
    """
    gw = test.dut if target == DUT else test.tester
    mqttc = test.get_mqttc_by_target(target)
    mqttc.flush_pkts()
    # Always send gw info in both JSON and protobuf
    cert_config.gw_info_action(test, target=target)
    gw.protobuf = not gw.protobuf
    cert_config.gw_info_action(test, target=target)
    gw.protobuf = not gw.protobuf

    start_time = datetime.datetime.now()
    while (datetime.datetime.now() - start_time).seconds < DEFAULT_GW_FIELD_UPDATE_TIMEOUT:
        for p in cert_mqtt.get_all_status_pkts(mqttc):
            if GW_INFO in p:
                if print:
                    print_pkt(p)
                return p
        print_update_wait()
    return NO_RESPONSE

def get_logs(test, target=DUT):
    """
    gets logs info json dict from a gw_logs action

    :param WltTest test: test with gw that it's info will be retreived
    :return str/dict[str, str]: json info dict from an info pkt OR a NO_RESPONSE str
    """
    mqttc = test.get_mqttc_by_target(target)
    mqttc.flush_pkts()
    cert_config.gw_logs_action(test)
    start_time = datetime.datetime.now()
    while (datetime.datetime.now() - start_time).seconds < DEFAULT_GW_FIELD_UPDATE_TIMEOUT:
        for p in cert_mqtt.get_all_status_pkts(mqttc):
            if GET_LOGS:
                print_pkt(p)
                return p
        print_update_wait()
    return NO_RESPONSE

def get_brg_cfg_pkts(test, last=False, cfg_info=False, target=DUT):
    """
    gets brg cfg data pkts (payload)

    :param WltTest test: test to be scanned (it's first brg is the default brg to be scanned for)
    :param bool last: set to True to get only the last pkt caught, defaults to False
    :param bool cfg_info: set to True to get cfg info sent by the brg (msg_type=1 instead of 5 which is the default for this function), defaults to False
    :param int brg_mac: specific brg_mac in case we want to get cfg pkts for a specific brg different than the default, defaults to 0
    :param bool module: Indicates we look for a module pkt as ack for config change
    :return str/list[str]: cfg pkts payloads list/last cfg pkt payload received
    """
    pkts = []
    msg_type = ag.BRG_MGMT_MSG_TYPE_CFG_SET
    if cfg_info:
        msg_type = ag.BRG_MGMT_MSG_TYPE_CFG_INFO

    mqttc = test.get_mqttc_by_target(target)
    brg = cert_config.get_brg_by_target(test, target)
    for p in cert_mqtt.get_brg2gw_mgmt_pkts(mqttc, brg):
        brg2gw_cfg = p[MGMT_PKT].pkt
        if type(brg2gw_cfg).__name__ in [module.__name__ for module in brg.modules]:
            if brg2gw_cfg.msg_type == msg_type:
                pkts += [p[PAYLOAD]]
    if pkts and last:
        return pkts[-1]
    return pkts

time_in_sec = lambda t : t.seconds + t.microseconds / 1000000

# Pandas DataFrame documentation: https://pandas.pydata.org/docs/reference/frame.html

def get_all_brg_pkts(test):
    utPrint(f"Collecting all BRG pkts", "BLUE")
    return cert_mqtt.get_unified_data_pkts(test, only_active_brg=True)

def get_all_brgs_pkts(test):
    utPrint(f"Collecting all BRG pkts", "BLUE")
    return cert_mqtt.get_unified_data_pkts(test, only_active_brg=False)

def get_pkts_data_frame(test, gw_data=False, brg_data=False, per_pkt_type=False):
    pkts = []
    tags_last_pkt_cntr = {}
    tags_received_per_src =  {}
    tbc = None
    nfpkt = None
    event_flag = None
    event_ctr = None
    gw_pkts = 0
    brg_pkts = 0
    all_data = {TIMESTAMP:[],TAG_ID:[],SRC_ID:[],NFPKT:[],EVENT_CTR:[],EVENT_FLAG:[],TBC:[],PACKET_CNTR:[],PKT_CNTR_DIFF:[],CER:[],RSSI:[],BRG_LATENCY:[],PAYLOAD:[],SEQUENCE_ID:[],GW_ID:[], PACKET_TYPE:[]}
    if gw_data:
        pkts += cert_mqtt.get_internal_brg_unified_data_pkts(test)
    if brg_data:
        if test.brg1 and test.multi_brg:
            pkts += get_all_brg_pkts(test)
            test.active_brg = test.brg1
            pkts += get_all_brg_pkts(test)
            test.active_brg = test.dut.internal_brg if cert_config.is_gw(test.dut) else test.dut
        else:
            pkts += get_all_brg_pkts(test)
    for p in pkts:
        # Protection from pkts of type "test_mode" from old tags
        if type(p[DECODED_DATA][PACKET_TYPE]) == str or p[DECODED_DATA][PACKET_TYPE] == None:
            print(f"Skipped packet {p}")
            continue
        if per_pkt_type:
            tag_id = p[DECODED_DATA][TAG_ID] + "_" + str(p[DECODED_DATA][PACKET_TYPE])
        else:
            tag_id = p[DECODED_DATA][TAG_ID]

        if UNIFIED_PKT in p:
            src_id = p[ALIAS_BRIDGE_ID]
            rssi = p[UNIFIED_PKT].pkt.rssi
            brg_latency = p[UNIFIED_PKT].pkt.brg_latency
            if isinstance(p[UNIFIED_PKT].pkt, ag.UnifiedEchoPktV0):
                nfpkt = p[UNIFIED_PKT].pkt.nfpkt
            if isinstance(p[UNIFIED_PKT].pkt, ag.UnifiedEchoPktV1) or isinstance(p[UNIFIED_PKT].pkt, ag.UnifiedEchoExtPktV0):
                tbc = p[UNIFIED_PKT].pkt.tbc
                nfpkt = p[UNIFIED_PKT].pkt.nfpkt
            if isinstance(p[UNIFIED_PKT].pkt, ag.UnifiedEchoPktV2) or isinstance(p[UNIFIED_PKT].pkt, ag.UnifiedEchoExtPktV1):
                tbc = p[UNIFIED_PKT].pkt.tbc
                event_flag = p[UNIFIED_PKT].pkt.event_flag
                event_ctr = p[UNIFIED_PKT].pkt.event_ctr

        all_data[TIMESTAMP] += [p[TIMESTAMP]]
        all_data[TAG_ID] += [tag_id]
        all_data[GW_ID] +=  [p[GW_ID]]
        all_data[SRC_ID] += [src_id]
        all_data[NFPKT] += [nfpkt]
        all_data[TBC] += [tbc]
        all_data[EVENT_FLAG] += [event_flag]
        all_data[EVENT_CTR] += [event_ctr]
        all_data[PACKET_CNTR] += [p[DECODED_DATA][PACKET_CNTR]]
        all_data[RSSI] += [rssi]
        all_data[BRG_LATENCY] += [brg_latency]
        all_data[PAYLOAD] += [p[PAYLOAD]]
        all_data[SEQUENCE_ID] += [p[SEQUENCE_ID]]
        all_data[PACKET_TYPE] += [p[DECODED_DATA][PACKET_TYPE]]

        # handling pkt_cntr_diff
        pkt_cntr_diff = (p[DECODED_DATA][PACKET_CNTR] - tags_last_pkt_cntr[tag_id])%255 if tag_id and tag_id in tags_received_per_src and src_id and src_id in tags_received_per_src[tag_id] else None
        all_data[PKT_CNTR_DIFF] += [pkt_cntr_diff]
        cer = 1-(nfpkt/pkt_cntr_diff) if (pkt_cntr_diff and nfpkt != None) else None
        all_data[CER] += [cer]

        # saving last pkt_cntr per tag
        tags_last_pkt_cntr[tag_id] = p[DECODED_DATA][PACKET_CNTR]

        # saving all srcs a tag was received from
        if tag_id and src_id:
            if tag_id not in tags_received_per_src:
                tags_received_per_src[tag_id] = [src_id]
            elif not src_id in tags_received_per_src[tag_id]:
                tags_received_per_src[tag_id] += [src_id]

            if gw_data:
                if src_id == test.internal_id_alias():
                    gw_pkts += 1
            if brg_data:
                if src_id != test.internal_id_alias():
                    brg_pkts += 1

    if gw_data:
        print(f"Found {gw_pkts} gw_tags_pkts")
    if brg_data:
        print(f"Found {brg_pkts} brg_tags_pkts")

    df = pd.DataFrame.from_dict(all_data)
    df = df.sort_values(by=TIMESTAMP)
    return df

def data_scan(test, gw_data=False, brg_data=False, scan_time=0, per_pkt_type=False, pkt_filter_cfg=0, flush_pkts=True, first_pkt_is_start_time=False, target=DUT):
    # MQTT scan
    mqttc = test.get_mqttc_by_target(target)
    if flush_pkts:
        mqttc.flush_pkts()
    start_time = datetime.datetime.now()
    if scan_time:
        mqtt_scan_start(test, scan_time)
        chars = ["|", "/", "-", "\\"]
        start_time = datetime.datetime.now()
        i = 0
        while not test.rc:
            cur_duration = (datetime.datetime.now() - start_time).seconds
            if cur_duration >= scan_time:
                break
            if pipeline_running():
                sys.stdout.write(".")
            else:
                sys.stdout.write("\r"+chars[i%4]*20+" "+str(cur_duration)+" "+chars[i%4]*20+" {} pkts captured".format(len(cert_mqtt.get_all_data_pkts(mqttc))))
            sys.stdout.flush()
            time.sleep(0.25)
            i += 1
        print("\n")

    if per_pkt_type:
        cert_mqtt.dump_pkts(test, log=str(pkt_filter_cfg))
        if pkt_filter_cfg == ag.PKT_FILTER_RANDOM_FIRST_ARRIVING_PKT:
            # When PKT_FILTER_RANDOM_FIRST_ARRIVING_PKT we don't want to split the tags to be per pkt_type
            per_pkt_type = False
    df = get_pkts_data_frame(test, gw_data=gw_data, brg_data=brg_data, per_pkt_type=per_pkt_type)
    if not df.empty:
        df['gw_id'] = test.internal_id_alias()
        if first_pkt_is_start_time:
            start_time = min(df[TIMESTAMP])
            df[TIMESTAMP_DELTA] = (df[TIMESTAMP]- start_time) / 1000
        else:
            df[TIMESTAMP_DELTA] = (df[TIMESTAMP] / 1000) - start_time.timestamp()
    return df

def pacing_analysis(test, pacer_interval, df, pkt_filter_cfg=ag.PKT_FILTER_RANDOM_FIRST_ARRIVING_PKT, num_of_pixels=0, is_ble5_test=False, ext_adv_brg2gw=False,
                    event_time_unit=ag.BRG_DEFAULT_EVENT_TIME_UNIT, phase=""):
    ROUND = 3

    # Validate pkts amount
    if df[TAG_ID].nunique() == 0:
        if pkt_filter_cfg == ag.PKT_FILTER_DISABLE_FORWARDING:
            print("Packets echo disabled and no packets were found accordingly")
        else:
            test.rc = TEST_FAILED
            test.add_reason("No packets found!\nMake sure you have an energizing BRG around you.")
            print(test.reason)
        return test
    elif pkt_filter_cfg == ag.PKT_FILTER_DISABLE_FORWARDING:
        test.rc = TEST_FAILED
        test.add_reason("Packets were found while packets echo is turned off!")
        print(test.reason)
        return test

    # Verify received pkt types are correct when cfg is not PKT_FILTER_RANDOM_FIRST_ARRIVING_PKT
    if pkt_filter_cfg != ag.PKT_FILTER_RANDOM_FIRST_ARRIVING_PKT:
        for pkt_type in list(df[PACKET_TYPE].unique()):
            if ((pkt_filter_cfg & (1 << pkt_type)) == 0
                and not (is_ble5_test and (test.internal_brg or test.dut_is_combo() or ext_adv_brg2gw) and pkt_type == ag.PKT_TYPE_BLE5_EXTENDED_TEMP_ADVANCED)):
                test.rc = TEST_FAILED
                test.add_reason(f"Tag is of packet type {pkt_type} which is turned off in packet_types_mask configuration!")
                return test

    # Verify the tags count according to simulation data and pkt_filter_cfg
    tags_count = len(list(df[TAG_ID].unique()))
    if test.data == DATA_SIMULATION and num_of_pixels:
        if is_ble5_test and (test.dut_is_combo() or ext_adv_brg2gw):
            # In ble5 bcc packet type 2 extended uploaded as is without splitting to ble4 packets
            expected_tags_count = num_of_pixels
        elif pkt_filter_cfg == ag.PKT_FILTER_TEMP_AND_ADVANCED_PKTS or pkt_filter_cfg == ag.PKT_FILTER_TEMP_AND_DEBUG_PKTS:
            expected_tags_count = num_of_pixels * 2
        elif pkt_filter_cfg == ag.PKT_FILTER_TEMP_ADVANCED_AND_DEBUG_PKTS:
            expected_tags_count = num_of_pixels * 3
        else:
            expected_tags_count = num_of_pixels
        if tags_count != expected_tags_count:
            test.rc = TEST_FAILED
            test.add_reason(f"Expected {expected_tags_count} pixels but found {tags_count}!")
            print(test.reason)
            return test

    # verify there is no event flag when not event test
    event_test = True if "event" in phase else False
    if not event_test and (df['event_flag'] == 1).any():
        test.rc = TEST_FAILED
        print(f"Got event flag when not testing events!")
        test.add_reason(f"Got event flag when not testing events!")

    # Verify the tags event pacing
    tag_event = True if "new_tag" not in phase else False
    if event_test:

        if event_time_unit == ag.EVENT_TIME_UNIT_SECONDS:
            pacing_window = TEST_EVENT_WINDOW_SEC_CFG if not tag_event else TEST_TAG_EVENT_WINDOW_CFG
        elif event_time_unit == ag.EVENT_TIME_UNIT_MINUTES:
            pacing_window = TEST_EVENT_WINDOW_MIN_CFG * 60
        elif event_time_unit == ag.EVENT_TIME_UNIT_HOURS:
            pacing_window = TEST_EVENT_WINDOW_HR_CFG * 3600

        # In seconds phase we also test the dynamic pacer interval
        if "rssi" in phase:
            event_pacing = DATA_SIM_RSSI_EVENT_TESTING_DELAY_SEC
        elif "seconds" in phase:
            event_pacing = DATA_SIM_EVENT_PACER_INTERVAL_TESTING
        else:
            event_pacing = DATA_SIM_EVENT_TESTING_DELAY_SEC

        expected_event_pkt_count = math.ceil(pacing_window / event_pacing)

        if "rssi" in phase:
            if not test.sterile_run:
                # In non-sterile runs - rssi is less stable and can trigger more events
                max_count_threshold = float('inf')
            else:
                # In rssi movement events the alpha filter takes about 13 packets to stabilize 
                max_count_threshold = 1 + (RSSI_EVENT_PKTS_TO_STABILIZE / expected_event_pkt_count)
        else:
            max_count_threshold = PACER_INTERVAL_CEIL_THRESHOLD

        for tag in list(df[TAG_ID].unique()):
            event_pkts = df.query('tag_id == @tag and event_flag == 1')
            avg_event_pacer = round(event_pkts.timestamp.diff().mean(skipna=True)/1000, ROUND)

            if not (PACER_INTERVAL_THRESHOLD <= len(event_pkts) / expected_event_pkt_count <= max_count_threshold):
                test.rc = TEST_FAILED
                msg = f"Packet count for dynamic tag {tag} is wrong! expected_event_pkt_count = {expected_event_pkt_count}, received pkt count = {len(event_pkts)}"
                test.add_reason(msg)
                utPrint(msg, "RED")
            if not (PACER_INTERVAL_THRESHOLD <= avg_event_pacer / event_pacing <= PACER_INTERVAL_CEIL_THRESHOLD):
                test.rc = TEST_FAILED
                msg = f"Tag {tag} has a wrong avg time diff. diff_time {list(event_pkts.timestamp.diff().div(1000))}, avg_event_pacer={avg_event_pacer} exceeds threshold!"
                test.add_reason(msg)
                utPrint(msg, "RED")

    # Verify the tags pacer interval (without event)
    failed_tags = 0
    max_received_pkts = max([len(df.query('tag_id == @tag and event_flag == 0'))  for tag in list(df[TAG_ID].unique())])
    for tag in list(df[TAG_ID].unique()):
        if tag_event:
            # No need to test regular pacing in tag event test
            break
        pkts = df.query('tag_id == @tag and event_flag == 0')
        avg_pacer = round(pkts.timestamp.diff().mean(skipna=True)/1000, ROUND)
        print(f"Tag: {tag} avg_pacer={avg_pacer} num_of_pkts={len(pkts)}")
        if ((avg_pacer / pacer_interval) < PACER_INTERVAL_THRESHOLD_HIGH and (pacer_interval - avg_pacer) > 1):
            failed_tags += 1
            test.rc = TEST_FAILED
            msg = f"Tag {tag} with diff_time {list(pkts.timestamp.diff().div(1000))}, avg_pacer={avg_pacer} exceeds {PACER_INTERVAL_THRESHOLD_HIGH} minimum threshold!"
            utPrint(msg, "RED")
            test.add_reason(msg)
            # Pass the test with real tags when less than 5% tag failed
            if test.data != DATA_SIMULATION and failed_tags / tags_count < 0.05:
                test.rc = TEST_PASSED

        if test.data == DATA_SIMULATION and (avg_pacer / pacer_interval) > PACER_INTERVAL_CEIL_THRESHOLD:
            if max_received_pkts == len(pkts):
                # we fail the tag only if it received all expected pkts and pacer caluculation is valid
                failed_tags += 1
                msg = f"Tag {tag} with diff_time {list(pkts.timestamp.diff().div(1000))}, avg_pacer={avg_pacer} exceeds {PACER_INTERVAL_CEIL_THRESHOLD} maximum threshold!"
                utPrint(msg, "RED")
                test.add_reason(msg)
            else:
                print(f"Tag {tag} received only {len(pkts)} pkts out of {max_received_pkts}, avg_pacer failed but skipping pacer ceil validation")
            if failed_tags / tags_count > 0.2:  # Fail the test on ceil threshold only when more than 20% tag failed
                test.reason = f"{failed_tags}/{tags_count} tags with wrong time diff"
                test.rc = TEST_FAILED

    return test


def brg2brg_ota_init(test, is_bl_ota=False):

    VERSIONS_SAME = "Both bridges FW versions are the same!"
    BL_VERSIONS_SAME = "Both bridges Bootloader versions are the same!"
    BOARDS_MISMATCH = "Bridges are of different board types!"

    # Initialize bridges
    # TODO - REMOVE CERT_CONFIG IMPORT
    brg0 = test.dut.internal_brg if cert_config.is_gw(test.dut) else test.dut
    brg1 = test.brg1

    # Protections from same version & different board types
    if not is_bl_ota and brg0.version == brg1.version:
        utPrint(VERSIONS_SAME, "RED")
        test.rc = TEST_FAILED
        test.add_reason(VERSIONS_SAME)
    if is_bl_ota and brg0.bl_version == brg1.bl_version:
        utPrint(BL_VERSIONS_SAME, "RED")
        test.rc = TEST_FAILED
        test.add_reason(BL_VERSIONS_SAME)
    if brg0.board_type != brg1.board_type:
        utPrint(BOARDS_MISMATCH, "RED")
        test.rc = TEST_FAILED
        test.add_reason(BOARDS_MISMATCH)

    # Active bridge will be the source bridge
    if is_bl_ota:
        test.active_brg = brg0 if brg0.bl_version > brg1.bl_version else brg1
    else:
        test.active_brg = brg0 if brg0.version > brg1.version else brg1

    return test


def send_brg2brg_ota_msg(test, src_brg, dest_brg, is_bl_ota=False, target=DUT):

    utPrint(f"Source {"bootloader" if is_bl_ota else "firmware"} bridge version: {src_brg.bl_version if is_bl_ota else src_brg.version}. "
            f"Destination bridge {"bootloader" if is_bl_ota else "firmware"} version: {dest_brg.bl_version if is_bl_ota else dest_brg.version}", "BLUE")

    # Send BRG2BRG_OTA message to source bridge
    functionality_run_print(f"BRG2BRG OTA - Source Bridge MAC: {src_brg.id_str}, Destination Bridge MAC: {dest_brg.id_str}")
    brg2brg_ota_pkt = eval_pkt(f'Brg2BrgOtaV{test.active_brg.api_version}')(src_brg_mac=src_brg.id_int,
                                                                            dest_brg_mac=dest_brg.id_int,
                                                                            seq_id=test.get_seq_id(),
                                                                            bootloader=is_bl_ota)
    brg2brg_ota_pkt_downlink = WltPkt(hdr=ag.Hdr(group_id=ag.GROUP_ID_GW2BRG), pkt=brg2brg_ota_pkt)
    # BRG OTA - Flush pkts ONLY before starting to avoid deletion of needed GW Logs
    test.get_mqttc_by_target(target).flush_pkts()
    cert_config.gw_downlink(test, raw_tx_data=brg2brg_ota_pkt_downlink.dump(), target=target)

    # Get version of the destination bridge
    test.active_brg = dest_brg
    # expected_hash=1 due to different cfgs and versions between builds
    test = reboot_config_analysis(test=test, expected_hash=1, ble_version=src_brg.version if not is_bl_ota else None,
                                              bl_version=src_brg.bl_version if is_bl_ota else None, timeout=VER_UPDATE_TIMEOUT)
    # Update back to original bridge version if test failed:
    if test.rc == TEST_FAILED:
        cert_config.brg_ota(test, ble_version=test.gw_orig_versions[BLE_VERSION], search_ack=False)

    return test


def run_event_test_phase(test, phase, datapath_module, values, scan_time, event_time_unit, ble5_test=False,
                         pkt_filter_cfg=ag.PKT_FILTER_RANDOM_FIRST_ARRIVING_PKT):
    # Generic runner for events tests

    fields = [BRG_EVENT_TIME_UNIT, BRG_EVENT_WINDOW, BRG_RX_CHANNEL, BRG_EVENT_TRIGGER, BRG_EVENT_PACER_INTERVAL]
    scan_time_multiplier = 1
    delay = DATA_SIM_EVENT_TESTING_DELAY_MS
    if "rssi" in phase:
        test.sterile_run = is_quiet_setup_running()
        delay = DATA_SIM_RSSI_EVENT_TESTING_DELAY_MS
        scan_time_multiplier = (1 / 3)
        fields += [BRG_RSSI_MOVEMENT_THRESHOLD]

    ble5 = ble5_test and test.dut_is_bridge()  # ble5 only for bridge dut (with combo we don't need to wait)
    test = cert_config.brg_configure(test, fields=fields, values=values, module=datapath_module, ble5=ble5)[0]
    test.set_phase_rc(phase, test.rc)
    test.add_phase_reason(phase, test.reason)
    if test.rc == TEST_FAILED and test.exit_on_param_failure:
        return test

    num_of_pixels = 0
    if test.data == DATA_SIMULATION:
        num_of_pixels = 1
        if ble5_test:
            pixel_sim_thread = cert_data_sim.DataSimThread(test=test, num_of_pixels=num_of_pixels, duplicates=6,
                                                            delay=delay, pkt_types=[2],
                                                            pixels_type=GEN3_EXTENDED)
        else:
            pixel_sim_thread = cert_data_sim.DataSimThread(test=test, num_of_pixels=num_of_pixels, duplicates=6,
                                                            delay=delay, pkt_types=[0],
                                                            pixels_type=GEN3)
        pixel_sim_thread.start()
    else:
        test.rc = TEST_FAILED
        warning_txt = "This test should be ran with data simulator!"
        utPrint(warning_txt, "RED")
        test.add_reason(warning_txt)
        return test

    df = data_scan(test, scan_time=scan_time * scan_time_multiplier, pkt_filter_cfg=pkt_filter_cfg, brg_data=(not test.internal_brg),
                   gw_data=test.internal_brg, per_pkt_type=True)

    if "rssi" in phase:
        # Configure data simulator to change output power for rssi change test
        test = cert_config.brg_configure(test, module=datapath_module, fields=[BRG_OUTPUT_POWER, BRG_RX_CHANNEL], values=[ag.OUTPUT_POWER_2_4_MAX_MINUS_26], wait=False, target=TESTER)[0]
        df_ext = data_scan(test, scan_time=scan_time * (1 - scan_time_multiplier), pkt_filter_cfg=pkt_filter_cfg, brg_data=(not test.internal_brg),
                       gw_data=test.internal_brg, per_pkt_type=True)
        df = pd.concat([df, df_ext]).sort_values(by=TIMESTAMP)
        test = cert_config.brg_configure(test, module=datapath_module, fields=[BRG_OUTPUT_POWER, BRG_RX_CHANNEL], values=[ag.BRG_DEFAULT_DATAPATH_OUTPUT_POWER], target=TESTER)[0]

    if test.data == DATA_SIMULATION:
        pixel_sim_thread.stop()
        time.sleep(5)

    cert_mqtt.dump_pkts(test, log=phase)
    display_data(df, event_flag=True, event_ctr=True, name_prefix=f"{phase}_", dir=test.dir)

    test = pacing_analysis(test, df=df, pkt_filter_cfg=pkt_filter_cfg, pacer_interval=ag.BRG_DEFAULT_PACER_INTERVAL,
                           num_of_pixels=num_of_pixels, event_time_unit=event_time_unit, is_ble5_test=ble5_test, phase=phase)
    test.set_phase_rc(phase, test.rc)
    test.add_phase_reason(phase, test.reason)
    return test

def reboot_config_analysis(test, expected_hash, timeout=ACTION_LONG_TIMEOUT, ble_version=None, bl_version=None, target=DUT):
    utPrint("Analyzing Reboot", "BLUE")
    # start with a 5 sec wait time before searching interface to allow the BRG to reboot
    time.sleep(5)

    start_time = datetime.datetime.now()
    seq_ids = []
    found = {ag.MODULE_IF : False, ag.MODULE_DATAPATH: False}
    received_hash = 0
    mqttc = test.get_mqttc_by_target(target)
    # Flush data pkts only to keep the GW logs which are in status topic
    mqttc.flush_data_pkts()

    while not all(found.values()):
        # scan for ModuleIf and ModuleDatapath pkts of all api versions to support api version change on update
        # ModuleDatapath arrival shows that the BLE really rebooted
        if_pkts_list = [eval_pkt(f'ModuleIfV{i}') for i in range(ag.API_VERSION_V9, ag.API_VERSION_LATEST+1)]
        datapath_pkts_list = [eval_pkt(f'ModuleDatapathV{i}') for i in range(ag.API_VERSION_V9, ag.API_VERSION_LATEST+1)]
        pkts = cert_mqtt.get_brg2gw_mgmt_pkts(mqttc, test.active_brg, mgmt_types=if_pkts_list+datapath_pkts_list)
        for p in pkts:
            if p[SEQUENCE_ID] not in seq_ids:
                seq_ids.append(p[SEQUENCE_ID])
                module_pkt = p[MGMT_PKT].pkt
                if not found[module_pkt.module_type]:
                    print("\nGot {} packet after {} sec!".format(type(module_pkt).__name__, (datetime.datetime.now() - start_time).seconds))
                    print(module_pkt)
                    if module_pkt.module_type == ag.MODULE_IF:
                        test.active_brg.api_version = module_pkt.api_version
                        print(f"received ModuleIfV{test.active_brg.api_version} pkt:")
                        # get received cfg_hash & expected cfg_hash
                        received_hash = module_pkt.cfg_hash
                        print(f"\nexpected cfg_hash: {hex(expected_hash)}")
                        print(f"received cfg_hash: {hex(received_hash)}")
                        # brg version update (OTA) analysis
                        if ble_version:
                            brg_version = f"{module_pkt.major_ver}.{module_pkt.minor_ver}.{module_pkt.patch_ver}"
                            print(f"\nBRG version: {brg_version}, expected version: {ble_version}")
                            # compare wanted version to received version
                            if brg_version == ble_version:
                                test.active_brg.version = brg_version
                                test.add_reason(BRG_VER_SUCCESS)
                                # ALSO compare received cfg_hash to expected cfg_hash
                                # expected_hash will be 1 if api_version was updated
                                if received_hash == expected_hash or expected_hash == 1:
                                    found[module_pkt.module_type] = True
                        elif bl_version:
                            brg_bl_version = module_pkt.bl_version
                            print(f"\nBRG bootloader version: {brg_bl_version}, expected bootloader version: {bl_version}")
                            # compare wanted version to received version
                            if brg_bl_version == bl_version:
                                test.active_brg.bl_version = brg_bl_version
                                test.add_reason(BRG_BL_VER_SUCCESS)
                                found[module_pkt.module_type] = True
                        # analysis of any other reboot actions with no version update (relevant only for api version 8 or higher)
                        # compare received cfg_hash to expected cfg_hash
                        elif received_hash == expected_hash:
                            found[module_pkt.module_type] = True
                    else:
                        found[module_pkt.module_type] = True
        print_update_wait()

        if (datetime.datetime.now() - start_time).seconds > timeout:
            test.rc = TEST_FAILED
            unfound = [f'{ag.MODULES_DICT[m]}{test.active_brg.api_version}' for m in found if not found[m]]
            test.add_reason(f"{unfound} not received in {timeout} sec.")
            break
    return test

def scan_for_mgmt_pkts(test, mgmt_type, target=DUT):

    start_time = datetime.datetime.now()
    # Search for module packets
    found = False
    ret_pkts = []
    mqttc = test.get_mqttc_by_target(target)
    while DEFAULT_BRG_FIELD_UPDATE_TIMEOUT > (datetime.datetime.now() - start_time).seconds:
        print_update_wait()
        pkts_collected = cert_mqtt.get_brg2gw_mgmt_pkts(mqttc, test.active_brg, mgmt_types=mgmt_type)
        if pkts_collected:
            seq_ids = []
            for p in pkts_collected:
                if seq_ids == [] or p[SEQUENCE_ID] not in seq_ids:
                    seq_ids.append(p[SEQUENCE_ID])
                    ret_pkts.append(p)
            found = True
            break
    if not found:
        test.rc = TEST_FAILED
        error = f"Didn't receive {mgmt_type[0].__name__} pkt after {DEFAULT_BRG_FIELD_UPDATE_TIMEOUT} seconds!"
        test.add_reason(error)
        utPrint(error, "RED")
    return test, ret_pkts

# Actions test functions
# modules should receive a list of module names to look for - identical to their actual classes' names!
def scan_for_modules(test, modules=[]):
    modules = test.active_brg.modules if not modules else modules
    found = {module.__name__: False for module in modules}
    start_time = datetime.datetime.now()

    # Search for packets
    while not all(found.values()):
        for module in found:
            pkts = cert_mqtt.get_brg2gw_mgmt_pkts(
                test.get_mqttc_by_target(DUT),
                test.active_brg,
                mgmt_types=[eval_pkt(module)],
            )
            if pkts and not found[module]:
                found[module] = True
                print("\nGot {} packet after {} sec!".format(module, (datetime.datetime.now() - start_time).seconds))
                print(pkts[-1][MGMT_PKT].pkt)
        print_update_wait()
        if (datetime.datetime.now() - start_time).seconds > DEFAULT_BRG_FIELD_UPDATE_TIMEOUT:
            test.rc = TEST_FAILED
            err_print = ','.join([module for module, value in found.items() if not value])
            test.add_reason("Didn't receive {} after {} seconds!".format(err_print, DEFAULT_BRG_FIELD_UPDATE_TIMEOUT))
            break
    return test


def search_action_ack(test, action_id, **kwargs):
    test, mgmt_pkts = scan_for_mgmt_pkts(test, mgmt_type=[eval_pkt(f'{ag.ACTIONS_DICT[action_id]}{test.active_brg.api_version}')])
    if test.rc == TEST_FAILED:
        return test
    print("\nReceived ACK pkts:")
    for p in mgmt_pkts:
        print(p[MGMT_PKT].pkt)
        pkt = cert_config.get_default_brg_pkt(test,
                                              pkt_type=eval_pkt(f'{ag.ACTIONS_DICT[action_id]}{test.active_brg.api_version}'),
                                              **kwargs).pkt
        if p[MGMT_PKT].pkt == pkt:
            utPrint("Received ACK for action", "GREEN")
            return test
    test.rc = TEST_FAILED
    test.add_reason(f"Didn't find action ACK for action id {action_id} {ag.ACTIONS_DICT[action_id]}")
    return test


def get_brg_non_default_module_pkt(test, module):
    if 'Energy2400' in module.__name__:
        if test.active_brg.board_type in [ag.BOARD_TYPE_ENERGOUS_V0, ag.BOARD_TYPE_ENERGOUS_V2,
                                          ag.BOARD_TYPE_ENERGOUS_V3, ag.BOARD_TYPE_ENERGOUS_V4]:
            # Increase output power offset by 1
            op_offset = BRG_NON_DEFAULT_OP_OFFSET_2_4 + 1
        else:
            op_offset = BRG_NON_DEFAULT_OP_OFFSET_2_4
        return cert_config.get_default_brg_pkt(test, pkt_type=test.active_brg.energy2400,
                                               duty_cycle=BRG_NON_DEFAULT_DUTY_CYCLE,
                                               output_power=op_offset, pattern=BRG_NON_DEFAULT_EP_2_4,
                                               signal_indicator_cycle=BRG_NON_DEFAULT_SIGNAL_INDICATOR_CYCLE_2_4,
                                               signal_indicator_rep=BRG_NON_DEFAULT_SIGNAL_INDICATOR_REP_2_4)
    elif 'EnergySub1G' in module.__name__:
        return cert_config.get_default_brg_pkt(test, pkt_type=test.active_brg.energy_sub1g,
                                               duty_cycle=BRG_NON_DEFAULT_DUTY_CYCLE,
                                               signal_indicator_cycle=BRG_NON_DEFAULT_SIGNAL_INDICATOR_CYCLE_SUB1G,
                                               signal_indicator_rep=BRG_NON_DEFAULT_SIGNAL_INDICATOR_REP_SUB1G)
    elif 'PwrMgmt' in module.__name__:
        return cert_config.get_default_brg_pkt(test, pkt_type=test.active_brg.pwr_mgmt,
                                               dynamic_keep_alive_scan=BRG_NON_DEFAULT_PWR_MGMT_KEEP_ALIVE_SCAN)
    elif 'Custom' in module.__name__:
        return cert_config.get_default_brg_pkt(test, pkt_type=test.active_brg.custom,
                                               motion_sensitivity_threshold=LIS2DW12_NON_DEFAULT_STATE_THRESHOLD,
                                               s2d_transition_time=LIS2DW12_NON_DEFAULT_WAKE_UP_DURATION,
                                               d2s_transition_time=LIS2DW12_NON_DEFAULT_SLEEP_DURATION)
    elif 'Datapath' in module.__name__:
        if test.active_brg.board_type in [ag.BOARD_TYPE_ENERGOUS_V0, ag.BOARD_TYPE_ENERGOUS_V2,
                                          ag.BOARD_TYPE_ENERGOUS_V3, ag.BOARD_TYPE_ENERGOUS_V4]:
            # Increase output power offset by 1
            op_offset = BRG_NON_DEFAULT_OP_OFFSET_2_4 + 1
        else:
            op_offset = BRG_NON_DEFAULT_OP_OFFSET_2_4
        return cert_config.get_default_brg_pkt(test, pkt_type=test.active_brg.datapath,
                                               tx_repetition=BRG_NON_DEFAULT_TX_REPETITION,
                                               pkt_filter=BRG_NON_DEFAULT_PKT_FILTER,
                                               output_power=op_offset,
                                               pattern=ag.DATAPATH_PATTERN_EU_PATTERN,
                                               pacer_interval=BRG_NON_DEFAULT_PACER_INTERVAL,
                                               rssi_threshold=BRG_NON_DEFAULT_RSSI_THRESHOLD,
                                               event_time_unit=BRG_NON_DEFAULT_EVENT_TIME_UNIT,
                                               event_window=BRG_NON_DEFAULT_EVENT_WINDOW,
                                               event_trigger=BRG_NON_DEFAULT_EVENT_TRIGGER,
                                               event_pacer_interval=BRG_NON_DEFAULT_EVENT_PACER_INTERVAL,
                                               rssi_movement_threshold=BRG_NON_DEFAULT_RSSI_MOVEMENT_THRESHOLD)
    elif 'Calibration' in module.__name__:
        if test.active_brg.board_type in [ag.BOARD_TYPE_ENERGOUS_V0, ag.BOARD_TYPE_ENERGOUS_V2,
                                          ag.BOARD_TYPE_ENERGOUS_V3, ag.BOARD_TYPE_ENERGOUS_V4]:
            # Increase output power offset by 1
            op_offset = BRG_NON_DEFAULT_CALIB_OUTPUT_POWER_OFFSET + 1
        else:
            op_offset = BRG_NON_DEFAULT_CALIB_OUTPUT_POWER_OFFSET
        return cert_config.get_default_brg_pkt(test, pkt_type=test.active_brg.calibration,
                                               output_power=op_offset,
                                               interval=BRG_NON_DEFAULT_CALIB_INTERVAL,
                                               pattern=BRG_NON_DEFAULT_CALIB_PATTERN)
    elif 'ExtSensors' in module.__name__:
        return cert_config.get_default_brg_pkt(test, pkt_type=test.active_brg.sensors,
                                               sensor0=ag.EXTERNAL_SENSORS_MINEWS1,
                                               sensor1=ag.EXTERNAL_SENSORS_ZEBRA_PRINTER,
                                               sensor2=ag.EXTERNAL_SENSORS_ERM_SMART_MS,
                                               rssi_threshold=BRG_NON_DEFAULT_RSSI_THRESHOLD,
                                               sub1g_rssi_threshold=BRG_NON_DEFAULT_RSSI_THRESHOLD)
    return None


def brg_non_default_modules_cfg(test):
    for module in test.active_brg.modules:
        cfg_pkt = get_brg_non_default_module_pkt(test, module)
        if cfg_pkt:
            utPrint(f"Configuring {module.__name__} non-default cfg", "BLUE")
            test = cert_config.brg_configure(test=test, cfg_pkt=cfg_pkt)[0]
        if test.rc == TEST_FAILED and test.exit_on_param_failure:
            test.add_reason(f"{module.__name__} non-default cfg pkt was not found after {DEFAULT_BRG_FIELD_UPDATE_TIMEOUT} sec!")
            return test
    return test

# Plotly graphing libraries documentation: https://plotly.com/python/

def display_data(df, csv=True, pkt_cntr_diff=False, cer_per_tag=False, tbc=False, rssi=False, ttfp=False, event_flag=False, event_ctr=False,
                 start_time=None, name_prefix="", dir=""):
    print("\nGenerating data analysis graphs and CSV file\n")
    df[DATETIME] = df[TIMESTAMP].apply(lambda x: datetime.datetime.fromtimestamp(x/1e3))
    df = df.sort_values(by=DATETIME)
    symbol_sequence = ["hourglass", "bowtie", "cross", "x"]
    all_graphs = []
    ttfp_graph = None
    # insert new start_time to override timestamp_delta from data_scan()
    if start_time:
        df[TIMESTAMP_DELTA] = (df[TIMESTAMP] / 1000) - start_time.timestamp()
    if rssi:
        rssi_graph = px.scatter(df, title=RSSI, x=DATETIME, y=RSSI, color=TAG_ID, symbol=SRC_ID, symbol_sequence=symbol_sequence)
        rssi_graph.update_traces(marker=dict(size=12, line=dict(width=2, color='DarkSlateGrey')), selector=dict(mode='markers'))
        all_graphs.append(rssi_graph)
    if pkt_cntr_diff:
        pkt_cntr_diff_graph = px.scatter(df, title=PKT_CNTR_DIFF, x=DATETIME, y=PKT_CNTR_DIFF, color=TAG_ID, symbol=SRC_ID, symbol_sequence=symbol_sequence)
        pkt_cntr_diff_graph.update_traces(marker=dict(size=12, line=dict(width=2, color='DarkSlateGrey')), selector=dict(mode='markers'))
        all_graphs.append(pkt_cntr_diff_graph)
    if cer_per_tag:
        cer_per_tag_graph = px.scatter(df, title=CER, x=DATETIME, y=CER, color=TAG_ID, symbol=SRC_ID, symbol_sequence=symbol_sequence)
        cer_per_tag_graph.update_traces(marker=dict(size=12, line=dict(width=2, color='DarkSlateGrey')), selector=dict(mode='markers'))
        all_graphs.append(cer_per_tag_graph)
    if tbc:
        tbc_graph = px.scatter(df, title=TBC, x=DATETIME, y=TBC, color=TAG_ID, symbol=SRC_ID, symbol_sequence=symbol_sequence)
        tbc_graph.update_traces(marker=dict(size=12, line=dict(width=2, color='DarkSlateGrey')), selector=dict(mode='markers'))
        all_graphs.append(tbc_graph)
    if event_flag:
        event_flag_graph = px.scatter(df, title=EVENT_FLAG, x=DATETIME, y=EVENT_FLAG, color=TAG_ID, symbol=SRC_ID, symbol_sequence=symbol_sequence)
        event_flag_graph.update_traces(marker=dict(size=12, line=dict(width=2, color='DarkSlateGrey')), selector=dict(mode='markers'))
        all_graphs.append(event_flag_graph)
    if event_ctr:
        event_ctr_graph = px.scatter(df, title=EVENT_CTR, x=DATETIME, y=EVENT_CTR, color=TAG_ID, symbol=SRC_ID, symbol_sequence=symbol_sequence)
        event_ctr_graph.update_traces(marker=dict(size=12, line=dict(width=2, color='DarkSlateGrey')), selector=dict(mode='markers'))
        all_graphs.append(event_ctr_graph)
    if ttfp:
        data = {TIMESTAMP_DELTA:[], TAGS_COUNT:[], NEW_TAGS:[]}
        tags_count = []
        # iterate all integers from 0 to the largest timestamp_delta as values for X
        for i in range(int(math.ceil(df[TIMESTAMP_DELTA].iloc[-1]))+1):
            new_tags = []
            # for every timestamp_delta value (i) add all NEW tags received in that timestamp_delta
            for row in df.query('timestamp_delta < @i').itertuples(index=False):
                if not row.tag_id in tags_count and not row.tag_id in new_tags:
                    new_tags += [row.tag_id]
            tags_count += new_tags
            data[TIMESTAMP_DELTA] += ([i])
            data[TAGS_COUNT] += [len(tags_count)]
            data[NEW_TAGS] += [new_tags]
        ttfp_graph = px.line(pd.DataFrame(data), x=TIMESTAMP_DELTA, y=TAGS_COUNT, title=TTFP,hover_data=[TIMESTAMP_DELTA,TAGS_COUNT,NEW_TAGS], markers=True)
        all_graphs.append(ttfp_graph)
    #generate
    file_path = os.path.join(ARTIFACTS_DIR, dir, f"{name_prefix}data_graphs.html")
    if not os.path.exists(os.path.dirname(file_path)):
        os.makedirs(os.path.dirname(file_path))
    with open(file_path, 'w') as f:
        for g in all_graphs:
            f.write(g.to_html(full_html=False, include_plotlyjs='cdn', include_mathjax='cdn'))
            f.write("<br>")
    if csv:
        df.to_csv(os.path.join(ARTIFACTS_DIR, dir, f"{name_prefix}all_data.csv"), index=False)

    return ttfp_graph

def single_log_search(test, s, found, fail_on_find=False, print_logs=True, additional_log="", target=DUT):    
    mqttc = test.get_mqttc_by_target(target)
    res = False
    for p in cert_mqtt.get_all_status_pkts(mqttc):
        if GW_LOGS in p:
            if cert_config.get_protobuf_by_target(test, target) and p[GW_LOGS]:
                # handle protobuf structure (when GW_LOGS is not empty)
                logs = p[GW_LOGS][LOGS]
            else:
                logs = p[GW_LOGS]
            for log in logs:
                if any([s in log]) and any([additional_log in log]) and (log not in found):
                    print(f"Log: {log}, Additional Log: {additional_log}")
                    found += [log]
                    res = True
                    if fail_on_find:
                        if test.rc == TEST_PASSED:
                            test= test.add_reason("Test functionality passed")
                        test.add_reason(f"Found {s}")
                        test.rc = TEST_FAILED
                        print(found)
                        return test, res, found
                    if print_logs:
                        print_pkt(s)
    return test, res, found

def gw_logs_search(test, strings, scan_time=GW_LOG_PERIOD+5, print_logs=False, fail_on_find=False):
    """searching for specific logs in mqtt status topic in GW_LOGS field

    :param WltTest test: test running
    :param [str] strings: list of logs to search
    :param int scan_time: time to scan for logs, defaults to GW_LOG_PERIOD+5
    :return WltTest: test with updated results
    """
    start_time = datetime.datetime.now()
    print(f"Searching for {strings} log in MQTT status topic.\nFail on find is set to {fail_on_find}")
    found = []
    while (len(strings) > len(found)):
        for s in strings:
            test, res, found = single_log_search(test, s, found, fail_on_find, print_logs)
            if res:
                break
        if (datetime.datetime.now() - start_time).seconds >= scan_time:
            if not fail_on_find:
                test.add_reason(f"Didnt find logs in [{scan_time}] seconds")
                print(test.reason)
                test.rc = TEST_FAILED
            break
    if test.rc == TEST_PASSED:
        if not fail_on_find:
            print(f"SUCCESS found all [{strings}]")
        else:
            print(f"SUCCESS Didnt find [{strings}]")
    return test

def gw_action_status_search(test, action_idx, status_code, target=DUT):
    """searching for action returned status code in mqtt status topic in ACTION field

    :param WltTest test: test running
    :param int action_idx: sent action index
    :param int status_code: expected status code for action
    :return WltTest: test with updated results
    """
    mqttc = test.get_mqttc_by_target(target)
    start_time = datetime.datetime.now()
    print(f"Searching for action idx ({action_idx}) update log in MQTT status topic")
    while (datetime.datetime.now() - start_time).seconds < GW_LOG_PERIOD:
        for p in cert_mqtt.get_all_status_pkts(mqttc):
            # JSON
            if ((ACTION in p) and (p[ACTION] == action_idx) and
                (STATUS_CODE_STR in p) and (p[STATUS_CODE_STR] == status_code) and
                (STEP not in p or p[STEP] == FINAL_OTA_STEP)):
                return test
            # Protobuf - when succeed status is not sent
            if ((ACTION_STATUS in p) and (p[ACTION_STATUS][ACTION] == action_idx) and
                STATUS_CODE not in p[ACTION_STATUS] and
                (STEP not in p[ACTION_STATUS] or p[ACTION_STATUS][STEP] == FINAL_OTA_STEP)):
                return test
    test.add_reason(f"ActionStatus message (idx={action_idx} status={status_code}) not found in {GW_LOG_PERIOD} sec")
    print(test.reason)
    test.rc = TEST_FAILED
    return test

def get_gw_logs_packets(test, last=False, print_log=True, target=DUT):
    """
    gets gw logs pkts
    :param WltTest test: test with gw that it's info will be retreived
    :param bool last: set to True to get only the last pkt caught, defaults to False
    :return pkt/list[pkt]: logs pkts list/last status pkt received
    """
    mqttc = test.get_mqttc_by_target(target)
    cert_config.gw_logs_action(test)
    pkts = []
    for p in cert_mqtt.get_all_status_pkts(mqttc):
        if GW_LOGS in p:
            if print_log:
                print("GW logs packet:\n", p[GW_LOGS])
            logs = p[GW_LOGS][LOGS] if test.tester.protobuf else p[GW_LOGS]
            pkts += [log for log in logs]
    if pkts and last:
        return pkts[len(pkts)-1]
    return pkts

def get_gw_type(mqttc):
    messages = cert_mqtt.get_all_status_pkts(mqttc)
    for msg in messages:
        if GW_STATUS in msg: # protobuf
            return msg[GW_STATUS][GW_TYPE], msg
        if GW_CONF in msg: # JSON
            return msg[GW_TYPE], msg
    return None, None

def get_module_if_pkt(test):
    cert_config.send_brg_action(test, ag.ACTION_GET_MODULE, interface=1)
    mgmt_type = [m for m in ag.MODULES_LIST if "ModuleIf" in m.__name__]
    test, pkts = scan_for_mgmt_pkts(test, mgmt_type=mgmt_type)

    if test.rc == TEST_FAILED:
        return test, NO_RESPONSE
    else:
        print(pkts[-1][MGMT_PKT].pkt)
        return test, pkts[-1][MGMT_PKT].pkt

def get_gw_api_version(mqttc):
    messages = cert_mqtt.get_all_status_pkts(mqttc)
    for msg in messages:
        if GW_CONF in msg: # JSON
            return msg[GW_CONF][GW_API_VERSION]
        if GW_STATUS in msg: # protobuf
            return msg[GW_STATUS][GW_API_VERSION]
    return None

def get_cfg_hash(test):
    utPrint(f"Fetching BRG cfg hash for BRG {test.active_brg.id_str}", "BLUE")
    test, module_if_pkt = get_module_if_pkt(test)
    if test.rc == TEST_FAILED:
        return test, 0
    else:
        return test, module_if_pkt.cfg_hash


def brg_restore_defaults_check(test, target=DUT):
    print("Starting Restore Defaults Check")
    start_time = datetime.datetime.now()
    found = False
    revived = False
    output = ""
    while not found:
        last_pkt = get_brg_cfg_pkts(test=test, cfg_info=True, last=True, target=target)
        if last_pkt:
            print(f"Got pkt after {(datetime.datetime.now() - start_time).seconds} sec!")
            wlt_pkt = WltPkt(last_pkt)
            print(f"SUCCESS: Found pkt from brg: {wlt_pkt}")
            found = True # exit
            revived = True
            output = "SUCCESS: brg is alive and restored to defaults!"
        if (datetime.datetime.now() - start_time).seconds > ACTION_LONG_TIMEOUT:
            print(f"FAILURE: Can't find bridge! Didn't get config pkt after {ACTION_LONG_TIMEOUT} seconds!")
            break
        print_update_wait()
    return test, revived, output

# Pwr Mgmt
def brg_pwr_mgmt_turn_on(test):
    utPrint("Sending pwr_mgmt static mode configuration - 30 seconds ON, 60 seconds SLEEP!", "BLUE")
    module = test.active_brg.pwr_mgmt
    # send pwr mgmt module packet
    wltpkt = WltPkt(hdr=DEFAULT_HDR, pkt=module(module_type=ag.MODULE_PWR_MGMT, msg_type=ag.BRG_MGMT_MSG_TYPE_CFG_SET,
                                                      api_version=ag.API_VERSION_LATEST,seq_id=random.randrange(99),
                                                      brg_mac=test.active_brg.id_int, static_on_duration=30, static_sleep_duration=60,
                                                      dynamic_leds_on=0,dynamic_keep_alive_period=0, dynamic_keep_alive_scan=0,
                                                      dynamic_on_duration=0,dynamic_sleep_duration=0))
    test = cert_config.brg_configure(test=test, cfg_pkt=wltpkt, module=module)[0]

    if test.rc == TEST_FAILED:
        test.add_reason("Turning pwr mgmt ON failed, Didn't receive GW MEL pwr mgmt ON pkt")
    else:
        utPrint("SUCCESS! pwr mgmt static mode turned on!", "GREEN")
    return test, wltpkt

def brg_pwr_mgmt_turn_off(test):
    utPrint("Turning pwr mgmt OFF - sending default configuration!", "BLUE")
    module = test.active_brg.pwr_mgmt
    start_time = datetime.datetime.now()
    wltpkt = WltPkt(hdr=DEFAULT_HDR, pkt=module(module_type=ag.MODULE_PWR_MGMT, msg_type=ag.BRG_MGMT_MSG_TYPE_CFG_SET,
                                                      api_version=ag.API_VERSION_LATEST,seq_id=random.randrange(99),
                                                      brg_mac=test.active_brg.id_int,static_leds_on=1,
                                                      static_keep_alive_period=0,static_keep_alive_scan=0,
                                                      static_on_duration=0,static_sleep_duration=0,
                                                      dynamic_leds_on=0,dynamic_keep_alive_period=0,
                                                      dynamic_keep_alive_scan=0,dynamic_on_duration=0,dynamic_sleep_duration=0))
    found = NOT_FOUND
    while found != DONE:
        test, found = cert_config.brg_configure(test=test, cfg_pkt=wltpkt, module=module, wait=False)
        if ((datetime.datetime.now() - start_time).seconds > (ag.PWR_MGMT_DEFAULTS_KEEP_ALIVE_PERIOD + 1)):
            test.add_reason(f"Didn't receive GW MEL pwr mgmt OFF ack after {ag.PWR_MGMT_DEFAULTS_KEEP_ALIVE_PERIOD + 1} seconds")
            test.rc = TEST_FAILED
            break
        print_update_wait()
    if found == DONE:
        utPrint(f"FOUND off pkt after {(datetime.datetime.now() - start_time)} secs", "GREEN")
        utPrint("SUCCESS! pwr mgmt static mode turned off!", "GREEN")
    return test

# LEDs tests funcs
def check_input_n_try_again(value):
    # check for valid input char - only 'Y', 'y', 'N' or 'n'
    while value.lower() != 'y' and value.lower() != 'n':
        utPrint("Wrong input, Please try Again!\n", "RED")
        value = input()
    return value

# Executed only when the received value is 'n'!
def value_check_if_y(test, received_value, stage):
    # check if the received value is different from the expected value
    if 'y' != received_value.lower():
        test.rc = TEST_FAILED
        test.add_reason(f"{stage} failed")
    return test


##########################################
# Signal Indicator functions
##########################################
def dual_polarization_ant_boards_get():
    return [ag.BOARD_TYPE_MINEW_SINGLE_BAND_V0, ag.BOARD_TYPE_MINEW_DUAL_BAND_V0,
            ag.BOARD_TYPE_ENERGOUS_V2, ag.BOARD_TYPE_ERM_V0, ag.BOARD_TYPE_ERM_V1,
            ag.BOARD_TYPE_MINEW_POE_V0]

def exp_sig_ind_pkts(tx_brg, rx_brg, cycles):
    if tx_brg.board_type in dual_polarization_ant_boards_get():
        tx_brg_ant_polarization_num = 2
    else:
        tx_brg_ant_polarization_num = 1
    if rx_brg.board_type in dual_polarization_ant_boards_get():
        rx_brg_ant_polarization_num = 2
    else:
        rx_brg_ant_polarization_num = 1

    expected = cycles * tx_brg_ant_polarization_num * rx_brg_ant_polarization_num
    # Allow missing 1 pkt
    return [expected - 1, expected]

def exp_sig_ind_pkts2(tx_brg, rx_brg, cycles):
    if tx_brg.board_type in dual_polarization_ant_boards_get():
        tx_brg_ant_polarization_num = 2
    else:
        tx_brg_ant_polarization_num = 1
    if rx_brg.board_type in dual_polarization_ant_boards_get():
        rx_brg_ant_polarization_num = 2
    else:
        rx_brg_ant_polarization_num = 1

    expected = cycles * tx_brg_ant_polarization_num * rx_brg_ant_polarization_num
    return expected

def sig_ind_pkts_fail_analysis(tx_brg, rx_brg, cycles, received_pkts):

    expected = exp_sig_ind_pkts2(tx_brg, rx_brg, cycles)
    print(f"Expected pkts: {expected}, Received pkts: {len(received_pkts)}")
    # Allow missing 25% max
    if int(0.75 * expected) <= len(received_pkts) <= int(1.25 * expected):
        return False
    return True

def get_all_sig_ind_pkts(test=None, rx_brg=None, tx_brg=None):
    if rx_brg == test.brg1:
        all_sensor_packets = cert_mqtt.get_all_brg1_ext_sensor_pkts(test=test, is_unified=True, target=TESTER)
    elif rx_brg == (test.dut.internal_brg if cert_config.is_gw(test.dut) else test.dut):
        all_sensor_packets = cert_mqtt.get_all_sensor_pkts(test=test, is_unified=True, target=DUT)
    signal_ind_pkts = []
    for p in all_sensor_packets:
        sensor_id = (f"{p[UNIFIED_SENSOR_PKT].pkt.sensor_ad_type:02X}"
                     f"{p[UNIFIED_SENSOR_PKT].pkt.sensor_uuid_msb:02X}"
                     f"{p[UNIFIED_SENSOR_PKT].pkt.sensor_uuid_lsb:02X}")
        if (sensor_id == f"{ag.SENSOR_SERVICE_ID_SIGNAL_INDICATOR:06X}" and
            p[ALIAS_BRIDGE_ID] == rx_brg.id_alias and f"{p[UNIFIED_SENSOR_PKT].pkt.sensor_mac:012X}" == tx_brg.id_alias):
            signal_ind_pkts.append(p)
    return signal_ind_pkts

def output_power_check(test, received_signal_ind_pkts, tx_brg_):
    output_power_default = tx_brg_.max_output_power_dbm - tx_brg_.datapath().output_power

    for p in received_signal_ind_pkts:
        if p[UNIFIED_SENSOR_PKT].pkt.signal_indicator_payload.output_power != output_power_default:
            test.rc = TEST_FAILED
            test.add_reason("output power of internal brg is incorrect!\n"
                            f"got:{p[UNIFIED_SENSOR_PKT].pkt.signal_indicator_payload.output_power}, expected: {output_power_default}\n")
    return test

def rssi_check(test, received_signal_ind_pkts):
    threshold_rssi = [0, 80]
    for p in received_signal_ind_pkts:
        if not threshold_rssi[0] < p[UNIFIED_SENSOR_PKT].pkt.rssi < threshold_rssi[1]:
            test.rc = TEST_FAILED
            test.add_reason("rssi value is wrong, out of 0 to 80 ")

    return test


def rx_tx_antenna_check(test, received_signal_ind_pkts, tx_brg_, rx_brg_, cycles):

    # Allow to miss 1 packet or get 1 extra packet
    expected = range(int(cycles * 0.5), cycles + 2)

    received = len(get_polar_signal_ind_pkt(received_signal_ind_pkts, rx_ant=0, tx_ant=0))
    if received not in expected:
        test.rc = TEST_FAILED
        test.add_reason(f"rx_ant=0 tx_ant=0 expected={cycles} received={received}")

    if tx_brg_.board_type in dual_polarization_ant_boards_get():
        received = len(get_polar_signal_ind_pkt(received_signal_ind_pkts, rx_ant=0, tx_ant=1))
        if received not in expected:
            test.rc = TEST_FAILED
            test.add_reason(f"rx_ant=0 tx_ant=1 expected={cycles} received={received}")

    if rx_brg_.board_type in dual_polarization_ant_boards_get():
        received = len(get_polar_signal_ind_pkt(received_signal_ind_pkts, rx_ant=1, tx_ant=0))
        if received not in expected:
            test.rc = TEST_FAILED
            test.add_reason(f"rx_ant=1 tx_ant=0 expected={cycles} received={received}")

    if (rx_brg_.board_type in dual_polarization_ant_boards_get() and
            tx_brg_.board_type in dual_polarization_ant_boards_get()):
        received = len(get_polar_signal_ind_pkt(received_signal_ind_pkts, rx_ant=1, tx_ant=1))
        if received not in expected:
            test.rc = TEST_FAILED
            test.add_reason(f"rx_ant=1 tx_ant=1 expected={cycles} received={received}")
    return test


def get_polar_signal_ind_pkt(pkts, rx_ant, tx_ant):
    return [p for p in pkts if p[UNIFIED_SENSOR_PKT].pkt.signal_indicator_payload.rx_antenna ==
            rx_ant and p[UNIFIED_SENSOR_PKT].pkt.signal_indicator_payload.tx_antenna == tx_ant]


def output_power_supported(board_type, output_power):
    if board_type in [ag.BOARD_TYPE_FANSTEL_WIFI_V0, ag.BOARD_TYPE_FANSTEL_LAN_V0]:
        return output_power in FANSTEL_GW_SUPPORTED_VALUES
    elif board_type in ENERGOUS_BOARD_TYPES_GROUP:
        return output_power in ENERGOUS_GROUP_SUPPORTED_VALUES
    elif board_type == ag.BOARD_TYPE_ENERGOUS_V1:
        return output_power in ENERGOUS_V1_SUPPORTED_VALUES
    else:
        return output_power in ag.OUTPUT_POWER_2_4_SUPPORTED_VALUES


def validate_received_packets(pkts_array):
    for pkt in pkts_array:
        # Check all required fields are present
        if TIMESTAMP not in pkt:
            return False, "timestamp field is missing in some of the packets"
        if ALIAS_BRIDGE_ID not in pkt:
            return False, "alias_bridge_id field is missing in some of the packets"
        if PAYLOAD not in pkt:
            return False, "payload field is missing in some of the packets"
        if SEQUENCE_ID not in pkt:
            return False, "sequence_id field is missing in some of the packets"
        # Check that the payload length is either 62 or 74 hex characters (equevelnt to 31 or 37 bytes)
        if len(pkt[PAYLOAD]) != 62 and len(pkt[PAYLOAD]) !=74:
            return False, f"Payload length is invalid for packet {pkt[PAYLOAD]}"
    return True, ""


def wiliot_pkts_validation(test, all_messages_in_test, all_data_pkts):
    PHASE_NAME = "Wiliot packets validation"
    phase_run_print(PHASE_NAME)
    wiliot_pkts_validation_phase = cert_utils.Phase(PHASE_NAME, rc=TEST_PASSED)

    if len(all_messages_in_test) == 0:
        wiliot_pkts_validation_phase.rc = TEST_FAILED
        wiliot_pkts_validation_phase.reason = "No packets to validate"

    if wiliot_pkts_validation_phase.rc != TEST_FAILED:
        wiliot_pkts_validation_phase = timestamps_validation(wiliot_pkts_validation_phase, all_messages_in_test, test.dut.upload_wait_time)

    if wiliot_pkts_validation_phase.rc != TEST_FAILED:
        wiliot_pkts_validation_phase = seq_id_validation(wiliot_pkts_validation_phase, all_data_pkts)

    field_functionality_pass_fail_print(wiliot_pkts_validation_phase, PHASE_NAME)
    test.add_phase(wiliot_pkts_validation_phase)
    return test


def seq_id_validation(wiliot_pkts_validation_phase, all_data_pkts):
    # Dedup packet if it is aggregated packets with the same sequenceId
    all_data_pkts = dedup_aggregated_packets(all_data_pkts)
    required_sequenceId = 0
    # check that for every packet received the sequenceId is incremental:
    for idx, pkt in enumerate(all_data_pkts):
        # check that there is sequenceId in all packets
        if SEQUENCE_ID not in pkt:
            wiliot_pkts_validation_phase.rc = TEST_FAILED
            wiliot_pkts_validation_phase.reason = f'No sequenceId in packet {pkt[PAYLOAD]}.'
            break
        if idx == 0:
            required_sequenceId = all_data_pkts[0][SEQUENCE_ID]
        pkt_sequenceId = pkt[SEQUENCE_ID]
        if pkt_sequenceId != required_sequenceId:
            wiliot_pkts_validation_phase.rc = TEST_FAILED
            wiliot_pkts_validation_phase.reason = (f'SequenceId is not incremental. Expected {required_sequenceId}, received {pkt_sequenceId}, '
                                                    'this may be caused by packets drops in the wifi chip side')
            break
        required_sequenceId += 1
    if len(all_data_pkts) == 0:
        wiliot_pkts_validation_phase.rc = TEST_FAILED
        wiliot_pkts_validation_phase.reason = "No packets to validate"
    return wiliot_pkts_validation_phase


def dedup_aggregated_packets(all_data_pkts):
    deduped_packets = []
    for pkt in all_data_pkts:
        if AGGREGATED_PAYLOAD not in pkt:
            deduped_packets.append(pkt)
        else:
            # Check if a packet with the same AGGREGATED_PAYLOAD already exists
            already_exists = any(existing_pkt[AGGREGATED_PAYLOAD] == pkt[AGGREGATED_PAYLOAD] 
                                for existing_pkt in deduped_packets 
                                if AGGREGATED_PAYLOAD in existing_pkt)
            if not already_exists:
                deduped_packets.append(pkt)

    return deduped_packets


def timestamps_validation(wiliot_pkts_validation_phase, all_messages_in_test, upload_wait_time):
    previous_ts = 0
    for full_pkt in all_messages_in_test:
        if full_pkt.mqtt_timestamp - full_pkt.body[TIMESTAMP] >= 10000:
            wiliot_pkts_validation_phase.rc = TEST_FAILED
            wiliot_pkts_validation_phase.reason = f'More then 10 seconds GW publication and MQTT receive time'
            return wiliot_pkts_validation_phase

        if PACKETS in full_pkt.body_ex:
            for idx, inner_pkt in enumerate(full_pkt.body_ex[PACKETS]):
                if TIMESTAMP not in inner_pkt:
                    wiliot_pkts_validation_phase.rc = TEST_FAILED
                    wiliot_pkts_validation_phase.reason = f"No timestamps in inner packet, for pkt {inner_pkt}"
                    return wiliot_pkts_validation_phase
                if idx == 0:
                    if full_pkt.body[TIMESTAMP] - inner_pkt[TIMESTAMP] >= 10000 + upload_wait_time and \
                    previous_ts < inner_pkt[TIMESTAMP]:
                        wiliot_pkts_validation_phase.rc = TEST_FAILED
                        wiliot_pkts_validation_phase.reason = f'More then {10 + upload_wait_time}'
                        f' seconds between publication and inner message,for ts {inner_pkt[TIMESTAMP]}'
                        return wiliot_pkts_validation_phase
                    previous_ts = inner_pkt[TIMESTAMP]
                else:
                    if inner_pkt[TIMESTAMP] < previous_ts:
                        wiliot_pkts_validation_phase.rc = TEST_FAILED
                        wiliot_pkts_validation_phase.reason = f'Timestamp is not incremental for inner packet {inner_pkt[PAYLOAD]}'
                        return wiliot_pkts_validation_phase
                    previous_ts = inner_pkt[TIMESTAMP]
    return wiliot_pkts_validation_phase

###################   Stress test helper functions   ###################

def generate_graph_stress_test(test, results, test_pkts_received):
    # Create DataFrame from results list [pps1, percentage1, pps2, percentage2, ...]
    graph_data = []
    for i in range(0, len(results), 2):
        if i + 1 < len(results):
            graph_data.append({'pkts_per_sec': results[i], 'received_pps': results[i + 1]})
    
    graph_df = pd.DataFrame(graph_data)
    html_file_path = os.path.join(ARTIFACTS_DIR, test.dir, 'stress_graph.html')
    
    # First graph: percentage received vs packets per second
    fig1 = px.line(graph_df, x='pkts_per_sec', y='received_pps',
                   title='Packets Per Second Uploaded vs Packets Per Second Advertised',
                   labels={'pkts_per_sec': 'Advertised PPS', 'received_pps': 'Uploaded PPS'},
                   markers=True, text='received_pps')
    
    # Set y-axis to [0 - highest_pps] scale
    fig1.update_yaxes(range=[0, results[-2]])
    
    # Position text labels next to the markers
    fig1.update_traces(textposition="top right")
    
    # Second graph: sequenceID vs time
    seq_id_fig = None
    seq_id_data = []
    for pkt in test_pkts_received:
        if SEQUENCE_ID in pkt and TIMESTAMP in pkt:
            seq_id_data.append({
                SEQUENCE_ID: pkt[SEQUENCE_ID],
                TIMESTAMP: pkt[TIMESTAMP]
            })
    
    if seq_id_data:
        seq_id_df = pd.DataFrame(seq_id_data)
        seq_id_df = seq_id_df.sort_values(by=TIMESTAMP)
        # Convert timestamp to datetime for better display
        seq_id_df['datetime'] = seq_id_df[TIMESTAMP].apply(lambda x: datetime.datetime.fromtimestamp(x/1e3))
        seq_id_fig = px.scatter(seq_id_df, x='datetime', y=SEQUENCE_ID,
                                title='Sequence ID vs Time',
                                labels={'datetime': 'Time', SEQUENCE_ID: 'Sequence ID'})
    
    # Write both graphs to HTML file
    with open(html_file_path, 'w') as f:
        f.write(fig1.to_html(full_html=False, include_plotlyjs='cdn', include_mathjax='cdn'))
        f.write("<br>")
        if seq_id_fig:
            f.write(seq_id_fig.to_html(full_html=False, include_plotlyjs='cdn', include_mathjax='cdn'))


def stress_analysis(test, pps, sent_pkts, received_pkts):

    _sent_pkts = [p[12:] for p in sent_pkts]
    sent_df = pd.DataFrame(_sent_pkts, columns=[PACKETS])
    received_df = pd.DataFrame(received_pkts, columns=[PACKETS])

    # No need to drop duplicates, in the stress test each packet is sent only once
    merged_df = pd.merge(sent_df, received_df, on=PACKETS, how='inner')
    pkts_sent_count = len(sent_df)
    pkts_received_count = len(merged_df)

    # Prints and calculations
    percentage_received = round(pkts_received_count * 100 / pkts_sent_count)
    utPrint(f'Sent: {pkts_sent_count}, Received: {pkts_received_count} ({percentage_received}%)', "BLUE")
    received_pps = pps * percentage_received / 100
    
    # PASS/FAIL logic
    if percentage_received < 1: # If less than 1% of the packets were received, fail the test
        test.set_phase_rc(str(pps), TEST_FAILED)
        test.add_phase_reason(str(pps), f"{percentage_received}% of the packets were scanned & uploaded by the gateway")
    else:
        test.set_phase_rc(str(pps), TEST_PASSED)
        test.add_phase_reason(str(pps), f"received pps: {received_pps} ({percentage_received}% of packets)")

    return test, received_pps


def generate_adv_payload(test_indicator, unique_pkt=False):
    # Keep last 4 bytes as zeroes so for incrementing them in FW 'ble_sim'
    adva = hex2alias_id_get(get_random_hex_str(12))
    unique_pkt_byte = get_random_hex_str(2) if unique_pkt == False else "00"
    payload = (ag.Hdr(group_id=ag.GROUP_ID_UNIFIED_PKT_V2).dump() + test_indicator +
               get_random_hex_str(32) + unique_pkt_byte + "00000000")
    return adva + payload

def change_endianness(hex_str: str) -> str:
    return ''.join(f"{b:02X}" for b in bytes.fromhex(hex_str)[::-1])
