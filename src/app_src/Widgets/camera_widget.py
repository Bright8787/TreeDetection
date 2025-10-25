from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QHBoxLayout, QTextEdit
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QImage, QPixmap
from picamera2 import Picamera2
from PySide6.QtGui import QShortcut, QKeySequence
import sys
from ultralytics import YOLO
import os
import cv2

# Flammability dictionary
flammability_dict = {
    "viburnum": {
        "index": 1,
        "description": "Very low flammability. Excellent for fire-resistant landscaping."
    },
    "quercus": {
        "index": 2,
        "description": "Low to moderate flammability. Safer when green, but leaf litter can burn."
    },
    "arbutus": {
        "index": 3,
        "description": "Moderate flammability. Waxy leaves and peeling bark; spacing recommended."
    },
    "pyrancanthan": {
        "index": 4,
        "description": "High flammability. Dense, twiggy growth and oils make it burn fast."
    },
    "pinus": {
        "index": 5,
        "description": "Very high flammability. Resin and needles ignite easily; maintain wide clearance."
    }
}

# Example usage
def get_flammability(plant_type):
    info = flammability_dict.get(plant_type.lower())
    if info:
        return f"Flammability Index: {info['index']}, Description: {info['description']}"
    else:
        return "Plant type not found."



# Camera feed window
class CameraWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pi Camera Feed")
        # self.resize(470, 310)
        # self.adjustSize()
        self.layout = QVBoxLayout()
        self.current_overlay_text = ""

        # self.layout.setContentsMargins(0, 0, 0, 0)   
        # layout.setSpacing(0)        
        self.layout.setAlignment(Qt.AlignCenter)  # 🔹 ensure top-left alignment
        
        self.label = QLabel()
        self.label.setMargin(0)    
        self.label.setScaledContents(True)  # the image will fill the label
        self.layout.addWidget(self.label)

        self.setLayout(self.layout)

        self.overlay_state = False
        self.overlay_label = QLabel(self.label)
        self.overlay_label.setWordWrap(True)
        self.overlay_label.setStyleSheet(
            "background-color: rgba(0,0,0,150); color: white; padding: 10px; border-radius: 5px;"
        )

        
        # self.overlay_label.setAlignment(Qt.AlignCenter)
        self.overlay_label.hide()  # start hidden

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

        # Button Layout
        btn_layout = QHBoxLayout()
        self.show_btn = QPushButton("Show description")
        self.show_btn.clicked.connect(self.show_description)
        btn_layout.addWidget(self.show_btn)
        self.layout.addLayout(btn_layout)

        model_path = os.path.join(os.path.dirname(__file__), "treeDetection.pt")
        self.model = YOLO(model_path)
        QShortcut(QKeySequence("Esc"), self, self.close)
        # self.shortcut.activated.connect(self.closeEvent)

    def show_description(self):

        if(not self.overlay_state): 
            frame = self.picam2.capture_array()
            #cv2.ROTATE_270_CLOCKWISE
            frame = cv2.rotate(frame, cv2.ROTATE_180)
            frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)

            results = self.model.predict(frame, verbose=False)
            pred_label = results[0].names[results[0].probs.top1]  # top-1 class name
            conf = results[0].probs.top1conf.item()

            if(conf < 0.9):
                self.overlay_label.setText("No tree found! Please try again!")
            else: 
                # self.overlay_label.setText(get_flammability("pyracantha"))
                self.overlay_label.setText(get_flammability(pred_label.lower()))

            self.adjustSize()
            self.center_description()
            self.overlay_state = True
            # self.current_overlay_text = get_flammability(pred_label.lower())
            self.show_btn.setText("Close description")
        else: 
            self.overlay_label.hide()
            self.show_btn.setText("Show description")
            # self.current_overlay_text = ""
            self.overlay_state = False


    def center_description(self):

        self.overlay_label.adjustSize()
        parent_width = self.label.width()
        parent_height = self.label.height()
        overlay_width = self.overlay_label.width()
        overlay_height = self.overlay_label.height()
        self.overlay_label.move(
            (parent_width - overlay_width) / 2,
            (parent_height - overlay_height) / 2
        )

        # self.adjustSize()
        self.overlay_label.show()
    # with button
    def update_frame(self):
        frame = self.picam2.capture_array()
        # frame = cv2.rotate(frame, cv2.ROTATE_270_CLOCKWISE)
        frame = cv2.rotate(frame, cv2.ROTATE_180)
        frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)

        results = self.model.predict(frame, verbose=False)
        pred_label = results[0].names[results[0].probs.top1]  # top-1 class name
        conf = results[0].probs.top1conf.item()
        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        if(conf > 0.9):
            cv2.putText(frame_bgr, f"{pred_label} ({conf:.2f})", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            self.show_description()
        
        frame = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        h, w, ch = frame.shape
        bytes_per_line = ch * w
        qt_image = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
        self.label.setPixmap(QPixmap.fromImage(qt_image))
        self.label.setScaledContents(True)

    # without button 
    # def update_frame(self):
    #     frame = self.picam2.capture_array()
    #     frame = cv2.rotate(frame, cv2.ROTATE_180)
    #     frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)

    #     results = self.model.predict(frame, verbose=False)
    #     pred_label = results[0].names[results[0].probs.top1]
    #     conf = results[0].probs.top1conf.item()

    #     frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    #     if conf > 0.9:
    #         cv2.putText(frame_bgr, f"{pred_label} ({conf:.2f})", (20, 40),
    #                     cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
    #         # Only update overlay if text changed
    #         overlay_text = get_flammability(pred_label.lower())
    #         if overlay_text != self.current_overlay_text:
    #             self.overlay_label.setText(overlay_text)
    #             self.overlay_label.adjustSize()
    #             # Center or lower slightly
    #             parent_w = self.label.width()
    #             parent_h = self.label.height()
    #             overlay_w = self.overlay_label.width()
    #             overlay_h = self.overlay_label.height()
    #             self.overlay_label.move(
    #                 (parent_w - overlay_w) // 2,
    #                 int((parent_h - overlay_h) * 0.6)
    #             )
    #             self.overlay_label.show()
    #             self.overlay_state = True
    #             self.current_overlay_text = overlay_text
    #     else:
    #         # Optional: hide overlay if confidence drops
    #         if self.overlay_state:
    #             self.overlay_label.hide()
    #             self.overlay_state = False
    #             self.current_overlay_text = ""


    def closeEvent(self, event):
        self.timer.stop()
        self.picam2.stop()
        self.picam2.close()
        del self.picam2  # ensure it's released
        event.accept()




