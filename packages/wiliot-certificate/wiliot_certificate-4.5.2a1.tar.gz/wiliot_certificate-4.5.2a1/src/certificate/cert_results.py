import os
import shutil
import tabulate
import subprocess
import datetime
import zoneinfo
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, KeepTogether, Image
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

# Local imports
import certificate.cert_prints as cert_prints
import certificate.cert_utils as cert_utils
from certificate.wlt_types import *
from certificate.cert_defines import *


##################################
# GENERIC
##################################
# Defines
WLT_CERT_HEADLINE =                "Wiliot Certificate {}"
WLT_NON_CERT_HEADLINE =            "Wiliot Non-Certifying Run {}"
SUMMARY_HEADLINE =                 "Summary"
RUN_INFO =                         "Run Information"
RUN_DATETIME =                     "Run Time & Date"
RUN_DUR =                          "Run Duration"
CERT_VER =                         "Certificate Version"
TESTING_DEVICE_INFO =              "Testing Device Information"
TESTED_DEVICE_INFO =               "Tested Device Information"
SIM =                              "Simulator"
GATEWAY =                          "Gateway"
BRG =                              "Bridge"
BLE_MAC_ADDRESS =                  "BLE MAC Address"
BOARD_TYPE =                       "Board Type"
BLE_VER =                          "BLE Version"
SUP_API_VER =                      "Supported API Version"
ADD_INFO =                         "Additional information"
# TODO: This is a temporary list of all schema module names - remove this when auto generated
MODULE_SCHEMA_NAMES_LIST = ["Cloud Connectivity", "Edge Management", "Calibration", "Datapath", "Energizer 2.4GHz",
                            "Energizer Sub-1GHz", "Power Management", "BLE Sensor", "Custom"]

result_map = {TEST_FAILED: cert_prints.color("RED", "FAIL"), TEST_SKIPPED: cert_prints.color("WARNING", "SKIPPED"),
              TEST_PASSED: cert_prints.color("GREEN", "PASS"), TEST_ABORTED: cert_prints.color("RED", "ABORTED")}
pass_or_fail = lambda obj : result_map[obj.rc]

result_map_txt = {TEST_FAILED: "FAIL", TEST_SKIPPED: "SKIPPED", TEST_PASSED: "PASS", TEST_ABORTED: "ABORTED"}
pass_or_fail_txt = lambda obj : result_map_txt[obj.rc]

param_name_to_title = lambda s : ' '.join(word.lower().capitalize() for word in s.split('_')).replace('2 4', '2.4') if '_' in s else s
headline_get = lambda non_cert_run, suffix : WLT_NON_CERT_HEADLINE.format(suffix) if non_cert_run else WLT_CERT_HEADLINE.format(suffix)

class TestResult:
    def __init__(self, name="", devices_to_print="", test_table=None, duration=0, purpose="", kb_link="", compliance="", rc=TEST_PASSED):
        self.name = name
        self.devices = devices_to_print
        self.test_table = test_table
        self.duration = duration
        self.purpose = purpose
        self.kb_link = kb_link
        self.compliance = compliance
        self.rc = rc

    def __repr__(self):
        return self.name

def generate_tests_table(tests=[], html=False):
    headers = ["Module", "Test Name", "Device", "Result Breakdown", "Result", "Run Time"]
    inner_format = "unsafehtml" if html else "simple"
    _pass_or_fail = pass_or_fail_html if html else pass_or_fail
    tests_results = []
    for test in tests:
        dut_to_print = (test.dut.internal_brg.id_str if isinstance(test.dut, cert_utils.Gateway) and test.dut.has_internal_brg()
                        else test.dut.id_str)
        dut_to_print += f"\n{test.brg1.id_str}" if test.brg1 and test.multi_brg else ""
        inner_table = [[phase.name, _pass_or_fail(phase), phase.reason] for phase in test.phases]
        result_breakdown_table = tabulate.tabulate(inner_table, headers=["Phase", "Result", "Notes"], tablefmt=inner_format)
        tests_results.append([cert_utils.module2name(test.test_module),
                              test.module_name if (not test.internal_brg or "gw" in test.module_name) else f"{test.module_name} (internal brg)",
                              dut_to_print,
                              result_breakdown_table,
                              _pass_or_fail(test),
                              test.duration])
    return tabulate.tabulate(tests_results, headers=headers, tablefmt="unsafehtml" if html else "fancy_grid")

