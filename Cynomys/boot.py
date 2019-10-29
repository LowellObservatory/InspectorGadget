import gc
import esp
esp.osdebug(0)

# Adding in a few here even if they're not called directly to make sure
#   they're always available in an interactive session
import time
import machine
import ubinascii
import ujson as json
from machine import Pin

import utils
import utils_wifi as uwifi

# On a WeMos D1 Mini (clone) the builtin LED is on pin 2
# ledIndicator = utils.shinyThing(pin=2, inverted=False)

# On the ESP32 DevKit, the LED indicator is tied to +5V and not a pin
ledIndicator = None

if ledIndicator is not None:
    ledIndicator.on()

# This gives time for any automatic wifi connection to finish
time.sleep(5)

# Define the known access points to try to connect to, and make them global
#   so the main loop can access them when/if needed
with open('./knownaps.json') as f:
    klines = f.read()
# Tidy up for parsing now
klines = klines.replace('\n', '')
knownaps = json.loads(klines)

# Attempt to connect to one of the strongest of knownaps
#   If repl is True, start the webrepl too
wlan, conncheck, wconfig = uwifi.checkWifiStatus(knownaps, repl=True)

if ledIndicator is not None:
    if conncheck is True:
        ledIndicator.off()
    else:
        utils.blinken(ledIndicator, 0.25, 10)
        ledIndicator.on()

# In case you want the MAC address, here it is
macaddr = ubinascii.hexlify(wlan.config('mac'),':').decode()
print("Device MAC:", macaddr)

# Ok, give even a little more time for things to settle before
#   we move on to main.py
time.sleep(2)

# Tidy up before the infinite loop
if ledIndicator is not None:
    ledIndicator.off()
gc.collect()

# Almost ready for main loop.  Read in the database information first
with open('./dbconfig.json') as f:
    dlines = f.read()
# Tidy up for parsing now
dlines = dlines.replace('\n', '')
dbconfig = json.loads(dlines)

# At this point, you're ready to go.  Define your specific sensor needs,
#   then import your main loop and call it, a la:
#
# dsPin = machine.Pin(21)
#
# import onewire_looper
# onewire_looper.runmain(dsPin,
#                        dbconfig['dbhost'],
#                        dbconfig['dbport'],
#                        dbconfig['dbname'],
#                        led=ledIndicator)
