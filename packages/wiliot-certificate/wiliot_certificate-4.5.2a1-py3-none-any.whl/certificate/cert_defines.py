# Files
import os
import random
import datetime
import importlib.metadata
import certificate.ag.wlt_types_ag as ag

get_random_hex_str = lambda n: ''.join([random.choice('0123456789ABCDEF') for _ in range(n)])

# BASE_DIR should be initiated in the same dir as certificate.py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ARTIFACTS_DIR = os.path.join(os.getcwd(), f"cert_artifacts_{datetime.datetime.now().strftime("%d_%m_%Y__%H_%M_%S")}")

# CERT_VERSION handling - local/PyPi
LOCAL_DEV = "local-dev"
try:
    CERT_VERSION = importlib.metadata.version("wiliot_certificate")
except importlib.metadata.PackageNotFoundError:
    CERT_VERSION = LOCAL_DEV
CERT_MQTT_LOG_FILE =            "cert_mqtt_log.json"
DATA_SIM_LOG_FILE =             "data_sim_log.txt"
RESULT_NOTES_FILE =             "results_notes.txt"
UT_RESULT_FILE_HTML =           "results.html"
UT_RESULT_FILE_PDF =            "results.pdf"
UTILS_BASE_REL_PATH =           "../../../utils"

# GW defines
ADDITIONAL =                    "additional"
REPORTED_CONF =                 "reportedConf"
GW_CONF =                       "gatewayConf"
GW_NAME =                       "gatewayName"
GW_API_VERSION =                "apiVersion"
LAT =                           "lat"
LNG =                           "lng"
NFPKT =                         "nfpkt"
TBC =                           "tbc"
EVENT_FLAG =                    "event_flag"
EVENT_CTR =                     "event_ctr"
RSSI =                          "rssi"
SRC_ID =                        "src_id"

INTERNAL_BRG_RSSI =             1
BRIDGE_ID =                     "bridgeId"
ALIAS_BRIDGE_ID =               "aliasBridgeId"
GROUP_ID =                      "group_id"
AGGREGATED_PAYLOAD =            "aggregated_payload"

WLT_SERVER =                    "wiliotServer"
PACER_INTERVAL =                "pacerInterval"
OUTPUT_POWER_2_4 =              "2.4GhzOutputPower"
USE_STAT_LOC =                  "useStaticLocation"
LOCATION =                      "location"
VERSION =                       "version"
WIFI_VERSION =                  "interfaceChipSwVersion"
BLE_VERSION =                   "bleChipSwVersion"
BLE_MAC_ADDR =                  "bleChipMacAddress"
PROD =                          "prod"
SERIALIZATION_FORMAT =          "serializationFormat"
PROTOBUF =                      "Protobuf"
JSON =                          "JSON"
ACL =                           "accessControlList"
ACL_MODE =                      "mode"
ACL_MODE_ALLOW =                "mode_allow"
ACL_BRIDGE_IDS =                "bridgeIds"
ACL_IDS =                       "ids"
ACL_DENY =                      "deny"
ACL_ALLOW =                     "allow"
ACL_DENY_VALUE =                 0
ACL_ALLOW_VALUE =                1

GET_INFO_ACTION =               "getGwInfo"
REBOOT_GW_ACTION =              "rebootGw"
LOG_PERIOD_ACTION =             "LogPeriodSet"
GET_LOGS =                      "getLogs"
GW_INFO =                       "gatewayInfo"
GW_LOGS =                       "gatewayLogs"
LOGS =                          "logs"
GW_LATITUDE =                   "Latitude"
GW_LONGITUDE =                  "Longitude"
ACL_COUNTERS =                  "aclCounters"
GW_LOG_PERIOD =                 30

# Thin gw defines
TX_PKT =                        "txPacket"
TX_MAX_DURATION_MS =            "txMaxDurationMs"
TX_MAX_RETRIES =                "txMaxRetries"
TRANPARENT_PKT_LEN =            31 * 2
ACTION_ADVERTISING =            0
ACTION_BRG_OTA =                1
ACTION_GW_OTA =                 2

# Simulator defines
GW_SIM_BLE_MAC_ADDRESS =       'GW_SIM_BLE_MAC_ADDRESS'
GW_APP_VERSION_HEADER =        'WILIOT_GW_BLE_CHIP_SW_VER'
GW_SIM_PREFIX =                'SIM'
DATA_SIMULATION =              'sim'
DATA_REAL_TAGS =               'tags'
GEN2 =                         2
GEN3 =                         3
GEN3_EXTENDED =                4
RAW_DATA =                     5
DUT =                          "DUT"
TESTER =                       "TESTER"
BRG1 =                         "BRG1"

