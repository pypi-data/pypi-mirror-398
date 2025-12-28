# from http import client
import time
import os
import json
from certificate.cert_prints import *
from certificate.cert_defines import *
from certificate.wlt_types import *
import certificate.cert_protobuf as cert_protobuf
import certificate.cert_common as cert_common
import certificate.cert_utils as cert_utils
import threading

# gw_sim defines
TAG_ID_OFFSET              = -16
TAG_ID_FROM_ADVA_LENGTH    = 8
TAG_ID_FROM_ADVA_OFFSET    = 2
HDR_BLE5_DEFAULT_PKT_SIZE  = 0x26
PIXEL_SIM_MIN_CYCLE        = 20 # 20 is the CYCLE_PERIOD_MS_DEFAULT
DEFAULT_DUPLICATES = 5
DEFAULT_DELAY = 20

SECONDARY_CHANNEL_10       = 10
SECONDARY_CHANNEL_21       = 21

# Randomize pixel simulation indicator once per run (6 hex chars)
PIXEL_SIM_INDICATOR = get_random_hex_str(6)

def init_adva(flow_version_major=0x4, flow_version_minor=0x34):
    return "{0:02X}".format(flow_version_major) + get_random_hex_str(8) + "{0:02X}".format(flow_version_minor)

random_bytes = lambda n: int.from_bytes(os.urandom(n), "big")

def write_to_data_sim_log_file(txt):
    write_to_log_file(DATA_SIM_LOG_FILE, txt, "a")

def brg_pkt_gen(num_of_pkts_per_brg, num_of_brgs, brgs_list=[], pkt_type=PIXELS_PKT, indicator='000000'):
    bridge_ids = []
    pkts = []
    idx = 0
    for i in range(num_of_brgs):
        if brgs_list:
            brg_mac = brgs_list[i]
        else:
            brg_mac = cert_common.hex2alias_id_get(get_random_hex_str(12))
            bridge_ids.append(brg_mac)
        adva = cert_common.change_endianness(brg_mac) # Change endianness to little endian

        for j in range(num_of_pkts_per_brg):
            serial_pkt_id = f"{i % 256:02X}{j % 256:02X}{idx:04X}"  # 8 hex chars - 4 bytes

            if pkt_type == PIXELS_PKT:
                payload = (ag.Hdr(group_id=ag.GROUP_ID_UNIFIED_PKT_V2).dump() +
                           indicator + brg_mac + get_random_hex_str(22) + serial_pkt_id)

            if pkt_type == MGMT_PKT:
                mgmt_pkt = eval_pkt(f'GenericV{ag.API_VERSION_LATEST}')
                body = mgmt_pkt(module_type=ag.MODULE_DATAPATH, msg_type=ag.BRG_MGMT_MSG_TYPE_CFG_INFO, brg_mac=hex_str2int(brg_mac))
                payload = ag.Hdr(group_id=ag.GROUP_ID_BRG2GW).dump() + body.dump()[:-14] + indicator + serial_pkt_id

            if pkt_type == SENSOR_PKT:
                payload = (ag.Hdr(uuid_msb=ag.HDR_DEFAULT_BRG_SENSOR_UUID_MSB, uuid_lsb=ag.HDR_DEFAULT_BRG_SENSOR_UUID_LSB).dump() +
                           indicator + brg_mac + get_random_hex_str(22) + serial_pkt_id)

            if pkt_type == SIDE_INFO_SENSOR_PKT:
                payload = (ag.Hdr(group_id=ag.GROUP_ID_SIDE_INFO_SENSOR).dump() +
                           indicator + brg_mac + get_random_hex_str(22) + serial_pkt_id)

            idx += 1
            pkts += [GenericPkt(adva=adva, payload=payload)]
    return pkts, bridge_ids


