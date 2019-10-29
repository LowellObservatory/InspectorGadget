import gc
import time
import machine
import binascii
import urequests

import onewire
import ds18x20


def postToInfluxDB(influxhost, influxport, dbname,
                   field, value,
                   tagN=None, tagV=None):
    """
    Just using the HTTP endpoint and the simple line protocol.

    Also letting the database time tag it for us.
    """
    url = "http://%s:%s/write?db=%s" % (influxhost, influxport, dbname)
    if (tagN is not None) and (tagV is not None):
        line = "%s,%s=%s value=%.02f" % (field, tagN, tagV, value)
    else:
        line = "%s value=%.02f" % (field, value)

    # There are few rails here so this could go ... poorly.
    try:
        urequests.post(url, data=line)
    except OSError as e:
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


def runmain(dsPin, dbhost, dbport, dbname, led=None):
    ow = onewire.OneWire(dsPin)
    ds = ds18x20.DS18X20(ow)

    while(True):
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
            postToInfluxDB(dbhost, dbport, dbname, "Temperature", thistemp,
                           tagN="DS18x20Sensor", tagV=sensor)

        gc.collect()
        if led is not None:
            led.off()

        print("Sleeping...")
        time.sleep(10)
