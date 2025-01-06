import socket
import time
import numpy as np
import cv2
import tornado.ioloop
import tornado.web
import tornado.gen
import threading
from picamera2 import Picamera2

connectedDevices = {}

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
UDP_SERVER_IP = '0.0.0.0'
UDP_SERVER_PORT = 7000

picam1 = Picamera2(0)
picam1.options["quality"] = 60
picam1.configure(picam1.create_video_configuration(
        buffer_count=3,
        queue=False,
        main={"size": (1640, 1232), "format": "RGB888"}))
picam1.start()

picam2 = Picamera2(1)
picam2.options["quality"] = 60
picam2.configure(picam2.create_video_configuration(
        buffer_count=3,
        queue=False,
        main={"size": (1640, 1232), "format": "RGB888"}))
picam2.start()

time.sleep(2)

device_ids = ['camera1', 'camera2']


def udp_client():
    global connectedDevices
    try:
        while True:
            frame1 = picam1.capture_array()
            frame1_resized = cv2.resize(frame1, (320, 240))
            _, buffer1 = cv2.imencode(".jpg", frame1_resized)
            sock.sendto(buffer1.tobytes(), ('192.168.0.138', 7000))
            connectedDevices[device_ids[0]] = {'image': buffer1.tobytes()}

            frame2 = picam2.capture_array()
            frame2_resized = cv2.resize(frame2, (320, 240))
            _, buffer2 = cv2.imencode(".jpg", frame2_resized)
            sock.sendto(buffer2.tobytes(), ('192.168.0.138', 7000))
            connectedDevices[device_ids[1]] = {'image': buffer2.tobytes()}

    except KeyboardInterrupt:
        print("stop")

    finally:
        picam1.stop()
        picam2.stop()
        sock.close()

class StreamHandler(tornado.web.RequestHandler):
    @tornado.gen.coroutine
    def get(self, slug):
        self.set_header('Cache-Control', 'no-store, no-cache, must-revalidate, >
        self.set_header('Pragma', 'no-cache')
        self.set_header('Content-Type', 'multipart/x-mixed-replace;boundary=--j>
        self.set_header('Connection', 'close')

        while True:
            client = connectedDevices.get(slug, None)
            if client is None:
                self.write("Device not found!")
                return

            jpgData = client.get('image', None)
            if jpgData is None:
                continue


            self.write(b"--jpgboundary\r\n")
            self.write(b"Content-type: image/jpeg\r\n")
            self.write(f"Content-length: {len(jpgData)}\r\n\r\n".encode())
            self.write(jpgData)
            yield self.flush()


class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        deviceIds = [str(d) for d in connectedDevices]
        self.write("""

<html>
<head>
<title>Picamera2 MJPEG Streaming Demo</title>
<style>
  body {
    background: black;
    margin: 0;
    display: flex;
    justify-content: center;
    align-items: center;
    height: 100vh;
    overflow: hidden;
  }
  .container {
    display: flex;
    justify-content: space-between;
    align-item: center;
    width: 80%;
    height: 80%;
  }
  img {
    flex: 1;
    width: 50%;
    height: 100%;
    object-fit: cover;
    margin: 0;
  }
  #stream1 {
    transform: rotate(90deg);
  }
  #stream2 {
    transform: rotate(270deg);
  }
</style>
</head>
<body>
<div class="container">
  <img id=stream2 src="/video_feed/camera1"/>
  <img id=stream1 src="/video_feed/camera2"/>
</div>
</body>
</html>
""")


application = tornado.web.Application([
    (r"/video_feed/([^/]+)", StreamHandler),
    (r"/", IndexHandler),
])


def start_server():
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(8888)
    print("Web server started at http://localhost:8888")
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    udp_thread = threading.Thread(target=udp_client)
    udp_thread.daemon = True
    udp_thread.start()

    start_server()

