from influxdb import InfluxDBClient
from dateutil import parser
import os
import matplotlib
if os.environ.get('DISPLAY','') == '':
    matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdate

class ReadPlotDB(object):

    def __init__(self, parent):
        self.parent = parent
        self.client = InfluxDBClient('localhost', 8086, 'zombie', 'zombie',
                                     'temps')

        self.temp1 = list()
        self.temp2 = list()
        self.time  = list()

    def read_plot(self):

        result = self.client.query('select temp from compresstemp \
                                    where time > now() - 24h;')

        points = result.get_points()

        for point in points:
            self.temp1.append(point["temp"])
            self.time.append(parser.parse(point["time"]))

        result = self.client.query('select temp from ambienttemp \
                                    where time > now() - 24h;')

        points = result.get_points()

        for point in points:
            self.temp2.append(point["temp"])

        # Make sure the lengths of the lists are equal.
        t1len = len(self.temp1)
        t2len = len(self.temp2)

        # If different lengths, pad with zeros.
        if (t1len > t2len):
          self.temp2.extend([0] * (t1len - t2len))
        elif (t1len < t2len):
          self.temp1.extend([0] * (t2len - t1len))
        
        # Convert to Matplotlib dates.
        dates = mdate.date2num(self.time)

        # Plot is 8" wide and 4" high.
        plt.figure(figsize=(8,4))

        # A formatter for the date.
        myFmt = mdate.DateFormatter('%d %H:%M')
        plt.gca().xaxis.set_major_formatter(myFmt)

        # Axis labels.
        plt.xlabel("Day Hour:Min (UTC)")
        plt.ylabel("temp (C)")

        # Extend the bottom area of the graph to allow for rotated dates.
        plt.gcf().subplots_adjust(bottom=0.25)

        # Rotate the X-axis labels.
        plt.xticks(rotation=70)

        # Plot the data, add a legend.
        plt.plot(dates, self.temp1, label='compressor')
        plt.plot(dates, self.temp2, label='ambient')
        plt.legend()

        # Save plot to an image.
        plt.savefig('bar.png')
        #plt.show()