# Configurable brg fields' names by modules
# common #
BRG_OUTPUT_POWER =              "output_power"
BRG_PATTERN =                   "pattern"
BRG_DUTY_CYCLE =                "duty_cycle"
BRG_SIGNAL_INDICATOR_CYCLE =    "signal_indicator_cycle"
BRG_SIGNAL_INDICATOR_REP =      "signal_indicator_rep"
# Datapath #
BRG_UNIFIED_ECHO_PKT =          "unified_echo_pkt"
BRG_ADAPTIVE_PACER =            "adaptive_pacer"
BRG_PACER_INTERVAL =            "pacer_interval"
BRG_EVENT_WINDOW =              "event_window"
BRG_EVENT_TIME_UNIT =           "event_time_unit"
BRG_RSSI_THRESHOLD =            "rssi_threshold"
BRG_SUB1G_RSSI_THRESHOLD =      "sub1g_rssi_threshold"
BRG_TX_REPETITION =             "tx_repetition"
BRG_PKT_FILTER =                "pkt_filter"
BRG_RX_CHANNEL =                "rx_channel"
BRG_EVENT_TRIGGER =             "event_trigger"
BRG_EVENT_PACER_INTERVAL =      "event_pacer_interval"
BRG_RSSI_MOVEMENT_THRESHOLD =   "rssi_movement_threshold"
# Calibration #
BRG_CALIB_INTERVAL =            "interval"
# Energy Sub1g #
BRG_CYCLE =                     "cycle"
# 3rd party sensors #
BRG_SENSOR0 =                   "sensor0"
BRG_SENSOR1 =                   "sensor1"
BRG_SENSOR2 =                   "sensor2"

# Common defines
PACKETS =                       "packets"
TIMESTAMP =                     "timestamp"
ACTION =                        "action"
ACTION_STATUS =                 "actionStatus" # Protobuf
PAYLOAD =                       "payload"
SEQUENCE_ID =                   "sequenceId"
MODULE_IF =                     "module IF"
HB =                            "HB"
DATETIME =                      "datetime"
TIME =                          "time"
TIMESTAMP_DELTA =               "timestamp_delta"
TAGS_COUNT =                    "tags_count"
NEW_TAGS =                      "new_tags"
TTFP =                          "ttfp"

# Protobuf related
ENTRIES =                       "entries"
STR_VAL =                       "stringValue"
NUM_VAL =                       "numberValue"
GW_STATUS =                     "gatewayStatus"
BRG_UPGRADE =                   "bridgeUpgrade"
REBOOT_PKT =                    "rebootPacket"
CONFIG =                        "config"
ACL_VALUE =                     "aclValue"

# Custom broker
CUSTOM_BROKER_ENABLE       = "customBroker"
CUSTOM_BROKER_PORT         = "port"
CUSTOM_BROKER_BROKER_URL   = "brokerUrl"
CUSTOM_BROKER_USERNAME     = "username"
CUSTOM_BROKER_PASSWORD     = "password"
CUSTOM_BROKER_UPDATE_TOPIC = "updateTopic"
CUSTOM_BROKER_STATUS_TOPIC = "statusTopic"
CUSTOM_BROKER_DATA_TOPIC   = "dataTopic"

# External Sensors
IS_SENSOR =                      "isSensor"
IS_EMBEDDED =                    "isEmbedded"
IS_SCRAMBLED =                   "isScrambled"
SENSOR_UUID =                    "sensorServiceId"
SENSOR_ID =                      "sensorId"
PKT_ID_CTR =                     "pkt_id_ctr"

# OTA
STATUS_CODE_STR =                "statusCode"
STATUS_CODE =                    "status" # Protobuf
IMG_DIR_URL =                    "imageDirUrl"
UPGRADE_BLSD =                   "upgradeBlSd"
VER_UUID_STR =                   "versionUUID"
STEP =                           "step"
PROGRESS =                       "progress"
VER_MAX_LEN =                    31
EXPECTED_REPORTS = {
    4: {0, 25, 50, 75, 100},
    5: {0, 100},
    6: {10, 20, 30, 40, 50, 60, 70, 80, 90, 100},
    7: {100}
}
FINAL_OTA_STEP =                 max(EXPECTED_REPORTS.keys())


