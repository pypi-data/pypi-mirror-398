
import os
import random
import tabulate
import importlib # needed for importing all of the tests
from requests import codes as r_codes

# Local imports
import certificate.cert_config as cert_config
import certificate.cert_common as cert_common
import certificate.cert_results as cert_results
from certificate.wlt_types import *
from certificate.cert_defines import *
from certificate.cert_prints import *

TESTER_FW_VERSIONS = ["4.6.26", "4.6.27"]
MULTI_BRG_STR =     "multi_brg"  # used for multi brg tests
GW_ONLY_STR =       "gw_only"  # used for gw only tests
INTERNAL_BRG_STR =  "internal_brg"
ORIGINAL_AG_FILE =  "wlt_types_ag.py"

##################################
# Utils
##################################

TEST_MODULES_MAP = {"calibration": ag.MODULE_CALIBRATION, "datapath": ag.MODULE_DATAPATH, "energy2400": ag.MODULE_ENERGY_2400, "energy_sub1g": ag.MODULE_ENERGY_SUB1G,
                    "pwr_mgmt": ag.MODULE_PWR_MGMT, "sensors": ag.MODULE_EXT_SENSORS, "custom": ag.MODULE_CUSTOM}

def module2name(module_id):
    for k, v in TEST_MODULES_MAP.items():
        if module_id == v:
            return k
    return ''

