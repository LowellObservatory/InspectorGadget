from picamera import PiCamera
import time
import os
from fractions import Fraction
 
camera = PiCamera(sensor_mode=3)
camera.resolution = (640, 480)
camera.framerate_range = (Fraction(1, 10), Fraction(30, 1))
camera.rotation = 180
camera.drc_strength = 'high'
camera.exposure_mode = 'night'
#camera.sensor_mode = 'matrix'
camera.iso = 800
camera.exposure_compensation = 25
camera.image_denoise = 'false'

time.sleep(3)

camera.exposure_mode = 'off'
camera.shutter_speed = 2800000
print("exp: %f, shut: %f" % (camera.shutter_speed, camera.exposure_speed))
camera.capture('testtest.jpg')
camera.framerate = 1
camera.close()

