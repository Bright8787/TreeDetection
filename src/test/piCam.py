import cv2
from ultralytics import YOLO # or your YOLOv5/yolov8 import

# Initialize YOLO model
model = YOLO("yolov8n.pt") # small model for Pi

# Open Pi camera
# Use CAP_V4L2 for better compatibility with Pi Camera on modern Pis
cap = cv2.VideoCapture(0, cv2.CAP_V4L2)

# --- Check if camera opened successfully ---
if not cap.isOpened():
    print("Error: Could not open camera.")
    exit()

# Set desired frame size (optional, but good practice)
# You might want to match this to what the camera is configured for, 
# or the default size used by your model/YOLO plot function.
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# Create a window to display the output
cv2.namedWindow("YOLO Detection", cv2.WINDOW_AUTOSIZE)

while True:
    ret, frame = cap.read()
    if not ret:
        print("Error: Could not read frame.")
        break

    # Run YOLO detection
    # Using 'stream=True' can be beneficial for performance
    results = model(frame, stream=True, verbose=False) 
    
    # Get the annotated frame (with bounding boxes drawn)
    # The plot() method returns an image array (numpy array)
    annotated_frame = results[0].plot() 

    # --- Display the annotated frame locally on the Pi's screen ---
    cv2.imshow("YOLO Detection", annotated_frame)

    # Exit when 'q' key is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# --- Cleanup ---
cap.release()
cv2.destroyAllWindows()
