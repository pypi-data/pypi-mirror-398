
import datetime
import time
import os
import requests
import json

from enum import Enum
from typing import Literal

from certificate.cert_defines import TEST_FAILED, TEST_PASSED, TEST_SKIPPED
from certificate.cert_prints import phase_run_print

import certificate.cert_utils as cert_utils
import certificate.cert_common as cert_common


# HELPER DEFINES
GW_REGISTER_DOC = "https://community.wiliot.com/customers/s/article/Registering-Third-Party-Gateways"
GW_MQTT_DOC = "https://community.wiliot.com/customers/s/article/Sending-Wiliot-Packets-to-the-Wiliot-Cloud"

REGISTRATION_API_KEY_ENV_VAR = "REGISTRATION_TEST_API_KEY"

REG_CERT_OWNER_ID = 'gw-certification-account'

STAGES_TIMEOUT_MINUTES = 2
TOKEN_EXPIRY_MINUTES = 3
CLOUD_DELAY_SEC = 7
BUSY_WAIT_DELAY_SEC = 5
STAGE_START_DELAY_MS = (BUSY_WAIT_DELAY_SEC + CLOUD_DELAY_SEC + 1) * 1000

ERROR_NO_REGISTER = 'Gateway did not register itself in time.'
ERROR_NO_ONLINE = 'Gateway did not connect to MQTT in time.'
ERROR_NO_ACTIVE = 'Gateway did not upload a status message with its configurations in time.'
ERROR_NO_REFRESH = 'Gateway did not reconnect to MQTT in time.'

HEADERS = {
    "accept": "application/json",
    "Content-Type": "application/json",
    "Authorization": None
}
BASE_URL = "https://api.us-east-2.prod.wiliot.cloud"
OWNER_URL = BASE_URL + f"/v1/owner/{REG_CERT_OWNER_ID}"
API_TOKEN_URL = BASE_URL + '/v1/auth/token/api'

# GLOBALS
api_key = None
gw_online_ts = None


