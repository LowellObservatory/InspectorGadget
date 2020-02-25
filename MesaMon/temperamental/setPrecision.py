# -*- coding: utf-8 -*-
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
#  Created on ??? (I forget)
#
#  @author: rhamilton

import time

from w1thermsensor import W1ThermSensor

import database
import packetizer


def setAllSensors(precision=9):
    for sensor in W1ThermSensor.get_available_sensors():
        sty = sensor.type_name
        sid = sensor.id
        stp = sensor.get_temperature()
        print("Setting precision of sensor %s (%s) to %d" %
              (sid, sty, precision))
        sensor.set_precision(precision, persist=True)


if __name__ == "__main__":
    """
    Be careful with this!  Don't do it in a loop, because the EEPROM
    that stores the desired precision has a limited amount of writes.

    This *probably* needs root permissions to succeed since it fiddles
    with stuff in /sys/bus/w1/...
    """
    # The precision can be set from 9 to 12 bits
    precision = 12
    setAllSensors(precision=precision)

