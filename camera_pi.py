#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  camera_pi.py
#  
#  
#  
import time
import io
import threading
import picamera


class Camera(object):
    thread = None  # background thread that reads frames from camera
    frame = None  # current frame is stored here by background thread
    last_access = 0  # time of last client access to the camera

    def __init__(self, shutter_speed, framerate, exposure_mode, iso, resolution, mode=2):
        self.shutter_speed=shutter_speed
        self.framerate = framerate
        self.exposure_mode = exposure_mode
        self.iso = iso
        self.resolution=resolution
        self.mode = mode
    def initialize(self):
        if Camera.thread is None:
            # start background frame thread
            Camera.thread = threading.Thread(target=self._thread, args=(self.resolution, self.framerate, self.iso, self.shutter_speed, self.exposure_mode, self.mode, 10, 20))
            Camera.thread.start()

            # wait until frames start to be available
            while self.frame is None:
                time.sleep(0)

    def get_frame(self):
        Camera.last_access = time.time()
        self.initialize()
        return self.frame

    @classmethod
    def _thread(cls, resolution, framerate, iso, shutter_speed, exposure_mode, mode, warmup, recording_time):
        with picamera.PiCamera() as camera:
            # camera setup
            camera.resolution = resolution
            camera.hflip = True
            camera.vflip = True
            camera.framerate = framerate
            camera.iso = iso
            camera.shutter_speed = shutter_speed
            camera.exposure_mode = exposure_mode

            # let camera warm up
            # camera.start_preview()
            time.sleep(warmup)

            stream = io.BytesIO()
            start = time.time()
            for foo in camera.capture_continuous(stream, 'jpeg',
                                                 use_video_port=True):
                # store frame
                stream.seek(0)
                cls.frame = stream.read()

                # reset stream for next frame
                stream.seek(0)
                stream.truncate()

                # if there hasn't been any clients asking for frames in
                # the last 10 seconds stop the thread
                if time.time() - cls.last_access > 10 or time.time() - start > recording_time:
                    break
        cls.thread = None
