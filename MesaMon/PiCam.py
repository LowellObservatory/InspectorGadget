from picamera import PiCamera
import time
import os
 
class PiCam(object):

    def __init__(self, parent):
        self.parent = parent
        string=os.popen('/opt/vc/bin/vcgencmd get_camera').read()
        substring="detected=1"
        if(substring in string):
            self.cameraexists = True
        else:
            self.cameraexists = False

        #print("does camera exist? ", self.cameraexists)

    def take_send_photo(self):
        if not self.cameraexists:
            print ("no camera found")
            return()

        camera = PiCamera()
        camera.resolution = (self.parent.picXres, self.parent.picYres)
        camera.rotation = 180
        camera.iso = self.parent.picISO
        camera.start_preview()
 
        # Camera warm-up time.
        time.sleep(2)
        camera.capture(self.parent.picname)
        camera.close()

        # Make a plot to send along with the picture.
        self.parent.rpdb.read_plot()

        # Send the photo (foo.jpg) to the appropriate mailing 42status.
        cmd = 'echo ' + '"' + self.parent.mailmessage + '"' + \
              ' | mailx -s ' + '"' + self.parent.mailsubject + '"' + \
              ' -A ' + self.parent.attachmentpath + ' ' + \
              ' -A ' + self.parent.plotpath + ' ' + \
              self.parent.mailsendaddress
        os.system(cmd)


