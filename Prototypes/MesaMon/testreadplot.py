#! /usr/bin/python3

import sys
import schedule
import time
import argparse
from ReadPlotDB import *

class testreadplot(object):

    def __init__(self):

        # Instantiate a ReadPlotDB
        self.rpdb = ReadPlotDB(self)

if __name__ == '__main__':
    
    trp = testreadplot()
    trp.rpdb.read_plot()

