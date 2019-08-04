# This file is executed on every boot (including wake-boot from deepsleep)
import gc
import esp
esp.osdebug(0)

# Adding in a few here even if they're not called directly to make sure
#   they're always available in an interactive session
import time
import machine
import ujson as json
from machine import Pin

import utils
import utils_wifi as uwifi


# Init the stuff
# WiFi Status, cmd status, onboard
ledBuiltin = utils.shinyThing(pin=18, inverted=False)

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

if conncheck is True:
    ledBuiltin.off()
else:
    utils.blinken(ledBuiltin, 0.25, 10)
    ledBuiltin.on()

# In case you want the MAC address, here it is in two parts
# macaddr = ubinascii.hexlify(wlan.config('mac'),':').decode()
# mac1 = macaddr[0:8]
# mac2 = macaddr[8:]

# Ok, give even a little more time for things to settle before
#   we move on to main.py
time.sleep(2)

# Tidy up before the infinite loop
ledBuiltin.off()
gc.collect()

# Start the main loop
