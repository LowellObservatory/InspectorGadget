# -*- coding: utf-8 -*-
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
#  Created on 24 May 2018
#
#  @author: rhamilton

"""One line description of module.
Further description.
"""

from __future__ import division, print_function, absolute_import

import time
import statistics

import serial

from ligmos.utils.database import influxobj
from ligmos.utils.packetizer import makeInfluxPacket


def encoder(msg):
    """
    """
    if isinstance(msg, str):
        msg = msg.encode("ascii")
    return msg


def read_all(port, chunk_size=1024):
    """Read all characters on the serial port and return them."""
    # https://stackoverflow.com/a/47614497
    if not port.timeout:
        raise TypeError('Port needs to have a timeout set!')
    read_buffer = b''
    while True:
        # Read in chunks. Each chunk will wait as long as specified by
        # timeout. Increase chunk_size to fail quicker
        byte_chunk = port.read(size=chunk_size)
        read_buffer += byte_chunk
        if not len(byte_chunk) == chunk_size:
            break
    return read_buffer


def serWriter(ser, msg):
    """
    """
    try:
        nwritten = ser.write(msg)
        if nwritten != len(msg):
            print("Wrote less bytes than in the message?")
        else:
            print("Good write: %s" % (str(msg)))
    except Exception as err:
        print(str(err))


def serComm(host, port, cmds):
    """
    """
    hosturl = "socket://%s:%s" % (host, port)
    byteReply = None

    with serial.serial_for_url(hosturl, write_timeout=2., timeout=2.) as ser:
        print("Connection openeed")
        if isinstance(cmds, list):
            for each in cmds:
                msg = encoder(each)
                serWriter(ser, msg)
                byteReply = read_all(ser)
                print(str(byteReply))
        elif isinstance(cmds, str):
            msg = encoder(cmds)
            serWriter(ser, msg)
            byteReply = read_all(ser)
            print(str(byteReply))

    return byteReply


def hp34401a_query(ip, port, samples=7):
    msgsSetup = ["SYST:REM\n", "disp on\n", "trig:sour bus\n"]
    samps = "sample:count %d\n" % (int(samples))
    msgsSetup.append(samps)

    msgsTrigger = ["init\n", "*trg\n"]
    msgsRead = ["fetch?\n"]
    msgsCleanup = ["disp off\n", "*cls\n"]

    # Store things in a dict for easier access
    msgs = {"setup": msgsSetup,
            "trigger": msgsTrigger,
            "read": msgsRead,
            "cleanup": msgsCleanup}

    # We need to do this in a sequence, and wait for the *trg to finish
    #   before we call fetch as well.  So do that.
    # Could have just looped over keys() if I made msgs an OrderedDict
    #   but whatever this works too
    seqKeys = ['setup', 'trigger', 'read', 'cleanup']
    for seq in seqKeys:
        mset = msgs[seq]
        retVal = serComm(ip, port, mset)
        if seq == 'trigger':
            time.sleep(int(samples*1.5))

        if seq == "read":
            try:
                decoded = retVal.decode("ascii")
            except Exception as err:
                print(str(err))
                decoded = None

            if decoded is not None:
                vals = decoded.strip().split(",")
                try:
                    vals = [float(each) for each in vals]
                except Exception as err:
                    print(str(err))
                    vals = None

                if vals is not None:
                    # Aggregate the data into a medianed value for storage
                    medVal = statistics.median(vals)
                    print("Median Value: %f" % (medVal))
                else:
                    medVal = None

    return medVal


if __name__ == "__main__":
    ip = "127.0.0.1"
    port = 5300
    loopTimer = 30.

    dbhost = "127.0.0.1"
    dbport = 8086
    dbuser = None
    dbpass = None
    dbtable = 'hp34401a'

    idb = influxobj(host=dbhost, port=dbport, tablename=dbtable,
                    user=dbuser, pw=dbpass, connect=True)

    # This is a 4th order polynomial fit to the specific RTDs I'm measuring
    #   based on the provided datasheet.  I forget what RTD it was,
    #   but probably one from Omega.
    fps = [3.05E-08, -1.34E-05, 3.19E-03, 2.20E+00, -2.42E+02]

    while True:
        print("Querying multimeter ...")
        medVal = hp34401a_query(ip, port)
        if medVal is not None:
            # If we got a value, store it
            tempConverted = fps[0]*medVal**4 + fps[1]*medVal**3 + \
                            fps[2]*medVal**2 + fps[3]*medVal + fps[4]
            fields = {"resistance": medVal,
                      "temperature": tempConverted}
            pkt = makeInfluxPacket(meas=['hp34401a'], fields=fields)
            idb.singleCommit(pkt, table=dbtable, debug=True)

            print(pkt)

        print("Sleeping for %d seconds ..." % (loopTimer))
        time.sleep(loopTimer)
