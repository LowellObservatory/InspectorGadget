import gc
import time
import machine
import binascii
import micropython

import onewire
import ds18x20

import utils as utils
import utils_wifi as uwifi


def go(knownaps, dbconfig, wlconfig, loops=25):
    """
    Every single board deployment must have this function accepting these
    exact arguments.  Only way to ensure a non-maddening structure!
    """
    # Unpack the wireless configuration stuff
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

    loopCounter = 0
    while loopCounter < loops:
        print("")
        print("Starting loop %d of %d" % (loopCounter+1, loops))
        print("Checking WiFi status ...")
        # Attempt to connect to one of the strongest of knownaps
        wlan, wconfig = uwifi.checkWifiStatus(knownaps,
                                              wlan=wlan,
                                              conf=wconfig,
                                              repl=False)

        # Try to store the connection information
        sV = utils.postNetConfig(wlan, dbconfig)

        # We only should attempt a measurement if the wifi is good, so 
        #   keep this all in the conditional!
        if wlan.isconnected() is True:
            # If the network config dropped out suddenly, sV will be false.
            #   That lets us skip the rest so we can get a WiFi status check 
            #   sooner rather than later
            if sV is True:
                doDS18x(ds, dbconfig, led=ledIndicator)

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

    # Since we're at the end of our rope here, drop the hammer and reset
    print("Resetting in 5 seconds ...")
    time.sleep(5)
    machine.reset()


def doDS18x(ds, dbconfig, led=None):
    """
    """
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
        sV = utils.postToInfluxDB(dbconfig, thistemp, keyname="Temperature",
                                  tagN="DS18x20Sensor", tagV=sensor)

    if led is not None:
        led.off()


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