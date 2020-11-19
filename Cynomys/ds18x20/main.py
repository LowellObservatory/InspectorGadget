import gc
import time
import machine
import binascii
import micropython
from machine import WDT

import onewire
import ds18x20

import utils as utils
import utils_wifi as uwifi


def go(deviceid, config, wlconfig, loops=25):
    """
    Every single board deployment must have this function accepting these
    exact arguments.  Only way to ensure a non-maddening structure!
    """
    # Unpack the things
    knownaps = config['knownaps']
    dbconfig = config['dbconfig']
    wlan = wlconfig['wlan']
    wconfig = wlconfig['wconfig']

    # Indicate our WiFi connection status
    ledIndicator = utils.shinyThing(pin=4, inverted=False, startBlink=True)
    if wlan.isconnected() is True:
        ledIndicator.off()
    else:
        utils.blinken(ledIndicator, 0.25, 10)
        ledIndicator.on()

    # Set up the onewire stuff
    dsPin = machine.Pin(21)
    ow = onewire.OneWire(dsPin)
    ds = ds18x20.DS18X20(ow)

    # Set up our last ditch hang preventer
    dogfood = 60000
    wdt = WDT(timeout=dogfood)
    print("Watchdog set for %.2f seconds" % (dogfood/1000.))

    loopCounter = 0
    while loopCounter < loops:
        # Feed the dog. We'll do this a bunch since wifi can be slow
        wdt.feed()
        print("\nFed the dog")
        print("Starting loop %d of %d" % (loopCounter+1, loops))
        print("Checking WiFi status ...")
        # Attempt to connect to one of the strongest of knownaps
        wlan, wconfig = uwifi.checkWifiStatus(knownaps,
                                              wlan=wlan,
                                              conf=wconfig,
                                              repl=False)

        # Try to store the connection information
        wdt.feed()
        print("Fed the dog")
        sV = utils.postNetConfig(wlan, dbconfig, tagname=deviceid)

        # We only should attempt a measurement if the wifi is good, so
        #   keep this all in the conditional!
        if wlan.isconnected() is True:
            # If the network config dropped out suddenly, sV will be false.
            #   That lets us skip the rest so we can get a WiFi status check
            #   sooner rather than later
            if sV is True:
                wdt.feed()
                print("Fed the dog")
                doDS18x(ds, dbconfig, led=ledIndicator)

        gc.collect()
        # Print some memory statistics so I can watch for problems
        micropython.mem_info()
        print("Sleeping (and feeding the dog) ...\n")
        for sc in range(0, 60):
            if sc % 10 == 0 and sc != 0:
                print("\n")
            else:
                print(".", end='')
            time.sleep(1)
            wdt.feed()

        loopCounter += 1

    # Since we're at the end of our rope here, drop the hammer and reset
    print("Resetting in 5 seconds ...")
    time.sleep(5)
    machine.reset()


def doDS18x(ds, dbconfig, led=None):
    """
    """
    if led is not None:
        led.on()

    try:
        # First read can be junk/noisy so just toss it
        print("Grabbing initial/throwaway value...")
        _ = getDS18x20val(ds)
        time.sleep(1)

        # Do 5 reads, then average them
        avgs = DS18x20multiread(ds, nreads=5, delay=1.0)
        print("Grabbed all values and averaged them!")

        for sensor in avgs:
            thistemp = avgs[sensor]
            print("Posting %s to influxdb..." % (sensor))
            sV = utils.postToInfluxDB(dbconfig, thistemp,
                                      keyname="Temperature",
                                      tagN="DS18x20Sensor", tagV=sensor)
            print("Posting succeeded: %s" % (sV))
    except Exception as err:
        # The ds18x20 lib just raises 'Exception' if there's a CRC err
        #   The CRC error seems to be random and depends on the
        #   specific MP build being used?  It's weird.
        #   https://forum.micropython.org/viewtopic.php?t=7135
        # Decided to trap it here in the meta loop rather than
        #   in the helper functions since
        print(str(err))

    if led is not None:
        led.off()


def getDS18x20val(dssens):
    """
    Make sure to trap this in a try...except block to catch CRC exceptions
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
    Make sure to trap this in a try...except block to catch CRC exceptions
    """
    allvals = {}
    avgvals = {}

    # Get the list of DS18x20 sensors on the onewire bus
    print("Scanning for devices...")
    roms = dssens.scan()

    # Read each sensor we find on the bus and store their values
    for rom in roms:
        for i in range(0, nreads):
            # You must sleep for 750ms after starting convert_temp
            dssens.convert_temp()
            time.sleep_ms(750)
            print("convert_temp finished")
            temp = dssens.read_temp(rom)
            romStr = binascii.hexlify(rom).decode('ascii')
            print(time.time(), romStr, temp)

            if temp is not None:
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
