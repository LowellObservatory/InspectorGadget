import os
import glob
import time
import datetime
from database import influxobj
from packetizer import makeInfluxPacket
 
class TempSensors(object):

    """
    Database table must be created before this program is run.
    Currently we use a table called 'temps'.
    """

    def __init__(self, parent):
        
        self.parent = parent

        os.system('modprobe w1-gpio')
        os.system('modprobe w1-therm')
          
        self.ifdbio = influxobj(tablename=self.parent.tablename)
        
        
    def read_store(self):
        sensornum = 0
        for sensor in glob.glob("/sys/bus/w1/devices/28-01*/w1_slave"):
            #print(sensor)
            id = sensor.split("/")[5]
        
            try:
                f = open(sensor, "r")
                data = f.read()
                f.close()
                if "YES" in data:
                    (discard, sep, reading) = data.partition(' t=')
                    t = float(reading) / 1000.0
                    if (sensornum == 0):
                        t1 = t
                        print("t1 = ", t1)
                    else:
                        t2 = t
                        print("t2 = ", t2)
                else:
                    print("999.9")
        
            except:
                pass
            sensornum = sensornum + 1

        # Send the collected temperatures to the database.
        d = {'temp': t1}
        m = [self.parent.meas1name]
        pkt = makeInfluxPacket(meas=m, fields=d)
        self.ifdbio.singleCommit(pkt, table=self.parent.tablename)
        d = {'temp': t2}
        m = [self.parent.meas2name]
        pkt = makeInfluxPacket(meas=m, fields=d)
        self.ifdbio.singleCommit(pkt, table=self.parent.tablename)