def get_update_status_from_log_file(log_file="update_log.txt"):
    update_status = "No version update logs were found"
    if os.path.isfile("update_log.txt"):
        with open(os.path.join(BASE_DIR, log_file), "r") as update_log:
            for l in update_log.readlines():
                if "ERROR: Didn't get response from BRG" in l:
                    update_status = "Didn't get response from BRG in order to start the update!"
                    break
                elif "ERROR: Didn't get response from" in l:
                    update_status = "Didn't get response from GW in order to start the update!"
                    break
                elif "version_update_test failed!" in l:
                    update_status = "GW version update failed!"
                    break
                elif "ota_test failed!" in l:
                    update_status = "BRG OTA failed!"
                    break
                elif "PASSED!" in l:
                    update_status = "GW and BRG versions were updated to latest successfully!"
                    break
                elif "SKIPPED!" in l:
                    update_status = "GW and BRG versions update skipped!"
                    break
    return update_status

def get_important_tests_info():
    patterns = ["DISCONNECTED", "WLT_ERROR", "free heap size", "python_mqtt_disconnect"]
    return "".join([l.strip(' "') for l in open(os.path.join(ARTIFACTS_DIR, CERT_MQTT_LOG_FILE)).readlines() if any([p in l for p in patterns])])

def generate_results_files(html=True, pdf=True, failures=0, skipped=0, start_time=datetime.datetime.now(), tests=[], error=None, non_cert_run=False):
    print(cert_prints.SEP)
    duration = (datetime.datetime.now()-start_time)
    print("Tests duration: {}".format(str(duration).split(".")[0]))
    pipeline = cert_prints.pipeline_running()
    test = tests[-1] if tests else None
    if test and test.dut_is_bridge():
        print("Bridge version: {}".format(test.dut.version))
    if not error:
        print(generate_tests_table(tests))
        print(tabulate.tabulate([[len(tests), len(tests)-(failures+skipped), skipped, failures, len(tests)]],
                                headers=["FINISHED", "PASSED", "SKIPPED", "FAILED", "TOTAL"], tablefmt="pretty"))
        print(cert_prints.WIL_CERT_TEXT)
        cert_prints.print_warn(get_important_tests_info())
    print(f"Run artifacts saved in \"{ARTIFACTS_DIR}\" directory")
    run_type = headline_get(non_cert_run, "").strip()
    cert_prints.print_pass_or_fail(not failures and not error, run_type)

    # Generate HTML file
    if html:
        file_path = os.path.join(ARTIFACTS_DIR, UT_RESULT_FILE_HTML)
        f = open(file_path, "w", encoding="utf-8")
        html_title = headline_get(non_cert_run, "Results")
        html_start_modified = HTML_START.format(html_title)
        f.write(html_start_modified)
        update_status = get_update_status_from_log_file()
        if pipeline:
            p = subprocess.Popen('git log --format=%B -n 1 {}'.format(os.environ['BITBUCKET_COMMIT']),
                                stdout=subprocess.PIPE, shell=True, cwd=os.environ['BITBUCKET_CLONE_DIR'])
            output, err = p.communicate()
        if error:
            headline = headline_get(non_cert_run, "Error!")
            f.write(f"<br><h1 style='color:#ab0000'>{headline}</h1><br>")
            if pipeline:
                f.write("<hr>" + output.decode("utf-8") + "<br>")
                f.write("<p><a href='https://bitbucket.org/wiliot/wiliot-nordic-firmware/commits/{}'>Commit page on bitbucket</a><hr>".format(os.environ['BITBUCKET_COMMIT']))
            f.write(update_status + "<br><br>")
            f.write(error + "<br><br>")
            f.write(f"{RUN_DUR}: {str(duration).split('.')[0]} <br><br>")
            if test and test.dut_is_bridge():
                f.write(f"{BRG} {BLE_VER}: {test.dut.version} <br><br>")
        elif tests:
            if not failures and ("successfully!" in update_status or "skipped!" in update_status or not pipeline):
                headline = headline_get(non_cert_run, "Passed!")
                f.write(f"<br><h1 style='color:#00AB83'>{headline}</h1>")
            else:
                headline = headline_get(non_cert_run, "Failed!")
                f.write(f"<br><h1 style='color:#ab0000'>{headline}</h1>")
            if pipeline:
                f.write("<hr>" + output.decode("utf-8") + "<br>")
                f.write("<p><a href='https://bitbucket.org/wiliot/wiliot-nordic-firmware/commits/{}'>Commit page on bitbucket</a><hr>".format(os.environ['BITBUCKET_COMMIT']))
                f.write(update_status + "<br><br>")
            f.write(f"{RUN_DATETIME}: {start_time.strftime('%d/%m/%Y, %H:%M:%S')} <br><br>")
            f.write(f"{RUN_DUR}: {str(duration).split('.')[0]} <br><br>")
            f.write(f"{CERT_VER}: {CERT_VERSION} <br><br>")
            if test and test.dut_is_gateway():
                f.write(f"{GATEWAY} ID: {test.dut.id_str} <br><br>")
                f.write(f"{GATEWAY} {SUP_API_VER}: {test.dut.gw_api_version} <br><br>")
                f.write(f"{GATEWAY} {SERIALIZATION_FORMAT}: {PROTOBUF if test.dut.protobuf else JSON} <br><br>")
                if test.dut_is_combo():
                    f.write(f"{BRG} {BLE_MAC_ADDRESS}: {test.dut.internal_brg.id_str} <br><br>")
                    f.write(f"{BRG} {BLE_VER}: {test.dut.internal_brg.version} <br><br>")
            if test.dut_is_bridge():
                f.write(f"{BRG} {BLE_MAC_ADDRESS}: {test.dut.id_str} <br><br>")
                f.write(f"{BRG} {BLE_VER}: {test.dut.version} <br><br>")
            if test.tester:
                f.write(f"{SIM} {BLE_MAC_ADDRESS}: {test.tester.internal_brg.id_str} <br><br>")
                f.write(f"{SIM} {BLE_VER}: {test.tester.internal_brg.version} <br><br>")

            f.write(tabulate.tabulate([[len(tests)-(failures+skipped), skipped, failures, len(tests)]], headers=["PASSED", "SKIPPED", "FAILED", "TOTAL"], tablefmt="html"))
            f.write(generate_tests_table(tests, html=True))
            f.write("<br><br>")
        if pipeline:
            f.write(f"<p><a href='https://bitbucket.org/wiliot/wiliot-nordic-firmware/pipelines/results/{os.environ['BITBUCKET_BUILD_NUMBER']}'>Build's page and artifacts on bitbucket</a></p><br><br>")
        f.write("<img src='https://www.wiliot.com/src/img/svg/logo.svg' width='100' height='40' alt='Wiliot logo'>")
        f.write(HTML_END)
        f.close()
        if pipeline:
            # copy results for having it in the email
            shutil.copy(file_path, os.path.join(os.getcwd(), UT_RESULT_FILE_HTML))
    
    # Generate PDF file
    if pdf:
        doc = SimpleDocTemplate(os.path.join(ARTIFACTS_DIR, UT_RESULT_FILE_PDF), pagesize=letter)
        doc.title = headline_get(non_cert_run, "Results")
        elements, hdr_page = [], []

        # Add Wiliot Logo
        img = Image(os.path.join(BASE_DIR, "../common", "wlt_logo.png"), width=100, height=40)  # Adjust size as needed
        hdr_page.append(img)
        hdr_page.append(Spacer(1, 20))

        # Title and Summary
        red_header = STYLES_PDF.get("RED_HEADER", ParagraphStyle("Default"))
        green_header = STYLES_PDF.get("GREEN_HEADER", ParagraphStyle("Default"))
        black_header = STYLES_PDF.get("BLACK_HEADER", ParagraphStyle("Default"))
        module_header = STYLES_PDF.get("MODULE_HEADER", ParagraphStyle("Default"))
        test_header = STYLES_PDF.get("TEST_LINK_HEADER", ParagraphStyle("Default"))
        test_purpose = STYLES_PDF.get("TEST_HEADER", ParagraphStyle("Default"))
        bold_text_style = STYLES_PDF.get("BLACK_BOLD", ParagraphStyle("Default"))
        bold_right_text_style = STYLES_PDF.get("BLUE_BOLD_RIGHT", ParagraphStyle("Default"))
        centered_text_style = STYLES_PDF.get("BLACK", ParagraphStyle("Default"))
        if error:
            headline = headline_get(non_cert_run, "Error!")
            title = Paragraph(f"<b>{headline}</b>", red_header)
            hdr_page.append(title)
            hdr_page.append(Spacer(1, 20))
            hdr_page.append(Paragraph(f"{error}", bold_text_style))
        else:
            headline = headline_get(non_cert_run, "Results")
            title = Paragraph(f"<b>{headline}</b>", black_header)
            hdr_page.append(title)
        
        # Add Passed/Failed status header
        if not error:
            is_passed = failures == 0
            status_text = "Passed" if is_passed else "Failed"
            status_header_style = green_header if is_passed else red_header
            status_header = Paragraph(f"<b>{status_text}</b>", status_header_style)
            hdr_page.append(Spacer(1, 10))
            hdr_page.append(status_header)
        
        hdr_page.append(Spacer(1, 20))
        hdr_page.append(Paragraph(f"<a name='{SUMMARY_HEADLINE}'/><b>{SUMMARY_HEADLINE}</b>", module_header))
        hdr_page.append(Spacer(1, 10))
        hdr_page.append(Paragraph(f"<u>{RUN_INFO}:</u>", bold_text_style))
        hdr_page.append(Paragraph(f"{RUN_DATETIME}: {start_time.strftime('%d/%m/%Y, %H:%M:%S')}", bold_text_style))
        hdr_page.append(Paragraph(f"{RUN_DUR}: {str(duration).split('.')[0]}", bold_text_style))
        hdr_page.append(Paragraph(f"{CERT_VER}: {CERT_VERSION}", bold_text_style))
        hdr_page.append(Spacer(1, 10))
        if test:
            hdr_page.append(Paragraph(f"<u>{TESTED_DEVICE_INFO}:</u>", bold_text_style))
            if test.dut_is_gateway():
                hdr_page.append(Paragraph(f"{GATEWAY} ID: {test.dut.id_str}", bold_text_style))
                hdr_page.append(Paragraph(f"{GATEWAY} {SUP_API_VER}: {test.dut.gw_api_version}", bold_text_style))
                hdr_page.append(Paragraph(f"{GATEWAY} {SERIALIZATION_FORMAT}: {PROTOBUF if test.dut.protobuf else JSON}", bold_text_style))
            if test.dut_is_combo() or test.dut_is_bridge():
                brg = test.dut.internal_brg if test.dut_is_combo() else test.dut
                hdr_page.append(Paragraph(f"{BRG} {BLE_MAC_ADDRESS}: {brg.id_str}", bold_text_style))
                hdr_page.append(Paragraph(f"{BRG} {BOARD_TYPE}: {ag.BOARD_TYPES_LIST[brg.board_type]}", bold_text_style))
                hdr_page.append(Paragraph(f"{BRG} {BLE_VER}: {brg.version}", bold_text_style))
                hdr_page.append(Paragraph(f"{BRG} {SUP_API_VER}: {brg.api_version}", bold_text_style))
            hdr_page.append(Spacer(1, 10))

            # In wlt-cert-reg there is no tester
            if test.tester:
                hdr_page.append(Paragraph(f"<u>{TESTING_DEVICE_INFO}:</u>", bold_text_style))
                hdr_page.append(Paragraph(f"{SIM} {BLE_MAC_ADDRESS}: {test.tester.internal_brg.id_str}", bold_text_style))
                hdr_page.append(Paragraph(f"{SIM} {BOARD_TYPE}: {ag.BOARD_TYPES_LIST[test.tester.internal_brg.board_type]}", bold_text_style))
                hdr_page.append(Paragraph(f"{SIM} {BLE_VER}: {test.tester.internal_brg.version}", bold_text_style))
                hdr_page.append(Spacer(1, 10))
        notes_file_path = os.path.join(ARTIFACTS_DIR, RESULT_NOTES_FILE)
        if os.path.exists(notes_file_path):
            hdr_page.append(Paragraph(f"<u>{ADD_INFO}:</u>", bold_text_style))
            with open(notes_file_path, 'r') as f:
                for line in f.readlines():
                    hdr_page.append(Paragraph(f"{line}", bold_text_style))

        hdr_page.append(Spacer(1, 15))

        # Analyze results per module and generate results per module for PDF
        results_per_module = generate_results_per_module_for_pdf(tests=tests)

        # Modules Table
        hdr_page.append(Paragraph(f"<b>Modules Overview</b>", module_header))
        hdr_page.append(Spacer(1, 15))
        modules_overview = get_modules_overview(results_per_module)
        module_stats_table_data = []
        for module_name, status in modules_overview.items():
            module_stats_table_data.append([Paragraph(module_name, centered_text_style), pdf_result_map[status]])
        module_stats_table = Table([["Module", "Status"]] + module_stats_table_data, colWidths=[100, 100])
        module_stats_table.setStyle(inner_table_style('CENTER'))
        hdr_page.append(module_stats_table)
        hdr_page.append(PageBreak())

        # Tests Tables
        hdr_page.append(Paragraph(f"<b>Tests Overview</b>", module_header))
        hdr_page.append(Spacer(1, 20))

        # Tests Count Table
        count_data = [
            ["PASSED", "SKIPPED", "FAILED", "TOTAL"],
            [len(tests)-(failures+skipped), skipped, failures, len(tests)]
        ]
        count_table = Table(count_data)
        count_table.setStyle(inner_table_style('CENTER'))
        hdr_page.append(count_table)
        hdr_page.append(Spacer(1, 10))
        
        # Tests Results Table
        summary_data = []
        for module, test_results in results_per_module.items():
            module_objects = []
            module_skipped = True # Remains True if all tests are skipped
            module_objects.append(Paragraph(f"<b>{module + ' Module' if (not 'Edge' in module and not 'Cloud' in module) else module}</b>", module_header))
            module_objects.append(Spacer(1, 20))
            for test_result in test_results:
                test_skipped = test_result.rc == TEST_SKIPPED
                test_objects = []
                name = Paragraph(f'<a href="#{module}_{test_result.name}">{test_result.name}</a>', centered_text_style) if not test_skipped else test_result.name
                summary_data += [[module, name, pass_or_fail_pdf(test_result), test_result.compliance]]
                test_objects.append(Paragraph(f'<a name="{module}_{test_result.name}"/><a href="{test_result.kb_link}">{test_result.name}</a>', test_header))
                test_objects.append(Spacer(1, 10))
                test_objects.append(pass_or_fail_pdf(test_result))
                test_objects.append(Spacer(1, 10))
                test_objects.append(Paragraph(test_result.purpose, test_purpose))
                test_objects.append(Spacer(1, 10))
                if not test_skipped:
                    module_skipped = False # Set to False if at least one test isn't skipped
                    test_objects.append(Paragraph(f"Tested devices: {test_result.devices}", bold_text_style))
                    test_objects.append(Paragraph(f"Test duration: {test_result.duration}", bold_text_style))
                    test_objects.append(Spacer(1, 10))
                    test_objects.append(test_result.test_table)
                    test_objects.append(Spacer(1, 10))
                    test_objects.append(Paragraph(f"<a href='#{SUMMARY_HEADLINE}'>Back to {SUMMARY_HEADLINE}</a>", bold_right_text_style))
                    test_objects.append(Spacer(1, 20))
                module_objects.append(KeepTogether(test_objects))
            if not module_skipped:
                elements += module_objects
                elements.append(PageBreak())
        summary_table = Table([["Module", "Name", "Result", "Compliance"]] + summary_data)
        summary_table.setStyle(inner_table_style('LEFT'))
        elements = hdr_page + [summary_table, PageBreak()] + elements

        doc.build(elements)

    # Upload pipeline results to DB
    if pipeline:
        import boto3
        import json
        import io
        from botocore.exceptions import ClientError

        if test:
            device_id = f"{test.dut.id_str}:{test.dut.internal_brg.id_str}" if test.dut_is_combo() else test.dut.id_str
            version = test.dut.internal_brg.version if test.dut_is_combo() else test.dut.version
        else:
            device_id = "NO_ID"
            version = "0.0.0"
        json_data = {
            "setup_name": os.environ['PIPELINE_NAME'],
            "device_id": device_id,
            "version": version,
            "run_type": os.environ['PIPELINE_TYPE'],
            "pipeline_url": f"https://bitbucket.org/wiliot/wiliot-nordic-firmware/pipelines/results/{os.environ['BITBUCKET_BUILD_NUMBER']}",
            "run_datetime": str(datetime.datetime.now(zoneinfo.ZoneInfo("Asia/Jerusalem"))),
            "passed_tests": len(tests)-(failures+skipped),
            "failed_tests": failures,
            "skipped_tests": skipped,
            "total_tests": len(tests),
            "run_time_seconds": duration.total_seconds(),
            "tests": generate_results_for_db(tests)
        }
        print(json_data)

        # upload to S3
        timestamp = datetime.datetime.now().strftime("%d_%m_%Y_%H_%M_%S_%f")[:-3]
        key = f"triggers/projects/fm-certificate/pending/{timestamp}/payload/data.json"
        bucket = "wiliot-systemlab"
        s3 = boto3.client("s3", region_name="us-east-1",
                            aws_access_key_id=os.environ['DB_AWS_ACCESS_KEY'],
                            aws_secret_access_key=os.environ['DB_AWS_SECRET_ACCESS_KEY'])

        try:
            body = io.BytesIO(json.dumps(json_data).encode())
            s3.upload_fileobj(body, bucket, key)
            print(f"Uploaded successfully to s3://{bucket}/{key}")
        except ClientError as e:
            print(f"S3 Error: {e}")

