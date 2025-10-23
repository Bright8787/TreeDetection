from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QSizePolicy, QPushButton, QHBoxLayout
from PySide6.QtCore import QTimer, Qt, QObject, Signal, Slot
from PySide6.QtGui import QImage, QPixmap, QKeySequence, QShortcut
import cv2
from ultralytics import YOLO
import os

'''class CameraWindowDroidCam(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DroidCam Feed")
        # initialise Model
        model_path = os.path.join(os.path.dirname(__file__), "treeDetection.pt")
        self.model = YOLO(model_path)

        layout = QVBoxLayout(self)
        self.label = QLabel("Waiting for feed...")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setScaledContents(False)  # Keep aspect ratio instead of stretching

        layout.addWidget(self.label)
        self.setLayout(layout)
        self.resize(200, 200)               # default starting size
        self.setMaximumSize(200, 200)       # don't let it grow too big

    @Slot(object)
    def update_frame(self, frame):
        """Receive frame from worker and show on QLabel."""

        results = self.model.predict(frame, verbose=False)
        pred_label = results[0].names[results[0].probs.top1]  # top-1 class name
        conf = results[0].probs.top1conf.item()

        # Draw prediction text
        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        frame_bgr = cv2.resize(frame_bgr, (480, 320))  # same as your window size
        cv2.putText(frame_bgr, f"{pred_label} ({conf:.2f})", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        # rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = frame_bgr.shape
        bytes_per_line = ch * w
        qt_img = QImage(frame_bgr.data, w, h, bytes_per_line, QImage.Format_RGB888)
        self.label.setPixmap(QPixmap.fromImage(qt_img))
'''

class CameraWindowDroidCam(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DroidCam Feed")

        # --- Load YOLO model ---
        model_path = os.path.join(os.path.dirname(__file__), "treeDetection.pt")
        self.model = YOLO(model_path)

        # --- Layout setup ---
        #layout = QVBoxLayout(self)
        # --- Layout setup ---
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(4)


        # --- Buttons layout at top-left ---
        btn_layout = QHBoxLayout()
        btn_layout.setAlignment(Qt.AlignLeft)  # 🔹 ensure top-left alignment
        self.capture_btn = QPushButton("📸 Capture and Detect")
        self.capture_btn.clicked.connect(self.capture_frame)
        btn_layout.addWidget(self.capture_btn)

        self.resume_btn = QPushButton("▶ Continue Stream")
        self.resume_btn.clicked.connect(self.resume_stream)
        self.resume_btn.setVisible(False)
        btn_layout.addWidget(self.resume_btn)


        layout.addLayout(btn_layout)

        # Live feed display
        self.label = QLabel("Waiting for feed...")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.label.setScaledContents(True)
        layout.addWidget(self.label)

        # Buttons
        #btn_layout = QHBoxLayout()
        #self.capture_btn = QPushButton("📸 Capture and Detect")
        #self.capture_btn.clicked.connect(self.capture_frame)
        #btn_layout.addWidget(self.capture_btn)

        #self.resume_btn = QPushButton("▶ Continue Stream")
        #self.resume_btn.clicked.connect(self.resume_stream)
        #self.resume_btn.setVisible(False)  # hidden until paused
        #btn_layout.addWidget(self.resume_btn)



        # Detection result label
        self.result_label = QLabel("")
        self.result_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.result_label)

        self.setLayout(layout)
        #self.resize(480, 320)
        #self.setMinimumSize(320, 240)
        #self.setMaximumSize(800, 480)  # optional limit for small displays

        screen = self.screen().availableGeometry()
        self.resize(screen.width() * 0.6, screen.height() * 0.6)
        self.setMinimumSize(320, 240)

        # --- Internal state ---
        self.current_frame = None
        self.frozen = False

    @Slot(object)
    def update_frame(self, frame):
        """Show the live feed only if not frozen."""
        if self.frozen:
            return
        self.current_frame = frame
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        qt_img = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
        self.label.setPixmap(QPixmap.fromImage(qt_img))

    @Slot()
    def capture_frame(self):
        """Freeze stream and run YOLO once on current frame."""
        if self.current_frame is None:
            self.result_label.setText("❌ No frame to capture yet.")
            return

        # Freeze live feed
        self.frozen = True
        self.capture_btn.setEnabled(False)
        self.resume_btn.setVisible(True)
        self.result_label.setText("🔍 Detecting...")

        # Run YOLO detection
        results = self.model.predict(self.current_frame, verbose=False)
        if not results:
            self.result_label.setText("No detections.")
            return

        # Draw bounding boxes and labels
        annotated_frame = results[0].plot()  # ultralytics utility draws all boxes
        rgb_annotated = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_annotated.shape
        qt_img = QImage(rgb_annotated.data, w, h, ch * w, QImage.Format_RGB888)
        self.label.setPixmap(QPixmap.fromImage(qt_img))

        # Display prediction summary (best class + confidence)
        try:
            pred_label = results[0].names[results[0].probs.top1]
            conf = results[0].probs.top1conf.item()
            self.result_label.setText(f"✅ {pred_label} ({conf:.2f})")
        except Exception:
            self.result_label.setText("✅ Detection complete")

    @Slot()
    def resume_stream(self):
        """Unfreeze and continue showing live video feed."""
        self.frozen = False
        self.capture_btn.setEnabled(True)
        self.resume_btn.setVisible(False)
        self.result_label.setText("▶ Live stream resumed.")

class CameraWorker(QObject):
    frame_ready = Signal(object)  # emits cv2 frames
    finished = Signal()

    def __init__(self, url):
        super().__init__()
        self.url = url
        self.running = True

    @Slot()
    def run(self):
        cap = cv2.VideoCapture(self.url)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 200)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 200)
        if not cap.isOpened():
            print(f"Could not open camera: {self.url}")
            self.finished.emit()
            return

        print(f"✅ Connected to {self.url}")
        while self.running:
            ret, frame = cap.read()
            if not ret:
                print("Failed to read frame")
                break
            self.frame_ready.emit(frame)

        cap.release()
        self.finished.emit()

    def stop(self):
        self.running = False
