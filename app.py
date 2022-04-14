from flask import Flask, render_template, Response, request, redirect
import io
import socket
import struct
import time
import picamera
from fractions import Fraction
# Raspberry Pi camera module (requires picamera package)
from flask import send_file
from math import cos, atan, degrees, pi, radians
import Camera

from werkzeug.exceptions import HTTPException
import json

app = Flask(__name__)

focal_length = 800
aperture = 60
pixel_size = 1.14
total_exposure_length = 30
des_trail_len = 7

camera = None


def calculate_max_exposure(declination, focal_length):
    return abs((27 * 1.12) / (focal_length * cos(declination)))


def resolving_power(a):
    return 115.824 / a


def fov(flength):
    fovw = 120 * degrees(atan((3280 * (1.12 / 1000)) / (2 * flength)))
    fovh = 120 * degrees(atan((2464 * (1.12 / 1000)) / (2 * flength)))
    return fovw, fovh


def resolution_per_pixel(fovw):
    return (fovw / 3280) * 60


def exposure_len_given_desired_trail_len(trail_pixels, F, D):
    sidereal = (2 * pi) / 86164.1
    return (1.14 * trail_pixels) / (F * sidereal * 1000 * cos(radians(D * pi / 180)))


def angular_resolution_per_pixel(pixel_size, focal_length):
    return (pixel_size / focal_length) * 206.265

frame_exposure_length = int(exposure_len_given_desired_trail_len(des_trail_len, focal_length, 0) * 1000000)

# def start_streaming():
#     client_socket.connect((ip, port))
#
#     # Make a file-like object out of the connection
#     connection = client_socket.makefile('wb')
#
#     try:
#         with picamera.PiCamera() as camera:
#             camera.resolution = (3280, 2464)
#             # Start a preview and let the camera warm up for 2 seconds
#             # camera.start_preview()
#             time.sleep(10)
#
#             # Note the start time and construct a stream to hold image data
#             # temporarily (we could write it directly to connection but in this
#             # case we want to find out the size of each capture first to keep
#             # our protocol simple)
#             start = time.time()
#             stream = io.BytesIO()
#             for foo in camera.capture_continuous(stream, 'jpeg'):
#                 # Write the length of the capture to the stream and flush to
#                 # ensure it actually gets sent
#                 connection.write(struct.pack('<L', stream.tell()))
#                 connection.flush()
#                 # Rewind the stream and send the image data over the wire
#                 stream.seek(0)
#                 connection.write(stream.read())
#                 # If we've been capturing for more than 30 seconds, quit
#                 if time.time() - start > capture_time:
#                     break
#                 # Reset the stream for the next capture
#                 stream.seek(0)
#                 stream.truncate()
#         # Write a length of zero to the stream to signal we're done
#         connection.write(struct.pack('<L', 0))
#     finally:
#         connection.close()
#         client_socket.close()


@app.route('/')
def index():
    """Video streaming home page."""

    return render_template('settings.html',
                           frame_exposure_length=frame_exposure_length,
                           total_exposure_length=total_exposure_length,
                           focal_length=focal_length,
                           aperture=aperture,
                           arpp=angular_resolution_per_pixel(pixel_size, focal_length),
                           calc_exp_min=exposure_len_given_desired_trail_len(des_trail_len, focal_length, 0),
                           calc_exp_max=exposure_len_given_desired_trail_len(des_trail_len, focal_length, 90),
                           trail_len=des_trail_len,
                           mrp=resolving_power(aperture),
                           camera_on=camera.cam_active.value() if camera is not None else False)


# def gen(camera):
#     """Video streaming generator function."""
#     global add_frame
#     while True:
#         frame = camera.get_frame()
#         if add_frame is None:
#             add_frame = np.asarray(Image.open(io.BytesIO(frame))).astype('uint16')
#             show_frame = Image.open(io.BytesIO(frame))
#             print(add_frame)
#             print(add_frame.max())
#         else:
#
#             add_frame = add_frame + np.asarray(Image.open(io.BytesIO(frame)))
#
#             show_array = (add_frame * (255.0 / add_frame.max())).astype('uint8')
#             show_frame = Image.fromarray(show_array)
#         with io.BytesIO() as output:
#             show_frame.save(output, 'BMP')
#             data = output.getvalue()
#         yield (b'--frame\r\n'
#                b'Content-Type: image/jpeg\r\n\r\n' + data + b'\r\n')


@app.route('/settingsSubmit', methods=['POST'])
def camera_settings():
    global frame_exposure_length, total_exposure_length, focal_length, capture_time, des_trail_len, aperture
    # print(exposure)
    print(request.form)

    frame_exposure_length = int(float(request.form['frame_exposure_length']) * 1000000)
    total_exposure_length = int(float(request.form['total_exposure_length']))
    if camera is not None:
        camera.total_exposure_time= total_exposure_length
        camera.frame_exposure_time = frame_exposure_length
    focal_length = int(request.form['focal_length'])
    aperture = int(request.form['aperture'])
    des_trail_len = int(request.form['trail_len'])

    return redirect('/', code=302)


# @app.route('/video_feed')
# def video_feed():
#     """Video streaming route. Put this in the src attribute of an img tag."""
#     global add_frame
#     add_frame = None
#     return Response(gen(Camera(shutter_speed, framerate, exposure_mode, 800, (320, 240))),
#                     mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/view_live')
def live_view():
    """Video streaming route. Put this in the src attribute of an img tag."""
    return render_template('index.html')


@app.route('/start_camera')
def start_cam():
    """Video streaming route. Put this in the src attribute of an img tag."""
    global camera
    if camera is None:
        camera = Camera.Camera(frame_exposure_time=frame_exposure_length, total_exposure_time=total_exposure_length)
    camera.start()
    return redirect('/', code=302)


@app.route('/stop_camera')
def stop_cam():
    """Video streaming route. Put this in the src attribute of an img tag."""
    global camera
    if camera is not None:
        camera.stop()
    return redirect('/', code=302)

@app.route('/start_recording')
def start_recording():
    global camera
    if not camera.recording.value():
        camera.start_recording()
    return redirect('/', code=302)


@app.route("/download/<path>")
def DownloadLogFile(path=None):
    print('done')
    return send_file(path, as_attachment=True)


if __name__ == '__main__':
    exposure = 10

    # app.run(host='0.0.0.0', port=8080, threaded=True)
