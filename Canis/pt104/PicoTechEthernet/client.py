"""."""

import socket
from PicoTechEthernet import PicoTechEthernetCM3


from datetime import datetime

from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

token = "TOKEN"
org = "ORG"
bucket = "BUCKET"

client = InfluxDBClient(url="http://127.0.0.1:8086", token=token)


# sudo nmap -sU -p 6554 192.168.1.0/24
CM3 = PicoTechEthernetCM3(ip='192.168.1.200', port=6554)

while True:  # Loop forever
    try:
        print(CM3.connect())
        print(CM3.lock())
        CM3.filter(50)
        # print(CM3.EEPROM())
        CM3.set('1w', b'Converting\x00')  # channel setup ??

        for load in next(CM3):
            # print(load)

            # Submit information to a time series database, InfluxDB
            # eg  load = '0, 0.21761050447821617'
            # AKA channel 0, 0.21761050447821617 mV

            write_api = client.write_api(write_options=SYNCHRONOUS)

            data = f"Channel{load[0]} current={load[1]}"
            print(data)
            write_api.write(bucket, org, data)

    except socket.timeout:
        print('Connection timeout to PicoTech device')

