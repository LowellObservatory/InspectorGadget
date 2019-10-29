from picamera import PiCamera
import time
import os
from fractions import Fraction


 
class PiCam(object):

    def __init__(self, parent):
        self.parent = parent
        string=os.popen('/opt/vc/bin/vcgencmd get_camera').read()
        substring="detected=1"
        if(substring in string):
            self.cameraexists = True
        else:
            self.cameraexists = False

        print("does camera exist? ", self.cameraexists)

    def take_send_photo(self):
        if not self.cameraexists:
            print ("no camera found")
            return()

        camera = PiCamera(sensor_mode=3)
        camera.resolution = (self.parent.picXres, self.parent.picYres)
        camera.framerate_range = (Fraction(1, 10), Fraction(30, 1))
        camera.rotation = 180
        camera.drc_strength = 'high'
        camera.exposure_mode = 'night'
        camera.iso = self.parent.picISO
        camera.exposure_compensation = 25
        camera.image_denoise = 'false'
 
        time.sleep(3)

        camera.exposure_mode = 'off'
        camera.shutter_speed = 2800000
        camera.capture(self.parent.picname)
        camera.framerate = 1
        camera.close()

        # Make a plot to send along with the picture.
        self.parent.rpdb.read_plot()

        # Send the photo (foo.jpg) and plot (bar.png) to the appropriate
        # mailing 31status.
        cmd = 'echo ' + '"' + self.parent.mailmessage + '"' + \
              ' | mailx -s ' + '"' + self.parent.mailsubject + '"' + \
              ' -A ' + self.parent.attachmentpath + ' ' + \
              ' -A ' + self.parent.plotpath + ' ' + \
              self.parent.mailsendaddress
        os.system(cmd)


