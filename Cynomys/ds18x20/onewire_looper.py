import gc
import time
import machine
import binascii
import urequests
import micropython

import onewire
import ds18x20

import utils_wifi as uwifi


def postToInfluxDB(host, port, dbname,
                   metric, value, keyname='value',
                   tagN=None, tagV=None,
                   dbuser=None, dbpass=None):
    """
    Just using the HTTP endpoint and the simple line protocol.

    Also letting the database time tag it for us.
    """
    if dbuser is not None and dbpass is not None:
        url = "http://%s:%s/write?u=%s&p=%s&db=%s" % (host, port,
                                                      dbuser, dbpass, dbname)
    else:
        url = "http://%s:%s/write?db=%s" % (host, port, dbname)

    print("Using HTTP URL:")
    print(url)

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
        print("Posting to %s:%s %s.%s" % (host, port,
                                          dbname, metric))
        # print("%s=%s, %s=%s" % (tagN, tagV, keyname, value))
        print(line)
        response = urequests.post(url, data=line)
        print("Response:", response.status_code, response.text)
    except Exception as e:
        print(str(e))


def getDS18x20val(dssens):
    """
    """
    # Get the list of DS18x20 sensors on the onewire bus
    print("Scanning for devices...")
    roms = dssens.scan()

    # Initiate the temperature reading. You must sleep for 750 ms afterwards!
    dssens.convert_temp()
    time.sleep_ms(750)
    print("convert_temp finished")

    # Read each sensor we find on the bus and store their values
    retvals = {}
    for rom in roms:
        temp = dssens.read_temp(rom)

        romStr = binascii.hexlify(rom).decode('ascii')
        print(time.time(), romStr, temp)
        retvals.update({romStr: temp})

    return retvals


def DS18x20multiread(dssens, nreads=5, delay=0.1):
    """
    """
    allvals = {}
    avgvals = {}

    # Get the list of DS18x20 sensors on the onewire bus
    print("Scanning for devices...")
    roms = dssens.scan()

    # Read each sensor we find on the bus and store their values

    retvals = {}
    for rom in roms:
        for i in range(0, nreads):
            # Initiate the temperature reading. You must sleep for 750ms after
            dssens.convert_temp()
            time.sleep_ms(750)
            print("convert_temp finished")
            temp = dssens.read_temp(rom)

            romStr = binascii.hexlify(rom).decode('ascii')
            print(time.time(), romStr, temp)

            try:
                storedVals = allvals[romStr]
                storedVals.append(temp)
            except KeyError:
                # This means we haven't stored anything yet, so store it
                storedVals = [temp]

            allvals.update({romStr: storedVals})

        time.sleep(delay)

    # Finish up the averages
    for sensorKey in allvals:
        nreadings = len(allvals[sensorKey])
        avgvalue = sum(allvals[sensorKey])/nreadings
        avgvals.update({sensorKey: avgvalue})

    return avgvals


def main(dsPin, dbconfig, wlconfig, loops=10, led=None):
    # Unpack some things for clarity
    dbhost = dbconfig['dbhost']
    dbport = dbconfig['dbport']
    dbname = dbconfig['dbname']
    dbuser = dbconfig['dbuser']
    dbpass = dbconfig['dbpass']

    wlan = wlconfig['wlan']
    conncheck = wlconfig['conncheck']
    wconfig = wlconfig['wconfig']
    knownaps = wlconfig['knownaps']

    ow = onewire.OneWire(dsPin)
    ds = ds18x20.DS18X20(ow)

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

            postToInfluxDB(dbhost, dbport, dbname, "DyerDome", curIP,
                           keyname="ipaddress",
                           tagN="config", tagV="network",
                           dbuser=dbuser, dbpass=dbpass)
            time.sleep(0.25)
            print()

            postToInfluxDB(dbhost, dbport, dbname, "DyerDome", curGW,
                           keyname="gateway",
                           tagN="config", tagV="network",
                           dbuser=dbuser, dbpass=dbpass)
            time.sleep(0.25)
            print()

            postToInfluxDB(dbhost, dbport, dbname, "DyerDome", curDNS,
                           keyname="dns",
                           tagN="config", tagV="network",
                           dbuser=dbuser, dbpass=dbpass)
            time.sleep(0.25)
            print()

            postToInfluxDB(dbhost, dbport, dbname, "DyerDome", curAP,
                           keyname="accesspoint",
                           tagN="config", tagV="network",
                           dbuser=dbuser, dbpass=dbpass)
            time.sleep(0.25)
            print()

            postToInfluxDB(dbhost, dbport, dbname, "DyerDome", curRSSI,
                           keyname="rssi",
                           tagN="config", tagV="network",
                           dbuser=dbuser, dbpass=dbpass)
            print()

            # Given the fact that this is a wifi sensor, we only should
            #   attempt a measurement if the wifi is good.  So keep this
            #   all in the .isconnected() block!

            if led is not None:
                led.on()

            # First read is probably junk so just toss it
            print("Grabbing initial/throwaway value...")
            _ = getDS18x20val(ds)
            time.sleep(1)

            # Do 5 reads, then average them
            avgs = DS18x20multiread(ds, nreads=5, delay=1.0)
            print("Grabbed all values and averaged them!")

            for sensor in avgs:
                thistemp = avgs[sensor]
                print("Posting %s to influxdb..." % (sensor))
                postToInfluxDB(dbhost, dbport, dbname, "DyerDome", thistemp,
                               keyname="Temperature",
                               tagN="DS18x20Sensor", tagV=sensor,
                               dbuser=dbuser, dbpass=dbpass)

            if led is not None:
                led.off()

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
