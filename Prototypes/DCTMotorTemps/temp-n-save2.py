import os
import glob
import time
import matplotlib.pyplot as plt
from influxdb import InfluxDBClient
from influxdb import SeriesHelper
 
os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')
  
base_dir = '/sys/bus/w1/devices/'
device_folder = glob.glob(base_dir + '28*')[0]
device_file = device_folder + '/w1_slave'

sens1 = [0.0] * 50
sens2 = [0.0] * 50
xval = list(range(50))

plt.ion()
fig = plt.figure(1)

ax1 = fig.add_subplot(211)
ax1.set_ylim([0.0,50.0])
line1, = ax1.plot(xval, sens1)

ax2 = fig.add_subplot(212)
ax2.set_ylim([0.0,50.0])
line2, = ax2.plot(xval, sens2)

host = 'astropci.lowell.edu'
port = 8086
user = 'dlytle'
password = 'dlytle'
dbname = 'temps'

# Establish connection to influxdb database.

myinfluxdbclient = InfluxDBClient(host, port, user, password, dbname)

myinfluxdbclient.create_database(dbname)
myinfluxdbclient.create_retention_policy('awesome_policy', '3d', 3,
    default=True)

class MySeriesHelper(SeriesHelper):
    """Instantiate SeriesHelper to write points to the backend."""

    class Meta:
        """Meta class stores time series helper configuration."""

        # The client should be an instance of InfluxDBClient.
        client = myinfluxdbclient

        # The series name must be a string. Add dependent fields/tags
        # in curly brackets.
        series_name = 'events.stats.{server_name}'

        # Defines all the fields in this time series.
        fields = ['temp1', 'temp2']

        # Defines all the tags for the series.
        tags = ['server_name']

        # Defines the number of data points to store prior to writing
        # on the wire.
        bulk_size = 5

        # autocommit must be set to True when using bulk_size
        autocommit = True


def read_temp():
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
                print(
                    "Sensor: {}, Id: {} Temp: {:.1f}".format(sensornum, id, t))
                if (sensornum == 0):
                    sens1.pop(49)
                    sens1.insert(0, t)
                    t1 = t
                else:
                    sens2.pop(49)
                    sens2.insert(0, t)
                    t2 = t
            else:
                print("999.9")

        except:
            pass
        sensornum = sensornum + 1
    MySeriesHelper(server_name='us.east-1', temp1=t1, temp2=t2)



while True:
    read_temp()        
    # Update plot.
    line1.set_ydata(sens1)
    line2.set_ydata(sens2)
    fig.canvas.draw()
    fig.canvas.flush_events()
    time.sleep(1)
