import time
import urequests
from machine import Pin


def postToInfluxDB(influxhost, influxport, dbname,
                   metric, value, keyname='value',
                   tagN=None, tagV=None):
    """
    Just using the HTTP endpoint and the simple line protocol.

    Also letting the database time tag it for us.
    """
    success = False

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
        print(url)
        print(line)
        response = urequests.post(url, data=line)
        print("Response:", response.status_code, response.text)
        success = True
    except OSError as e:
        print(str(e))
    except Exception as e:
        print(str(e))

    return success


class shinyThing(object):
    def __init__(self, pin=None, inverted=False, startBlink=True):
        self.pinnum = pin
        self.inverted = inverted

        # Should probably put this in a try...except block?
        self.pin = initLED(self.pinnum)

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


def initLED(pinno):
    """
    """
    # Regular (non-pwm, just on/off)
    print("Setting Pin %02d as OUTPUT" % (pinno))
    led = Pin(pinno, Pin.OUT)

    return led


def blinken(led, duration=0.5, nblinks=1):
    # duration is in seconds
    for _ in range(0, nblinks):
        led.on()
        time.sleep(duration)
        led.off()
        time.sleep(duration)
