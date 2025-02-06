"""."""

import socket
import asyncio as aio

from numpy.polynomial.polynomial import Polynomial

from ligmos.workers import connSetup, workerSetup
from ligmos.utils.packetizer import makeInfluxPacket

from PicoTechEthernet.PicoTechEthernet import PicoTechEthernetPT104


async def pt104Runner(pt104, chans, gains, nWires,
                      interval=60., database=None,
                      connectSequence=10):
    """
    connectSequence denotes how many "interval" durations elapse before
    the PT-104 is disconnected and reconnected to on the next run through.
    """
    # If this is true, any values that end up at -9999. are not posted
    ignoreInvalids = True
    aliveInterval = 5.

    if pt104.info['calibration'] is None:
        print("WARNING: Missing calibration info! Trying again...")
        pt104 = pt104_getInfo(pt104)

    connectCnt = 0

    # We MUST lock first, otherwise the critcal pt104.alive() calls will return
    #   the full status string indicating it's not yet locked! Tricksy.
    pt104.lock()

    while True:
        print("%02d, %s" % (connectCnt, pt104.ip))
        try:
            thisTempUpdate = {}

            # Really just "hotplug" support here
            if pt104.info['calibration'] is None:
                print("WARNING: Missing calibration info! Trying again...")
                pt104 = pt104_getInfo(pt104)

            if connectCnt == connectSequence-1:
                # Note that lock() is held until after connectSequence elapsed!
                pt104.unlock()
                await aio.sleep(1)
                pt104.connect()
                pt104.lock()
                connectCnt = 0

            if pt104.alive() is True:
                i = 0
                for i, chan in enumerate(chans):
                    if chan is True:
                        print("Reading channel %02d" % (chan))
                        thisChan, cal, val = pt104.singleRead(i,
                                                              gains[i],
                                                              nWires[i],
                                                              unlock=False)

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
                        chanLabel = "Channel_%d" % (thisChan+1)
                        print("%s: %d %f" % (chanLabel, cal, val))

                pkt = makeInfluxPacket(meas=['glycolTemps'],
                                       tags=pt104.metadata,
                                       fields=thisTempUpdate)
                print(pkt)
                if database is not None:
                    database.singleCommit(pkt,
                                          table=database.tablename,
                                          close=True)

            # Increment our connection counter even if we may have failed
            else:
                print("WARNING: Could not lock device!  Is it on?")
                pt104.unlock()
                # pt104.disconnect()

            connectCnt += 1

        except socket.timeout:
            pass
            # print('Connection timeout to PicoTech device')

        # Wait in small increments so we can send alive() requests
        #   and not have to completely restart the connection.
        #   PT-104 disconnects after 15 seconds otherwise!
        j = 0
        # REMEMBER: *2 because we're sleeping for 1/2 second each time
        for _ in range(int(interval)*2):
            await aio.sleep(0.5)
            j += 1
            if j*0.5 >= aliveInterval:
                print("PT-104 aliveness ping during query interval...")
                isAlive = pt104.alive()
                if isAlive is False:
                    print("Device not alive!")
                    pt104.unlock()
                    good = pt104.connect()
                    if good is True:
                        pt104.lock()
                j = 0


def pt104_getInfo(pt104):
    # Only really need to do this bit once
    try:
        pt104.connect()
        good = pt104.lock()
        print("PT-104 lock status:", good)
        # Make sure the AC filter is set up right
        good = pt104.filter(Hz=60)
        # pt104.setupDevice(chanMask, gainMask, wireMask)

        # Parse the EEPROM data and store it for later use internally
        pt104.EEPROM()
        pt104.metadata = {"SerialNumber": pt104.info['SerialNumber'],
                          "MAC": pt104.info['MAC'],
                          "IP": pt104.ip,
                          "port": pt104.port,
                          "recordingDevice": "PT-104"}

        pt104.unlock()
    except socket.timeout:
        print('Connection timeout to PicoTech device')

    return pt104


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


async def loop_stopper(runner):
    while runner.halt is False:
        await aio.sleep(1.)
        if runner.halt is True:
            loop.stop()


class pt104ConfConfig(object):
    """
    Standalone!
    """
    def __init__(self):
        self.name = None
        self.extratag = None
        self.broker = None
        self.brokertopic = None
        self.database = None
        self.tablename = None
        self.devhost = None
        self.devport = None
        self.devtype = "pt104"
        self.nwires = [4, 4, 4, 4]
        # gain 0 == 1x (0-10k ohm range; PT-1000)
        # gain 1 == 21x (0-375 ohm range; PT-100)
        self.gains = [1, 1, 1, 1]
        self.channels = [True, True, True, True]
        self.enabled = False


if __name__ == "__main__":
    # Define the default files we'll use/look for. These are passed to
    #   the worker constructor (toServeMan).
    conf = './pt104.conf'
    desc = "PT104 Async Query Looper"
    logfile = './pt104.log'
    conftype = pt104ConfConfig

    config, comm, args, runner = workerSetup.toServeMan(conf,
                                                        None,
                                                        logfile,
                                                        desc=desc,
                                                        extraargs=None,
                                                        conftype=conftype,
                                                        logfile=True)

    idbs = connSetup.connIDB(comm)
    loop = aio.new_event_loop()

    queryInterval = 25.

    # Pack the active things into a more helpful itterable
    pt104Objs = {}
    for each in config:
        thisSect = config[each]
        if thisSect.devtype.lower().strip() == "pt104":
            # Take care of some silly in-place type conversions
            thisSect.devport = int(thisSect.devport)
            thisSect.gains = [int(x) for x in thisSect.gains]
            thisSect.nwires = [int(x) for x in thisSect.nwires]

            po = PicoTechEthernetPT104(ip=thisSect.devhost,
                                       port=thisSect.devport)
            po = pt104_getInfo(po)

            # NOTE FOR FUTURE: Is deepcopy() required, or will the refs
            #   not collide catastrophically if we keep this simple?
            thisDB = idbs[thisSect.database]
            thisDB.tablename = thisSect.tablename

            pt104Objs.update({thisSect.name: {"obj": po, "config": thisSect}})
            loop.create_task(pt104Runner(po, thisSect.channels,
                                         thisSect.gains, thisSect.nwires,
                                         interval=queryInterval,
                                         database=thisDB))

    loop.create_task(loop_stopper(runner))
    loop.run_forever()

    print("Done!")
