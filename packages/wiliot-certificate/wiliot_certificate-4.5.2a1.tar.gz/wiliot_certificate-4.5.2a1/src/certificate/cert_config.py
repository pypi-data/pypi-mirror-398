from certificate.cert_defines import *
from certificate.cert_prints import *
from certificate.wlt_types import *
import certificate.cert_common as cert_common
import certificate.cert_protobuf as cert_protobuf
import certificate.cert_mqtt as cert_mqtt
import datetime, string, json, random, inspect

BLE5_MAX_RETRIES = BLE5_MAX_DURATION_MS//20

#################################
# GW
#################################

def is_gw(obj):
    return hasattr(obj, 'mqttc') and hasattr(obj, 'id_str')

def get_protobuf_by_target(test, target):
    return test.dut.protobuf if is_gw(test.dut) and target == DUT else test.tester.protobuf

def gw_configure(test, cfg={}, version="", extended_cfg={}, ret_pkt=False, wait=False, serialization_change=False, target=DUT):
    mqttc = test.get_mqttc_by_target(target)
    cfg = cfg if cfg else get_default_gw_dict(test, target=target)
    gw_config = create_gw_config(test, cfg, target=target, version=version)
    gw_config[GW_CONF][ADDITIONAL].update(extended_cfg)
    gw_config[GW_CONF].update(extended_cfg)
    if get_protobuf_by_target(test, target):
        payload = cert_protobuf.downlink_to_pb(gw_config)
        utPrint(f"Configuring GW with cfg pkt:\n{payload}", "BLUE")
    else:
        if not serialization_change:
            gw_config[GW_CONF][ADDITIONAL][SERIALIZATION_FORMAT] = JSON
        payload = json.dumps(gw_config)
        utPrint(f"Configuring GW with cfg pkt:\n{payload}", "BLUE")
    mqttc.flush_pkts()
    mqttc.publish(mqttc.update_topic, payload=payload, qos=1)
    if wait:
        # Search for update packet
        start_time = datetime.datetime.now()
        while (datetime.datetime.now() - start_time).seconds < DEFAULT_GW_FIELD_UPDATE_TIMEOUT:
            for p in cert_mqtt.get_all_status_pkts(mqttc):
                if GW_CONF in p or GW_STATUS in p:
                    test.gw_api_version = (p.get(GW_CONF, {}).get(GW_API_VERSION) or p.get(GW_STATUS, {}).get(GW_API_VERSION))
                    if target == DUT and is_gw(test.dut):
                        test.dut.gw_api_version = test.gw_api_version
                    print_pkt(p)
                    utPrint("SUCCESS: Found GW cfg", "GREEN")
                    wait_time_n_print(2)
                    if ret_pkt:
                        return test, p
                    else:
                        return test, DONE
            print_update_wait()
        test.rc = TEST_FAILED
        test.add_reason(f"FAILURE: GW cfg not found after {DEFAULT_GW_FIELD_UPDATE_TIMEOUT} seconds!")
        return test, NO_RESPONSE
    else:
        utPrint("Sent GW cfg, Wait is set to False", "BLUE")
        return test, DONE

def gw_fw_upgrade(test, version, board_type, target=DUT):
    
    # GW FW upgrade by action
    gw_config = dict({ACTION: ACTION_GW_OTA,
                    # The URL here is for testing. The cloud using the BTM urls
                    IMG_DIR_URL: f"https://api.us-east-2.prod.wiliot.cloud/v1/bridge/type/{board_type}/version/{version[BLE_VERSION]}/binary/",
                    WIFI_VERSION: version[WIFI_VERSION],
                    BLE_VERSION: version[BLE_VERSION]})
    if test.tester.protobuf:
        payload = cert_protobuf.downlink_to_pb(gw_config)
    else:
        payload = json.dumps(gw_config)
    utPrint(f"Upgrading GW with action pkt:\n{payload}", "BLUE")

    mqttc = test.get_mqttc_by_target(target)
    mqttc.flush_pkts()
    mqttc.publish(mqttc.update_topic, payload=payload, qos=1)

