import certificate.ag.wlt_types_ag as ag

def eval_pkt(string):
    try:
        return eval(f'ag.{string}')
    except:
        return None

def eval_one_param(string):
    string = string.strip("' ")
    if string in ag.__dict__:
        return eval(f'ag.{string}')
    try:
        return eval(string)
    except:
        return string

def eval_param(string):
    if "," in string:
        return [eval_one_param(x) for x in string.strip("[]").split(",")]
    else:
        return eval_one_param(string)

class WltPkt():
    supported_pkt_types = ag.WLT_PKT_TYPES

    def __init__(self, raw='', hdr=None, data_hdr=None, generic=None, pkt=None):
        self.hdr = ag.Hdr() if hdr is None else hdr
        self.data_hdr = ag.DataHdr() if data_hdr is None else data_hdr
        self.generic = generic
        self.pkt = pkt
        if raw:
            self.set(raw)

    def __repr__(self) -> str:
        if isinstance(self.pkt, (ag.UnifiedEchoPktV0, ag.UnifiedEchoPktV1, ag.UnifiedEchoPktV2, ag.UnifiedEchoExtPktV0, ag.UnifiedEchoExtPktV1)):
            return f"{self.data_hdr}\n{self.pkt}"
        return f"{self.hdr}\n{self.pkt}"

    def __eq__(self, other):
        if isinstance(other, WltPkt):
            return (
                (self.hdr == other.hdr or
                self.data_hdr == other.data_hdr) and
                self.generic == other.generic and
                self.pkt == other.pkt
            )
        return False

    def dump(self):
        if self.pkt:
            if isinstance(self.pkt, (ag.UnifiedEchoPktV0, ag.UnifiedEchoPktV1, ag.UnifiedEchoPktV2, ag.UnifiedEchoExtPktV0, ag.UnifiedEchoExtPktV1)):
                return self.data_hdr.dump() + self.pkt.dump()
            else:
                return self.hdr.dump() + self.pkt.dump()
        return self.data_hdr.dump() + self.generic.dump()

    def set(self, string):

        self.hdr.set(string[0:14])
        self.data_hdr.set(string[0:14])
        # Sensor pkts
        if self.hdr.uuid_lsb == ag.HDR_DEFAULT_BRG_SENSOR_UUID_LSB and self.hdr.uuid_msb == ag.HDR_DEFAULT_BRG_SENSOR_UUID_MSB:
            unified_sensor_id = int(string[52:58], 16)
            # Unified Sensor pkt - can be identified using bytes 26-28 for the sensor id
            if unified_sensor_id in ag.UNIFIED_SENSOR_ID_LIST:
                self.pkt = ag.UnifiedSensorPkt(string[8:62])
            else:
                # Sensor Data pkt
                self.pkt = ag.SensorData(string)
        else:
            if self.hdr.group_id == ag.GROUP_ID_BRG2GW or self.hdr.group_id == ag.GROUP_ID_GW2BRG:
                # GROUP_ID_BRG2GW & GROUP_ID_GW2BRG
                self.generic = eval_pkt(f'GenericV{ag.API_VERSION_LATEST}()')
                self.generic.set(string[14:62])

                # MEL modules
                if self.generic.module_type and self.generic.module_type in ag.MODULES_DICT:
                    self.pkt = eval_pkt(f'{ag.MODULES_DICT[self.generic.module_type]}{self.generic.api_version}()')
                elif self.generic.module_type == ag.MODULE_GLOBAL:
                    # Action pkts
                    if self.generic.msg_type == ag.BRG_MGMT_MSG_TYPE_ACTION:
                        pkt = eval_pkt(f'ActionGenericV{self.generic.api_version}("{string[14:62]}")')
                        if self.generic.api_version >= ag.API_VERSION_V8:
                            pkt = eval_pkt(f'{ag.ACTIONS_DICT[pkt.action_id]}{self.generic.api_version}()')
                        self.pkt = pkt
                    # OLD global config (GW2BRG & BRG2GW)
                    elif self.hdr.group_id == ag.GROUP_ID_GW2BRG and self.generic.msg_type == ag.BRG_MGMT_MSG_TYPE_CFG_SET:
                        self.pkt = eval_pkt(f'Gw2BrgCfgV8()') # no api_version field in Gw2BrgCfg pkts - default parse as api version 8 (Latest Gw2BrgCfg)
                    elif self.hdr.group_id == ag.GROUP_ID_BRG2GW:
                        if self.generic.msg_type == ag.BRG_MGMT_MSG_TYPE_CFG_SET or self.generic.msg_type == ag.BRG_MGMT_MSG_TYPE_CFG_INFO:
                            self.pkt = eval_pkt(f'Brg2GwCfgV{self.generic.api_version}()')
                        elif self.generic.msg_type == ag.BRG_MGMT_MSG_TYPE_HB:
                            self.pkt = eval_pkt(f'Brg2GwHbV{self.generic.api_version}()')
                        elif self.generic.msg_type == ag.BRG_MGMT_MSG_TYPE_HB_SLEEP:
                            self.pkt = eval_pkt(f'Brg2GwHbSleepV{self.generic.api_version}()')
            # Unified pkt
            elif self.data_hdr.group_id_major in ag.UNIFIED_GROUP_ID_LIST:
                if self.data_hdr.group_id_major == ag.GROUP_ID_UNIFIED_PKT_V0:
                    self.pkt = ag.UnifiedEchoPktV0()
                elif self.data_hdr.group_id_major == ag.GROUP_ID_UNIFIED_PKT_V1 or self.data_hdr.group_id_major == ag.GROUP_ID_BLE5_PKT0_V0: 
                    self.pkt = ag.UnifiedEchoPktV1()
                elif self.data_hdr.group_id_major == ag.GROUP_ID_UNIFIED_PKT_V2 or self.data_hdr.group_id_major == ag.GROUP_ID_BLE5_PKT0_V1: 
                    self.pkt = ag.UnifiedEchoPktV2()
                elif self.data_hdr.group_id_major == ag.GROUP_ID_BLE5_EXTENDED_V0: 
                    self.pkt = ag.UnifiedEchoExtPktV0()
                elif self.data_hdr.group_id_major == ag.GROUP_ID_BLE5_EXTENDED_V1: 
                    self.pkt = ag.UnifiedEchoExtPktV1()
            # SideInfo pkts
            elif self.hdr.group_id == ag.GROUP_ID_SIDE_INFO_SENSOR:
                self.pkt = ag.SideInfoSensor()
            elif self.hdr.group_id == ag.GROUP_ID_SIDE_INFO:
                self.pkt = ag.SideInfo()
            if self.pkt:
                if self.data_hdr.group_id_major == ag.GROUP_ID_BLE5_EXTENDED_V0 or self.data_hdr.group_id_major == ag.GROUP_ID_BLE5_EXTENDED_V1:
                    self.pkt.set(string[14:84])
                else:
                    self.pkt.set(string[14:62])
            # Unparsed pkts
            else:
                # print(f"Unable to parse packet with payload: {string}")
                pass