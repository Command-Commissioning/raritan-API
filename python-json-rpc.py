#!/usr/bin/python3
# SPDX-License-Identifier: BSD-3-Clause
#
# Copyright 2015 Raritan Inc. All rights reserved.

import sys, time, csv, os

sys.path.append("pdu-python-api")
from raritan.rpc import Agent, pdumodel, firmware

ip = "10.0.42.2"
user = "admin"
pw = "raritan"

try:
    ip = sys.argv[1]
    user = sys.argv[2]
    pw = sys.argv[3]
except IndexError:
    pass # use defaults

agent = Agent("https", ip, user, pw, disable_certificate_verification=True)
pdu = pdumodel.Pdu("/model/pdu/0", agent)
firmware_proxy = firmware.Firmware("/firmware", agent)

inlets = pdu.getInlets()
ocps = pdu.getOverCurrentProtectors()
outlets = pdu.getOutlets()

print ("PDU: %s" % (ip))
print ("Firmware version: %s" % (firmware_proxy.getVersion()))
print ("Number of inlets: %d" % (len(inlets)))
print ("Number of over current protectors: %d" % (len(ocps)))
print ("Number of outlets: %d" % (len(outlets)))

outlet = outlets[0]
outlet_sensors = outlet.getSensors()
outlet_metadata = outlet.getMetaData()
outlet_settings = outlet.getSettings()

# Prepare CSV logging
csv_filename = 'power_log.csv'
write_header = not os.path.exists(csv_filename)

def get_sensor_value(sensor):
    if sensor:
        reading = sensor.getReading()
        if reading.valid:
            return reading.value
    return None

print ("Outlet %s:" % (format(outlet_metadata.label)))
print ("  Name: %s" % (outlet_settings.name if outlet_settings.name != "" else "(none)"))
print ("  Switchable: %s" % ("yes" if outlet_metadata.isSwitchable else "no"))


# Get sensor values
voltage = get_sensor_value(outlet_sensors.voltage)
current = get_sensor_value(outlet_sensors.current)
active_power = get_sensor_value(getattr(outlet_sensors, 'activePower', None))
apparent_power = get_sensor_value(getattr(outlet_sensors, 'apparentPower', None))

print ("  Voltage: %s" % (f"{voltage} V" if voltage is not None else "n/a"))
print ("  Current: %s" % (f"{current} A" if current is not None else "n/a"))
print ("  Active Power: %s" % (f"{active_power} W" if active_power is not None else "n/a"))
print ("  Apparent Power: %s" % (f"{apparent_power} VA" if apparent_power is not None else "n/a"))

# Log to CSV
with open(csv_filename, 'a', newline='') as csvfile:
    writer = csv.writer(csvfile)
    if write_header:
        writer.writerow(['timestamp', 'voltage', 'current', 'active_power', 'apparent_power'])
    writer.writerow([
        time.strftime('%Y-%m-%d %H:%M:%S'),
        voltage if voltage is not None else '',
        current if current is not None else '',
        active_power if active_power is not None else '',
        apparent_power if apparent_power is not None else ''
    ])

if outlet_metadata.isSwitchable:
    outlet_state_sensor = outlet_sensors.outletState
    outlet_state = outlet_state_sensor.getState()
    if outlet_state.available:
        print ("  Status :%s" % ("on" if outlet_state.value == outlet_state_sensor.OnOffState.ON.val else "off"))
    print ("  Turning outlet off...")
    outlet.setPowerState(outlet.PowerState.PS_OFF)
    print ("  Sleeping 4 seconds...")
    time.sleep(4)
    print ("  Turning outlet on...")
    outlet.setPowerState(outlet.PowerState.PS_ON)
    outlet_state = outlet_state_sensor.getState()
    if outlet_state.available:
        print ("  Status :%s" % ("on" if outlet_state.value == outlet_state_sensor.OnOffState.ON.val else "off"))