##################################
# HTML
##################################
COLORS_HTML = {
    "HEADER": "color: #ff00ff;",  # Purple
    "BLUE": "color: #0000ff;",   # Blue
    "CYAN": "color: #00ffff;",   # Cyan
    "GREEN": "color: #00ff00;",  # Green
    "WARNING": "color: #ffff00;",  # Yellow
    "RED": "color: #ff0000;",    # Red
    "BOLD": "font-weight: bold;",
    "UNDERLINE": "text-decoration: underline;",
}
color_html = lambda c, t: f'<span style="{COLORS_HTML.get(c, "")}{COLORS_HTML["BOLD"]}">{t}</span>'
html_result_map = {TEST_FAILED: color_html("RED", "FAIL"), TEST_SKIPPED: color_html("WARNING", "SKIPPED"),
                   TEST_PASSED: color_html("GREEN", "PASS"), TEST_ABORTED: color_html("RED", "ABORTED")}
pass_or_fail_html = lambda obj : html_result_map[obj.rc]

HTML_START = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset='utf-8'>
        <meta http-equiv='X-UA-Compatible' content='IE=edge'>
        <title>{}</title>
        <meta name='viewport' content='width=device-width, initial-scale=1'>
        <style>
        html, body {{
                height: 100%;
            }}

            html {{
                display: table;
                margin: auto;
            }}

            body {{
                display: table-cell;
                vertical-align: middle;
            }}
        table {{
            border-collapse: collapse;
            font-family: Tahoma, Geneva, sans-serif;
        }}
        table td {{
            padding: 15px;
        }}
        table thead td {{
            background-color: #54585d;
            color: #ffffff;
            font-weight: bold;
            font-size: 13px;
            border: 1px solid #54585d;
        }}
        table tbody td {{
            color: #636363;
            border: 1px solid #dddfe1;
        }}
        table tbody tr {{
            background-color: #f9fafb;
        }}
        table tbody tr:nth-child(odd) {{
            background-color: #ffffff;
        }}
        </style>
    </head>
    <body>
    """
HTML_END = """
    </body>
    </html>
    """

##################################
# PDF
##################################
STYLES_PDF = {
    "BLACK_HEADER": ParagraphStyle("Black Header", fontName="Helvetica-Bold", fontSize=20, textColor=colors.black, alignment=TA_CENTER),
    "RED_HEADER": ParagraphStyle("Red Header", fontName="Helvetica-Bold", fontSize=20, textColor=colors.red, alignment=TA_CENTER),
    "GREEN_HEADER": ParagraphStyle("Green Header", fontName="Helvetica-Bold", fontSize=20, textColor=colors.green, alignment=TA_CENTER),
    "GRAY": ParagraphStyle("Gray", fontName="Helvetica-Bold", fontSize=9, textColor=colors.grey, splitLongWords=False, alignment=TA_LEFT, wordWrap = 'CJK'),
    "MODULE_HEADER": ParagraphStyle("Module Header", fontName="Helvetica-Bold", fontSize=16, textColor=colors.navy, alignment=TA_CENTER),
    "TEST_HEADER": ParagraphStyle("Test Header", fontName="Helvetica-Bold", fontSize=12, textColor=colors.black, alignment=TA_LEFT),
    "TEST_LINK_HEADER": ParagraphStyle('Test Link Header', fontName="Helvetica-Bold", fontSize=14, textColor=colors.blue, alignment=TA_LEFT),
    "BLACK": ParagraphStyle("Black", fontName="Helvetica", fontSize=9, textColor=colors.black, splitLongWords=False, alignment=TA_LEFT, wordWrap = 'CJK'),
    "BLACK_BOLD": ParagraphStyle("Black Bold", fontName="Helvetica-Bold", fontSize=9, textColor=colors.black, splitLongWords=False, alignment=TA_LEFT, wordWrap = 'CJK'),
    "BLUE_BOLD_RIGHT": ParagraphStyle("Black Bold", fontName="Helvetica-Bold", fontSize=9, textColor=colors.blue, splitLongWords=False, alignment=TA_RIGHT, wordWrap = 'CJK'),
    "BLUE": ParagraphStyle("Blue", fontName="Helvetica-Bold", fontSize=9, textColor=colors.navy, splitLongWords=False, alignment=TA_CENTER),
    "CYAN": ParagraphStyle("Cyan", fontName="Helvetica-Bold", fontSize=9, textColor=colors.cyan, splitLongWords=False, alignment=TA_LEFT),
    "GREEN": ParagraphStyle("Green", fontName="Helvetica-Bold", fontSize=9, textColor=colors.green, splitLongWords=False, alignment=TA_LEFT),
    "WARNING": ParagraphStyle("Warning", fontName="Helvetica-Bold", fontSize=9, textColor=colors.gold, splitLongWords=False, alignment=TA_LEFT),
    "RED": ParagraphStyle("Red", fontName="Helvetica-Bold", fontSize=9, textColor=colors.red, splitLongWords=False, alignment=TA_LEFT),
}
def color_pdf(c, t):
    style = STYLES_PDF.get(c, ParagraphStyle("Default"))
    return Paragraph(t, style)
pdf_result_map = {TEST_FAILED: color_pdf("RED", "FAILED"), TEST_SKIPPED: color_pdf("WARNING", "SKIPPED"), 
                  TEST_PASSED: color_pdf("GREEN", "PASSED"), TEST_ABORTED: color_pdf("RED", "ABORTED"),
                  MODULE_UNSUPPORTED: color_pdf("GRAY", "UNSUPPORTED")}
pass_or_fail_pdf = lambda obj : pdf_result_map[obj.rc]

inner_table_style = lambda align :  TableStyle([
                                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                                    ('ALIGN', (0, 0), (-1, -1), f'{align}'),
                                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                                    ('FONTSIZE', (0, 0), (-1, 0), 9),
                                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                                    ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
                                    ('WORDWRAP', (0, 0), (-1, -1), False),
                                ])

def get_modules_overview(results_per_module):
    """Get modules overview for the tests."""
    modules_overview = {}
    for module_name in MODULE_SCHEMA_NAMES_LIST:
        if module_name in results_per_module:  # Module is in run - check if it passed/failed/skipped
            test_results = results_per_module[module_name]
            modules_overview[module_name] = TEST_SKIPPED  # Assume all tests are skipped until proven otherwise
            for test_result in test_results:
                # If any test failed, the module failed
                if test_result.rc == TEST_FAILED:
                    modules_overview[module_name] = TEST_FAILED
                    break
                # If any test passed, the module passed until proven otherwise
                elif test_result.rc == TEST_PASSED:
                    modules_overview[module_name] = TEST_PASSED
                # If any mandatory test is skipped, the module is skipped
                elif test_result.rc == TEST_SKIPPED and test_result.compliance == "Mandatory":
                    modules_overview[module_name] = TEST_SKIPPED
        else:  # Module not in run - show as Unsupported
            modules_overview[module_name] = MODULE_UNSUPPORTED
    return modules_overview


def generate_results_per_module_for_pdf(tests=[]):
    text_style = STYLES_PDF.get("BLACK", ParagraphStyle("Default"))
    results_per_module = {}
    for test in tests:
        devices_to_print = (f"{test.dut.id_str}\n{test.brg1.id_str}" if test.brg1 and test.multi_brg else test.dut.id_str)
        inner_table = [[Paragraph(param_name_to_title(phase.name), text_style), pass_or_fail_pdf(phase), Paragraph(phase.reason, text_style)] for phase in test.phases]
        test_table = Table([["Phase", "Result", "Notes"]] + inner_table)
        test_table.setStyle(inner_table_style('LEFT'))
        compliance = "Mandatory" if test.test_json[MANDATORY] else "Optional"
        test_result = TestResult(name=test.test_json[NAME], devices_to_print=devices_to_print, test_table=test_table, rc=test.rc,
                                 duration=test.duration, purpose=str(test.test_json[PURPOSE]), compliance=compliance, kb_link=test.test_json[DOCUMENTATION])
        module_name = test.test_json[MODULE]
        if module_name not in results_per_module:
                results_per_module[module_name] = [test_result]
        else:
            results_per_module[module_name] += [test_result]
    return results_per_module

def generate_results_for_db(tests=[]):
    results = []
    for test in tests:
        internal_brg_txt = " (internal brg)" if test.internal_brg else ""
        result = {
            "module_name": test.test_json[MODULE],
            "test_name": test.test_json[NAME] + internal_brg_txt,
            "result": pass_or_fail_txt(test),
            "run_time": test.duration,
        }
        result["phases"] = [{"phase_name": param_name_to_title(phase.name), "result": pass_or_fail_txt(phase), "notes": phase.reason} for phase in test.phases]
        results.append(result)
    return results
