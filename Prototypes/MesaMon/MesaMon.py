#! /usr/bin/python3

import sys
import schedule
import time
import argparse
from PiCam import *
from TempSensors import *
from ReadPlotDB import *
from configparser import ConfigParser, ExtendedInterpolation

class MesaMon(object):

    """
    A Raspberry Pi/Raspbian program to monitor temps and take pictures.

    This program takes one argument, the configuration file.

    Currently configured to monitor two temperature sensors and store
    the data into an InfluxDB database.

    The picture is taken with a Raspberry Pi camera and sent via email.
    """


    def __init__(self, configfile):

        # Read the configuration file, store information in instance variables.
        config = ConfigParser(interpolation=ExtendedInterpolation())
        config.read(configfile)

        self.pictime = config['camera']['pictime']
        self.picname = config['camera']['picname']
        self.picISO = int(config['camera']['picISO'])
        self.picXres = int(config['camera']['picXres'])
        self.picYres = int(config['camera']['picYres'])

        self.tablename = config['database']['tablename']
        self.meas1name = config['database']['meas1name']
        self.meas2name = config['database']['meas2name']

        self.mailmessage = config['mail']['mailmessage']
        self.mailsubject = config['mail']['mailsubject']
        self.mailsendaddress = config['mail']['mailsendaddress']
        self.attachmentpath = config['mail']['attachmentpath']
        self.plotpath = config['mail']['plotpath']

        self.sleeptime = int(config['main']['sleeptime'])

        # Instantiate a PiCam, and TempSensors.
        self.cam = PiCam(self)
        self.temps = TempSensors(self)

        # Instantiate a ReadPlotDB
        self.rpdb = ReadPlotDB(self)

        # Set up a schedule for the camera.
        schedule.every().day.at(self.pictime).do(self.foto,'It is ' +
            self.pictime)

    def foto(self, t):
        # Called by schedule, instruct the camera to take a photo.
        # Use configuration information to email the photo.
        print ("I'm takeing a photo...", t)
        self.cam.take_send_photo()
        return

if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(description='MesaMon')
    parser.add_argument('configfile')
    args = parser.parse_args()
    mm = MesaMon(args.configfile)
    while True:
        mm.temps.read_store()
        schedule.run_pending()
        time.sleep(mm.sleeptime) # Wait sleeptime.

