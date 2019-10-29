# Cynomys

"sin-o-mis" or "sy-no-mis" (seems like there's a slight preference out there for the latter)

Sensor platform that will go basically anywhere to monitor stuff.

![cynomys](./images/gunnisonprariedog.jpg)

Image credit: Ronan Donovan for The New York Times

Source: https://pressfrom.info/us/news/us/-48831-can-prairie-dogs-talk.html

Cynomys - A taxonomic genus within the family Sciuridae – the prairie dogs, rodents native to the grasslands of 
central North America.  Here in Flagstaff, the dominant population of prarie dogs are _cynomys gunnisoni_, or 
[Gunnison's Prarie Dog](https://en.wikipedia.org/wiki/Gunnison%27s_prairie_dog).

## Why cynomys for a name?  

I see prarie dogs everywhere around town!  Plus, prior Lowell projects have used small pest names 
already (tick, flea, mite, etc.) so I moved up in scale slightly to the rodent population.  Prarie dogs seemed 
like a good fit for all this additional monitoring, they have a complex warning/community alert structure.

## Hardware

The base/platform of choice is an ESP32 development board, mainly for 3 reasons:

- Cheap cost (~$11 USD/board in mid-2019)
- Support for Micropython, with a fallback option of an Arduino-style sketch
- Built in WiFi

The last one is particularly important, since these will be riding along
on the back of a telescope where wiring is _already_ a bit of a mess.

### Specifics

[ESP32-DevKitC-VB (v4 purchased)](https://www.mouser.com/ProductDetail/356-ESP32-DEVKITC-VB)

This one in particular is nice because it's the WROVER-B variant, which
comes with an additional 8 MB of PSRAM (SPI attached).  It's slower,
but that's not an issue for this particular application!

### Micropython Installation

Install the Silicon Labs driver for your platform, only needed for Windows and
OS X.  You can find that at 
[CP210x drivers](https://www.silabs.com/products/development-tools/software/usb-to-uart-bridge-vcp-drivers).

In the past, using knock-off/dirt-cheap ESP development 
boards, I've had a crappy time with this variant of UART-to-USB chip.  I
haven't had any trouble with the above board, though, which makes me think
that the other boards had a ... less-than-honest CP210x chip.  Since this
one is the actual espressif branded board, it's a legit SI labs chip.

The driver itself can be annoying to install in OS X, because Apple.
I've run into cases where it silently fails because it doesn't trigger
Apple's security prompt, which is annoying.  So:

- CLOSE ALL BROWSER WINDOWS 
- Open the OS X "Security & Privacy" window
- Start the driver installation process
- Watch for an 'authorize' button to show up to allow it to proceed, 
and authorize it when it does

I've run into stupidness with OS X and Chrome, where the 'authorize' button
would do literally *nothing* when pressed if Chrome was open.  So, close all
browsers before hand and it should be ok.

Once the driver is installed, plug the board into a computer and look for 
the new entry in your devices/com port listing.  On linux/OS X, it usually
shows up in ```/dev/``` as ```/dev/tty.SLAB_USBtoUART``` or something
very similar.  If it doesn't, CHECK THAT YOU'RE USING AN ACTUAL USB
DATA CABLE!  I don't know how many times I've accidentally used a stupid
"charging only" cable that has its data lines tied/disconnected.

Download [MicroPython](http://micropython.org/download#esp32), and for
this particular board grab the "SPIRAM" enabled stable (non-latest) build.

Install ```esptool.py``` via pip, and then you're ready.

```
esptool.py --port /dev/tty.SLAB_USBtoUART erase_flash
esptool.py --chip esp32 --port /dev/tty.SLAB_USBtoUART write_flash -z 0x1000 esp32spiram-20190529-v1.11.bin
```

To uninstall, just run the Arduino IDE and upload a new sketch
