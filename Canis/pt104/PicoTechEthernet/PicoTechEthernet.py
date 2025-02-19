"""."""
import time
import socket
import binascii

# for disconnection cases, otherwise it stalls
socket.setdefaulttimeout(1)


class PicoTechEthernet(object):
    """."""
    def __init__(self):
        self.info = {"SerialNumber": None,
                     "CalibrationDate": None,
                     "MAC": None,
                     "calibration": None}

    def connect(self):
        """Connect to device."""
        print("Connecting to device...")
        # prepare socket for UDP
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Connect, then greet/acknowledge
        self.socket.connect((self.ip, self.port))
        self.socket.send('\x00'.encode('ascii'))
        recv = self.socket.recv(200)

        if recv.startswith(self.model):
            # Get an initial response
            return(recv)
        else:
            # print(recv)
            return(False)

    def lock(self):
        """Establish control of device."""
        responseList = [b'Lock Success\x00',
                        b'Lock Success (already locked to this machine)\x00']
        # NOTE: Keeping this seperate and not stuffed into the return() makes
        #   using the debugging easier, so preferably keep it this way
        resp = self.set(b'lock', response=responseList)
        return(resp)

    def disconnect(self):
        """ Emergency hammer """
        # self.socket.shutdown(socket.SHUT_RDWR)
        self.socket.close()

    def unlock(self):
        """Establish control of device."""
        resp = self.set(b'\x33', response=b'Unlocked\x00')
        return(resp)

    def alive(self):
        """Send the keepalive command."""
        resp = self.set(b'\x34', response=b'Alive\x00')
        return(resp)
        # return(self.set(b'\x34', response=None))

    def set(self, value, response=None):
        """Send text, if required check response."""
        self.socket.send(value)
        responseGood = False
        # self.socket.send(value.encode('ascii'))

        if response is not None:
            recv = self.socket.recv(60)
            # print(recv)
            if isinstance(response, list):
                for item in response:
                    if recv == item:
                        responseGood = True
                        break
            else:
                if recv == response:
                    responseGood = True
                else:
                    # print(recv)
                    responseGood = False
        else:
            # Assume the worst!
            responseGood = False
        return responseGood

    def filter(self, Hz=50):
        """Set the filters for 50 or 60 Hz mains."""
        good = False
        if Hz == 50:
            good = self.set(b'\x30\x00', response=b"Mains Changed\x00")
        else:
            # NOTE: This is an 'else' because the device only supports 50/60
            #   Any non-zero byte denotes 60 hz mains, so I chose 42
            good = self.set(b'\x30\x42', response=b"Mains Changed\x00")
        return good

    def parseCal(self, calData):
        raw = binascii.hexlify(calData)
        chanBig = bytearray.fromhex(str(raw, 'utf-8'))
        chanBig.reverse()
        littleStr = ''.join(f"{n:02X}" for n in chanBig)
        chanLittle = int(littleStr, 16)
        return chanLittle

    def EEPROM(self):
        """Read the EEPROM."""
        # NOTE: Not using self.set here because the response is
        # EEPROM=<128 bytes> and I didn't feel like adding a parse check.
        # BUT because we're not using .set we have to check for a valid
        #   response ourselves to make sure it's not telling us it's locked.
        #   Checking the length is way easier and faster than anything else.
        self.socket.send('\x32'.encode('ascii'))  # Ask for EEPROM of device
        try:
            eepromDataRaw = self.socket.recv(136)
            # NOTE: -1 because there's an end bit that gets stripped?
            print("EEPROM data length: %d" % (len(eepromDataRaw)))
            if len(eepromDataRaw) != 136-1:
                print("Invalid EEPROM response length! Device may be locked?")
            else:
                # Snip out the initial response!
                eepromData = eepromDataRaw[7:]

                # Parse EEPROM. Remember that the last index is not included!
                # print(eepromData)
                self.info["SerialNumber"] = eepromData[19:29].decode("UTF-8").rstrip('\x00')
                self.info["CalibrationDate"] = eepromData[29:37].decode("UTF-8").rstrip('\x00')
                self.info["MAC"] = binascii.hexlify(eepromData[53:59], sep=":").decode("UTF-8")

                chan0Cal = self.parseCal(eepromData[37:41])
                chan1Cal = self.parseCal(eepromData[41:45])
                chan2Cal = self.parseCal(eepromData[45:49])
                chan3Cal = self.parseCal(eepromData[49:53])

                cals = {0: chan0Cal, 1: chan1Cal, 2: chan2Cal, 3: chan3Cal}
                self.info["calibration"] = cals
        except Exception as err:
            print(str(err))

    def read(self):
        """Read value from device."""
        recv = self.socket.recv(60)
        if len(recv) == 20:  # assume len of 20 is valid data
            return(binascii.hexlify(recv).decode())
        else:
            # print(recv)
            return(False)

    def __next__(self):
        """Read values and decode."""
        while True:  # Loop forever
            self.alive()
            for _ in range(3):  # every N reads send/read a keepalive
                read = self.read()
                if read is not False:
                    # self.decode should give channel, cal, value
                    # print("raw read:", read)
                    yield self.decode(read)