class WiliotPixelGen2:
    """Represents 1 Wiliot Gen2 BLE4 Pixel"""
    def __init__(self, pixel_sim_indicator=PIXEL_SIM_INDICATOR):
        self.adva = init_adva(flow_version_major=0x4, flow_version_minor=0x34)
        self.hdr = ag.DataHdr(uuid_msb=ag.HDR_DEFAULT_TAG_UUID_MSB, uuid_lsb=ag.HDR_DEFAULT_TAG_UUID_LSB, group_id_minor=0x0300)
        self.pixel_sim_indicator = pixel_sim_indicator
        self.payload0 = "010203040506070809"
        self.payload1 = "0A0B0C0D"
        self.pkt_id = 0

    def __repr__(self) -> str:
        return f'TagID: {self.get_tag_id()} PktID: {self.get_pkt_id()} PktType: {self.hdr.pkt_type} RawPkt: {self.get_pkt()}'

    def get_tag_id(self):
        return self.adva[TAG_ID_FROM_ADVA_OFFSET:TAG_ID_FROM_ADVA_OFFSET + TAG_ID_FROM_ADVA_LENGTH]

    def set_pkt_type(self, pkt_type):
        assert pkt_type in [0, 1, 2], "Packet type Must be 0, 1 or 2!"
        self.hdr.pkt_type = pkt_type

    def randomize_pkt_id(self):
        self.pkt_id = random_bytes(4)

    def randomize_payload1(self):
        self.payload1 = f"{random_bytes(4):08X}"

    def get_pkt_id(self):
        return "{0:08X}".format(self.pkt_id)

    def get_pkt(self):
        """Get current packet from generator (hex string)
        adva-6 hdr-7 sim_indicator-3 payload-13 tag_id-4 pkt_id-4 """
        return self.adva + self.hdr.dump() + self.get_pkt_id() + self.pixel_sim_indicator + self.payload0 + self.get_tag_id() + self.payload1

class WiliotPixelGen3:
    """Represents 1 Wiliot Gen3 BLE4 Pixel"""
    def __init__(self, pixel_sim_indicator=PIXEL_SIM_INDICATOR):
        self.adva = init_adva(flow_version_major=0x08, flow_version_minor=0x10) # flow versions 0x080F and down do not support temp events from tag
        self.hdr = ag.DataHdr(uuid_msb=ag.HDR_DEFAULT_TAG_UUID_MSB, uuid_lsb=ag.HDR_DEFAULT_TAG_UUID_LSB, group_id_minor=0x0500)
        self.pixel_sim_indicator = pixel_sim_indicator
        self.payload0 = "010203040506070809"
        self.payload1 = "0A0B0C0D"
        self.pkt_id = 0

    def __repr__(self) -> str:
        return f'TagID: {self.get_tag_id()} PktID: {self.get_pkt_id()} PktType: {self.hdr.pkt_type} RawPkt: {self.get_pkt()}'

    def get_tag_id(self):
        return self.adva[TAG_ID_FROM_ADVA_OFFSET:TAG_ID_FROM_ADVA_OFFSET + TAG_ID_FROM_ADVA_LENGTH]

    def set_pkt_type(self, pkt_type):
        assert pkt_type in [0, 1], "Packet type Must be 0 or 1!"
        self.hdr.pkt_type = pkt_type

    def randomize_pkt_id(self):
        self.pkt_id = random_bytes(4)

    def randomize_payload1(self):
        self.payload1 = f"{random_bytes(4):08X}"

    def get_pkt_id(self):
        return "{0:08X}".format(self.pkt_id)

    def get_pkt(self):
        """Get current packet from generator (hex string)
        adva-6 hdr-7 nonce/pkt_id-4 sim_indicator-3 payload0-9 tag_id-4 payload1-4 """
        return self.adva + self.hdr.dump() + self.get_pkt_id() + self.pixel_sim_indicator + self.payload0 + self.get_tag_id() + self.payload1
