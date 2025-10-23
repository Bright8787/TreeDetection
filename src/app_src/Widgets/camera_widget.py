from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QImage, QPixmap
from picamera2 import Picamera2
from PySide6.QtGui import QShortcut, QKeySequence
import sys
from ultralytics import YOLO
import os
import cv2
# Camera feed window
class CameraWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pi Camera Feed")
        self.resize(470, 310)
               
        layout = QVBoxLayout()
        # layout.setContentsMargins(0, 0, 0, 0)   
        # layout.setSpacing(0)        
        self.label = QLabel()
        self.label.setMargin(0)    
        layout.addWidget(self.label)
        layout.setAlignment(Qt.AlignLeft)  # 🔹 ensure top-left alignment
        self.setLayout(layout)
        # Initialize camera
        self.picam2 = Picamera2()   
        config = self.picam2.create_preview_configuration(
            main={"format": "BGR888", "size": (240, 400)}
        )
        self.picam2.configure(config)
       
        self.picam2.start()
        # Timer for updating frames
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

        model_path = os.path.join(os.path.dirname(__file__), "treeDetection.pt")
        self.model = YOLO(model_path)
        QShortcut(QKeySequence("Esc"), self, self.close)
        # self.shortcut.activated.connect(self.closeEvent)

    def update_frame(self):
        frame = self.picam2.capture_array()
        # frame = cv2.rotate(frame, cv2.ROTATE_270_CLOCKWISE)
        frame = cv2.rotate(frame, cv2.ROTATE_180)
        frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)

        results = self.model.predict(frame, verbose=False)
        pred_label = results[0].names[results[0].probs.top1]  # top-1 class name
        conf = results[0].probs.top1conf.item()

        # # Draw prediction text
        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        cv2.putText(frame_bgr, f"{pred_label} ({conf:.2f})", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        frame = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)

        h, w, ch = frame.shape
        bytes_per_line = ch * w
        qt_image = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
        self.label.setPixmap(QPixmap.fromImage(qt_image))
        self.label.setScaledContents(True)


    def closeEvent(self, event):
        self.timer.stop()
        self.picam2.stop()
        self.picam2.close()
        del self.picam2  # ensure it's released
        event.accept()




