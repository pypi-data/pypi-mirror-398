import sys
import os
sys.path.insert(0, os.path.abspath(".."))
import argparse
from certificate.cert_defines import DATA_SIMULATION, GW_SIM_PREFIX
from certificate.cert_mqtt import EMQX
import certificate.certificate as certificate
TEST_LIST_DEFAULT_FILE = "certificate_test_list.txt"

def parse_dict_arg(arg):
    """Parse key=value pairs type arguments"""
    d = {}
    for pair in arg.split(","):
        if "=" not in arg:
            raise argparse.ArgumentTypeError('Use "KEY1=VALUE1,KEY2=VALUE2..." format')
        k, v = pair.split("=")
        d[k] = v
    return d
class CertificateCLI:
    """Certificate CLI."""
    def __init__(self):
        self.parser = argparse.ArgumentParser(
            prog='wlt-certificate',
            description='Certificate - CLI Tool to test Wiliot Devices',
            epilog=
            "run examples:\n"
            "  Run command example with COM PORT tester:\n"
            "  wlt-cert-cli --tester SIM --dut <XXXXXXXXXXXX> --port <COM_PORT>\n"
            "  Run command example with remote GW tester:\n"
            "  wlt-cert-cli --tester <YYYYYYYYYYYY> --dut <XXXXXXXXXXXX>\n"
            "  Run command example for running datapath module tests only:\n"
            "  wlt-cert-cli --tester <YYYYYYYYYYYY> --dut <XXXXXXXXXXXX> --run datapath\n"
            "  Run command example with sanity test list:\n"
            "  wlt-cert-cli --tester <YYYYYYYYYYYY> --dut <XXXXXXXXXXXX> --tl certificate_sanity_test_list.txt\n"
            "  Run command example with COM PORT tester for combo device:\n"
            "  wlt-cert-cli --tester SIM --dut <XXXXXXXXXXXX>:<YYYYYYYYYYYY> --port <COM_PORT>\n",
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        self.parser.add_argument('--validation_schema', '-vs', required=True, help='Validation schema json file path to use for the run')
        self.parser.add_argument('--dut', required=True, help="Tested device ID. When DUT is a combo device, use <Gateway_ID>:<BLE_MAC>")
        self.parser.add_argument('--combo_ble_addr', default="", help="Combo device BLE MAC address" + argparse.SUPPRESS)
        self.parser.add_argument('--tester', default=GW_SIM_PREFIX, help='Tester id to run on the test, SIM prefix is default and used for COM tester')
        self.parser.add_argument('--port', '-p', default='', help='UART PORT connection to use for the run, if not provided tries to scan for tester port')
        self.parser.add_argument('--custom_broker', '-cb', required=True, help='Choose custom MQTT broker configuration json file to use for the run,' \
                                                                              ' for explanation of the format see https://community.wiliot.com/customers/s/article/Wiliot-Gateway-Certification')
        self.parser.add_argument('--clean', default=False, action='store_true', help='Clean old logs before running the tests')
        self.parser.add_argument('--tl', default=TEST_LIST_DEFAULT_FILE, type=str, help='Test list file to use ' + argparse.SUPPRESS)
        self.parser.add_argument('--run', type=str, help='String (regex) to filter tests to run ' + argparse.SUPPRESS)
        self.parser.add_argument('--drun', type=str, help='String (regex) to filter tests not to run ' + argparse.SUPPRESS)
        self.parser.add_argument('--exit_on_test_failure', default=False, action='store_true', help='Stop running the tests if a test failed ' + argparse.SUPPRESS)
        self.parser.add_argument('--exit_on_param_failure', default=False, action='store_true', help='Sets exit_on_param_failure mode to true in order to prevent \
                                 tests from continuing iteration over all possibilities in case of failure ' + argparse.SUPPRESS)
        self.parser.add_argument('--disable_interference_analyzer', '-dia', default=False, action='store_true', help='Disable interference analysis before tests')
        self.parser.add_argument('--unsterile_run', '-ur', default=False, action='store_true',
                                 help="Set unsterile run mode for the run if there are pixels or energizing devices nearby")
        self.parser.add_argument("--overwrite_defaults", '-od', type=parse_dict_arg, help='Manually overwrite default defines for the bridge (key1=value1,key2=value2...)')
        self.parser.add_argument('--agg', type=int, help='Aggregation time [seconds] the Uplink stages adds to wait before processing results', default=0)
        self.parser.add_argument('--non_cert_run', default=False, action='store_true', help='Mark this as a non-certifying run ' + argparse.SUPPRESS)

    def parse_args(self, args=None):
        """Parse arguments and return them."""
        return self.parser.parse_args(args)

def main():
    cli = CertificateCLI()
    args = cli.parse_args()
    # Set extra args to defaults
    args.data = DATA_SIMULATION
    args.brg1 = None
    args.latest = False
    args.rc = False
    args.sterile_run = not args.unsterile_run
    certificate.main(args)

if __name__ == '__main__':
    main()
