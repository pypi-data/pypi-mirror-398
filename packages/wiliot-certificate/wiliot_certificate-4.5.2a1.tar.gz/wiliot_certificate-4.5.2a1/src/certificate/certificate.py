
# generic
import sys
import os
sys.path.insert(0, os.path.abspath(".."))
import webbrowser
import glob
import datetime
import tabulate
import threading
import traceback
import shutil
# Local imports
from certificate.wlt_types import *
from certificate.cert_defines import *
from certificate.cert_prints import *
import certificate.cert_utils as cert_utils
import certificate.cert_results as cert_results
import certificate.cert_gw_sim as cert_gw_sim
import certificate.cert_mqtt as cert_mqtt
import certificate.cert_common as cert_common

TEST_LIST_FW_UPDATE_FILE = "ut/fw_update_test_list.txt"

os.system('')

def filter_tests(test_list, run, drun):
    test_lines = [l.strip() for l in open(os.path.join(BASE_DIR, test_list)).readlines() if l.strip() and not l.strip().startswith("#")]
    if run:
        test_lines = [tl for tl in test_lines if re.search(run, tl.strip().split()[0])]
    if drun:
        test_lines = [tl for tl in test_lines if not re.search(drun, tl.strip().split()[0])]
    return test_lines


def skip_test_check(test, validation_schema):
    skip_string = ""
    if test.multi_brg and (not cert_utils.brg_flag(validation_schema) or not test.active_brg):
        skip_string = f"Skipped {test.module_name} multi brg test because device under test isn't a bridge"
    elif test.multi_brg and not test.brg1:
        skip_string = f"Skipped {test.module_name} multi brg test because brg1 wasn't given"
    # TODO - check if module is supported by the bridge in the validation schema
    elif test.active_brg and not test.active_brg.is_sup_cap(test):
        skip_string = f"Skipped {test.module_name} because {cert_utils.module2name(test.test_module)} module is not supported"
    # TODO - check if module is supported by the bridge in the validation schema
    elif test.active_brg and ag.MODULE_EXT_SENSORS not in test.active_brg.sup_caps and "signal_indicator" in test.name:  
        skip_string = f"Skipped signal indicator tests because they are not supported when external sensors module not supported"
    elif test.data != DATA_SIMULATION and test.test_json[DATA_SIMULATION_ONLY_TEST]:
        skip_string = f"Skipped {test.module_name} because it can run only with data simulation mode"
    elif GW_ONLY_TEST in test.test_json and test.test_json[GW_ONLY_TEST] and test.dut_is_bridge():
        skip_string = f"Skipped {test.module_name} because it can run only with Gateway or Combo devices"
    elif BRIDGE_ONLY_TEST in test.test_json and test.test_json[BRIDGE_ONLY_TEST] and not test.dut_is_bridge():
        skip_string = f"Skipped {test.module_name} because it can run only with Bridge devices without Gateway functionality"
    elif SUPPORTED_FROM_API_VERSION in test.test_json:
        if test.test_json[MODULE] == "Cloud Connectivity" and test.dut_is_gateway() and int(test.dut.gw_api_version) < test.test_json[SUPPORTED_FROM_API_VERSION]:
            skip_string = f"Skipped {test.module_name} because it is supported from api version {test.test_json[SUPPORTED_FROM_API_VERSION]} and dut api version is {test.dut.gw_api_version}"
        elif test.test_json[MODULE] != "Cloud Connectivity" and test.active_brg.api_version < test.test_json[SUPPORTED_FROM_API_VERSION]:
            skip_string = f"Skipped {test.module_name} because it is supported from api version {test.test_json[SUPPORTED_FROM_API_VERSION]} and dut api version is {test.active_brg.api_version}"
    if skip_string:
        utPrint(f"{SEP}{skip_string}{SEP}", "WARNING")
        test.reason = skip_string
        test.rc = TEST_SKIPPED
    return test

