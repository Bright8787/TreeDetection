# # camera_widget.py
# import cv2
# from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout
# from PySide6.QtGui import QImage, QPixmap
# from PySide6.QtCore import QTimer

# class CameraWindow(QWidget):  # QWidget instead of QMainWindow to make it inside the same window
#     def __init__(self):
#         super().__init__()

#         self.label = QLabel("Camera feed will appear here")
#         self.label.setStyleSheet("background-color: black;")  # placeholder

#         layout = QVBoxLayout()
#         layout.addWidget(self.label)
#         self.setLayout(layout)

#         # OpenCV camera
#         self.cap = cv2.VideoCapture(0)

#         # Timer to update frames
#         self.timer = QTimer()
#         self.timer.timeout.connect(self.update_frame)
#         self.timer.start(30)

#     def update_frame(self):
#         ret, frame = self.cap.read()
#         if ret:
#             rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#             h, w, ch = rgb_image.shape
#             bytes_per_line = ch * w
#             qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
#             pixmap = QPixmap.fromImage(qt_image)
#             self.label.setPixmap(pixmap)

#     def closeEvent(self, event):
#         self.cap.release()
#         super().closeEvent(event)

import sys
import cv2
from PySide6.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QImage, QPixmap
from picamera2 import Picamera2


class CameraWidget(QWidget):
    def __init__(self):
        super().__init__()

        # --- Camera Setup ---
        self.picam2 = Picamera2()
        config = self.picam2.create_preview_configuration(main={"size": (640, 480)})
        self.picam2.configure(config)
        self.picam2.start()

        # --- UI Setup ---
        self.setWindowTitle("Pi Camera Feed - PySide6")
        self.image_label = QLabel("Camera feed will appear here")
        self.image_label.setStyleSheet("background-color: black; color: white; font-size: 16px;")
        self.image_label.setAlignment(Qt.AlignCenter)

        layout = QVBoxLayout()
        layout.addWidget(self.image_label)
        self.setLayout(layout)

        # --- Timer for updating frames ---
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)  # ~30 FPS

    def update_frame(self):
        try:
            # Capture frame from PiCamera
            frame = self.picam2.capture_array()

            # Convert from BGR (OpenCV) to RGB (Qt)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Convert to QImage
            h, w, ch = rgb_frame.shape
            bytes_per_line = ch * w
            qt_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)

            # Display in QLabel
            self.image_label.setPixmap(QPixmap.fromImage(qt_image))
        except Exception:
            # Keep placeholder text if camera fails
            self.image_label.setText("⚠️ Camera feed not available")

    def closeEvent(self, event):
        # Clean up camera on exit
        self.picam2.stop()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CameraWidget()
    window.show()
    sys.exit(app.exec())
