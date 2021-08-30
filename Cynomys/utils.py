import time
import urequests
from machine import Pin

import utils_influx as uinflux


class Button:
    # Since we're using .ticks_ms(), the times are all in milliseconds!
    _debounce = 100

    def __init__(self, pin, name, onrelease=None):
        self.name = name
        self.checkin = time.ticks_ms()
        self.state = True
        self.onrelease = onrelease
        print("Setting Pin %02d as INPUT" % (pin))
        self.input = Pin(pin, Pin.IN, Pin.PULL_UP)

    def press(self):
        print(self.name, "pressed")

    def release(self):
        print(self.name, "released")
        if self.onrelease is not None:
            self.onrelease()

    def check(self):
        return self.input.value()

    def update(self):
        if time.ticks_diff(time.ticks_ms(), self.checkin) > self._debounce:
            if self.state and not self.check():
                self.press()

            if not self.state and self.check():
                self.release()

            self.state = self.check()

            self.checkin = time.ticks_ms()


def postNetConfig(wlan, dbconfig, deviceid="cynomys", debug=True):
    """
    This is intended to post the info to a metric in a table called 'netinfo'
    tagged with the DeviceID specified in the config.json file
    """
    dbconfig.update({"dbtabl": "netinfo"})

    # Quick and early exit
    if wlan.isconnected() is False:
        sV = False
        return sV

    # curIPs: ip, subnet, gateway, dns
    curIPs = wlan.ifconfig()
    curAP = wlan.config('essid')
    curRSSI = wlan.status('rssi')

    if debug is True:
        print("Connected to %s at %s thru %s at %.0f dBm\n" % (curAP,
                                                               curIPs[0],
                                                               curIPs[2],
                                                               curRSSI))

    storageFields = {"ipaddress": curIPs[0],
                     "gateway": curIPs[2],
                     "dns": curIPs[3],
                     "accesspoint": curAP,
                     "curRSSI": curRSSI}
    
    pkt = uinflux.makeInfluxPacket(meas=dbconfig['dbtabl'],
                                   fields=storageFields, 
                                   tags={"DeviceID": deviceid})
    print(pkt)
    sV = uinflux.postToInfluxDB(dbconfig, pkt)
    
    return sV


class shinyThing(object):
    def __init__(self, pin=None, inverted=False, startBlink=True):
        self.pinnum = pin
        self.inverted = inverted

        # Should probably put this in a try...except block?
        self.pin = initLED(self.pinnum, inverted=self.inverted)
        self.off()

        if startBlink is True:
            self.on()
            time.sleep(1)
            self.off()

    def on(self):
        """
        Alternate/backup interface to self.pin.on(). Allows me to wrap the
        inversion logic into it so I can always use on() and off().
        """
        if self.inverted is True:
            self.pin.value(0)
        else:
            self.pin.value(1)

    def off(self):
        if self.inverted is True:
            self.pin.value(1)
        else:
            self.pin.value(0)

    def toggle(self):
        self.pin.value(not self.pin.value())


def initButton(pinno):
    """
    """
    print("Setting Pin %02d as INPUT" % (pinno))
    butt = Pin(pinno, Pin.IN, Pin.PULL_UP)

    # I am a simple man.
    return butt


def initLED(pinno, inverted=False):
    """
    """
    # Regular (non-pwm, just on/off)
    print("Setting Pin %02d as OUTPUT" % (pinno))
    if inverted is False:
        led = Pin(pinno, Pin.OUT)
    else:
        led = Pin(pinno, Pin.OUT, 1)

    return led


def blinken(led, duration=0.5, nblinks=1):
    # duration is in seconds
    for _ in range(0, nblinks):
        led.on()
        time.sleep(duration)
        led.off()
        time.sleep(duration)
