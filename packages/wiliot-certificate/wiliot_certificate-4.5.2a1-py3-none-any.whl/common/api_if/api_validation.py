import json
from jsonschema import Draft202012Validator
import pkg_resources
from enum import Enum

from certificate.cert_prints import *
from certificate.cert_defines import GW_LOGS
import certificate.cert_utils as cert_utils
import certificate.cert_mqtt as cert_mqtt

class MESSAGE_TYPES(Enum):
    STATUS = "status"
    DATA = "data"
    LOGS = "logs"

API_VALIDATION = "API Validation"

def api_validation(test):
    phase_run_print(API_VALIDATION)
    api_validation_phase = cert_utils.Phase(API_VALIDATION, rc=TEST_PASSED)

    if test.dut.protobuf:
        utPrint("API validation is skipped for protobuf messages", "WARNING")
        api_validation_phase.rc = TEST_SKIPPED
        api_validation_phase.reason = "API validation is skipped for protobuf messages"
        test.add_phase(api_validation_phase)
        return test
    elif not test.dut.gw_api_version:
        utPrint("API validation is skipped because no API version was specified", "WARNING")
        api_validation_phase.rc = TEST_FAILED
        api_validation_phase.reason = "API validation is skipped because no API version was specified"
        test.add_phase(api_validation_phase)
        return test
    else:
        def validate_message(message: dict, msg_type=MESSAGE_TYPES.DATA.value) -> tuple[bool, str]:
            json_path = pkg_resources.resource_filename(__name__, f"{test.dut.gw_api_version}/{msg_type}.json")
            with open(json_path) as f:
                relevant_schema = json.load(f)
            validator = Draft202012Validator(relevant_schema)
            valid = validator.is_valid(message)
            errors = [e for e in validator.iter_errors(message)]
            return (valid, errors)

        utPrint(f"Validating all messages in the test according to API version {test.dut.gw_api_version} validation schema", "BLUE")
        report = []
        phase_passed = True
        for msg_type in MESSAGE_TYPES:
            if msg_type.value == MESSAGE_TYPES.STATUS.value:
                all_msgs = [msg.body for msg in test.get_mqttc_by_target(DUT)._userdata[PKTS].status if GW_LOGS not in msg.body]
            elif msg_type.value == MESSAGE_TYPES.LOGS.value:
                all_msgs = [msg.body for msg in test.get_mqttc_by_target(DUT)._userdata[PKTS].status if GW_LOGS in msg.body]
            else:
                all_msgs = [msg.body for msg in test.get_mqttc_by_target(DUT)._userdata[PKTS].data]

            utPrint(f"Validating {msg_type.value} messages", "BLUE")
            message_type_passed = True
            total_num_of_errors = 0
            error_report = []
            for idx, message_body in enumerate(all_msgs):
                if msg_type.value == MESSAGE_TYPES.DATA.value and len(message_body[PACKETS]) == 0:
                    continue
                validation = validate_message(message_body, msg_type.value)
                errors = []
                for e in validation[1]:
                    if e.message not in errors:
                        errors.append(e.message)
                if not validation[0]:
                    phase_passed = False
                    message_type_passed = False
                    total_num_of_errors += len(errors)
                    error_report.append(f'The errors in message (idx={idx}, json timestamp={message_body.get(TIMESTAMP)}) Errors:')
                    for idx, e in enumerate(errors):
                        error_report.append(f'Error number {idx}:\n {e}')
            report.append("\n")
            report.append(f'Summary for {msg_type.value} messages')
            report.append({'valid': {message_type_passed}, 'num of errors': total_num_of_errors})
            report.append('******************************************************\n')
            report.extend(error_report)
        utPrint("\nAPI validation errors:", "BLUE")
        for line in report:
            print(line)
        report_path = os.path.join(ARTIFACTS_DIR, test.dir, 'api_validation_report.txt')
        with open(report_path, 'w') as f:
            for line in report:
                f.write(str(line) + '\n')
        if not phase_passed:
            api_validation_phase.rc = TEST_FAILED
            api_validation_phase.reason = "API (JSON strcture) is invalid"
        field_functionality_pass_fail_print(api_validation_phase, API_VALIDATION)
        test.add_phase(api_validation_phase)
        return test