def create_gw_config(test, cfg, target=DUT, version=""):
    gw = test.dut if is_gw(test.dut) and target == DUT else test.tester
    if version:
        conf = {LAT: GW_LATITUDE_DEFAULT, LNG: GW_LONGITUDE_DEFAULT, WIFI_VERSION: version[WIFI_VERSION],
                BLE_VERSION: version[BLE_VERSION], ADDITIONAL: dict(cfg)}
    elif gw.gw_orig_versions:
        conf = {LAT: GW_LATITUDE_DEFAULT, LNG: GW_LONGITUDE_DEFAULT, WIFI_VERSION: gw.gw_orig_versions[WIFI_VERSION],
                BLE_VERSION: gw.gw_orig_versions[BLE_VERSION], ADDITIONAL: dict(cfg)}
    # Protection for FDM gw config
    else:
        conf = {LAT: GW_LATITUDE_DEFAULT, LNG: GW_LONGITUDE_DEFAULT, ADDITIONAL: dict(cfg)}
    # If api version was not sent in gw info then the gw_api_version is None, we don't want to set it in the config
    if gw.gw_api_version is not None:
        conf[GW_API_VERSION] = gw.gw_api_version
    return dict({GW_CONF: conf})

def gw_downlink(test, raw_tx_data="", is_ota=False, version="", max_duration=100, max_retries=8, target=DUT):
    mqttc = test.get_mqttc_by_target(target)
    pkt = create_gw_downlink_pkt(test, raw_tx_data, is_ota, version=version, max_duration=max_duration, max_retries=max_retries, target=target)
    payload = cert_protobuf.downlink_to_pb(pkt) if get_protobuf_by_target(test, target) else json.dumps(pkt)
    mqttc.publish(mqttc.update_topic, payload=payload, qos=1)

def create_gw_downlink_pkt(test, raw_tx_data="", is_ota=False, version="", max_duration=100, max_retries=8, target=DUT):
    ret = dict({TX_PKT: raw_tx_data,
                TX_MAX_DURATION_MS: max_duration,
                TX_MAX_RETRIES: max_retries})
    if is_ota == False:
        ret[ACTION] = ACTION_ADVERTISING
    else:
        ret[ACTION] = ACTION_BRG_OTA
        ret[GW_ID] = test.dut.id_str if target == DUT and is_gw(test.dut) else test.tester.id_str
        # Determine destination bridge
        brg = get_brg_by_target(test, DUT if test.dut_is_bridge() else TESTER)
        ret[BRIDGE_ID] = brg.id_str
        ret[IMG_DIR_URL] = f"https://api.us-east-2.prod.wiliot.cloud/v1/bridge/type/{brg.board_type}/version/{version}/binary/"
        # Using a random uuid to force file download on the GW side
        ret[VER_UUID_STR] = ''.join(random.choices(string.digits, k=VER_MAX_LEN))
        ret[UPGRADE_BLSD] = False
        ret[TX_MAX_DURATION_MS] = 150
        utPrint(f"Publishing ACTION_BRG_OTA:\n{ret}", "BLUE")
    return ret

def get_default_gw_dict(test=None, target=DUT):
    if test:
        validation_schema = test.dut.validation_schema if target == DUT and is_gw(test.dut) else test.tester.validation_schema
    else:
        validation_schema = None
    gw_dict = {}

    def parse_properties(props):
        d = {}
        for prop_name, prop_desc in props.items():
            # If 'properties' key exists, recurse
            if "properties" in prop_desc:
                d[prop_name] = parse_properties(prop_desc["properties"])
            elif "default" in prop_desc:
                d[prop_name] = prop_desc["default"]
            else:
                # Set default values for known types if 'default' not specified
                prop_type = prop_desc.get("type")
                if prop_type == "string":
                    d[prop_name] = ""
                elif prop_type == "integer" or prop_type == "number":
                    d[prop_name] = 0
                elif prop_type == "boolean":
                    d[prop_name] = False
                elif prop_type == "array":
                    d[prop_name] = []
                elif prop_type == "object":
                    d[prop_name] = {}
        return d

    if validation_schema:
        gw_dict = parse_properties(validation_schema)
    else:
        gw_dict = dict({WLT_SERVER: PROD, USE_STAT_LOC: False,
                        SERIALIZATION_FORMAT: PROTOBUF, ACL: dict({ACL_MODE: ACL_DENY, ACL_BRIDGE_IDS: []})})
    return gw_dict

def config_gw_defaults(test, version="", target=DUT):
    gw = test.dut if target == DUT and is_gw(test.dut) else test.tester
    utPrint(f"Configuring gateway {gw.id_str} to defaults", "BLUE")
    return gw_configure(test, get_default_gw_dict(test, target=target), wait=True, version=version)

