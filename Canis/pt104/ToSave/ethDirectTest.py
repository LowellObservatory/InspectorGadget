"""."""

import socket
import asyncio as aio

from numpy.polynomial.polynomial import Polynomial

from ligmos.utils.database import influxobj
from ligmos.utils.common import HowtoStopNicely
from ligmos.utils.packetizer import makeInfluxPacket

from PicoTechEthernet.PicoTechEthernet import PicoTechEthernetPT104


async def pt104Runner(pt104, chans, gains, nWires,
                      interval=60., database=None):
    # If this is true, any values that end up at -9999. are not posted
    ignoreInvalids = True

    # Only really need to do this bit once
    try:
        pt104.connect()
        good = pt104.lock()
        print("PT-104 lock status:", good)

        # Parse the EEPROM data and store it for later use internally
        pt104.EEPROM()
        pt104.unlock()
    except socket.timeout:
        print('Connection timeout to PicoTech device')

    metadata = {"SerialNumber": pt104.info['SerialNumber'],
                "MAC": pt104.info['MAC']}

    try:
        thisTempUpdate = {}

        if pt104.alive() is False:
            print("Was dead! Reconnecting")
            pt104.connect()
        good = pt104.filter(Hz=60)
        good = pt104.lock()

        while good is True:
            i = 0
            for i, chan in enumerate(chans):
                if chan is True:
                    thisChan, cal, val = pt104.singleRead(i,
                                                          gains[i],
                                                          nWires[i])
                    chanLabel = "Channel_%d" % (thisChan)
                    # This just works around weird values for enabled
                    #   but disconnected channels
                    post = False
                    if val == -0.0 or val == 0.0 or \
                        val < 0. or val > 20000:
                        val = -9999.9
                        temp = -9999.9
                        if ignoreInvalids is True:
                            post = False
                        else:
                            post = True
                    else:
                        val = round(val, 5)
                        temp = round(pt100conv(val), 5)
                        if temp < -280.:
                            val = -9999.9
                            temp = -9999.9
                            if ignoreInvalids is True:
                                post = False
                            else:
                                post=True
                        else:
                            post = True

                    if post is True:
                        ohmLab = "Channel_%d_ohms" % (thisChan)
                        tmpLab = "Channel_%d_tempC" % (thisChan)
                        thisTempUpdate.update({ohmLab: val,
                                                tmpLab: temp})
                    print(thisChan, val)

            pkt = makeInfluxPacket(meas=['glycolTemps'],
                                    tags=metadata,
                                    fields=thisTempUpdate)
            print(pkt)
            if database is not None:
                #database.write(pkt)
                pass

            # Wait in small increments so we can send alive() requests
            #   and not have to completely restart the connection
            j = 0
            for _ in range(int(interval)*2):
                await aio.sleep(0.5)
                j += 1
                if j % 10 == 0:
                    good = pt104.alive()
                    if good is False:
                        print("Device disconnected!")
                        break

    except socket.timeout:
        pass
        # print('Connection timeout to PicoTech device')

    print("Unlocking PT-104...")
    pt104.unlock()


def pt100conv(resistance):
    """
    PT100 curve from the PicoTech PT-104 Programmers Guide fit with a
    5th degree polynomial since it was quite detailed at 1 C intervals.

    NOTE: Valid only from 80 to 175 ohms, or -50 C to 200 C
    """
    coeffs = [7.26299199e+01, 1.24919157e+02, 2.34838202e+00,
              1.02219094e-01, 2.01920028e-02, -2.08675751e-02]

    fitter = Polynomial(coeffs, domain=[80.306282, 175.856],
                        window=[-1.,  1.], symbol='x')

    if resistance != -9999.9:
        thisTemp = fitter(resistance)
    else:
        thisTemp = -9999.9

    return thisTemp


async def loop_stopper():
    while runner.halt is False:
        await aio.sleep(1.)
        if runner.halt is True:
            loop.stop()


if __name__ == "__main__":
    pt104_bunsen = PicoTechEthernetPT104(ip='10.0.0.42', port=6642)
    pt104_beaker = PicoTechEthernetPT104(ip='10.0.0.43', port=6642)

    idb = influxobj(host='tanagra.lowell.edu', port=8086,
                    tablename='ldtDevTests',
                    user='darmok', pw='jalad')

    # gain 0 == 1x (0-10k ohm range; PT-1000)
    # gain 1 == 21x (0-375 ohm range; PT-100)
    gains = [1, 1, 1, 1]

    chans = [True, False, True, True]
    nWires = [4, 4, 4, 4]

    runner = HowtoStopNicely()
    loop = aio.new_event_loop()
    loop.create_task(pt104Runner(pt104_bunsen, chans, gains, nWires,
                                 interval=25., database=idb))
    loop.create_task(pt104Runner(pt104_beaker, chans, gains, nWires,
                                 interval=25., database=idb))
    loop.create_task(loop_stopper())
    loop.run_forever()

    print("Done!")
