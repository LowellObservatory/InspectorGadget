#
# Copyright (C) 2022 Pico Technology Ltd. See LICENSE file for terms.
#
# PT104 Example
# This example opens a pt104, sets up a single channel and collects data before closing the pt104

import ctypes
from picosdk.usbPT104 import usbPt104 as pt104
import numpy as np
from picosdk.functions import assert_pico_ok
from time import sleep
#import matplotlib.pyplot as plt

# Create chandle and status ready for use
status = {}
chandle = ctypes.c_int16()

# Open the device
# sn = ctypes.c_char_p(b"KU551/161")
sn = ctypes.create_string_buffer(b"")
ip = ctypes.create_string_buffer(b"10.0.0.42:6642")
status["openUnit"] = pt104.UsbPt104OpenUnitViaIp(ctypes.byref(chandle),
                                                 sn, ip)

assert_pico_ok(status["openUnit"])

# Set mains noise filtering
sixty_hertz = 1
status["setMains"] = pt104.UsbPt104SetMains(chandle, sixty_hertz)
assert_pico_ok(status["setMains"])

chanList = []

# Setup channel 1
channel = pt104.PT104_CHANNELS["USBPT104_CHANNEL_1"] #channel 1
datatype = pt104.PT104_DATA_TYPE["USBPT104_PT100"] #pt100
noOfWires = 3 #wires

status["setChannel1"] = pt104.UsbPt104SetChannel(chandle, channel, datatype, noOfWires)
assert_pico_ok(status["setChannel1"])
chanList.append[channel]

# Setup channel 3
channel = pt104.PT104_CHANNELS["USBPT104_CHANNEL_3"] #channel 1
datatype = pt104.PT104_DATA_TYPE["USBPT104_PT100"] #pt100
noOfWires = 4 #wires

status["setChannel1"] = pt104.UsbPt104SetChannel(chandle, channel, datatype, noOfWires)
assert_pico_ok(status["setChannel3"])
chanList.append[channel]

# Setup channel 4
channel = pt104.PT104_CHANNELS["USBPT104_CHANNEL_4"] #channel 1
datatype = pt104.PT104_DATA_TYPE["USBPT104_PT100"] #pt100
noOfWires = 4 #wires

status["setChannel1"] = pt104.UsbPt104SetChannel(chandle, channel, datatype, noOfWires)
assert_pico_ok(status["setChannel4"])
chanList.append[channel]

#collect data
print("collecting data")
numSamples = 20

data1 = (ctypes.c_int32 * numSamples)()
data3 = (ctypes.c_int32 * numSamples)()
data4 = (ctypes.c_int32 * numSamples)()

dataList = []

for i in range(numSamples):

    #pause
    sleep(2)

    # Get values
    measurement = ctypes.c_int32()
    filtered = 1 # true
    for j, chan in enumerate(chanList):
        status["getValue"] = pt104.UsbPt104GetValue(chandle, chan,
                                                    ctypes.byref(measurement),
                                                    filtered)
        assert_pico_ok(status["getValue"])

        dataList[j][i] = measurement.value

samples = np.linspace(0, numSamples*2, numSamples)
data1Temp = [x /1000 for x in data1]
data3Temp = [x /1000 for x in data3]
data4Temp = [x /1000 for x in data4]

print(samples, data1Temp, data3Temp, data4Temp)

# Close the device
status["closeUnit"] = pt104.UsbPt104CloseUnit(chandle)
assert_pico_ok(status["closeUnit"])

print(status)
