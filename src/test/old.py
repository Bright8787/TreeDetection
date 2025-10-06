import cv2
from ultralytics import YOLO
from pathlib import Path
# Load YOLO11n pretrained detection model
model = YOLO("yolo11n.pt")
cap = cv2.VideoCapture(0)  # 0 = default camera
# Run real-time detection on webcam

# Define GStreamer pipeline for output (UDP to client IP)
gst_str = "appsrc ! videoconvert ! x264enc tune=zerolatency bitrate=800 speed>"

# Replace host IP above with your laptop’s IP address
out = cv2.VideoWriter(gst_str, cv2.CAP_GSTREAMER, 0, 20.0, (640, 480), True)

if not out.isOpened():
    print("Cannot open camera")
    exit()

while True:
    ret, frame = cap.read()
    if not ret:
        break

    results = model.predict(source=0, show=True, conf=0.5)
    annotated_frame = results[0].plot()
    out.imshow("YOLO Detection", annotated_frame)
    if out.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
out.destroyAllWindows()