# Actions tests related
BATTERY_SENSOR_SUPPORTING_BOARD_TYPES = [ag.BOARD_TYPE_MINEW_DUAL_BAND_V0, ag.BOARD_TYPE_ERM_V0,
                                         ag.BOARD_TYPE_ERM_V1, ag.BOARD_TYPE_KOAMTAC_V0]
POF_NOT_SUPPORTING_BOARD_TYPES = [ag.BOARD_TYPE_FANSTEL_WIFI_V0, ag.BOARD_TYPE_FANSTEL_LAN_V0]

BRG_NON_DEFAULT_DUTY_CYCLE = 15
BRG_NON_DEFAULT_OP_OFFSET_2_4 = 6
BRG_NON_DEFAULT_EP_2_4 = 1
BRG_NON_DEFAULT_SIGNAL_INDICATOR_CYCLE_2_4 = 100
BRG_NON_DEFAULT_SIGNAL_INDICATOR_REP_2_4 = 3
BRG_NON_DEFAULT_SIGNAL_INDICATOR_CYCLE_SUB1G = 100
BRG_NON_DEFAULT_SIGNAL_INDICATOR_REP_SUB1G = 3
BRG_NON_DEFAULT_OUTPUT_POWER_SUB1G = 26
BRG_NON_DEFAULT_PWR_MGMT_KEEP_ALIVE_SCAN = 0
BRG_NON_DEFAULT_TX_REPETITION = 2
BRG_NON_DEFAULT_PACER_INTERVAL = 20
BRG_NON_DEFAULT_RSSI_THRESHOLD = -80
BRG_NON_DEFAULT_EVENT_TIME_UNIT = 1
BRG_NON_DEFAULT_EVENT_WINDOW = 20
BRG_NON_DEFAULT_EVENT_TRIGGER = 8
BRG_NON_DEFAULT_RSSI_MOVEMENT_THRESHOLD = 15
BRG_NON_DEFAULT_EVENT_PACER_INTERVAL = 10
BRG_NON_DEFAULT_CALIB_OUTPUT_POWER_OFFSET = 2
BRG_NON_DEFAULT_PKT_FILTER = 17
BRG_NON_DEFAULT_CALIB_PATTERN = 2
BRG_NON_DEFAULT_CALIB_INTERVAL = 15

LIS2DW12_NON_DEFAULT_STATE_THRESHOLD = 620
LIS2DW12_NON_DEFAULT_WAKE_UP_DURATION = 120
LIS2DW12_NON_DEFAULT_SLEEP_DURATION = 35

# Versions
VERSIONS = {
    "1.5.0" : {WIFI_VERSION: "3.5.32", BLE_VERSION: "3.7.25"},
    "1.5.2" : {WIFI_VERSION: "3.5.132", BLE_VERSION: "3.7.25"},
    "1.6.1" : {WIFI_VERSION: "3.5.51", BLE_VERSION: "3.8.18"},
    "1.7.0" : {WIFI_VERSION: "3.9.8", BLE_VERSION: "3.9.24"},
    "1.7.1" : {WIFI_VERSION: "3.10.6", BLE_VERSION: "3.10.13"},
    "1.8.0" : {WIFI_VERSION: "3.11.36", BLE_VERSION: "3.11.40"},
    "1.8.2" : {WIFI_VERSION: "3.11.36", BLE_VERSION: "3.11.42"},
    "1.9.0" : {WIFI_VERSION: "3.12.10", BLE_VERSION: "3.12.36"},
    "1.10.1" : {WIFI_VERSION: "3.13.29", BLE_VERSION: "3.13.25"},
    "3.14.0" : {WIFI_VERSION: "3.14.33", BLE_VERSION: "3.14.64"},
    "3.15.0" : {WIFI_VERSION: "3.15.38", BLE_VERSION: "3.15.72"},
    "3.16.3" : {WIFI_VERSION: "3.16.20", BLE_VERSION: "3.16.96"},
    "3.17.0" : {WIFI_VERSION: "3.17.25", BLE_VERSION: "3.17.90"},
    "4.0.0" : {WIFI_VERSION: "4.0.8", BLE_VERSION: "4.0.65"},
    "4.1.0" : {WIFI_VERSION: "4.1.8", BLE_VERSION: "4.1.33"},
    "4.1.2" : {WIFI_VERSION: "4.1.11", BLE_VERSION: "4.1.35"},
    "4.2.0" : {WIFI_VERSION: "4.2.22", BLE_VERSION: "4.2.115"},
    "4.2.5" : {WIFI_VERSION: "4.2.26", BLE_VERSION: "4.2.125"},
    "4.3.0" : {WIFI_VERSION: "4.3.24", BLE_VERSION: "4.3.96"},
    "4.3.1" : {WIFI_VERSION: "4.3.24", BLE_VERSION: "4.3.98"},
    "4.3.2" : {WIFI_VERSION: "4.3.24", BLE_VERSION: "4.3.100"},
    "4.4.8" : {WIFI_VERSION: "4.4.44", BLE_VERSION: "4.4.95"},
    "4.4.10" : {WIFI_VERSION: "4.4.45", BLE_VERSION: "4.4.96"},
    "4.5.6" : {WIFI_VERSION: "4.5.36", BLE_VERSION: "4.5.69"},
}

