
import datetime
from argparse import ArgumentParser
import os
import traceback
import webbrowser
import tabulate

from certificate.cert_defines import CERT_VERSION, TEST_FAILED, TEST_PASSED, TEST_SKIPPED
from certificate.cert_prints import *
import certificate.cert_common as cert_common
import certificate.cert_utils as cert_utils
import certificate.cert_results as cert_results

import certificate.tests.cloud_connectivity.registration_test.registration_test as registration_test


# HELPER DEFINES
TEST_LINE = "cloud_connectivity/registration_test registry online refresh"


class RegTestCli:
    """Registration Test CLI."""
    def __init__(self):
        usage = ("wlt-reg-test [-h] -dut <GWID> -ak <API_KEY>\n")

        self.parser = ArgumentParser(prog='wlt-reg-test',
                                     description=f'Registration Test v{CERT_VERSION}', usage=usage)

        self.required = self.parser.add_argument_group('required arguments')
        self.required.add_argument('--dut', type=str, help="Gateway ID", required=True)
        self.required.add_argument('--apikey', '-ak', type=str, help="API key provided by Wiliot", required=True)

    def parse_args(self, args=None):
        """Parse arguments and return them."""
        return self.parser.parse_args(args)


def prepare_results(stage, phase_pass, skip_stage):
    stage.rc = TEST_SKIPPED if skip_stage else TEST_PASSED if phase_pass else TEST_FAILED


def main():
    cli = RegTestCli()
    args = cli.parse_args()

    os.environ[registration_test.REGISTRATION_API_KEY_ENV_VAR] = f"{args.apikey}"

    start_time = datetime.datetime.now()
    dut = cert_utils.Gateway(id_str=args.dut)

    test = cert_utils.WltTest(TEST_LINE, '', dut, exit_on_param_failure=True)
    tests = [test]

    # Running the tests
    utPrint(SEP)
    utPrint("\n - ".join([f"\nRunning {len(tests)} tests:"] +
                         [t.name if not t.internal_brg else f"{t.name} (internal brg)" for t in tests]))

    failures, skipped = 0, 0
    i = 0

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
    print(f"Test Duration: {test.duration}")
    print(tabulate.tabulate([[i + 1, i + 1 - (failures + skipped), skipped, failures, len(tests)]],
                            headers=["FINISHED", "PASSED", "SKIPPED", "FAILED", "TOTAL"], tablefmt="pretty"))
    cert_common.wait_time_n_print(2)

    # Print results
    cert_results.generate_results_files(html=True, pdf=True, failures=failures,
                                        skipped=skipped, start_time=start_time, tests=tests)
    if not pipeline_running():
        webbrowser.open('file://' + os.path.realpath(os.path.join(ARTIFACTS_DIR, UT_RESULT_FILE_PDF)))

    if failures:
        sys.exit(-1)


if __name__ == '__main__':
    main()
