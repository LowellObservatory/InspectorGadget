import gc
import time
import machine
import micropython

import bme280 as bme
import utils as utils
import utils_wifi as uwifi


def doBME(bmePwr, dbconfig):
    """
    """
    print("Turning BME on ...")
    bmePwr.on()
    time.sleep(1)

    try:
        sensor = bme.BME280(i2c=i2c, address=bmeaddr)
    except Exception as e:
        print(str(e))
        sensor = None

    if sensor is not None:
        # Toss the first read just in case it's junk/not settled
        _ = getBMEval(sensor)
        time.sleep(1)

        # Do 5 reads, which are then averaged and returned
        temp, apre, humi = BMEmultivals(sensor, ntries=2, nreads=5)

        sV = utils.postToInfluxDB(dbconfig, temp, keyname="temperature",
                                  tagN="sensor", tagV="bme280")
        time.sleep(0.25)
        print()

        sV = utils.postToInfluxDB(dbconfig, apre, keyname="apparentpressure",
                                  tagN="sensor", tagV="bme280")
        time.sleep(0.25)
        print()

        sV = utils.postToInfluxDB(dbconfig, humi, keyname="relativehumidity",
                                  tagN="sensor", tagV="bme280")

        print(temp, apre, humi)
    else:
        print("No BME sensor found or error establishing it!")
        print("Aborting...")

    print("Turning BME off ...")
    bmePwr.off()
    print()


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
        # Actually average the values we found
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

        # Try to store the connection information
        sV = utils.postNetConfig(wlan, dbconfig)

        # We only should attempt a measurement if the wifi is good, so 
        #   keep this all in the conditional!
        if wlan.isconnected() is True:
            sV = utils.postNetConfig(wlan, dbconfig)

            # If the network config dropped out suddenly, sV will be false.
            #   That lets us skip the rest so we can get a WiFi status check 
            #   sooner rather than later
            if sV is True:
                startBMELoop(bmePwr, dbconfig)

        gc.collect()
        # Print some memory statistics so I can watch for problems
        micropython.mem_info()
        print("Sleeping ...\n")
        for sc in range(0, 60):
            if sc % 10 == 0 and sc != 0:
                print("\n")
            else:
                print(".", end='')
            time.sleep(1)

        loopCounter += 1
