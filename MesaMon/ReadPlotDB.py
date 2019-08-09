from influxdb import InfluxDBClient
from dateutil import parser
import numpy
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

    def running_mean(self, x, N):
        cumsum = numpy.cumsum(numpy.insert(x, 0, 0)) 
        return (cumsum[N:] - cumsum[:-N]) / float(N)

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

        self.temp1 = (self.running_mean(self.temp1, 11)).tolist()
        self.temp2 = (self.running_mean(self.temp2, 11)).tolist()

        # Make sure the lengths of the lists are equal.
        t1len = len(self.temp1)
        t2len = len(self.temp2)

        # If different lengths, truncate long data (and time if needed)..
        if (t1len > t2len):
          self.temp1 = self.temp1[:-(t1len - t2len)]
          self.time = self.time[:-(t1len - t2len)]
        elif (t1len < t2len):
          self.temp2 = self.temp2[:-(t2len - t1len)]

        t1len = len(self.temp1)
        ttlen = len(self.time)
        if (t1len > ttlen):
          self.temp1 = self.temp1[:-(t1len - ttlen)]
          self.temp2 = self.temp2[:-(t1len - ttlen)]
        elif (t1len < ttlen):
          self.time = self.time[:-(ttlen - t1len)]

        # Convert to Matplotlib dates.
        dates = mdate.date2num(self.time)

        # Plot is 8" wide and 4" high.
        fig = plt.figure(figsize=(8,4))
        ax = fig.add_subplot(111)

        # A formatter for the date.
        myFmt = mdate.DateFormatter('%d %H:%M')
        plt.gca().xaxis.set_major_formatter(myFmt)

        # Axis labels.
        ax.set_xlabel("Day Hour:Min (UTC)")
        ax.set_ylabel("temp (C)", color='tab:green')
        ax.tick_params(axis='y', labelcolor='tab:green')

        # Extend the bottom area of the graph to allow for rotated dates.
        plt.gcf().subplots_adjust(bottom=0.25)

        # Rotate the X-axis labels.
        plt.xticks(rotation=70)

        # Plot the data, add a legend.
        lns1 = ax.plot(dates[:-11], self.temp1[:-11], '-g', label='compressor')
        ax2 = ax.twinx()
        ax2.set_ylabel("temp (C)", color='tab:red')
        ax2.tick_params(axis='y', labelcolor='tab:red')
        lns2 = ax2.plot(dates[:-11], self.temp2[:-11], '-r', label='ambient')
        lns = lns1+lns2
        labs = [l.get_label() for l in lns]
        ax.legend(lns, labs)

        # Save plot to an image.
        plt.savefig('bar.png')
        #plt.show()