class WiliotPixelGen3Extended:
    """Represents 1 Wiliot Gen3 BLE5 Pixel"""
    def __init__(self, pixel_sim_indicator=PIXEL_SIM_INDICATOR, secondary_channel=SECONDARY_CHANNEL_10):
        self.adi = '0000'
        self.adva = init_adva(flow_version_major=0x08, flow_version_minor=0x10) # flow versions 0x080F and down do not support temp events from tag
        self.hdr = ag.DataHdr(pkt_size=HDR_BLE5_DEFAULT_PKT_SIZE, uuid_msb=ag.HDR_DEFAULT_TAG_UUID_MSB, uuid_lsb=ag.HDR_DEFAULT_TAG_UUID_LSB, group_id_minor=0x0500)
        self.uid = f"0102030405{secondary_channel:02X}" # 6 bytes UID
        self.mic = pixel_sim_indicator + pixel_sim_indicator # 6 bytes MIC (mico and mic1 are set to the sim indicator)
        self.payload0 = self.get_tag_id() + f"{random_bytes(4):08X}" # 8 bytes payload. We will use first 4 bytes for the tag_id to keep the same location as in Gen2 and Gen3 BLE4
        self.payload1 = self.get_tag_id() + f"{random_bytes(4):08X}" # 8 bytes payload. We will use first 4 bytes for the tag_id to keep the same location as in Gen2 and Gen3 BLE4
        self.pkt_id = 0

    def __repr__(self) -> str:
        return f'TagID: {self.get_tag_id()} PktID: {self.get_pkt_id()} RawPkt: {self.get_pkt()}'

    def get_tag_id(self):
        return self.adva[TAG_ID_FROM_ADVA_OFFSET:TAG_ID_FROM_ADVA_OFFSET + TAG_ID_FROM_ADVA_LENGTH]

    def set_pkt_type(self, pkt_type):
        assert pkt_type in [2, 3], "Packet type Must be 2 or 3!"
        self.hdr.pkt_type = pkt_type

    def randomize_pkt_id(self):
        self.pkt_id = random_bytes(4)

    def get_pkt_id(self):
        return "{0:08X}".format(self.pkt_id)

    def get_pkt(self):
        """ Get current packet from generator (hex string) - 47 bytes
        adva-6 adi-2 hdr-7 nonce/pkt_id-4 uid-6 mic-6 payload0-8 payload1-8 """
        return self.adva + self.adi + self.hdr.dump() + self.get_pkt_id() + self.uid + self.mic + self.payload0 + self.payload1

class GenericPkt:
    """Represents Explicit Data. Can be sensors, tags or anything else"""
    def __init__(self, adva, payload, duplicates=0, delay=0):
        self.adva = adva
        self.payload = payload

    def __repr__(self) -> str:
        return f'RawPkt: {self.get_pkt()}'

    def set_pkt_type(self, _):
        pass
    def get_pkt(self):
        return self.adva + self.payload

class GenericSimThread(threading.Thread):
    def __init__(self, test, duplicates=DEFAULT_DUPLICATES, delay=DEFAULT_DELAY, send_single_cycle=False, pkts=[]):
        super().__init__()
        self.test = test
        self.duplicates = duplicates
        self.delay = delay
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        self._pause_event.set()
        self.daemon = True
        self.send_single_cycle = send_single_cycle
        self.pkts = pkts

    def run(self):
        write_to_data_sim_log_file(f"num_of_raw_pkts={len(self.pkts)} duplicates={self.duplicates} delay={self.delay}\n")
        # Run pixel_sim loop
        while not self._stop_event.is_set():
            self._pause_event.wait()
            for pkt in self.pkts:
                if self._stop_event.is_set():
                    return  
                if not self._pause_event.is_set():
                    break
                self.publish_pkt_to_mqtt(pkt)
            if self.send_single_cycle:
                self.stop()
    
    def stop(self):
        """Stops the thread completely"""
        self._stop_event.set()
        write_to_data_sim_log_file(f"DataSimThread stopped\n")

    def pause(self):
        """Pauses the thread execution"""
        self._pause_event.clear()
        write_to_data_sim_log_file(f"DataSimThread paused\n")

    def resume(self):
        """Resumes the thread execution"""
        self._pause_event.set()
        write_to_data_sim_log_file(f"DataSimThread resumed\n")

    def publish_pkt_to_mqtt(self, pkt):
        msg = {TX_PKT: pkt.get_pkt(),
            TX_MAX_RETRIES: self.duplicates,
            TX_MAX_DURATION_MS: 100,
            ACTION: 0}
        # Use protobuf if protubuf flag is set to True
        if self.test.tester.protobuf:
            payload = cert_protobuf.downlink_to_pb(msg)
        else:
            payload = json.dumps(msg)
        self.test.tester.mqttc.publish(self.test.tester.mqttc.update_topic, payload=payload)
        write_to_data_sim_log_file(f"{pkt}" + " {}\n".format(datetime.datetime.now().strftime("%d/%m,%H:%M:%S.%f")[:-4]))
        actual_delay = max(self.delay, self.duplicates * (PIXEL_SIM_MIN_CYCLE))
        time.sleep(actual_delay/1000)