def config_gw_version(test, version, board_type=None, target=DUT):

    utPrint(f"Updating GW versions to {version[WIFI_VERSION]} , {version[BLE_VERSION]}", "BLUE")
    # Search for current api version
    response = cert_common.get_gw_info(test, target=target)
    if response == NO_RESPONSE:
        print("Didn't get GW_INFO response from GW!")
        return

    cur_api_version = 0
    if ENTRIES in response[GW_INFO]:
        if GW_API_VERSION in response[GW_INFO][ENTRIES]:
            cur_api_version = int(response[GW_INFO][ENTRIES][GW_API_VERSION][STR_VAL])
    else:
        if GW_API_VERSION in response[GW_INFO]:
            cur_api_version = int(response[GW_INFO][GW_API_VERSION])

    # Support for legacy esp api version below 206 where the upgrade was done by configuration and not action
    print(f'ESP api version: {cur_api_version}')
    if cur_api_version < 206:
        print("Legacy ESP - using old version configuration approach")
        gw_configure(test, get_default_gw_dict(test, target=target), version)
        return

    if not board_type:
        board_type = get_brg_by_target(test, target).board_type

    gw_fw_upgrade(test, version, board_type)

def gw_info_action(test, target=DUT):
    pkt = {ACTION: GET_INFO_ACTION}
    mqttc = test.get_mqttc_by_target(target)
    payload = cert_protobuf.downlink_to_pb(pkt) if get_protobuf_by_target(test, target) else json.dumps(pkt)
    mqttc.publish(mqttc.update_topic, payload=payload, qos=1)

def gw_reboot_action(test, target=DUT):
    pkt = {ACTION: REBOOT_GW_ACTION}
    payload = cert_protobuf.downlink_to_pb(pkt) if get_protobuf_by_target(test, target) else json.dumps(pkt)
    test.get_mqttc_by_target(target).publish(test.get_mqttc_by_target(target).update_topic, payload=payload, qos=1)

def gw_action(test, action, target=DUT):
    mqttc = test.get_mqttc_by_target(target)
    pkt = {ACTION: action}
    payload = cert_protobuf.downlink_to_pb(pkt) if get_protobuf_by_target(test, target) else json.dumps(pkt)
    mqttc.publish(mqttc.update_topic, payload=payload, qos=1)

def gw_log_period_action(test, period, target=DUT):
    pkt = {ACTION: f"{LOG_PERIOD_ACTION} {period}"}
    payload = cert_protobuf.downlink_to_pb(pkt) if get_protobuf_by_target(test, target) else json.dumps(pkt)
    test.get_mqttc_by_target(target).publish(test.get_mqttc_by_target(target).update_topic, payload=payload, qos=1)

def gw_logs_action(test, target=DUT):
    pkt = {ACTION: GET_LOGS}
    payload = cert_protobuf.downlink_to_pb(pkt) if get_protobuf_by_target(test, target) else json.dumps(pkt)
    test.get_mqttc_by_target(target).publish(test.get_mqttc_by_target(target).update_topic, payload=payload, qos=1)

def gw_status_wait(test, cond, str, time_limit, target=DUT): #cond gatewayLogs str test type
    mqttc = test.get_mqttc_by_target(target)
    mqttc.flush_pkts()
    start_time = datetime.datetime.now()
    while (datetime.datetime.now() - start_time).seconds < time_limit:
        for p in cert_mqtt.get_all_status_pkts(mqttc):
            if cond in p:
                if str in p[cond]:
                    print_pkt(p)
                    return
        print_update_wait()

#################################
# BRG
#################################

def get_brg_by_target(test, target):
    if target == DUT:
        return test.dut.internal_brg if is_gw(test.dut) else test.dut
    elif target == BRG1:
        return test.brg1
    elif target == TESTER:
        return test.tester.internal_brg
    return None

def fields_n_vals_dict_get(fields, values):
    # initiate fields and values
    fields_and_values = {}
    for field, value in zip(fields, values):
        fields_and_values[field] = int(value)
    # functionality run print
    print_string = generate_print_string(fields_and_values)
    functionality_run_print(print_string)
    return fields_and_values

