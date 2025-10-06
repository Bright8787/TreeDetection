
from picamera2 import Picamera2
import cv2
import time
from ultralytics import YOLO

model = YOLO("yolov8n.pt")

picam2 = Picamera2()
fps = 60
frame_us_us = int(1_000_000 / fps)
config = picam2.create_preview_configuration(
main={"size": (470,320)}, controls = {"FrameDurationLimits": (frame_us_us, frame_us_us)})
picam2.configure(config)
picam2.start()

while True:
    frame = picam2.capture_array()
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)
    results = model.predict(frame_rgb, conf=0.8)
    annotated_frame = results[0].plot()
    cv2.imshow("Pi Camera", annotated_frame) 	
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

picam2.stop()
cv2.destroyAllWindows()
