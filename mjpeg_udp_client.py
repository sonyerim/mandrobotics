import socket
import cv2
import numpy as np

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('0.0.0.0', 7000))

while True:
    data, addr = sock.recvfrom(65507)
    
    np_arr = np.frombuffer(data, dtype=np.uint8)
    frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    if frame is not None:
        cv2.imshow("Received Frame", frame)

    if cv2.waitKey(1) & 0xFF == 27:
        break

sock.close()
cv2.destroyAllWindows()
