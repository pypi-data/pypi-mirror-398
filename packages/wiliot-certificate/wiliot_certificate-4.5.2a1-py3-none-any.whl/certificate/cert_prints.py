from certificate.cert_defines import *
import time, datetime
import sys
import json
import os
import re

COLORS = {
    "HEADER" : '\033[95m',
    "BLUE" : '\033[94m',
    "CYAN" : '\033[96m',
    "GREEN" : '\033[92m',
    "WARNING" : '\033[93m',
    "RED" : '\033[91m',
    "ENDC" : '\033[0m',
    "BOLD" : '\033[1m',
    "UNDERLINE" : '\033[4m',
}
color = lambda c, t : COLORS["BOLD"]+COLORS[c]+t+COLORS["ENDC"]
pipeline_running = lambda : True if 'BITBUCKET_BUILD_NUMBER' in os.environ else False
is_quiet_setup_running = lambda : True if 'CI_GW' in os.environ else False
camelcase_to_title = lambda s: ' '.join(word.capitalize() for word in re.split('(?=[A-Z])', s))
SEP = '\n' + '#'*100 + '\n'
SEP2 = '\n' + '#'*100 + '\n' + '#'*100 + '\n'
WIL_CERT_TEXT = r'''
 __        _____ _     ___ ___ _____    ____ _____ ____ _____ ___ _____ ___ ____    _  _____ _____ 
 \ \      / /_ _| |   |_ _/ _ \_   _|  / ___| ____|  _ \_   _|_ _|  ___|_ _/ ___|  / \|_   _| ____|
  \ \ /\ / / | || |    | | | | || |   | |   |  _| | |_) || |  | || |_   | | |     / _ \ | | |  _|  
   \ V  V /  | || |___ | | |_| || |   | |___| |___|  _ < | |  | ||  _|  | | |___ / ___ \| | | |___ 
    \_/\_/  |___|_____|___\___/ |_|    \____|_____|_| \_\|_| |___|_|   |___\____/_/   \_\_| |_____|
                                                                                                   
'''

hex_str2int = lambda s : int(s, 16)

def write_to_log_file(file, txt, mode):
    file_path = os.path.join(ARTIFACTS_DIR, file)
    if not os.path.exists(os.path.dirname(file_path)):
        os.makedirs(os.path.dirname(file_path))
    f = open(file_path, mode)
    f.write(txt)
    f.close()

def print_pkt(p):
    print(datetime.datetime.now().strftime("%d/%m/%Y, %H:%M:%S"))
    print(json.dumps(p, indent=4, default=lambda o: o.__dict__, sort_keys=True))

def print_warn(txt):
    if txt:
        utPrint(f"WARNING: {txt}","WARNING")

def mqtt_scan_start(test, duration, target=DUT):
    gw = test.dut if target == DUT else test.tester
    utPrint("Scanning mqtt packets on {} for {} seconds...".format(gw.id_str, duration), "WARNING")
    sys.stdout.flush()


def mqtt_scan_wait(test, duration, target=DUT):
    mqttc = test.get_mqttc_by_target(target)
    gw = test.dut if target == DUT else test.tester
    utPrint("Scanning mqtt packets on {} for {} seconds...".format(gw.id_str, duration), "WARNING")
    sys.stdout.flush()
    chars = ["|", "/", "-", "\\"]
    start_time = datetime.datetime.now()
    i = 0
    while True:
        cur_duration = (datetime.datetime.now() - start_time).seconds
        if cur_duration >= duration:
            break
        if pipeline_running():
            sys.stdout.write(".")
        else:
            sys.stdout.write("\r"+chars[i%4]*20+" "+str(cur_duration)+" "+chars[i%4]*20+" {} pkts captured".format(len(mqttc._userdata[PKTS].data)))
        sys.stdout.flush()
        time.sleep(0.25)
        i += 1
    print("\n")


def print_update_wait(secs=1):
    sys.stdout.write(".")
    sys.stdout.flush()
    time.sleep(secs)

def wait_time_n_print(secs, txt=""):
    if txt:
        utPrint(txt, "CYAN")
    utPrint(f"Waiting for {secs} seconds", "CYAN")
    while secs:
        print_update_wait()
        secs -= 1

