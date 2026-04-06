import time
from datetime import datetime as dt, timezone
import csv
import os
from raritan.rpc import Agent, pdumodel
from influxdb_client import InfluxDBClient, Point, WritePrecision

# Configuration
PDU_IP = "10.0.42.2"
PDU_USER = "admin"
PDU_PW = "raritan"
INFLUX_URL = "https://db.command-cx.com:8086"
INFLUX_TOKEN = "tnQAjQR478oG7hmg7N-hvE9JyoTkG7ie70OT2psXPozeYw6HmhV___IGxIZrCoR5kOaAuma21ehNTVGKNNJbbA=="
INFLUX_ORG = "CommandCommissioning"
INFLUX_BUCKET = "your-bucket"
POLL_INTERVAL = 10  # seconds
PDU_Name = "PDU-1"
CSV_FILENAME = f"{PDU_Name}.csv"

# Helper to get sensor value
def get_sensor_value(sensor):
    if sensor:
        reading = sensor.getReading()
        if reading.valid:
            return reading.value
    return None

def poll_and_log():
    agent = Agent("https", PDU_IP, PDU_USER, PDU_PW, disable_certificate_verification=True)
    pdu = pdumodel.Pdu("/model/pdu/0", agent)
    outlet = pdu.getOutlets()[0]
    outlet_sensors = outlet.getSensors()

    write_header = not os.path.exists(CSV_FILENAME)
    with open(CSV_FILENAME, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        if write_header:
            writer.writerow(['timestamp', 'voltage', 'current', 'active_power', 'apparent_power'])

        with InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG) as influx_client:
            write_api = influx_client.write_api(write_options=None)
            while True:
                voltage = get_sensor_value(outlet_sensors.voltage)
                current = get_sensor_value(outlet_sensors.current)
                active_power = get_sensor_value(getattr(outlet_sensors, 'activePower', None))
                apparent_power = get_sensor_value(getattr(outlet_sensors, 'apparentPower', None))
                timestamp = time.strftime('%Y-%m-%d %H:%M:%S')

                # Write to CSV
                writer.writerow([
                    timestamp,
                    voltage if voltage is not None else '',
                    current if current is not None else '',
                    active_power if active_power is not None else '',
                    apparent_power if apparent_power is not None else ''
                ])
                csvfile.flush()

                # Write to InfluxDB
                point = Point(PDU_Name) \
                    .tag("outlet", "0") \
                    .field("voltage", voltage if voltage is not None else 0) \
                    .field("current", current if current is not None else 0) \
                    .field("active_power", active_power if active_power is not None else 0) \
                    .field("apparent_power", apparent_power if apparent_power is not None else 0) \
                    .time(dt.now(timezone.utc), WritePrecision.S)
                write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=point)
                write_api.close()

                print(f"Logged at {timestamp}")
                time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    poll_and_log()
