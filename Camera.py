from picamera2.picamera2 import *
import time
import psutil
import io
import threading
import queue

class Counter(object):
    def __init__(self, value=0):
        # RawValue because we don't need it to create a Lock:
        self.val = value
        self.lock = threading.Lock()

    def increment(self):
        with self.lock:
            self.val += 1

    def value(self):
        with self.lock:
            return self.val


class Flag(object):
    def __init__(self, value=False):
        # RawValue because we don't need it to create a Lock:
        self.val = value
        self.lock = threading.Lock()

    def off(self):
        with self.lock:
            self.val = False

    def on(self):
        with self.lock:
            self.val = True

    def value(self):
        with self.lock:
            return self.val

class Camera:
    cam_thread = None  # background thread that reads frames from camera
    write_threads = []  # background thread that reads frames from camera
    frames = queue.Queue(20)
    print('Queue size: ', psutil.virtual_memory().available / 1024**2 / 14 - 10)
    cur_frame = None  # current frame is stored here by background thread
    last_access = 0  # time of last client access to the camera
    frame_counter = Counter()
    recording = Flag()
    cam_active = Flag()


    def __init__(self, frame_exposure_time=10000, total_exposure_time=10, n_jobs=6):
        self.cam_active.off()
        self.recording.off()
        self.analogue_gain = 10000
        self.frame_exposure_time = frame_exposure_time
        self.total_exposure_time = total_exposure_time
        print('Starting Camera')
        self._camera = Picamera2()
        self._camera.start_preview()
        print('Camera Started')
        self.config = self._camera.still_configuration()
        self._camera.configure(self.config)
        print("Camera Configured")
        self.num_write_threads = n_jobs

    def start(self):
        print('Camera Starting up...')
        self._camera.start({"ExposureTime": self.frame_exposure_time,
                            "AnalogueGain": self.analogue_gain,
                            "AwbEnable": 0,
                            "AeEnable": 0
                            })

        print('Camera started')
        if Camera.cam_thread is None:
            # start background frame thread
            Camera.cam_thread = threading.Thread(target=self._cam_thread, args=(self,))
            Camera.cam_thread.start()

        for i in range(self.num_write_threads):
            t = threading.Thread(target=self._write_thread, args=(self,))
            t.start()
            Camera.write_threads.append(t)
        print('Camera threads started...')


    def stop(self):
        self.recording.off()
        self.cam_active.off()

    def get_frame(self):
        if self.started:
            Camera.last_access = time.time()
            return self.frame

    def start_recording(self):
        manager_thread = threading.Thread(target=self._start_recording())
        manager_thread.start()

    def _start_recording(self):
        print('recording thread started. Recording time: ', self.total_exposure_time)
        self.recording.on()
        print('recording started')
        time.sleep(self.total_exposure_time)
        print('time complete')
        self.recording.off()
        print('recording complete')

    @classmethod
    def _cam_thread(cls, self):
        print('cam thread started. Recording: ', cls.recording.value())
        start = time.time()
        while cls.cam_active:
            request = self._camera.capture_request()
            image = request.make_image("main")
            request.release()
            cls.cur_frame = image
            if cls.recording.value():
                cls.frames.put_nowait(image)
        cls.cam_thread = None
        print('Cam Thread done')

    @classmethod
    def _write_thread(cls, self):
        print("Write thread started", not cls.frames.empty(), cls.cam_thread is not None)
        last = time.time()
        while not cls.frames.empty() or cls.cam_thread is not None:
            if cls.frames.full():
                continue
            image = cls.frames.get()
            image.convert('RGB').save(f"fnoa{cls.frame_counter.value()}.jpg", quality=100, subsampling=0)
            print("frame num", cls.frame_counter.value(), "written")
            cls.frame_counter.increment()
            last = time.time()
        print('Write thread done')
