#!/usr/bin/python3

# This is the same as mjpeg_server.py, but uses the h/w MJPEG encoder.

import io
import logging
import socketserver
from http import server
from threading import Condition

from picamera2 import Picamera2
from picamera2.encoders import MJPEGEncoder
from picamera2.outputs import FileOutput

from libcamera import Transform
from libcamera import Rectangle

PAGE = """\
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
  }
  .case {
    display: flex;
  .box {
    overflow: hidden;
    position: relative;
    border: 0px solid grey;

    &.hori_1 {
      width: 480px;
      height: 640px;

      img {
        position: absolute;
        left: -25%;
        transform: rotate(90deg);
        width: auto;
        height: 100%;
      }
    }
    &.hori_2 {
      width: 480px;
      height: 640px;

      img {
        position: absolute;
        left: -50%;
        transform: rotate(270deg);
        width: auto;
        height: 100%;
      }
    }

  }
}
</style>
</head>
<body>
<div class="case">
      <div class="box hori_1">
        <img src="stream1.mjpg">
      </div> 
      <div class="box hori_2">
        <img src="stream2.mjpg">
      </div> 
    </div>
</body>
</html>"""
class StreamingOutput(io.BufferedIOBase):
    def __init__(self):
        self.frame = None
        self.condition = Condition()

    def write(self, buf):
        with self.condition:
            self.frame = buf
            self.condition.notify_all()

class StreamingHandler(server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(301)
            self.send_header('Location', '/index.html')
            self.end_headers()
        elif self.path == '/index.html':
            content = PAGE.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
        elif self.path == '/stream1.mjpg':
            self.send_response(200)
            self.send_header('Age', 0)
            self.send_header('Cache-Control', 'no-cache, private')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Content-Type', 'multipart/x-mixed-replace; bounda>
            self.end_headers()
            try:
                while True:
                    with output1.condition:
                        output1.condition.wait()
                        frame = output1.frame
                    self.wfile.write(b'--FRAME\r\n')
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-Length', len(frame))
                    self.end_headers()
                    self.wfile.write(frame)
                    self.wfile.write(b'\r\n')
            except Exception as e:
                logging.warning(
                    'Removed streaming client %s: %s',
                    self.client_address, str(e))
        elif self.path == '/stream2.mjpg':
            self.send_response(200)
            self.send_header('Age', 0)
            self.send_header('Cache-Control', 'no-cache, private')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
            self.end_headers()
            try:
                while True:
                    with output2.condition:
                        output2.condition.wait()
                        frame = output2.frame
                    self.wfile.write(b'--FRAME\r\n')
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-Length', len(frame))
                    self.end_headers()
                    self.wfile.write(frame)
                    self.wfile.write(b'\r\n')
            except Exception as e:
                logging.warning(
                    'Removed streaming client %s: %s',
                    self.client_address, str(e))
        else:
            self.send_error(404)
            self.end_headers()


class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True


picam1 = Picamera2(0)
picam1.options["quality"] = 65
picam1.configure(picam1.create_video_configuration(
        buffer_count = 3,
        queue = False,
        main={"size": (1640, 1232),"format": "YUV420"},
        lores={"size": (960, 720)},
        encode="lores",
        display="lores",
        transform=Transform(rotation=90)))
output1 = StreamingOutput()
picam1.start_recording(MJPEGEncoder(), FileOutput(output1))

picam2 = Picamera2(1)
picam2.options["quality"] = 65
picam2.configure(picam2.create_video_configuration(
        buffer_count = 3,
        queue = False,
        main={"size": (1640, 1232),"format": "YUV420"},
        lores={"size": (960, 720)},
        encode="lores",
        display="lores",
        transform=Transform(rotation=270)))
output2 = StreamingOutput()
picam2.start_recording(MJPEGEncoder(), FileOutput(output2))

try:
    address = ('', 8000)
    server = StreamingServer(address, StreamingHandler)
    server.serve_forever()
finally:
    picam1.stop_recording()
    picam2.stop_recording()

