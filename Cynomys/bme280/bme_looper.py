import gc
import time
import machine
import urequests

import bme280 as bme


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


def getBMEval(bmesensor):
    """
    """
    try:
        cvals = bmesensor.read_compensated_data()
        #           Deg. C            hPA          Percent (0-100)
        cvals = [cvals[0]/100., cvals[1]/256/100., cvals[2]/1024.]
    except OSError as e:
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


def main(i2c, bmeaddr, dbhost, dbport, dbname):
    try:
        sensor = bme.BME280(i2c=i2c, address=bmeaddr)
    except OSError as e:
        print(str(e))
        sensor = None

    if sensor is not None:
        while(True):
            # First read is probably junk so just toss it
            _ = getBMEval(sensor)
            time.sleep(1)

            # Do 5 reads, then average them
            temp, apre, humi = BMEmultivals(sensor, ntries=2, nreads=5)

            postToInfluxDB(dbhost, dbport, dbname, "DCTMezz", temp,
                           tagN="EnvType", tagV="Temperature")
            time.sleep(0.25)
            postToInfluxDB(dbhost, dbport, dbname, "DCTMezz", apre,
                           tagN="EnvType", tagV="ApparentPressure")
            time.sleep(0.25)
            postToInfluxDB(dbhost, dbport, dbname, "DCTMezz", humi,
                           tagN="EnvType", tagV="RelativeHumidity")

            print(temp, apre, humi)

            time.sleep(10)
            gc.collect()
        else:
            print("No BME sensor found or error establishing it!")
            print("Aborting...")