def brg_configure(test, cfg_pkt=None, module=None, fields=[], values=[], wait=True, ret_cfg_pkt=False, ble5=False, target=DUT):
    brg = get_brg_by_target(test, target)
    mqttc = test.get_mqttc_by_target(target)
    if ble5:
        return brg_configure_ble5(test, cfg_pkt=cfg_pkt, module=module, fields=fields,
                                  values=values, ret_cfg_pkt=ret_cfg_pkt, wait=wait, target=target)
    retries = 3
    if not cfg_pkt:
        fields_n_vals = fields_n_vals_dict_get(fields, values)
        cfg_pkt = get_default_brg_pkt(test, pkt_type=module, target=target, **fields_n_vals)

    if not wait:
        gw_downlink(test=test, raw_tx_data=cfg_pkt.dump(), target=target)
        utPrint("Wait is set to False, not waiting for Bridge cfg ACK", "CYAN")
        return test, DONE
    else:
        mqttc.flush_pkts()

    # Search for update packet
    for retry in range(retries):
        gw_downlink(test=test, raw_tx_data=cfg_pkt.dump(), target=target)
        pkts_found = False
        seq_ids = []
        wlt_pkt = WltPkt()
        start_time = datetime.datetime.now()
        while (datetime.datetime.now() - start_time).seconds < DEFAULT_BRG_FIELD_UPDATE_TIMEOUT:
            pkts = cert_common.get_brg_cfg_pkts(test=test, target=target)
            if pkts:
                pkts_found = True
                for p in pkts:
                    wlt_pkt = WltPkt(p)
                    if seq_ids == [] or wlt_pkt.pkt.seq_id not in seq_ids:
                        print(wlt_pkt.pkt)
                        if cfg_pkt.pkt == wlt_pkt.pkt:
                            utPrint("SUCCESS: Bridge cfg", "GREEN")
                            return (test, DONE) if not ret_cfg_pkt else (test, wlt_pkt)
                        seq_ids.append(wlt_pkt.pkt.seq_id)
            print_update_wait()
        utPrint(f"brg_configure: No pkts found retry={retry}!", "WARNING")
    if not pkts_found:
        utPrint(f"brg_configure: No pkts found retry={retry}!", "RED")
        test.add_reason(f"brg_configure: No pkts found. retry={retry}")
    test.rc = TEST_FAILED
    if wlt_pkt.pkt:
        # In case of failure, we want to see if it's api version issue
        brg.api_version = wlt_pkt.pkt.api_version
        print(f"-->> api_version:{brg.api_version}\nFailed brg_configure with pkt ({cfg_pkt.pkt.__dict__})")
        test.add_reason(f"Failed brg_configure")
    return test, NO_RESPONSE

def brg_configure_ble5(test, cfg_pkt=None, module=None, fields=None, values=None, ret_cfg_pkt=False, wait=True, target=DUT):
    mqttc = test.get_mqttc_by_target(target)
    if not cfg_pkt:
        fields_n_vals = fields_n_vals_dict_get(fields, values)
        cfg_pkt = get_default_brg_pkt(test, pkt_type=module, target=target, **fields_n_vals)
    # Search for update packet
    mqttc.flush_pkts()

    num_of_tries = 0
    pkts_found = False
    seq_ids = []
    wlt_pkt = WltPkt()
    start_time = datetime.datetime.now()
    gw_downlink(test=test, raw_tx_data=cfg_pkt.dump(), max_duration=BLE5_MAX_DURATION_MS, max_retries=BLE5_MAX_RETRIES, target=target)
    if wait is False:
        return test, DONE
    while not pkts_found:
        if ((datetime.datetime.now() - start_time).seconds > BLE5_MAX_DURATION_SEC):
            if num_of_tries < 3:
                num_of_tries += 1
                start_time = datetime.datetime.now()
                gw_downlink(test=test, raw_tx_data=cfg_pkt.dump(), max_duration=BLE5_MAX_DURATION_MS, max_retries=BLE5_MAX_RETRIES, target=target)
                print(f"Brg configure - BLE5 mode : No pkts found after {BLE5_MAX_DURATION_SEC} seconds, in try number {num_of_tries}")
            else:
                test.add_reason(f"Brg configure - BLE5 mode : No pkts found after {BLE5_MAX_DURATION_SEC} seconds, in 3 tries")
                test.rc = TEST_FAILED
                time.sleep(1)
                mqttc.flush_pkts()
                return test, NO_RESPONSE
        pkts = cert_common.get_brg_cfg_pkts(test=test, target=target)
        if pkts:
            for p in pkts:
                wlt_pkt = WltPkt(p)
                if seq_ids == [] or wlt_pkt.pkt.seq_id not in seq_ids:
                    print(wlt_pkt.pkt)
                    if cfg_pkt.pkt == wlt_pkt.pkt:
                        utPrint("SUCCESS: Bridge cfg", "GREEN")
                        time.sleep(15)
                        mqttc.flush_pkts()
                        return (test, DONE) if not ret_cfg_pkt else (test, wlt_pkt)
                    seq_ids.append(wlt_pkt.pkt.seq_id)
        print_update_wait()

