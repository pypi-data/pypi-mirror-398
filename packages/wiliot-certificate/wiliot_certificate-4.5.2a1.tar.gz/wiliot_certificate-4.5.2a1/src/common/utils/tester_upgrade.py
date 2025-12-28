import sys
import serial
import time
import argparse
import subprocess
import serial.tools.list_ports
import datetime
import os
import re

SEP = "#"*100
NRFUTIL_MAP = {"linux": "nrfutil-linux", "linux2": "nrfutil-linux", "darwin": "nrfutil-mac", "win32": ".\\nrfutil.exe"}
LATEST_BOOTLOADER_VERSION = "0x15"

def read_from_ble(ble_ser):
    ble_ser_bytes = ble_ser.readline()
    input = ble_ser_bytes.decode("utf-8", "ignore").strip()
    return input

class Command:
    def __init__(self, cmd, expected):
        self.cmd = cmd
        self.cmd_exec = b'\r\n!'+bytes(cmd, encoding='utf-8')+b'\r\n'
        self.expected = expected
    def exec_cmd(self, ble_ser):
        print("==>> !{}".format(self.cmd))
        ble_ser.write(self.cmd_exec)
        start_time = datetime.datetime.now()
        while (datetime.datetime.now() - start_time).seconds < 2:
            response = read_from_ble(ble_ser)
            if self.expected in response:
                return response
        return None

def run_cmd(cmd):
    print("Running: " + cmd)
    p = subprocess.Popen(cmd, shell=True, cwd=os.path.dirname(__file__))
    p.wait()
    if p.returncode:
        print(f"\nFailed running : {cmd}\n")
        sys.exit(-1)
    else:
        print(f"\nSuccess running : {cmd}\n")

def main():

    parser = argparse.ArgumentParser(description='Used to load gw image')
    parser.add_argument('--port', '-p', type=str, help='COM for the ble - meaning loading gw zip file from UART')
    args = parser.parse_args()

    if args.port:
        port = args.port
    elif not args.port:
        print("\nNo COM port given. Scanning for available ports:")
        for port, desc, hwid in sorted(serial.tools.list_ports.comports()):
            print("{}: {} [{}]".format(port, desc, hwid))
    if not port:
        print("\nNo available COM port found!")
        sys.exit(-1)

    # Connect to the BLE device and check the version and upgrade the firmware
    ble_ser = serial.Serial(port=port, baudrate=921600, timeout=0.1)
    ble_ser.flushInput()

    # Check for version response
    cmd = Command(cmd="version", expected="WILIOT_GW_BLE_CHIP_SW_VER")
    response = cmd.exec_cmd(ble_ser)
    if response == None:
        print("ERROR: failed to get firmware version!")
        sys.exit(-1)
    else:
        print(response)
    # Check for bootloader version and decide if update is needed
    bootloader_update = True
    cmd = Command(cmd="pce", expected="BootloaderVer")
    response = cmd.exec_cmd(ble_ser)
    if response:
        r = re.search("BootloaderVer=(.*?),", response)
        if r:
            bootloader_update = r.group(1) != LATEST_BOOTLOADER_VERSION
            print(f"Bootloader version: {r.group(1)}")
    print(f"Bootloader update: {bootloader_update}")

    # move to bootloader
    cmd = Command(cmd="move_to_bootloader", expected='')
    cmd.exec_cmd(ble_ser)

    # Upgrade the firmware
    ble_ser.close()
    time.sleep(2)
    if bootloader_update:
        zip_file = [f for f in os.listdir(os.path.dirname(__file__)) if "bl" in f and f.endswith('.zip')][0]
    else:
        zip_file = [f for f in os.listdir(os.path.dirname(__file__)) if "bl" not in f and f.endswith('.zip')][0]
    cmd = f'{NRFUTIL_MAP[sys.platform]} dfu serial --package "{zip_file}" -p {port} -fc 0 -b 115200 -t 10'
    run_cmd(cmd)


if __name__ == "__main__":
    main()