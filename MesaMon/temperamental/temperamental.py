import time

from w1thermsensor import W1ThermSensor

import database
import packetizer


def readAllSensors():
    fields = {}
    for sensor in W1ThermSensor.get_available_sensors():
        sty = sensor.type_name
        sid = sensor.id
        stp = sensor.get_temperature()
        print("Sensor %s (%s) has temperature %.2f" % (sid, sty, stp))
        fields.update({sid: stp})

    pkt = packetizer.makeInfluxPacket(meas=['temperatures'], fields=fields)
    print(pkt)

    return pkt


if __name__ == "__main__":
    dbhost = 'localhost'
    dbport = 8086
    dbname = 'mesa42'

    idb = database.influxobj(tablename=dbname, 
                             host=dbhost, port=dbport,
                             connect=True)

    while True:
        pkt = readAllSensors()
        idb.singleCommit(pkt, table=dbname)

        print("Sleeping ...")
        time.sleep(10)