def send_brg_action(test, action_id, target=DUT, **kwargs):
    brg = get_brg_by_target(test, target)
    mqttc = test.get_mqttc_by_target(target)
    mqttc.flush_pkts()
    action_pkt = get_default_brg_pkt(test, pkt_type=eval_pkt(f'{ag.ACTIONS_DICT[action_id]}{brg.api_version}'), **kwargs)
    gw_downlink(test, raw_tx_data=action_pkt.dump(), target=target)

def backward_compatible_handler(test, pkt_type, **kwargs):
    datapath_output_power = 8
    energy_2400_output_power = 2
    calibration_output_power = 2
    init_params = inspect.signature(pkt_type.__init__).parameters
    safe_kwargs = {}
    for k, v in kwargs.items():
        if k in init_params:
             safe_kwargs[k] = v
        else:
            utPrint(f"WARNING: Parameter {k} not in {pkt_type.__name__} parameters, ignoring it!", "WARNING")

    if test.active_brg.api_version < ag.API_VERSION_V13:
        if "ModuleDatapathV12" in pkt_type.__name__ and BRG_OUTPUT_POWER not in safe_kwargs:
            safe_kwargs.update({BRG_OUTPUT_POWER: datapath_output_power})
        if "ModuleEnergy2400V12" in pkt_type.__name__ and BRG_OUTPUT_POWER not in safe_kwargs:
            safe_kwargs.update({BRG_OUTPUT_POWER: energy_2400_output_power})
        if "ModuleCalibrationV12" in pkt_type.__name__ and BRG_OUTPUT_POWER not in safe_kwargs:
            safe_kwargs.update({BRG_OUTPUT_POWER: calibration_output_power})
    return safe_kwargs

def get_default_brg_pkt(test, pkt_type, group_id=ag.GROUP_ID_GW2BRG, seq_id=0, target=DUT, **kwargs):
    brg = get_brg_by_target(test, target)
    seq_id = test.get_seq_id() if seq_id == 0 else seq_id
    safe_kwargs = backward_compatible_handler(test, pkt_type, **kwargs)
    # Bypass from default sub1g ep cfg of 0 (no energizing) ONLY if not using data simulation
    if "ModuleEnergySub1G" in pkt_type.__name__ and BRG_PATTERN not in safe_kwargs and test.data != DATA_SIMULATION:
        safe_kwargs.update({BRG_PATTERN: ag.SUB1G_ENERGY_PATTERN_ISRAEL})
    brg_pkt = WltPkt(hdr=ag.Hdr(group_id=group_id), pkt=pkt_type(brg_mac=brg.id_int if brg else 0, seq_id=seq_id, **safe_kwargs))
    return brg_pkt

def config_brg_defaults(test, modules=[], ble5=False, wait=True, target=DUT):
    failed_cfg = False
    brg = get_brg_by_target(test, target)
    modules = brg.modules if not modules else modules
    for module in modules:
        utPrint(f"Configuring {module.__name__} to defaults. board type[{brg.board_type}] api version[{brg.api_version}]", "BLUE")
        cfg_pkt = get_default_brg_pkt(test, module, target=target)
        if ble5:
            test, res = brg_configure_ble5(test=test, cfg_pkt=cfg_pkt, wait=wait, target=target)
        else:
            test, res = brg_configure(test=test, cfg_pkt=cfg_pkt, wait=wait, target=target)
        if res == NO_RESPONSE:
            utPrint(f"FAILURE: {module.__name__} not configured to defaults", "RED")
            failed_cfg = True
        else:
            utPrint(f"SUCCESS: {module.__name__} configured to defaults", "GREEN")
    return (test, DONE) if not failed_cfg else (test, NO_RESPONSE)