class DataSimThread(GenericSimThread):
    def __init__(self, test, num_of_pixels, pkt_types, pixels_type=GEN2, channel=SECONDARY_CHANNEL_10, **kwargs):
        self.test = test
        self.__dict__.update(kwargs)
        super().__init__(**self.__dict__)
        self.num_of_pixels = num_of_pixels
        # Create data list
        if pixels_type == GEN2:
            self.pixels = [WiliotPixelGen2() for _ in range(self.num_of_pixels)]
        elif pixels_type == GEN3:
            self.pixels = [WiliotPixelGen3() for _ in range(self.num_of_pixels)]
        elif pixels_type == GEN3_EXTENDED:
            self.pixels = [WiliotPixelGen3Extended(secondary_channel=channel) for _ in range(self.num_of_pixels)]
        else:
            print(f"Didn't define pixels type")
        self.pkt_types = pkt_types

    def run(self):
        write_to_data_sim_log_file(f"num_of_pixels={self.num_of_pixels} duplicates={self.duplicates} delay={self.delay} pkt_types={self.pkt_types}\n")
        # Run pixel_sim loop
        sent_pkt_ctr = 0
        while not self._stop_event.is_set():
            self._pause_event.wait()
            for i in range(self.num_of_pixels):
                if self._stop_event.is_set():
                    return  
                if not self._pause_event.is_set():
                    break
                for pkt_type in self.pkt_types:
                    if not self._pause_event.is_set():
                        break
                    pkt = self.pixels[i]
                    pkt.set_pkt_type(pkt_type)

                    # Adding 1 to tx rate & temp counters for event tests (0b001001)
                    if "event" in self.test.name: 
                        sent_pkt_ctr += 1
                        if sent_pkt_ctr == 20:
                            pkt.hdr.group_id_major += 0x09

                    # Set pkt_id, in Gen3 pkt_type_1 has pkt_id_0+1
                    if type(pkt) == WiliotPixelGen3:
                        if pkt_type == 1:
                            if self.pkt_types == [0,1]:
                                pkt.pkt_id += 1
                            else:
                                pkt.randomize_pkt_id()
                            pkt.randomize_payload1() # In the FW we assume data is random at the place gen2 pkt id was (4 last bytes)
                        else:
                            # pkt type 0
                            pkt.randomize_pkt_id()
                            pkt.randomize_payload1() # In the FW we assume data is random at the 4 last bytes
                    else:
                        pkt.randomize_pkt_id()
                        if type(pkt) == WiliotPixelGen2:
                            pkt.randomize_payload1() # In the FW we assume data is random at the 4 last bytes
                    # Publish pkt to MQTT
                    self.publish_pkt_to_mqtt(pkt)

    def stop(self):
        """Stops the thread completely"""
        self._stop_event.set()
        write_to_data_sim_log_file(f"DataSimThread stopped\n")

    def pause(self):
        """Pauses the thread execution"""
        self._pause_event.clear()
        write_to_data_sim_log_file(f"DataSimThread paused\n")

    def resume(self):
        """Resumes the thread execution"""
        self._pause_event.set()
        write_to_data_sim_log_file(f"DataSimThread resumed\n")