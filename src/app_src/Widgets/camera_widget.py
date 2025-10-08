from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel
from PySide6.QtCore import QTimer
from PySide6.QtGui import QImage, QPixmap
from picamera2 import Picamera2
from PySide6.QtGui import QShortcut, QKeySequence
import sys

# Camera feed window
class CameraWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pi Camera Feed")
        self.resize(470, 310)

        layout = QVBoxLayout()
        self.label = QLabel()
        layout.addWidget(self.label)
        self.setLayout(layout)

        # Initialize camera
        self.picam2 = Picamera2()
        config = self.picam2.create_preview_configuration(
            main={"format": "BGR888", "size": (470, 310)}
        )
        self.picam2.configure(config)
        self.picam2.start()

        # Timer for updating frames
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)
        QShortcut(QKeySequence("Esc"), self, self.close)
        # self.shortcut.activated.connect(self.closeEvent)

    def update_frame(self):
        frame = self.picam2.capture_array()
        h, w, ch = frame.shape
        bytes_per_line = ch * w
        qt_image = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
        self.label.setPixmap(QPixmap.fromImage(qt_image))

    def closeEvent(self, event):
        self.timer.stop()
        self.picam2.stop()
        self.picam2.close()
        del self.picam2  # ensure it's released
        event.accept()