def field_functionality_pass_fail_print(test, field, value=""):
    print_string = f"{field}={value}"
    if value == "":
        print_string = str(field)
    if test.rc == TEST_FAILED:
        utPrint(print_string + " functionality failed!", "RED")
        utPrint(test.reason, "RED")
    elif test.rc == TEST_SKIPPED:
        utPrint(print_string + " functionality skipped!", "WARNING")
    else:
        utPrint(print_string + " functionality passed!", "GREEN")

def test_run_print(test):
    brg_txt = ""
    if test.params:
        params = " (params: {})".format(test.params)
    else:
        params = " (without params)"
    if test.active_brg:
        brg_txt = " ({}: {}".format("INTERNAL BRG" if test.internal_brg else "BRG", test.active_brg.id_str)
        if test.brg1 and test.multi_brg:
            brg_txt += " & " + test.brg1.id_str
        brg_txt += ")"
    log_txt = f"{SEP}==>> Running {test.module_name}{params}{brg_txt}{SEP}"
    utPrint(log_txt, "BLUE")
    utPrint("Test Information:\n", "HEADER")
    test_json_print(test)
    utPrint("Test Configuration:", "HEADER")
    params = [{'name':p.name, 'value':p.value} for p in test.params]
    utPrint(f"""    - internal_brg={test.internal_brg}\n    - tester={test.tester}
    - dut={test.dut}\n    - brg1={test.brg1}\n    - active_brg={test.active_brg}
    - params={params}\n""")
    write_to_log_file(DATA_SIM_LOG_FILE, log_txt, "a")
    write_to_log_file(CERT_MQTT_LOG_FILE, log_txt, "a")

def test_json_print(test):
    for key, value in test.test_json.items():
        if key == 'procedure':
            print(f"    {camelcase_to_title(key)}:")
            for i in range(len(value)):
                print(f"        ({i}) {value[i]}")
        else:
            print(f"    {camelcase_to_title(key)}: {value}")

def test_epilog_print(test):
    if any([phase.rc == TEST_FAILED for phase in test.phases]):
        utPrint(test.reason, "RED")
        utPrint("==>> Test {} failed!".format(test.module_name), "RED")
    else:
        utPrint(test.reason, "GREEN")
        utPrint("==>> Test {} passed!".format(test.module_name), "GREEN")

def functionality_run_print(func):
    txt = "{0}==>> Running {1}\n".format(SEP, func)
    utPrint(txt, "CYAN")
    write_to_log_file(DATA_SIM_LOG_FILE, txt, "a")
    write_to_log_file(CERT_MQTT_LOG_FILE, txt, "a")

def phase_run_print(func):
    txt = f"{SEP2}==>> Phase {func}{SEP2}\n"
    utPrint(txt, "CYAN")
    write_to_log_file(DATA_SIM_LOG_FILE, txt, "a")
    write_to_log_file(CERT_MQTT_LOG_FILE, txt, "a")


def generate_print_string(fields_and_values):
    list_to_print = []
    for f in fields_and_values:
        list_to_print.append(str(f) + "=" + str(fields_and_values[f]))
    return " & ".join(list_to_print)

ENERGY_GRAPH_HTML = """
<h1 style="color:blue;text-align:center;">{}</h1>
<div style="width:80%;margin:auto;"><canvas id="myChart"></canvas></div>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script>
    const labels = {};
    const data = {{labels: labels, datasets: [{}]}};
    const config = {{type: 'line', data: data, options: {{}}}};
    const myChart = new Chart(document.getElementById('myChart'), config);
</script>\n"""

def print_pass_or_fail(rc, text):
    if rc:
        utPrint(text+" PASSED!", "GREEN")
    else:
        utPrint(text+" FAILED!", "RED")

def utPrint(text, chosenColor="none"):
    if chosenColor == "none":
        print("\n"+text)
    else:
        print("\n"+(color(chosenColor.upper(), text)))

def format_for_table(string, width):
    while len(string) < width:
        if len(string) == width-1:
            string+="_"
        else:
            string="_"+string+"_"
    return string

def print_duration(test):
    duration = str(datetime.datetime.now() - test.start_time).split(".")[0]
    print(f"## Duration of the test until now is {duration}")
    return test
