import io
import time
import picamera
from fractions import Fraction
import os

filepath = '/home/pi/mnt/test/'
# os.mkdir(filepath)
frames = 10

shutter_speed = 1 * 1000000
framerate = Fraction(1000000, shutter_speed)
exposure_mode = 'off'
iso = 800
ip = '192.168.0.10'
port = 8000
capture_time = 30
resolution = (3280, 2464)

def filenames():
    frame = 0
    while frame < frames:
        yield filepath + 'image%02d.png' % frame
        frame += 1

with picamera.PiCamera() as camera:
    camera.resolution = resolution
    camera.hflip = True
    camera.vflip = True
    camera.framerate = framerate
    camera.iso = iso
    camera.shutter_speed = shutter_speed
    camera.exposure_mode = exposure_mode
    camera.start_preview()
    # Give the camera some warm-up time
    time.sleep(2)
    start = time.time()
    camera.capture_sequence(filenames(), use_video_port=True)
    finish = time.time()
print('Captured %d frames at %.2ffps' % ( frames, frames / (finish - start)))