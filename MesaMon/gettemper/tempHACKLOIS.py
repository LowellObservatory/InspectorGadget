# -*- coding: utf-8 -*-
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
#  Created on 8 Sep 2019
#
#  @author: rhamilton

"""One line description of module.

Further description.
"""

from __future__ import division, print_function, absolute_import

import os
import datetime as dt

from ligmos import utils


def parserLOlogs(hed, msg, db=None, badFWHM=100.):
    """
    '22:26:55 Level_4:CCD Temp:-110.06 18.54 Setpoints:-109.95 0.00 '
    '22:26:55 Level_4:Telescope threads have been reactivated'
    """
    # ts = hed['timestamp']
    topic = os.path.basename(hed['destination'])

    # print(ts, msg)
    # Some time shenanigans; the LOIS log doesn't include date but
    #   we can assume it's referencing UT time on the same day.
    #   I suppose that there could be some ambiguity right at UT midnight
    #   ... but oh well.
    now = dt.datetime.utcnow()
    ltime = msg[0:8].split(":")
    # Bail early since this indicates it's not really a log line but
    #   some other type of message (like a LOIS startup or something)
    if len(ltime) != 3:
        print("Unknown log line!")
        print(msg)
        return

    now = now.replace(hour=int(ltime[0]), minute=int(ltime[1]),
                      second=int(ltime[2]), microsecond=0)

    # lts = now.strftime("%Y-%m-%dT%H:%M:%S.%f")
    # Get just the log level
    loglevel = msg.split(" ")[1].split(":")[0]
    # Now get the message, putting back together anything split by ":"
    #   this is so we can operate fully on the full message string
    logmsg = " ".join(msg.split(":")[3:]).strip()

    # print("%s from %s:" % (lts, topic))

    # Set the stage for our eventual influxdb packet
    meas = ['InstrumentTelemetry']
    tags = {'name': topic.split(".")[1]}

    if loglevel == "Level_2":
        fields = None
        if logmsg.startswith("SendAnalysis"):
            apts = logmsg.split()
            if apts[3].startswith("PHOT"):
                fnum, subfno = apts[3].split("(")[1].split(")")[0].split(",")
                centx = float(apts[4])
                centy = float(apts[5])
                fwhm = float(apts[6])
                instmag = float(apts[7])
                instmagerr = float(apts[8])
                skymean = float(apts[9])

                tags.update({"frame": fnum})
                tags.update({"subframenum": subfno})

                fields = {"centx": centx}
                fields.update({"centy": centy})
                fields.update({"fwhm": fwhm})
                fields.update({"instmag": instmag})
                fields.update({"instmagerr": instmagerr})
                fields.update({"skymean": skymean})

                # Final check for goodness.
                #   NOTE: The badFWHM value is hardcoded into LOIS when the
                #         centroid or profile fit fails. So we'll skip those.
                if fwhm == badFWHM:
                    # Nuke the entire site from orbit...
                    fields = None
                    tags = None
    elif loglevel in ["Level_5", "Level_4"]:
        #
        # THIS IS A TEMPORARY HACK UNTIL MR FREEZE ARRIVES
        #               EVERYBODY CHILL
        #
        fields = parse_deboned_LOISTemps(logmsg)
    else:
        # Need this otherwise we'll get an exception error for all
        #   unparsed log lines! fields won't be defined right below here
        #   and it'll trigger a NameError for 'fields'
        fields = None

    # Make the InfluxDB packet and store it, skipping if fields is None
    if fields is not None:
        # Note: passing ts=None lets python Influx do the timestamp for you
        packet = utils.packetizer.makeInfluxPacket(meas=meas,
                                                   ts=None,
                                                   tags=tags,
                                                   fields=fields)

        # print(packet)

        # Actually commit the packet. singleCommit opens it,
        #   writes the packet, and then optionally closes it.
        if db is not None:
            db.singleCommit(packet, table=db.tablename, close=True)


def parse_deboned_LOISTemps(logmsg):
    """
    A stripped down version of the original living over in Mr. Freeze,
    but since he's not awake yet I need this here as a shim.
    """
    fields = {}
    if logmsg.startswith("CCD sensor adus"):
        # print("Parsing: %s" % (logmsg))
        # CCD sensor adus temp1 2248 temp2 3329 set1 2249 heat1 2016'
        adutemp1 = int(logmsg.split(" ")[4])
        adutemp2 = int(logmsg.split(" ")[6])
        aduset1 = int(logmsg.split(" ")[8])
        aduheat1 = int(logmsg.split(" ")[10])

        fields = {"aduT1": adutemp1}
        fields.update({"aduT2": adutemp2})
        fields.update({"aduT2": adutemp2})
        fields.update({"aduS1": aduset1})
        fields.update({"aduH1": aduheat1})

        # print(adutemp1, adutemp2, aduset1, aduheat1)
    elif logmsg.startswith("CCD Heater"):
        # NOTE! This one will have had a ":" removed by the
        #   logmsg creation line above, so you can just split normally
        # print("Parsing: %s" % (logmsg))
        # CCD Heater Values:1.21 0.00
        heat1 = float(logmsg.split(" ")[3])
        heat2 = float(logmsg.split(" ")[4])

        fields = {"H1": heat1}
        fields.update({"H2": heat2})

        # print(heat1, heat2)
    elif logmsg.startswith("CCD Temp"):
        # Same as "CCD Heater" in that ":" have been removed by this point
        # print("Parsing: %s" % (logmsg))
        # CCD Temp -110.06 18.54 Setpoints -109.95 0.00 '
        temp1 = float(logmsg.split(" ")[2])
        temp2 = float(logmsg.split(" ")[3])
        set1 = float(logmsg.split(" ")[5])
        set2 = float(logmsg.split(" ")[6])

        fields = {"T1": temp1}
        fields.update({"T2": temp2})
        fields.update({"S1": set1})
        fields.update({"S2": set2})
        fields.update({"T1S1delta": temp1-set1})

        # print(temp1, temp2, set1, set2)
    else:
        fields = {}
        # print(loglevel, logmsg)

    return fields