def load_and_validate_schema(validation_schema_path, start_time):
        """
        Loads and validates the validation schema JSON file.
        Exits if it is invalid, missing, or missing required keys.
        Also exits if neither cloud_connectivity_flag nor brg_flag is True.
        Returns the loaded JSON dict.
        """
        try:
            with open(validation_schema_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            utPrint("The given validation schema is a valid JSON file", 'BLUE')
        except json.JSONDecodeError as e:
            error = f"The given validation schema is an invalid JSON file: {e}"
            cert_utils.handle_error(error, start_time)
        except FileNotFoundError:
            error = f"The given validation schema file was not found!"
            cert_utils.handle_error(error, start_time)
        except Exception as e:
            error = f"Unexpected error received trying to decode the given validation schema JSON file: {e}"
            cert_utils.handle_error(error, start_time)
        # Check for required fields
        if "properties" not in data and "modules" not in data:
            error = "The validation schema is missing both 'properties' and 'modules' keys!"
            cert_utils.handle_error(error, start_time)
        # Check for cloud_connectivity_flag or brg_flag
        if not (cert_utils.cloud_connectivity_flag(data) or cert_utils.brg_flag(data)):
            error = "The validation schema must support either cloud connectivity or bridge device. None found."
            cert_utils.handle_error(error, start_time)
        return data

def clean(args):
    if args.clean:
        print(os.getcwd())
        for dir in glob.glob('**/cert_artifacts_*/', recursive=True):
            print(f"Removing folder: {dir}")
            shutil.rmtree(dir)

def main(args):
    args.tester = cert_utils.get_tester_id(args.tester)
    if ':' in args.dut:
        args.dut, args.combo_ble_addr = args.dut.split(':')

    utPrint(f"wiliot_certificate version: {CERT_VERSION}")
    utPrint(str(args.__dict__))
    start_time = datetime.datetime.now()

    # Clean
    clean(args)
    # Create artifacts dir
    os.makedirs(ARTIFACTS_DIR, exist_ok=True)

    # Filter tests
    test_list = TEST_LIST_FW_UPDATE_FILE if args.latest or args.rc else args.tl
    test_lines = filter_tests(test_list=test_list, run=args.run, drun=args.drun)

    # JSON validation schema basic validation
    validation_schema = load_and_validate_schema(args.validation_schema, start_time)

    # Init mqtt client for tester
    tester_mqttc = cert_mqtt.mqttc_init(args.tester, args.custom_broker, data=args.data)

    # Init mqtt client for device under test when it is cloud connectivity bridge
    if cert_utils.cloud_connectivity_flag(validation_schema) and args.dut != args.tester:
        dut_mqttc = cert_mqtt.mqttc_init(args.dut, args.custom_broker, data=args.data)
    else:
        # Use the same mqtt client of the tester if device under test is a bridge only
        dut_mqttc = tester_mqttc

    # Prepare tester
    gw_sim_thread = None
    if GW_SIM_PREFIX in args.tester:
        # Run Gateway Simulator in separate thread
        gw_sim_thread = threading.Thread(target=cert_gw_sim.gw_sim_run, daemon=True, kwargs={'port':args.port, 'gw_id': args.tester,
                                                                                             'custom_broker':args.custom_broker,
                                                                                             'disable_interference_analyzer':args.disable_interference_analyzer})
        gw_sim_thread.start()
        sleep_time = (len(cert_gw_sim.CHANNELS_TO_ANALYZE) * 30) + 15 if not args.disable_interference_analyzer else 10
        time.sleep(sleep_time)
    tester = cert_utils.prep_tester(args, tester_mqttc, start_time, gw_sim_thread)
    
    # Prepare device under test
    dut = cert_utils.prep_dut(args, tester, validation_schema, dut_mqttc, start_time, upload_wait_time=args.agg)

    # Prepare second bridge (brg1) if given
    brg1 = None
    if args.brg1:
        brg1 = cert_utils.ut_prep_brg(args, start_time, tester, args.brg1)

    # Collecting the tests
    tests = []
    for tl in test_lines:
        test = cert_utils.WltTest(tl, tester, dut, brg1=brg1, exit_on_param_failure=args.exit_on_param_failure,
                       latest=args.latest, release_candidate=args.rc, sterile_run=args.sterile_run, data=args.data)
        tests += [test]

    # Running the tests
    utPrint(SEP)
    utPrint("\n - ".join([f"\nRunning {len(tests)} tests:"] + [t.name if not t.internal_brg else f"{t.name} (internal brg)" for t in tests]))

    failures, skipped = 0, 0
    exit_on_test_failure = args.exit_on_test_failure
    i = 0

    for i, test in enumerate(tests):
        test = skip_test_check(test, validation_schema)
        if test.rc == TEST_SKIPPED:
            for phase in test.phases:
                phase.rc = TEST_SKIPPED
            skipped += 1
        else:
            try:
                test_module_name = cert_utils.load_module(f'{test.module_name}.py', f'{test.dir}/{test.module_name}.py')
                test = test_module_name.run(test)
            except Exception as e:
                traceback.print_exc()
                test.add_phase_reason(RESTORE_CONFIG, f"Exception occurred: {e!r}")
                test.rc = TEST_FAILED
            finally:
                test.update_overall_rc()
        if test.rc == TEST_FAILED:
            failures += 1
            if "versions_test" in test.module_name and f"EXITING CERTIFICATE" in test.reason:
                exit_on_test_failure = True
        print(f"Test Duration: {test.duration}")
        print(tabulate.tabulate([[i+1, i+1-(failures+skipped), skipped, failures, len(tests)]],
                            headers=["FINISHED", "PASSED", "SKIPPED", "FAILED", "TOTAL"], tablefmt="pretty"))
        if test.rc != TEST_SKIPPED:
            wait_time_n_print(2)
        if exit_on_test_failure and test.rc == TEST_FAILED:
            break

    # Print results
    cert_results.generate_results_files(html=True, pdf=True, failures=failures, skipped=skipped, start_time=start_time, tests=tests, non_cert_run=args.non_cert_run)
    if not pipeline_running():
        webbrowser.open('file://' + os.path.realpath(os.path.join(ARTIFACTS_DIR, UT_RESULT_FILE_PDF)))

    if failures:
        sys.exit(-1)

if __name__ == '__main__':
    main()