# -*- coding: utf-8 -*-
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
#  Created on ??? (I forget)
#
#  @author: rhamilton

from __future__ import division, print_function, absolute_import

import time

from w1thermsensor import W1ThermSensor

from ligmos.utils import database
from ligmos.utils import packetizer


def readAllSensors():
    fields = {}
    for sensor in W1ThermSensor.get_available_sensors():
        sty = sensor.type_name
        sid = sensor.id
        stp = sensor.get_temperature()
        print("Sensor %s (%s) has temperature %.2f" % (sid, sty, stp))
        fields.update({sid: stp})

    pkt = packetizer.makeInfluxPacket(meas=['temperatures'],
                                      fields=fields)
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