def load_module(module_name, module_path, rel_path="."):
    spec = importlib.util.spec_from_file_location(module_name, os.path.join(BASE_DIR, rel_path, module_path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def handle_error(error, start_time):
    utPrint(error, "red")
    cert_results.generate_results_files(html=True, pdf=False, start_time=start_time, error=error)
    sys.exit(-1)

def overwrite_defines_file(file_name, brg_id, overwrite_defs):
    overwritten = {key: False for key in overwrite_defs}
    with open(os.path.join(BASE_DIR, "ag", file_name), "r") as f:
        lines = f.readlines()
    for i, line in enumerate(lines):
        for key,val in overwrite_defs.items():
            pattern = r"^(\s*" + re.escape(key) + r"\s*=\s*).*$" # match the key before the "=", capture it, then replace what's after
            if re.match(pattern, line):
                lines[i] = re.sub(pattern, rf"\g<1>{val}", line)
                overwritten[key] = True
                break
    for key,flag in overwritten.items():
        if not flag:
            utPrint(f"Couldn't overwrite '{key}' as it was not found in {file_name}!", "WARNING")
    with open(os.path.join(BASE_DIR, "ag", file_name.replace('.py', f'_overwritten_for_{brg_id}.py')), "w") as f:
        f.writelines(lines)
    return file_name.replace('.py', f'_overwritten_for_{brg_id}.py')

def parse_cfg_file(filepath):
    config = {}
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue  # skip empty lines and comments
            if "=" in line:
                key, value = line.split("=", 1)
                config[key.strip()] = value.strip()
    return config

##################################
# Test
##################################

class WltTest:
    """
    Wiliot Test class representing a single test case.
    
    This class encapsulates all information needed to run a certification test,
    including gateway information, bridge information, test parameters, and test results.
    
    Attributes:
        name: Test name from test list
        tester: Gateway object (or string ID for backward compatibility)
        dut: Device under test object (or string ID for backward compatibility)
        brg1: Secondary bridge object for multi-bridge tests (optional)
        active_brg: Currently active bridge being tested
        test_json: Test configuration from JSON file
        phases: List of test phases
        params: List of test parameters
        rc: Test result code (TEST_PASSED, TEST_FAILED, TEST_SKIPPED, etc.)
        reason: Reason for test result
        start_time: Test start time
        end_time: Test end time
        duration: Test duration
        exit_on_param_failure: Whether to exit on parameter failure
        latest: Whether to use latest version
        release_candidate: Whether to use release candidate version
        sterile_run: Whether to run in sterile run mode
        data: Test data
        rand: Random number
    """
    def __init__(self, line, tester, dut, brg1=None, exit_on_param_failure=False,
                 latest=False, release_candidate=False, sterile_run=False, data=''):
        if line:
            test_list_line = line.strip().split()
            self.name = test_list_line[0]
            self.test_module = ag.MODULE_EMPTY # Default test module
            # Determine test's module
            for s in self.name.split('/'):
                if s in TEST_MODULES_MAP:
                    self.test_module = TEST_MODULES_MAP[s]
                    break
            line_params = test_list_line[1:]
            self.dir = os.path.join("tests", self.name)
            self.module_name = os.path.join(os.path.basename(self.name))
            self.file = os.path.join(self.dir, os.path.basename(self.name)+".py")
            # Load test json
            test_json_file = open(os.path.join(BASE_DIR, self.dir, os.path.basename(self.name)+".json"))
            self.test_json = json.load(test_json_file)
            self.gw_only = self.test_json[GW_ONLY_TEST]
            self.multi_brg = self.test_json[MULTI_BRG_TEST]
            self.internal_brg = INTERNAL_BRG_STR in line_params
            if INTERNAL_BRG_STR in line_params: line_params.remove(INTERNAL_BRG_STR)
            self.create_test_phases_and_params(line_params)
        else:
            self.test_json = {}
            self.internal_brg = False
            self.multi_brg = False
            self.phases = [Phase(PRE_CONFIG), Phase(TEST_BODY), Phase(RESTORE_CONFIG)]
            self.params = []

        self.tester = tester
        self.dut = dut
        # Actual brg to cfg - can be dut, its internal_brg or None
        if isinstance(self.dut, Bridge):
            self.active_brg = self.dut
        elif isinstance(self.dut, Gateway) and self.dut.has_internal_brg():
            self.active_brg = self.dut.internal_brg
        else:
            self.active_brg = None
        self.brg1 = brg1 if brg1 else (self.tester.internal_brg if tester and tester.internal_brg else None)
        self.rc = TEST_PASSED
        self.reason = ""
        self.start_time = None
        self.end_time = None
        self.duration = None
        self.exit_on_param_failure = exit_on_param_failure
        self.rand = random.randrange(255)
        self.latest = latest
        self.release_candidate = release_candidate
        self.sterile_run = sterile_run
        self.data = data

    def create_test_phases_and_params(self, line_params):
        self.params = []
        phases_source = []
        dynamic_parameters = "dynamic_parameters" in self.test_json[ALL_SUPPORTED_VALUES]
        if dynamic_parameters:
            self.test_json[ALL_SUPPORTED_VALUES].remove("dynamic_parameters")
        if len(self.test_json[ALL_SUPPORTED_VALUES]) > 0:
            if dynamic_parameters:
                if line_params:
                    phases_source = line_params
                elif len(self.test_json[ALL_SUPPORTED_VALUES]) > 0:
                    phases_source = self.test_json[ALL_SUPPORTED_VALUES]
                else:
                    error = f"ERROR: No dynamic parameters provided for test {self.name}! Check test list file and update the supported values!\n{[f.__dict__ for f in self.phases]}"
                    handle_error(error, datetime.datetime.now())
            else:
                phases_source = self.test_json[ALL_SUPPORTED_VALUES]
            self.phases = [Phase(PRE_CONFIG)] + [Phase(phase) for phase in phases_source] + [Phase(RESTORE_CONFIG)]
            for param_phase in self.phases:
                param = Param(param_phase.name)
                if (param.name in line_params or param.value in [eval_param(p) for p in line_params]):
                    self.params += [param]
                else:
                    param_phase.tested = False
                    param_phase.rc = TEST_SKIPPED
            if all([param_phase.rc == TEST_SKIPPED for param_phase in self.phases]):
                error = f"ERROR: All params skipped for test {self.name}! Check test list file and update the supported values!\n{[f.__dict__ for f in self.phases]}"
                handle_error(error, datetime.datetime.now())
        else:
            if line_params:
                error = f"ERROR: For {self.name} params exist in test_list but not in test_json!\nline_params:{line_params}"
                handle_error(error, datetime.datetime.now())
            self.phases = [Phase(PRE_CONFIG), Phase(TEST_BODY), Phase(RESTORE_CONFIG)]

    
    def get_mqttc_by_target(self, target=DUT):
        if target == DUT:
            return self.dut.mqttc if isinstance(self.dut, Gateway) else self.tester.mqttc
        return self.tester.mqttc

    # Flush all existing mqtt packets
    def flush_all_mqtt_packets(self):
        self.get_mqttc_by_target(TESTER).flush_pkts()
        self.get_mqttc_by_target(DUT).flush_pkts()

    # Phase rc
    def set_phase_rc(self, phase_name, rc):
        phase = self.get_phase_by_name(phase_name)
        phase.rc = rc

    def get_phase_rc(self, phase_name):
        phase = self.get_phase_by_name(phase_name)
        return phase.rc

    # Phase reason
    def add_phase_reason(self, phase_name, reason):
        phase = self.get_phase_by_name(phase_name)
        if phase.reason:
            phase.reason += "\n"
        if reason not in phase.reason:
            phase.reason += reason

    def get_phase_reason(self, phase_name):
        phase = self.get_phase_by_name(phase_name)
        return phase.reason

    # Test funcs
    def get_phase_by_name(self, phase_name):
        for phase in self.phases:
            if phase.name == phase_name:
                return phase
        return None

    def add_phase(self, phase):
        self.phases[-1:-1] = [phase]

    def update_overall_rc(self):
        if any([phase.rc == TEST_FAILED for phase in self.phases]):
            self.rc = TEST_FAILED
    
    def reset_result(self):
        self.rc = TEST_PASSED
        self.reason = ""

    def get_seq_id(self):
        self.rand = (self.rand + 1) % 256
        return self.rand

    # TODO - remove when test reason is re-designed
    def add_reason(self, reason):
        if self.reason:
            self.reason += "\n"
        if reason not in self.reason:
            self.reason += reason

    def internal_id_alias(self):
        return self.dut.internal_brg.id_alias if isinstance(self.dut, Gateway) and self.dut.has_internal_brg() else self.tester.internal_brg.id_alias
    
    def dut_is_gateway(self):
        return isinstance(self.dut, Gateway)
    
    def dut_is_bridge(self):
        return isinstance(self.dut, Bridge)
    
    def dut_is_combo(self):
        return hasattr(self.dut, 'internal_brg') and self.dut.has_internal_brg()

##################################
# Phases
##################################
class Phase:
    def __init__(self, input=None, tested=True, rc=TEST_ABORTED, reason=""):
        self.name = str(input)
        self.tested = tested
        self.rc = rc
        self.reason = reason
    
    def __repr__(self):
        return self.name

##################################
# Param
##################################
class Param:
    def __init__(self, input=None):
        self.name = str(input)
        self.value = eval_param(input)
    
    def __repr__(self):
        return self.name

##################################
# Bridge
##################################
brg_flag = lambda validation_schema: 'modules' in validation_schema

class Bridge:
    def __init__(self, id_str="", board_type=0, cfg_hash=0, api_version=ag.API_VERSION_LATEST, interface_pkt=None, import_defs=True, overwrite_defs={}, rel_path=".", validation_schema=None):
        """
        Initialize a Bridge object.
        
        Args:
            id_str: Bridge ID string (hex format)
            board_type: Board type identifier (default: 0)
            cfg_hash: Configuration hash value (default: 0)
            api_version: Bridge API version (default: ag.API_VERSION_LATEST)
            interface_pkt: Interface packet containing bridge information (optional)
            import_defs: Whether to import and overwrite defines (default: True)
            overwrite_defs: Dictionary of defines to overwrite (default: {})
            rel_path: Relative path for loading modules (default: ".")
            validation_schema: Validation schema dictionary
        """
        self.id_str = id_str
        self.id_int = hex_str2int(id_str)
        self.id_alias = cert_common.hex2alias_id_get(id_str)
        self.board_type = interface_pkt.board_type if interface_pkt else board_type
        self.version = f"{interface_pkt.major_ver}.{interface_pkt.minor_ver}.{interface_pkt.patch_ver}" if interface_pkt else ""
        self.bl_version = interface_pkt.bl_version if interface_pkt else ""
        self.cfg_hash = interface_pkt.cfg_hash if interface_pkt else cfg_hash
        self.api_version = interface_pkt.api_version if interface_pkt else api_version
        if import_defs:
            if self.board_type >= len(ag.BOARD_TYPES_LIST):
                # Temporary. Remove once we work according to schema
                utPrint(f"Note: DUT board type set to 13 since {self.board_type} is unsupported", "WARNING")
                self.board_type = 13
            self.defines_file_name = f'{ag.BOARD_TYPES_LIST[self.board_type]}_defines.cfg'
            overwrite_dict = {}
            # Overwrite auto-generated defines for the specific bridge
            if os.path.exists(os.path.join(BASE_DIR, "ag", self.defines_file_name)):
                overwrite_dict.update(parse_cfg_file(os.path.join(BASE_DIR, "ag", self.defines_file_name))) 
            overwrite_dict.update(overwrite_defs) # Defines overwritten manually through cli
            overwritten_defs_file = overwrite_defines_file(ORIGINAL_AG_FILE, self.id_str, overwrite_dict)
            new_defines = load_module(overwritten_defs_file, f"./ag/{overwritten_defs_file}", rel_path)
            ag.__dict__.update(new_defines.__dict__)
            self.max_output_power_dbm = ag.BRG_DEFAULT_TX_POWER_MAX_2_4_DBM
        self.validation_schema = validation_schema
        self.sup_caps = []
        self.modules = []
        if interface_pkt:
            for key, value in interface_pkt.__dict__.items():
                if 'sup_cap_' in key and value:
                    module = key.replace('sup_cap_','')
                    if module in TEST_MODULES_MAP:
                        self.sup_caps += [TEST_MODULES_MAP[module]]
                        self.modules += [eval_pkt(ag.MODULES_DICT[TEST_MODULES_MAP[module]] + str(self.api_version))]
                        setattr(self, module, eval_pkt(ag.MODULES_DICT[TEST_MODULES_MAP[module]] + str(self.api_version)))

    def update_modules(self):
        self.modules = []
        for sup_cap in self.sup_caps:
            self.modules += [eval_pkt(ag.MODULES_DICT[sup_cap] + str(self.api_version))]
    
    def is_sup_cap(self, test):
        """Check if bridge supports the test module capability."""
        return test.test_module in self.sup_caps if test.test_module and self.sup_caps else True
    
    def __repr__(self):
        version_str = f", version={self.version}" if self.version else ""
        return f"Bridge(id={self.id_str}, board_type={self.board_type}{version_str})"

def cfg_brg_defaults_ret_after_fail(test):
    utPrint(f"Configuring bridge {test.active_brg.id_str} to defaults", "BLUE")
    modules = test.active_brg.modules
    for module in modules:
        utPrint(f"Configuring {module.__name__} to defaults", "BLUE")
        cfg_pkt = cert_config.get_default_brg_pkt(test, module)
        res = cert_config.brg_configure(test=test, cfg_pkt=cfg_pkt)[1]
        if res == NO_RESPONSE:
            utPrint(f"FAILURE: {module.__name__} configuration to defaults", "RED")
            return NO_RESPONSE
        else:
            utPrint(f"SUCCESS: {module.__name__} configured to defaults", "GREEN")
    return DONE

def handle_prep_brg_for_latest(test, interface, brg_id, start_time):
    if test.rc == TEST_FAILED:
        utPrint(f"No ModuleIf pkts found, try again", "BLUE")
        test.rc = ""
        test, interface = cert_common.get_module_if_pkt(test)
    if test.rc == TEST_FAILED:
        error = f"ERROR: No ModuleIf pkts found for 2 tries, couldn't perform OTA for bridge"
        handle_error(error, start_time)
    version = f"{interface.major_ver}.{interface.minor_ver}.{interface.patch_ver}"
    board_type = interface.board_type
    utPrint(f"BRG version [{version}], board type [{board_type}]", "BLUE")
    utPrint(f"Skipping configurations for BRG {brg_id} to defaults because of latest/rc flag", "BLUE")
    return Bridge(brg_id, interface_pkt=interface)

# Check BRGs are online and configure to defaults
def ut_prep_brg(args, start_time, tester, brg_id, tester_flag=False, validation_schema=None):
    overwrite_defs = {} if (tester_flag or not args.overwrite_defaults) else args.overwrite_defaults
    brg = Bridge(brg_id)
    utPrint(SEP)
    if not cert_common.is_cert_running:
        versions_mgmt = load_module('versions_mgmt.py', f'{UTILS_BASE_REL_PATH}/versions_mgmt.py')
        brg_owner = versions_mgmt.gw_brg_owner(env=AWS, server=PROD, brg=brg.id_str)
        if brg_owner and not brg_owner in r_codes:
            print_warn(f"{brg} owned by account {brg_owner}")
    test = WltTest("", tester, dut=brg, exit_on_param_failure=args.exit_on_param_failure, data=args.data)
    utPrint(f"Getting {brg} version and board type", "BLUE")
    test, interface = cert_common.get_module_if_pkt(test)
    # TODO - check validation against device response!
    if args.latest or args.rc:
        return handle_prep_brg_for_latest(test, interface, brg_id, start_time)
    elif test.rc == TEST_FAILED:
        error = f"ERROR: Didn't get ModuleIfV{test.active_brg.api_version} from BRG:{brg.id_str}!\nCheck that the brg responded with the correct module"
        handle_error(error, start_time)
    version = f"{interface.major_ver}.{interface.minor_ver}.{interface.patch_ver}"
    board_type = interface.board_type
    utPrint(f"BRG version [{version}], board type [{board_type}]", "BLUE")
    test.active_brg = Bridge(brg.id_str, interface_pkt=interface, overwrite_defs=overwrite_defs, validation_schema=validation_schema)
    test.dut = test.active_brg
    modules_support = []
    for module in TEST_MODULES_MAP:
        modules_support.append([module, color("GREEN", "SUPPORTED") if TEST_MODULES_MAP[module] in test.active_brg.sup_caps else color("WARNING", "UNSUPPORTED")])
    utPrint(f"BRG {brg.id_str} modules support coverage:", "BLUE")
    print(tabulate.tabulate(modules_support, headers=['Module', 'Support'], tablefmt="fancy_grid"))
    test.active_brg.board_type = board_type
    cfg_output = cfg_brg_defaults_ret_after_fail(test=test)[1]
    if cfg_output == NO_RESPONSE:
        error = f"ERROR: Didn't get response from BRG:{brg.id_str}!"
        handle_error(error, start_time)
    test, interface = cert_common.get_module_if_pkt(test)
    if test.rc == TEST_FAILED:
        error = f"ERROR: Didn't get ModuleIfV{test.active_brg.api_version} from BRG:{brg.id_str}!"
        handle_error(error, start_time)
    utPrint(f"Received cfg hash {hex(interface.cfg_hash)}", "BLUE")
    if not interface.cfg_hash or len(str(interface.cfg_hash)) < BRG_CFG_HAS_LEN:
        error = f"ERROR: invalid cfg_hash for BRG:{brg.id_str}!"
        handle_error(error, start_time)
    utPrint(f"BRG {brg.id_str} cfg_hash_default={hex(interface.cfg_hash)}", "BLUE")
    return Bridge(brg.id_str, interface_pkt=interface, overwrite_defs=overwrite_defs, validation_schema=validation_schema)

##################################
# Gateway
##################################
cloud_connectivity_flag = lambda validation_schema: 'properties' in validation_schema
class Gateway:
    def __init__(self, id_str="", gw_version=None, gw_api_version=GW_API_VER_LATEST, 
                 protobuf=False, mqttc=None, gw_sim=None, port='', 
                 internal_brg=None, gw_orig_versions=None, validation_schema=None, upload_wait_time=0):
        """
        Initialize a Gateway object.
        
        Args:
            id_str: Gateway ID string
            gw_version: Dictionary with BLE_VERSION and WIFI_VERSION keys
            gw_api_version: Gateway API version
            protobuf: Boolean indicating if gateway uses protobuf (default: False)
            mqttc: MQTT client for the gateway
            gw_sim: Gateway simulator thread (optional)
            port: Port number (optional)
            internal_brg: Internal Bridge object (optional)
            gw_orig_versions: Original gateway versions dictionary (optional)
            validation_schema: Validation schema dictionary
        """
        self.id_str = id_str
        self.gw_version = gw_version or {}
        self.gw_api_version = gw_api_version
        self.mqttc = mqttc
        self.gw_sim = gw_sim
        self.port = port
        self.internal_brg = internal_brg
        self.gw_orig_versions = gw_orig_versions or gw_version or {}
        self.protobuf = protobuf
        self.validation_schema = validation_schema
        self.upload_wait_time = upload_wait_time

    def __repr__(self):
        internal_brg_str = f", {self.internal_brg}" if self.internal_brg else ""
        return f"Gateway(id={self.id_str}, api_version={self.gw_api_version}{internal_brg_str})"
    
    def has_internal_brg(self):
        """Check if gateway has an internal bridge."""
        return self.internal_brg is not None
    
    def is_simulated(self):
        """Check if gateway is simulated."""
        return self.gw_sim is not None

def get_tester_id(tester):
    if not tester or tester == GW_SIM_PREFIX:
        return f"GW_SIM_{get_random_hex_str(12)}"
    else:
        # Allow tester to be specified as tester_id:ble_addr
        if ':' in tester:
            tester, _ = tester.split(':')
        return tester

def prep_dut(args, tester, validation_schema, mqttc, start_time, upload_wait_time):
    """
    Prepare device under test - returns Gateway() or Bridge() object.
    
    Returns:
        Gateway object if device is a gateway (with optional internal Bridge)
        Bridge object if device is a standalone bridge
    """
    utPrint(SEP + f"Preparing DUT with ID {args.dut}" + SEP, "BLUE")
    if cloud_connectivity_flag(validation_schema):
        dut = Gateway(
            id_str=args.dut,
            gw_version=None,
            gw_api_version=None,
            protobuf=False,
            mqttc=mqttc,
            internal_brg=None,
            gw_orig_versions=None,
            validation_schema=validation_schema['properties'],
            upload_wait_time=upload_wait_time
        )
        test = WltTest("", tester=None, dut=dut)
        test, gw_info_ble_addr = prep_gw_info_action(test=test, start_time=start_time, brg_flag=brg_flag(validation_schema), target=DUT)
        if brg_flag(validation_schema):
            if not args.combo_ble_addr:
                handle_error(f"ERROR: combo_ble_addr is missing! dut should be {args.dut}:<combo_ble_addr>", start_time)
            elif gw_info_ble_addr and gw_info_ble_addr != args.combo_ble_addr:
                handle_error(f"ERROR: DUT internal BRG ID from gw_info ({gw_info_ble_addr}) doesn't match the provided combo_ble_addr ({args.combo_ble_addr})!", start_time)

        test.dut.gw_orig_versions = test.dut.gw_version.copy()
        internal_brg_str = f":{args.combo_ble_addr}" if args.combo_ble_addr else ""
        print(f"Starting certification for {test.dut}{internal_brg_str}")
        # Configure GW to defaults
        if not args.latest and not args.rc:
            test, res = cert_config.config_gw_defaults(test, target=DUT)
            if res == NO_RESPONSE:
                handle_error("ERROR: Configuring gateway to defaults failed!", start_time)
            # TODO - check validation against device response! (API_VALIDATION script from uplink_test)
        else:
            utPrint(f"Skipping configurations for gateway {test.dut.id_str} to defaults because of latest/rc flag", "BLUE")
        # Prepare gateway's internal BRG
        if brg_flag(validation_schema):
            dut.internal_brg = ut_prep_brg(args, start_time, tester=test.dut, brg_id=args.combo_ble_addr, validation_schema=validation_schema['modules'])
            if dut.internal_brg.api_version < API_OLDEST_SUPPORTED_VERSION:
                 handle_error(f"ERROR: DUT internal brg FW api_version={dut.internal_brg.api_version} is lower then the oldest supported = {API_OLDEST_SUPPORTED_VERSION}! Please upgrade the internal brg FW!", start_time)
        # Return Gateway object
        return dut

    elif brg_flag(validation_schema):
        # Prepare standalone bridge using prepared tester
        brg = ut_prep_brg(args, start_time, tester=tester, brg_id=args.dut, validation_schema=validation_schema['modules'])
        if brg.api_version < API_OLDEST_SUPPORTED_VERSION:
            handle_error(f"ERROR: DUT brg FW api_version={brg.api_version} is lower then the oldest supported = {API_OLDEST_SUPPORTED_VERSION}! Please upgrade the brg FW!", start_time)
        return brg


def prep_tester(args, mqttc, start_time, gw_sim_thread=None):
    """
    Prepare tester gateway - returns Gateway() object (can also be a simulated GW).
    
    Returns:
        Gateway object with optional internal Bridge
    """
    utPrint(SEP + f"Preparing tester with ID {args.tester}" + SEP, "BLUE")
    tester = Gateway(
        id_str=args.tester,
        gw_version=None,
        gw_api_version=None,
        protobuf=False,
        mqttc=mqttc,
        gw_sim=gw_sim_thread,
        port=args.port,
        internal_brg=None,
        gw_orig_versions=None,
        validation_schema=None
    )
    # Prepare a GW SIM tester
    if gw_sim_thread:
        # Check simulator is online and configure to defaults
        utPrint("Checking UART response and configure internal brg to defaults", "BLUE")
        internal_brg_mac_addr = os.getenv(GW_SIM_BLE_MAC_ADDRESS)
        internal_brg_ble_ver = os.getenv(GW_APP_VERSION_HEADER)
        if not internal_brg_mac_addr:
            handle_error(f"ERROR: Didn't receive {GW_SIM_BLE_MAC_ADDRESS} response!", start_time)
        tester.gw_version = {BLE_VERSION:internal_brg_ble_ver, WIFI_VERSION:"0.0.0"}
        tester.gw_api_version = GW_API_VER_LATEST

    # Prepare a GW tester
    else:
        test = WltTest("", tester=tester, dut=None)
        test, internal_brg_mac_addr = prep_gw_info_action(test=test, start_time=start_time, brg_flag=True, target=TESTER)
        # Tester is expected to have ble addr in gw info response
        if internal_brg_mac_addr == "":
            handle_error(f"ERROR: internal_brg_mac_addr in response is empty!", start_time)
        test.tester.gw_orig_versions = test.tester.gw_version.copy()
        print(f"Starting certification with tester ID {test.tester.id_str} and tester's internal BRG ID {internal_brg_mac_addr}")
        # Configure GW to defaults
        if not args.latest and not args.rc:
            test, res = cert_config.config_gw_defaults(test, target=TESTER)
            if res == NO_RESPONSE:
                handle_error("ERROR: Config tester to defaults failed!", start_time)
        else:
            utPrint(f"Skipping configurations for tester {tester} to defaults because of latest/rc flag", "BLUE")
        tester = test.tester

    # Prepare tester's internal BRG
    tester.internal_brg = ut_prep_brg(args, start_time, tester, internal_brg_mac_addr, tester_flag=True, validation_schema=None)
    # Return Gateway object
    return tester

def prep_gw_info_action(test, start_time, brg_flag, target):
    # TODO - make sure certification can run with new assumptions (results, bitbucket-pipelines, etc.)
    gw = test.dut if target == DUT else test.tester
    utPrint(f"Getting {gw} information", "BLUE")
    response = cert_common.get_gw_info(test, target=target)
    if response == NO_RESPONSE:
        error = f"ERROR: Didn't get response from {gw} !"
        handle_error(error, start_time)
    internal_brg_mac_addr = ""
    if ENTRIES in response[GW_INFO]:
        # Protobuf
        info = response[GW_INFO][ENTRIES]
        gw.protobuf = True
        if BLE_VERSION in info and WIFI_VERSION in info:
            gw.gw_version = {BLE_VERSION : info[BLE_VERSION][STR_VAL], WIFI_VERSION : info[WIFI_VERSION][STR_VAL]}
        if brg_flag and BLE_MAC_ADDR in info:
            internal_brg_mac_addr = info[BLE_MAC_ADDR][STR_VAL]
        if GW_API_VERSION in info:
            gw.gw_api_version = info[GW_API_VERSION][STR_VAL]
    else:
        # JSON
        info = response[GW_INFO]
        gw.protobuf = False
        if BLE_VERSION in info and WIFI_VERSION in info:
            gw.gw_version = {BLE_VERSION : info[BLE_VERSION], WIFI_VERSION : info[WIFI_VERSION]}
        if brg_flag and BLE_MAC_ADDR in info:
            internal_brg_mac_addr = info[BLE_MAC_ADDR]
        # For internal use only in versions update test 
        if GW_API_VERSION in info:
            gw.gw_api_version = info[GW_API_VERSION]

    if target == DUT:
        test.dut = gw
    else:
        test.tester = gw
    
    return test, internal_brg_mac_addr