# Energous boards specific values for output power
ENERGOUS_BOARD_TYPES_GROUP = [ag.BOARD_TYPE_ENERGOUS_V0, ag.BOARD_TYPE_ENERGOUS_V2, ag.BOARD_TYPE_ENERGOUS_V3, ag.BOARD_TYPE_ENERGOUS_V4]
ENERGOUS_GROUP_SUPPORTED_VALUES = [ag.OUTPUT_POWER_2_4_MAX, ag.OUTPUT_POWER_2_4_MAX_MINUS_3, ag.OUTPUT_POWER_2_4_MAX_MINUS_7,
                                   ag.OUTPUT_POWER_2_4_MAX_MINUS_11, ag.OUTPUT_POWER_2_4_MAX_MINUS_15,
                                   ag.OUTPUT_POWER_2_4_MAX_MINUS_19, ag.OUTPUT_POWER_2_4_MAX_MINUS_23]

# Energous_V1 board group #
ENERGOUS_V1_SUPPORTED_VALUES = [ag.OUTPUT_POWER_2_4_MAX, ag.OUTPUT_POWER_2_4_MAX_MINUS_2, ag.OUTPUT_POWER_2_4_MAX_MINUS_4,
                                ag.OUTPUT_POWER_2_4_MAX_MINUS_6, ag.OUTPUT_POWER_2_4_MAX_MINUS_10,
                                ag.OUTPUT_POWER_2_4_MAX_MINUS_14, ag.OUTPUT_POWER_2_4_MAX_MINUS_18,
                                ag.OUTPUT_POWER_2_4_MAX_MINUS_22, ag.OUTPUT_POWER_2_4_MAX_MINUS_26]

# Fanstel board group #
FANSTEL_GW_SUPPORTED_VALUES = [ag.OUTPUT_POWER_2_4_MAX, ag.OUTPUT_POWER_2_4_MAX_MINUS_2, ag.OUTPUT_POWER_2_4_MAX_MINUS_4,
                               ag.OUTPUT_POWER_2_4_MAX_MINUS_6, ag.OUTPUT_POWER_2_4_MAX_MINUS_8,
                               ag.OUTPUT_POWER_2_4_MAX_MINUS_12, ag.OUTPUT_POWER_2_4_MAX_MINUS_16,
                               ag.OUTPUT_POWER_2_4_MAX_MINUS_20]

# Tests defines
DEFAULT_GW_FIELD_UPDATE_TIMEOUT =           10
DEFAULT_BRG_FIELD_UPDATE_TIMEOUT =          10
HB_PERIOD =                                 30
VER_UPDATE_TIMEOUT =                        400
GW_LATITUDE_DEFAULT =                       33.0222
GW_LONGITUDE_DEFAULT =                      -117.0839
# Set to work with default when versions tests only pass through new api ver
GW_API_VER_DEFAULT =                "201"
GW_API_VER_OLD =                    "200"
GW_API_VER_LATEST =                 "206"
API_OLDEST_SUPPORTED_VERSION =      ag.API_VERSION_V12
BRG_CFG_HAS_LEN =                   2
CLEAR_DATA_PATH_TIMEOUT =           10
ACTION_LONG_TIMEOUT =               120
ACTION_SHORT_TIMEOUT =              5