def brg_ota(test, ble_version, search_ack=True, ble5=False, target=DUT, upgrader=TESTER, timeout=VER_UPDATE_TIMEOUT):
    brg = get_brg_by_target(test, target)
    mqttc = test.get_mqttc_by_target(upgrader)

    if ble_version != brg.version:
        utPrint(f"Updating BRG version to {ble_version}", "BLUE")
        functionality_run_print(f"OTA for brg: {brg.id_str}")
        action_pkt = get_default_brg_pkt(test=test, pkt_type=eval_pkt(f'ActionGenericV{brg.api_version}'), action_id=ag.ACTION_REBOOT,
                                         target=target)
        # BRG OTA - Flush pkts ONLY before starting to avoid deletion of needed GW Logs which are in the status topic
        mqttc.flush_status_pkts()
        # If the bridge is configured to ble5 then we need to broadcast the reboot packet for 15 seconds
        if not ble5:
            gw_downlink(test, raw_tx_data=action_pkt.dump(), is_ota=True, version=ble_version, target=upgrader)
        else:
            gw_downlink(test=test, raw_tx_data=action_pkt.dump(), is_ota=True, version=ble_version, max_duration=BLE5_MAX_DURATION_MS, max_retries=BLE5_MAX_RETRIES, target=upgrader)

        # expected_hash=1 due to different cfgs and versions between builds
        test = cert_common.reboot_config_analysis(test=test, expected_hash=1, ble_version=ble_version, timeout=timeout)
        # for debug - print all logs to see failure reason
        cert_common.get_gw_logs_packets(test, print_log=True)
        if test.rc == TEST_FAILED and test.exit_on_param_failure:
            return test
        elif search_ack:
            test = cert_common.gw_action_status_search(test, ag.BRG_MGMT_MSG_TYPE_OTA_UPDATE, 0, target=upgrader)
            if test.rc == TEST_FAILED and test.exit_on_param_failure:
                return test
    else:
        test.add_reason(WANTED_VER_SAME)
    if test.rc == TEST_PASSED:
        brg.version = ble_version
        brg.update_modules()
    return test

def update_versions(test, versions, update_gw=True, update_brg=True, target=DUT):
    mqttc = test.get_mqttc_by_target(target)
    #update gw versions
    if update_gw:
        config_gw_version(test, versions, target=TESTER)
        # Search for update packet
        start_time = datetime.datetime.now()
        found = {BLE_VERSION: False, WIFI_VERSION: False}
        while not all([found[version] for version in found]):
            duration = (datetime.datetime.now() - start_time).seconds
            for p in cert_mqtt.get_all_status_pkts(mqttc):
                if GW_CONF in p or GW_STATUS in p:
                    print("\nConfig pkts:")
                    print_pkt(p)
                    bkv = BLE_VERSION.replace('Chip', '') if test.tester.protobuf else BLE_VERSION
                    wkv = WIFI_VERSION.replace('Chip', '') if test.tester.protobuf else WIFI_VERSION
                    ckv = GW_STATUS if test.tester.protobuf else GW_CONF
                    if p[ckv][bkv] == versions[BLE_VERSION]:
                        found[BLE_VERSION] = True
                    if p[ckv][wkv] == versions[WIFI_VERSION]:
                        found[WIFI_VERSION] = True
                    if not all([found[version] for version in found]):
                        # WIFI configured, need to configure again for BLE
                        if duration > 5:
                            # First pkt may be received is GW "cfg ack" so skip it
                            print(f"\nVersions Update Status:\n{found}\nUpdate Time: {duration} seconds")
                            config_gw_version(test, versions, target=TESTER)
                    mqttc.flush_pkts()
            print_update_wait()
            if duration > VER_UPDATE_TIMEOUT:
                test.rc = TEST_FAILED
                failed_versions = " & ".join([f"{k}={v}" for k,v in versions.items() if not found[k]])
                test.add_reason(f"{failed_versions} not found after {VER_UPDATE_TIMEOUT} seconds!")
                print(f"\n{test.reason}")
                break
        wait_time_n_print(10)
    if not test.rc:
        if update_gw:
            print(f"\nGW versions updated successfully!\n")
        # update brg version if test is not an internal_brg test
        if update_brg and not test.internal_brg:
            test = brg_ota(test, ble_version=versions[BLE_VERSION], search_ack=False)

    return test
