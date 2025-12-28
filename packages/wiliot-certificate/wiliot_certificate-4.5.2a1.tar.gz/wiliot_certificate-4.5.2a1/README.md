# wiliot-certificate

<!-- Description -->
wiliot-certificate is a Python library that provides tools for testing and certifying boards for compatibility with Wiliot’s ecosystem.
This python package includes the following tools:
 - Certification Wizard (`wlt-cert`)
 - Certificate CLI (`wlt-cert-cli`)
 - Tester Upgrade (`wlt-cert-tester-upgrade`)
 - Registration Certificate Test (`wlt-cert-reg`)

# Versioning: 
wiliot-certificate versions 4.5.x are compatible with firmware version >=4.4.0 (API VERSION: 12)

## Installing wiliot-certificate
````commandline
pip install wiliot-certificate
````

## Using wiliot-certificate
### Certification
````commandline
wlt-cert
````
This tool is the default to test and certify your device.
It runs a setup wizard that walks you through the initialization steps before running the tests.
You'll need a [validation schema](https://community.wiliot.com/customers/s/article/Validation-Schema) and a [tester device](https://community.wiliot.com/customers/s/article/Wiliot-Certification).
Once set up it opens a terminal and tests your device.



### Certificate CLI
````commandline
wlt-cert-cli -h
````
CLI version of the certificate. Use -h for details on the different arguments.


### Tester Upgrade
````commandline
wlt-cert-tester-upgrade
````
Upgrades the firmware of the tester device to the version required for certification.


### Registration Certificate
````commandline
wlt-cert-reg
````
Certify the gateway registration process to Wiliot platform.
The gateway must use Wiliot production MQTT broker, and mustn't be registered to any account on Wiliot platform.
Use -h for details on the arguments (see [Registration](https://community.wiliot.com/customers/s/article/Wiliot-Certification) for more info).


## The following capabilities are not tested in this version
##### Cloud Connectivity & Misc
 - Board type registered within the Board Type Management system
 - Bridge OTA progress reporting
##### Module Energy 2400
  - Functionality of energy pattern, output power and duty cycle
##### Module Energy SUB1G
  - Functionality of energy pattern and duty cycle 
##### Module Datapath 
  - RSSI edge cases: -127 and 0 
  - Functionality of transmission pattern, output power
##### Calibration 
  - Functionality of output power and interval calibration 
  - Functionality of calibration transmission patterns for the configuration STANDARD & EU & DISABLE
