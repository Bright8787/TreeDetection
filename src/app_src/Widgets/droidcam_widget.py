from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QImage, QPixmap, QKeySequence, QShortcut
import cv2

# DroidCam feed window
class DroidCamWindow(QWidget):
    def __init__(self, url):
        """
        url: full DroidCam URL, e.g., http://192.168.1.82:8080/video
        """
        super().__init__()
        self.setWindowTitle("DroidCam Feed")
        self.resize(470, 310)
        print("Starting")

        layout = QVBoxLayout()
        self.label = QLabel()
        layout.addWidget(self.label)
        self.setLayout(layout)

        # Initialize camera capture from URL
        self.cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
        # self.cap = cv2.VideoCapture("http://192.168.1.48:4747/video")

        if not self.cap.isOpened():
            raise RuntimeError(f"Cannot connect to DroidCam at {url}")
        # Timer for updating frames
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)  # ~33 FPS

        # Shortcut to close window
        QShortcut(QKeySequence("Esc"), self, self.close)

    def update_frame(self):
        ret, frame = self.cap.read()
        if not ret or frame is None:
            print("❌ No frame received")
            return

        print(f"✅ Got frame of shape: {frame.shape}")
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = frame.shape
        bytes_per_line = ch * w
        qt_image = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
        self.label.setPixmap(QPixmap.fromImage(qt_image))

    def closeEvent(self, event):
        self.timer.stop()
        if self.cap.isOpened():
            self.cap.release()
        event.accept()
