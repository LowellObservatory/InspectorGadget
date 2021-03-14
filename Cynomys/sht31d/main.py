import gc
import time
import micropython
from machine import WDT, Pin, I2C, reset

import adafruit_sht31d_micropy as asht

import utils as utils
import utils_wifi as uwifi


def go(deviceid, config, wlconfig, loops=25):
    """
    Every single board deployment must have this function accepting these
    exact arguments.  Only way to ensure a non-maddening structure!
    """
    disableLEDs = True

    # Set up our last ditch hang preventer
    # wdt = WDT()

    # Unpack the things
    knownaps = config['knownaps']
    dbconfig = config['dbconfig']
    wlan = wlconfig['wlan']
    wconfig = wlconfig['wconfig']

    # Set up our WiFi indicator
    ledIndicator = utils.shinyThing(pin=2, inverted=True, startBlink=False)
    if disableLEDs is False:
        if wlan.isconnected() is True:
            ledIndicator.off()
        else:
            utils.blinken(ledIndicator, 0.25, 10)
            ledIndicator.on()

    # Set up the SHT31D reset switch, the activity indicator, and the i2c bus
    shtaddr = 0x44
    shtrst = Pin(12, Pin.OUT)
    shtIndicator = utils.shinyThing(pin=13, inverted=False, startBlink=False)
    i2c = I2C(scl=Pin(5), sda=Pin(4), freq=100000)

    loopCounter = 0
    while loopCounter < loops:
        print("")
        # wdt.feed()
        print("\nFed the dog")
        print("Starting loop %d of %d" % (loopCounter+1, loops))
        print("Checking WiFi status ...")
        # Attempt to connect to one of the strongest of knownaps
        wlan, wconfig = uwifi.checkWifiStatus(knownaps,
                                              wlan=wlan,
                                              conf=wconfig,
                                              repl=False)

        # Try to store the connection information
        sV = utils.postNetConfig(wlan, dbconfig, deviceid)
        # wdt.feed()

        # We only should attempt a measurement if the wifi is good, so
        #   keep this all in the conditional!
        if wlan.isconnected() is True:
            ledIndicator.off()
            # If the network config dropped out suddenly, sV will be false.
            #   That lets us skip the rest so we can get a WiFi status check
            #   sooner rather than later
            if sV is True:
                if disableLEDs is False:
                    shtIndicator.on()
                    
                print("Turning sensor on ...")
                shtrst.on()
                doSHT(i2c, shtaddr, dbconfig, deviceid)
                print("Turning sensor off ...")
                shtrst.off()
                shtIndicator.off()
        else:
            if disableLEDs is False:
                ledIndicator.on()

        # wdt.feed()
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
            # wdt.feed()

        loopCounter += 1

    # Since we're at the end of our rope here, drop the hammer and reset
    print("Resetting in 5 seconds ...")
    time.sleep(5)
    reset()


def doSHT(i2c, addr, dbconfig, deviceid):
    """
    """
    dbconfig.update({"dbtabl": deviceid})

    try:
        print("Creating SHT31D object...")
        sensor = asht.SHT31D(i2c)
        sensor.heater = False
        sensor._reset()
        time.sleep(1)
    except Exception as e:
        print(str(e))
        sensor = None

    if sensor is not None:
        sensor.mode = "Periodic"
        time.sleep(3)
        temp, humi = getSHTval(sensor)

        # Get many values, average them, and return the result
        # temp, humi = SHTmultivals(sensor, ntries=2, nreads=3)

        sV = utils.postToInfluxDB(dbconfig, temp, keyname="temperature",
                                  tagN="DeviceType", tagV="SHT31D")
        time.sleep(0.25)
        print()

        sV = utils.postToInfluxDB(dbconfig, humi, keyname="relativehumidity",
                                  tagN="DeviceType", tagV="SHT31D")

        # print(temp, humi)
    else:
        print("No sensor found or error establishing it!")
        print("Aborting...")


def getSHTval(sensor, mode="Single"):
    """
    """
    # If mode is Periodic, these values for humidity and temperature are
    #   filled to the returned list if the SHT buffer isn't full yet
    tempBad = 130.0
    humiBad = 100.01831417975366

    try:
        temp = sensor.temperature
        humi = sensor.relative_humidity

        if isinstance(temp, list):
            # This means our mode was "Periodic" and there are multiple values
            #   so we look for the default/fill values defined above.
            # Only do this if the two lists are equal length, if they're not 
            #   that implies something went wrong
            if len(temp) == len(humi):
                nGoodTemp = 0
                nGoodHumi = 0
                tempAvg = None
                humiAvg = None
                for i, each in enumerate(temp):
                    if temp[i] != tempBad:
                        nGoodTemp += 1
                        # This means we haven't had any good values yet
                        #   so start counting from here
                        if tempAvg == None:
                            tempAvg = temp[i]
                        else:
                            tempAvg += temp[i]
                    if humi[i] != humiBad:
                        nGoodHumi += 1
                        # This means we haven't had any good values yet
                        #   so start counting from here
                        if humiAvg == None:
                            humiAvg = humi[i]
                        else:
                            humiAvg += humi[i]

                if nGoodTemp != 0:
                    tempAvg /= nGoodTemp

                if nGoodHumi != 0:
                    humiAvg /= nGoodHumi
        else:
            # Just return the single values
            nGoodTemp = 1
            nGoodHumi = 1
            tempAvg = temp
            humiAvg = humi

        print(temp, nGoodTemp, tempAvg)
        print(humi, nGoodHumi, humiAvg)

    except Exception as e:
        print(str(e))
        tempAvg = None
        humiAvg = None

    return tempAvg, humiAvg
