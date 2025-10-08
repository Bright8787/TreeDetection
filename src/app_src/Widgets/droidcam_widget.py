from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import QTimer, Qt, QObject, Signal, Slot
from PySide6.QtGui import QImage, QPixmap, QKeySequence, QShortcut

import cv2


class CameraWindowDroidCam(QWidget):
    def __init__(self, url):
        super().__init__()
        self.setWindowTitle("DroidCam Feed")
        self.resize(480, 360)

        layout = QVBoxLayout()
        self.label = QLabel("Waiting for feed...")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setScaledContents(True)
        layout.addWidget(self.label)
        self.setLayout(layout)
        self.url = url

    @Slot(object)
    def update_frame(self, frame):
        """Receive frame from worker and show on QLabel."""
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        bytes_per_line = ch * w
        qt_img = QImage(rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
        self.label.setPixmap(QPixmap.fromImage(qt_img))


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