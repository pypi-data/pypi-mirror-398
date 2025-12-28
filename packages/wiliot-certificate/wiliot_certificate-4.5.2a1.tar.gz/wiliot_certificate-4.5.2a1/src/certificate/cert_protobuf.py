
from certificate.cert_defines import *

import common.wltPb_pb2 as wpb

def action_pb(msg: dict):
    pb_msg = wpb.DownlinkMessage()
    pb_msg.gatewayAction.action = msg[ACTION]
    return pb_msg.SerializeToString()

def tx_pkt_pb(msg: dict):
    pb_msg = wpb.DownlinkMessage()
    pb_msg.txPacket.payload = bytes.fromhex(msg[TX_PKT])
    pb_msg.txPacket.maxDurationMs = msg[TX_MAX_DURATION_MS]
    pb_msg.txPacket.maxRetries = int(msg[TX_MAX_RETRIES])
    return pb_msg.SerializeToString()

def gw_ota_pb(msg: dict):
    pb_msg = wpb.DownlinkMessage()
    pb_msg.gatewayUpgrade.imageDirUrl = msg[IMG_DIR_URL]
    pb_msg.gatewayUpgrade.interfaceSwVersion = msg[WIFI_VERSION]
    pb_msg.gatewayUpgrade.bleSwVersion = msg[BLE_VERSION]
    return pb_msg.SerializeToString()

def brg_ota_pb(msg: dict):
    pb_msg = wpb.DownlinkMessage()
    pb_msg.bridgeUpgrade.bridgeId = msg[BRIDGE_ID]
    pb_msg.bridgeUpgrade.imageDirUrl = msg[IMG_DIR_URL]
    pb_msg.bridgeUpgrade.versionUuid = msg[VER_UUID_STR]
    pb_msg.bridgeUpgrade.upgradeBlSd = msg[UPGRADE_BLSD]
    pb_msg.bridgeUpgrade.rebootPacket = bytes.fromhex(msg[TX_PKT])
    pb_msg.bridgeUpgrade.txMaxDurationMs = msg[TX_MAX_DURATION_MS]
    pb_msg.bridgeUpgrade.txMaxRetries = msg[TX_MAX_RETRIES]
    return pb_msg.SerializeToString()

def gw_cfg_pb(msg: dict):
    pb_msg = wpb.DownlinkMessage()
    pb_msg.gatewayConfig.location.lat = msg[LAT]
    pb_msg.gatewayConfig.location.lng = msg[LNG]
    if WIFI_VERSION in msg.keys():
        pb_msg.gatewayConfig.interfaceSwVersion = msg[WIFI_VERSION]
    if BLE_VERSION in msg.keys():
        pb_msg.gatewayConfig.bleSwVersion = msg[BLE_VERSION]

    for key, val in msg[ADDITIONAL].items():
        # Skip lat & lng to create duplicate values
        if key == LAT or key == LNG:
            continue
        pb_value = wpb.GatewayConfigValue()
        if type(val) is int:
            pb_value.integerValue = val
        elif type(val) is float:
            pb_value.numberValue = val
        elif type(val) is str:
            pb_value.stringValue = val
        elif type(val) is bool:
            pb_value.boolValue = val
        elif type(val) is dict and key == ACL:
            pb_value.aclValue.mode_allow = ACL_DENY_VALUE if msg[ADDITIONAL][ACL][ACL_MODE] == ACL_DENY else ACL_ALLOW_VALUE
            ids_bytes = [bytes.fromhex(id) for id in msg[ADDITIONAL][ACL][ACL_BRIDGE_IDS]]
            pb_value.aclValue.ids.extend(ids_bytes)
        else:
            raise ValueError(f"Unsupported value type for key '{key}': {type(val)}")
        pb_msg.gatewayConfig.config[key].CopyFrom(pb_value)

    return pb_msg.SerializeToString()

def custom_message_pb(msg: dict):
    pb_msg = wpb.DownlinkMessage()

    for key, val in msg.items():
        pb_value = wpb.Value()
        if isinstance(val, int):
            pb_value.integerValue = val
        elif isinstance(val, float):
            pb_value.numberValue = val
        elif isinstance(val, str):
            pb_value.stringValue = val
        elif isinstance(val, bool):
            pb_value.boolValue = val
        else:
            raise ValueError(f"Unsupported value type for key '{key}': {type(val)}")
        pb_msg.customMessage.entries[key].CopyFrom(pb_value)

    return pb_msg.SerializeToString()

def downlink_to_pb(msg: dict):
    if ACTION in msg.keys():
        if msg[ACTION] == ACTION_ADVERTISING:
            return tx_pkt_pb(msg)
        elif msg[ACTION] == ACTION_BRG_OTA:
            return brg_ota_pb(msg)
        elif msg[ACTION] == ACTION_GW_OTA:
            return gw_ota_pb(msg)
        else:
            return action_pb(msg)
    elif GW_CONF in msg.keys():
        return gw_cfg_pb(msg[GW_CONF])
    else:
        print("Can't find the message type to convert to protobuf. Using customMessage..")
        return custom_message_pb(msg)