# Internal python ut defines - used only in ut
PACER_INTERVAL_MIN_TAGS_COUNT =                     20
PACER_INTERVAL_MAX_FAILED_TAGS =                    2
PACER_INTERVAL_THRESHOLD_HIGH =                     0.90
PACER_INTERVAL_CEIL_THRESHOLD =                     1.2
PACER_INTERVAL_THRESHOLD =                          0.8
TEST_EVENT_WINDOW_SEC_CFG =                         60
TEST_TAG_EVENT_WINDOW_CFG =                         20
TEST_EVENT_WINDOW_MIN_CFG =                         1
TEST_EVENT_WINDOW_HR_CFG =                          1
SLEEP_TIME_AGING =                                  60
DATA_SIM_EVENT_TESTING_DELAY_MS  =                  1000
DATA_SIM_RSSI_EVENT_TESTING_DELAY_MS  =             300
BLE5_MAX_DURATION_MS =                              ag.BLE5_PARAM_PRIMARY_CHANNEL_SCAN_CYCLE + 1000 # In MS
BLE5_MAX_DURATION_SEC =                             BLE5_MAX_DURATION_MS // 1000
DATA_SIM_EVENT_TESTING_DELAY_SEC =                  DATA_SIM_EVENT_TESTING_DELAY_MS / 1000
DATA_SIM_RSSI_EVENT_TESTING_DELAY_SEC =             DATA_SIM_RSSI_EVENT_TESTING_DELAY_MS / 1000
DATA_SIM_EVENT_PACER_INTERVAL_TESTING =             10
RSSI_EVENT_PKTS_TO_STABILIZE =                      13 # The alpha filter takes about 13 packets to stabilize
PACKETS_ECHO_OFF =                                  16
TEST_PASSED =                                       0
TEST_FAILED =                                       -1
TEST_SKIPPED =                                      1
TEST_ABORTED =                                      2
MODULE_UNSUPPORTED =                                3
NO_RESPONSE =                                       "NO_RESPONSE"
NOT_FOUND =                                         "NOT_FOUND"
DONE =                                              "DONE"
MGMT_PKT =                                          "mgmt_pkt"
PIXELS_PKT =                                        "pixels_pkt"
UNIFIED_PKT =                                       "unified_pkt"
SIDE_INFO_SENSOR_PKT =                              "side_info_sensor_pkt"
SENSOR_PKT =                                        "sensor_pkt"
UNIFIED_SENSOR_PKT =                                "unified_sensor_pkt"
DECODED_DATA =                                      "decoded_data"
TAG_ID =                                            "tag_id"
BRG_LATENCY =                                       "brg_latency"
PACKET_CNTR =                                       "packet_cntr"
PACKET_TYPE =                                       "packet_type"
PACKET_DATA =                                       "packet_data"
PKTS =                                              "pkts"
MQTT_LOG_PRE_STR =                                  "mqtt_log_"
GW_DATA =                                           "gw_data"
GW_ID =                                             "gatewayId"
GW_TYPE =                                           "gatewayType"
CER =                                               "cer"
PKT_CNTR_DIFF =                                     "packet_cntr_diff"
AVG =                                               "avg_"
CER_PER_TAG =                                       "cer_per_tag"
AWS =                                               "aws"
TEST =                                              "test"
MULTI_BRG_TEST =                                    "multiBridgeTest" # used for multi brg tests
GW_ONLY_TEST =                                      "gwOnlyTest" # used for gw only tests
BRIDGE_ONLY_TEST =                                  "bridgeOnlyTest" # used for bridge only tests
DATA_SIMULATION_ONLY_TEST =                         "dataSimOnlyTest" # used for tests runable only with data simulation
PURPOSE =                                           "purpose"
MANDATORY =                                         "mandatory"
MODULE =                                            "module"
NAME =                                              "name"
DOCUMENTATION =                                     "documentation"
ALL_SUPPORTED_VALUES =                              "allSupportedValues"
SUPPORTED_FROM_API_VERSION =                        "SupportedFromApiVersion"
PRE_CONFIG =                                        "Pre Configuration"
TEST_BODY =                                         "Test Body"
RESTORE_CONFIG =                                    "Restore Configuration"
GEOLOCATION =                                       "geolocation"

# test reasons
NO_PARAMS_GIVEN =                                   "No parameters given!"
BRG_VER_SUCCESS =                                   "SUCCESS - BRG version matches expected version!"
BRG_BL_VER_SUCCESS =                                "SUCCESS - BRG Bootloader version matches expected version!"
WANTED_VER_SAME =                                   "Wanted version is same as original one!"
WANTED_VER_SAME_MUL =                               "Wanted versions are same as original ones!"
VER_UPDATE_PASSED =                                 "Version Update Ran Successfully!"
VER_UPDATE_FAILED =                                 "The Update Process Has Been Interrupted!"

# BLE simulator
BLE_SIM_ADV_37_38_39 =                              0
BLE_SIM_RADIO_1MBPS =                               1