from picamera2 import Picamera2
import socket
import time
import numpy as np
import cv2

from libcamera import Transform

connectedDevices = {}
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

picam2 = Picamera2(1)
picam2.options["quality"] = 60
picam2.configure(picam2.create_video_configuration(
        buffer_count = 3,
        queue = False,
        main={"size": (1640, 1232), "format": "RGB888"}))
picam2.start()

time.sleep(2)

device_id = '1'

try:
    while True:
        frame = picam2.capture_array()

        frame_resized = cv2.resize(frame, (320, 240))

        _, buffer = cv2.imencode(".jpg",frame_resized )

        sock.sendto(buffer.tobytes(), ('192.168.0.138', 7000))

        connectedDevices[device_id] = {'image': buffer.tobytes()}

except KeyboardInterrupt:
    print("stop")

finally:
    picam2.stop()
    sock.close()