class PicoTechEthernetPT104(PicoTechEthernet):
    """."""

    def __init__(self, ip='127.0.0.1', port=6554, superDebug=False):
        """."""
        super().__init__()
        self.model = b'PT-104'
        self.channeloffset = {'00': 0, '04': 1, '08': 2, '0c': 3}
        self.nWires = [4, 4, 4, 4]
        self.conversionTime = 0.720

        self.superDebug = superDebug

        self.ip = ip
        self.port = port
        self.metadata = None

    def singleRead(self, chanNum, chanGain, nWires, unlock=True):
        chanMask = [False, False, False, False]
        gainMask = [0, 0, 0, 0]
        wireMask = [4, 4, 4, 4]

        chanMask[chanNum] = True
        gainMask[chanNum] = chanGain
        wireMask[chanNum] = nWires

        self.alive()
        self.setupDevice(chanMask, gainMask, wireMask)
        time.sleep(self.conversionTime*1.05)

        read = self.read()
        if read is not False:
            # Disable everything again
            chanMask = [False, False, False, False]
            self.setupDevice(chanMask, gainMask, wireMask)
            if unlock is True:
                self.unlock()
            # self.decode should give channel, cal, value
            # print("raw read:", read)
            return self.decode(read)
        else:
            return None, None, None

    def setupDevice(self, channels, gains, nWires=None):
        if nWires is not None:
            self.nWires = nWires

        # \x31 start converting (measuring)
        cmd = f'{0x31:0>8b}'

        # Bit 0: enable channel 1
        # Bit 1: enable channel 2
        # Bit 2: enable channel 3
        # Bit 3: enable channel 4
        # Bit 4: channel 1 gain
        # Bit 5: channel 2 gain
        # Bit 6: channel 3 gain
        # Bit 7: channel 4 gain
        # NOTE: reversed() to preserve endian-ness
        chanCmd = ''.join([str(int(each)) for each in reversed(gains)])
        chanCmd += ''.join([str(int(each)) for each in reversed(channels)])
        setupCmd = cmd + chanCmd
        sendThis = int(setupCmd, 2).to_bytes((len(setupCmd) + 7) // 8,
                                             byteorder='big')

        self.alive()
        self.set(sendThis, response=b'Converting\x00')

    def parseMeasure(self, theseBytes, index):
        """ TCP/IP uses big-endian for numbers in packet headers.
            Don't blame me, blame RFC 1700!
        """
        return (theseBytes[index] << 24) | \
               (theseBytes[index + 1] << 16) | \
               (theseBytes[index + 2] << 8) | \
               (theseBytes[index + 3])

    def decode(self, data=''):
        """."""
        if data != '':
            theseBytes = binascii.unhexlify(data)

            channel = data[0:2]
            zero = self.parseMeasure(theseBytes, 1)
            one = self.parseMeasure(theseBytes, 6)
            two = self.parseMeasure(theseBytes, 11)
            three = self.parseMeasure(theseBytes, 16)

            thisChannel = self.channeloffset[channel]
            thisNWires = self.nWires[thisChannel]
            chanCal = self.info['calibration'][thisChannel]

            if self.superDebug is True:
                print(measurement)
                print(thisNWires)
                print(zero, one, two, three)
                print(chanCal)

            if thisNWires == 4:
                measurement='resistance_4wire'
            elif thisNWires == 3:
                measurement='resistance_3wire'

            if measurement == 'resistance_4wire':
                # (((three - zero))/(one - two))*chanCal
                try:
                    result = (chanCal*(three - two))/(one - zero)
                    result /= 1e6
                except ZeroDivisionError:
                    # This is a low chance event, mainly if someone
                    #   disconnects or bumps something
                    result = 0.0
                return thisChannel, chanCal, result
            elif measurement == 'resistance_3wire':
                result = chanCal*((zero + one) - (two + three))
                result /= 1e6
                return thisChannel, chanCal, result
        else:
            return None, None, None