# HTTP RELATED
class HttpMethod(str, Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"


def http_request(path, payload, request_method: HttpMethod):
    headers = HEADERS

    def get_token():
        headers = {
            'Authorization': api_key
        }
        response = requests.post(API_TOKEN_URL, headers=headers)
        if response.status_code == 200:
            token = response.json()
            return token["access_token"]
        else:
            raise Exception(f"Failed to get token. statuscode: {response.status_code}, {response.text}")

    headers['Authorization'] = get_token()
    response = requests.request(request_method, (OWNER_URL + path), headers=headers, data=payload)
    try:
        message = response.json()
    except json.JSONDecodeError:
        message = response.text
    if isinstance(message, str):
        message = {"data": message}
    message.update({'status_code': response.status_code})
    return message


def get_gateway(gateway_id):
    path = f"/gateway/{gateway_id}"
    result = http_request(path, payload=None, request_method=HttpMethod.GET)
    if result['status_code'] != 200:
        raise Exception(f"get_gateway request failed with status_code {result['status_code']}")
    return result["data"]


def register_gateway(gateways: list):
    payload = {
        "gateways": gateways
    }
    path = "/gateway"
    response = http_request(path, payload=json.dumps(payload), request_method=HttpMethod.PUT)
    return (response.get("data", "").lower() == "ok", response)


def delete_gateway(gateway_id):
    path = f"/gateway/{gateway_id}"
    response = http_request(path, payload=None, request_method=HttpMethod.DELETE)
    return response.get('message', "").lower().find("success") != -1


def kick_gw_from_mqtt(gw_id):
    path = f"/gateway/{gw_id}/kick-mqtt-connection"
    response = http_request(path, payload=None, request_method=HttpMethod.POST)
    return response


def get_kong_logs(gw_id):
    """
    Only available under the certificate registration account
    """
    path = f"/gateway/{gw_id}/auth-logs"

    return http_request(path, payload=None, request_method=HttpMethod.GET)


# TEST RELATED
class GetGwField(Enum):
    STATUS = 'status'
    ONLINE = 'online'
    ONLINE_UPDATED_AT = 'onlineUpdatedAt'
    ACTIVATED_AT = 'activatedAt'


class Status(Enum):
    PRE_REGISTERED = 'pre-registered'
    REGISTERED = 'registered'
    APPROVED = 'approved'
    ACTIVE = 'active'


class GenericRegistrationStage():
    def __init__(self, dut, **kwargs):
        self.__dict__.update(kwargs)
        self.dut = dut
        self.start_time = None
        self.duration = datetime.timedelta(0)
        self.report = ''
        self.error_summary = ''

    def calc_run_duration(self):
        self.duration = datetime.datetime.now() - self.start_time

    def add_report_header(self):
        self.report += f'This phase {(self.stage_tooltip.lower())}.\n'
        self.report += '-' * 50 + '\n'

    def get_gateway_field(self, field: GetGwField):
        temp = get_gateway(self.dut)
        return temp[field.value]

    def kick_gw_from_mqtt(self):
        response = kick_gw_from_mqtt(self.dut)
        print(f"Kick response:{response}")

    def validate_kong_logs(self, endpoint: Literal['device-authorize', 'registry', 'token', 'refresh']):
        message = get_kong_logs(self.dut)
        status_code = message.get('status_code')
        if status_code == 404:
            response_data = message.get('message')
            if 'not found' in response_data:
                print("Could not find gw when requesting for logs.")
                print("Either it is not registered, didn't issue any requests, or is missing the X-Gateway-ID header.")
                return False
            else:
                raise Exception(f'Failed getting kong logs: {response_data}')
        if isinstance(message, dict) and message.get('status_code') != 200:
            print(f"Failed fetching logs, status_code:{message.get('status_code')}")
            return False

        # Convert datetime.datetime.now() format to epoch in MS
        stage_start_ts = self.start_time.timestamp() * 1000 - STAGE_START_DELAY_MS

        for log in message['data']:
            if log['timestamp'] > stage_start_ts and endpoint in log['endpoint']:
                response_code = log['responseCode']
                if response_code != 200:
                    print(f"An HTTP request to /{endpoint} resulted in an invalid response code:{response_code}")
                else:
                    print(f"A valid HTTP request to /{endpoint} was received")
                    return True

        print(f"No valid HTTP request to /{endpoint} was found")
        return False

    def prepare_stage(self):
        pass


class Registry(GenericRegistrationStage):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        self.stage_tooltip = "Validate the gateway's registry step"
        super().__init__(name=type(self).__name__, **self.__dict__)

    def prepare_stage(self):
        print('Pre-registering the gateway, please make sure it is not registered to any other account '
              'and that your device is ready to run the registration flow')

        def pre_register_gw_anew(gw_id):
            pre_registered, message = register_gateway([gw_id])
            status_code = message.get('status_code')
            if status_code == 400:
                response_data = message.get('message')
                if 'already exists' in response_data:
                    print(f'{gw_id} already exists in Wiliot platform! Deleting and pre-registering from scratch')
                    self.kick_gw_from_mqtt()
                    delete_gateway(gw_id)
                    time.sleep(CLOUD_DELAY_SEC)
                    pre_registered, message = register_gateway([gw_id])
            if status_code == 403:
                raise Exception(f"The API key within {REGISTRATION_API_KEY_ENV_VAR} seems invalid."
                                " It is not authorized to pre-register the gateway")
            return pre_registered, message

        pre_registered, message = pre_register_gw_anew(self.dut)
        if not pre_registered:
            print(f'Failed pre-registering the gateway. HTTP response:\n{message}')
            raise Exception("Failed pre-registering the gateway. Make sure: Your API key is valid,"
                            " and you have a stable internet connection. Otherwise, try again later.")
        print(f"{self.dut} was pre-registered successfully")

    def run(self):
        self.start_time = datetime.datetime.now()
        print("Waiting for the gateway to finish the Registry step..")
        timeout = datetime.datetime.now() + datetime.timedelta(minutes=STAGES_TIMEOUT_MINUTES)
        self.status = self.get_gateway_field(GetGwField.STATUS)
        while datetime.datetime.now() < timeout and not any(self.status == s.value for s in {Status.APPROVED, Status.ACTIVE}):
            time.sleep(BUSY_WAIT_DELAY_SEC)
            self.status = self.get_gateway_field(GetGwField.STATUS)

        time.sleep(CLOUD_DELAY_SEC)
        self.validate_kong_logs('device-authorize')
        self.validate_kong_logs('registry')
        self.calc_run_duration()

    def generate_stage_report(self):
        self.add_report_header()
        if not any(self.status == s.value for s in {Status.APPROVED, Status.ACTIVE}):
            self.error_summary = ERROR_NO_REGISTER
            self.report += f'{ERROR_NO_REGISTER}\n'
            print(f"The gateway failed to register. Its status is '{self.status}' while it is expected to be '{Status.APPROVED.value}'.")
            self.report += "There was an error in the Device-authorize or Registry steps.\n"
            self.report += f"Please go over the Device-authorize and Registry sections in this document:\n{GW_REGISTER_DOC}\n"
            if self.status == Status.REGISTERED:
                self.report += "Highly likely that the gateway is missing the 'X-Gateway-ID' header in it's HTTP requests.\n"
            return False
        else:
            self.report += "Device-authorize and Registry requests were issued well.\n"
            self.report += "Gateway registered successfully.\n"
            print("Gateway registered successfully")
            return True


class Online(GenericRegistrationStage):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        self.stage_tooltip = "Validate the gateway become online on the platform"
        super().__init__(name=type(self).__name__, **self.__dict__)

    def run(self):
        self.start_time = datetime.datetime.now()
        print("Waiting for the gateway to connect to MQTT..")
        timeout = datetime.datetime.now() + datetime.timedelta(minutes=STAGES_TIMEOUT_MINUTES)
        self.online = self.get_gateway_field(GetGwField.ONLINE)
        while datetime.datetime.now() < timeout and self.online is not True:
            time.sleep(BUSY_WAIT_DELAY_SEC)
            self.online = self.get_gateway_field(GetGwField.ONLINE)

        time.sleep(CLOUD_DELAY_SEC)
        self.validate_kong_logs('token')
        if self.online:
            global gw_online_ts
            gw_online_ts = datetime.datetime.now()
        self.calc_run_duration()

    def generate_stage_report(self):
        self.add_report_header()
        if self.online is not True:
            self.error_summary = ERROR_NO_ONLINE
            self.report += f'{ERROR_NO_ONLINE}\n'
            self.report += "Either it didn't acquire a token or it didn't connect to MQTT in time.\n"
            self.report += f"Please go over the Poll For Token section in:\n{GW_REGISTER_DOC}\n"
            self.report += f"and the MQTT details in:\n{GW_MQTT_DOC}\n"
            print("Gateway did not connect to MQTT within time limit")
            return False
        else:
            self.report += "Token acquisition and MQTT connection were done succesfully.\n"
            self.report += "Gateway is online.\n"
            print("Gateway connected to MQTT successfully, it is online")
            return True


class Refresh(GenericRegistrationStage):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        self.stage_tooltip = "Validate the gateway refresh-token step"
        super().__init__(name=type(self).__name__, **self.__dict__)

    def run(self):
        self.start_time = datetime.datetime.now()
        print("Waiting for the token to expire..")
        timeout = gw_online_ts + datetime.timedelta(minutes=TOKEN_EXPIRY_MINUTES)
        while datetime.datetime.now() < timeout:
            time.sleep(BUSY_WAIT_DELAY_SEC)

        print("Token expired, kicking gateway")
        self.kick_gw_from_mqtt()

        # Sleep here since it sometimes take time for the cloud to kick and change the gateway's online status
        time.sleep(CLOUD_DELAY_SEC)
        print("Waiting for the gateway to refresh its token and connect to MQTT..")
        timeout = datetime.datetime.now() + datetime.timedelta(minutes=STAGES_TIMEOUT_MINUTES)
        self.online = self.get_gateway_field(GetGwField.ONLINE)
        while datetime.datetime.now() < timeout and self.online is not True:
            time.sleep(BUSY_WAIT_DELAY_SEC)
            self.online = self.get_gateway_field(GetGwField.ONLINE)

        time.sleep(CLOUD_DELAY_SEC)
        self.validate_kong_logs('refresh')
        self.calc_run_duration()

    def generate_stage_report(self):
        self.add_report_header()
        if self.online is not True:
            self.error_summary = ERROR_NO_REFRESH
            self.report += f'{ERROR_NO_REFRESH}\n'
            self.report += "Either it didn't refresh its token or it didn't connect to MQTT in time.\n"
            self.report += f"Please go over the Refresh Token section in:\n{GW_REGISTER_DOC}\n"
            self.report += f"and the MQTT details in:\n{GW_MQTT_DOC}\n"
            print("Gateway did not reconnect MQTT (was the token refreshed?)")
            return False
        else:
            self.report += "Token refresh and MQTT reconnection were done succesfully.\n"
            self.report += "Gateway is online.\n"
            return True


def end_test(dut):
    print(f'Deleting {dut} from {REG_CERT_OWNER_ID} before exiting')
    time.sleep(CLOUD_DELAY_SEC)
    delete_gateway(dut)


def prepare_results(stage, phase_pass, skip_stage):
    stage.rc = TEST_SKIPPED if skip_stage else TEST_PASSED if phase_pass else TEST_FAILED


def run(test: cert_utils.WltTest):
    test = cert_common.test_prolog(test, flush_mqtt=False)
    if test.rc == TEST_FAILED:
        return cert_common.test_epilog(test, flush_mqtt=False)

    global api_key
    api_key = os.getenv(REGISTRATION_API_KEY_ENV_VAR)
    if api_key is None:
        raise Exception('Must include an apikey')

    STAGES = [Registry, Online, Refresh]
    phases = {p.name: stage(dut=test.dut.id_str) for p, stage in zip(test.params, STAGES)}

    for param in test.params:
        phase_run_print(f" - {param.name}")
        phase = phases[param.name]
        phase.prepare_stage()
        phase.run()
        test.rc = TEST_PASSED if phase.generate_stage_report() else TEST_FAILED
        test.set_phase_rc(param.name, test.rc)
        test.add_phase_reason(param.name, phase.error_summary)

        if test.rc == TEST_FAILED and test.exit_on_param_failure:
            print(f'\nPhase {param.name} failed: {phase.report}')
            break
        test.reset_result()  # reset result and continue to next param

    end_test(test.dut.id_str)

    return cert_common.test_epilog(test, flush_mqtt=False)
