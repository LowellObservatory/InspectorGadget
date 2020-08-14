import gc
import time
import machine
import urequests
import micropython

import bme280 as bme
import utils_wifi as uwifi


def postToInfluxDB(influxhost, influxport, dbname,
                   metric, value, keyname='value',
                   tagN=None, tagV=None):
    """
    Just using the HTTP endpoint and the simple line protocol.

    Also letting the database time tag it for us.
    """
    url = "http://%s:%s/write?db=%s" % (influxhost, influxport, dbname)
    if (tagN is not None) and (tagV is not None):
        if isinstance(value, float):
            line = '%s,%s=%s %s=%.02f' % (metric, tagN, tagV, keyname, value)
        elif isinstance(value, int):
            line = '%s,%s=%s %s=%d' % (metric, tagN, tagV, keyname, value)
        elif isinstance(value, str):
            line = '%s,%s=%s %s="%s"' % (metric, tagN, tagV, keyname, value)
    else:
        if isinstance(value, float):
            line = '%s %s=%.02f' % (metric, keyname, value)
        if isinstance(value, int):
            line = '%s %s=%d' % (metric, keyname, value)
        elif isinstance(value, str):
            line = '%s %s="%s"' % (metric, keyname, value)

    # There are few rails here so this could go ... poorly.
    try:
        print("Posting to %s:%s %s.%s" % (influxhost, influxport, 
                                          dbname, metric))
        # print("%s=%s, %s=%s" % (tagN, tagV, keyname, value))
        print(line)
        response = urequests.post(url, data=line)
        print("Response:", response.status_code, response.text)
    except Exception as e:
        print(str(e))


def getBMEval(bmesensor):
    """
    """
    try:
        cvals = bmesensor.read_compensated_data()
        #           Deg. C            hPA          Percent (0-100)
        cvals = [cvals[0]/100., cvals[1]/256/100., cvals[2]/1024.]
    except Exception as e:
        print(str(e))
        cvals = None

    return cvals


def BMEmultivals(bmesensor, ntries=2, nreads=5, delay=0.1):
    """
    """
    vals = []
    valid = 0

    print("Getting BME values...")
    for i in range(0, nreads):
        ctries = 0
        cvals = None
        while (cvals is None) and (ctries < ntries):
            cvals = getBMEval(bmesensor)
            ctries += 1
            time.sleep(delay)

        if cvals is not None:
            # Need this for the final averaging
            valid += 1

            if i == 0:
                vals = cvals
            else:
                vals = [cvals[0]+vals[0], cvals[1]+vals[1], cvals[2]+vals[2]]

        time.sleep(delay)

    if (vals is not None) and (valid > 0):
        temperature = vals[0]/valid
        apparentpressure = vals[1]/valid
        humidity = vals[2]/valid
        print("BME values obtained!")
    else:
        temperature = -9999.
        apparentpressure = -9999.
        humidity = -9999.

    return temperature, apparentpressure, humidity


def main(i2c, bmeaddr, bmePwr, dbconfig, wlstuff, loops=10):
    dbhost = dbconfig['dbhost']
    dbport = dbconfig['dbport']
    dbname = dbconfig['dbname']

    wlan = wlstuff['wlan']
    conncheck = wlstuff['conncheck']
    wconfig = wlstuff['wconfig']
    knownaps = wlstuff['knownaps']

    loopCounter = 0
    while loopCounter < loops:
        print("")
        print("Starting loop %d of %d" % (loopCounter+1, loops))
        print("Checking WiFi status ...")
        # Attempt to connect to one of the strongest of knownaps
        wlan, conncheck, wconfig = uwifi.checkWifiStatus(knownaps,
                                                         wlan=wlan,
                                                         conn=conncheck,
                                                         conf=wconfig,
                                                         repl=False)

        # Store the connection information, if it's valid
        if wlan.isconnected() is True:
            curIP, curSN, curGW, curDNS = wlan.ifconfig()
            curAP = wlan.config('essid')
            curRSSI = wlan.status('rssi')
            print("Connected to %s at %s thru %s at %.0f dBm" % (curAP, curIP,
                                                                 curGW, 
                                                                 curRSSI))
            
            # Note: I'm skipping the subnet because I don't care
            print()

            postToInfluxDB(dbhost, dbport, dbname, "DCTMezz", curIP,
                           keyname="ipaddress", 
                           tagN="config", tagV="network")
            time.sleep(0.25)
            print()
            
            postToInfluxDB(dbhost, dbport, dbname, "DCTMezz", curGW,
                           keyname="gateway",
                           tagN="config", tagV="network")
            time.sleep(0.25)
            print()

            postToInfluxDB(dbhost, dbport, dbname, "DCTMezz", curDNS,
                           keyname="dns",
                           tagN="config", tagV="network")
            time.sleep(0.25)
            print()

            postToInfluxDB(dbhost, dbport, dbname, "DCTMezz", curAP,
                           keyname="accesspoint",
                           tagN="config", tagV="network")
            time.sleep(0.25)
            print()

            postToInfluxDB(dbhost, dbport, dbname, "DCTMezz", curRSSI,
                           keyname="rssi",
                           tagN="config", tagV="network")
            print()

            # Given the fact that this is a wifi sensor, we only should
            #   attempt a measurement if the wifi is good.  So keep this 
            #   all in the .isconnected() block!
            print("Turning BME on ...")
            bmePwr.on()
            time.sleep(1)

            try:
                sensor = bme.BME280(i2c=i2c, address=bmeaddr)
            except Exception as e:
                print(str(e))
                sensor = None

            if sensor is not None:
                # First read is probably junk so just toss it
                _ = getBMEval(sensor)
                time.sleep(1)

                # Do 5 reads, then average them
                temp, apre, humi = BMEmultivals(sensor, ntries=2, nreads=5)

                postToInfluxDB(dbhost, dbport, dbname, "DCTMezz", temp,
                               keyname="temperature",
                               tagN="sensor", tagV="bme280")
                time.sleep(0.25)
                print()

                postToInfluxDB(dbhost, dbport, dbname, "DCTMezz", apre,
                               keyname="apparentpressure",
                               tagN="sensor", tagV="bme280")
                time.sleep(0.25)
                print()

                postToInfluxDB(dbhost, dbport, dbname, "DCTMezz", humi,
                               keyname="relativehumidity",
                               tagN="sensor", tagV="bme280")

                print(temp, apre, humi)
            else:
                print("No BME sensor found or error establishing it!")
                print("Aborting...")

            print("Turning BME off ...")
            bmePwr.off()
            print()

        gc.collect()
        # Print some memory statistics so I can watch for problems
        micropython.mem_info()
        print("Sleeping ...")
        for sc in range(0, 60):
            if sc % 10 == 0 and sc != 0:
                 print("\n")
            else:
                print(".", end='')
            time.sleep(1)
        
        loopCounter += 1
