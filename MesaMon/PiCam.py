from picamera import PiCamera
import time
import os
 
class PiCam(object):

    def __init__(self, parent):
        self.parent = parent

    def take_send_photo(self):
        camera = PiCamera()
        camera.resolution = (self.parent.picXres, self.parent.picYres)
        camera.iso = self.parent.picISO
        camera.start_preview()
 
        # Camera warm-up time.
        time.sleep(2)
        camera.capture(self.parent.picname)
        camera.close()

        # Send the photo (foo.jpg) to the appropriate mailing 42status.
        cmd = 'echo ' + '"' + self.parent.mailmessage + '"' + \
              ' | mailx -s ' + '"' + self.parent.mailsubject + '"' + \
              ' -A ' + self.parent.attachmentpath + ' ' + \
              self.parent.mailsendaddress
        print(cmd)
        os.system(cmd)


