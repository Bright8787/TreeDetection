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
        self.showFullScreen()
        # self.resize(470, 310)
        # self.adjustSize()

        self.layout = QVBoxLayout()
        self.current_overlay_text = "No tree found! Please try again!"

# ----------- HIER Züruck button-----------
        # DIESEN GESAMTEN BLOCK ERSETZEN
        # ----------- NEUE TOP-LEISTE (Logo Links, Button Rechts) START -----------

        # 1. Logo-Setup (Links)
        self.logo_label = QLabel()
        try:
            # Korrigierter Pfad: Lade das Bild aus dem 'Window'-Ordner
            logo_pixmap = QPixmap("Window/logo.png")
            # Skaliere das Bild für die obere Leiste (z.B. 50x50 Pixel)
            scaled_pixmap = logo_pixmap.scaled(50, 50, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.logo_label.setPixmap(scaled_pixmap)
            self.logo_label.setMargin(5)
        except Exception:
            # Fallback, falls das Logo nicht gefunden wird
            self.logo_label.setText("BOTANIDENT")
            self.logo_label.setStyleSheet("font-size: 14px; font-weight: bold; padding: 5px;")


        # 2. Zurück-Button-Setup (Rechts)
        self.back_button = QPushButton("↩ Zurück")
        self.back_button.clicked.connect(self.close)
        self.back_button.setStyleSheet("padding: 5px 10px; font-size: 16px; max-width: 150px;")

        # 3. Horizontales Layout zusammenstellen
        top_layout = QHBoxLayout()
        top_layout.addWidget(self.logo_label)  # Logo ist links
        top_layout.addStretch(1)               # Stretch füllt den gesamten mittleren Raum
        top_layout.addWidget(self.back_button) # Button wird nach rechts geschoben

        self.layout.addLayout(top_layout)
        # ----------- NEUE TOP-LEISTE ENDE -----------
        # ----------- HIER ENDEN -----------

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
            "background-color: rgba(0,0,0,150); color: white; padding: 10px; border-radius: 5px; margin: 5px"
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
        #btn_layout = QHBoxLayout()
        #self.show_btn = QPushButton("Show description")
        #self.show_btn.clicked.connect(self.show_description)
        #btn_layout.addWidget(self.show_btn)
        #self.layout.addLayout(btn_layout)

        model_path = os.path.join(os.path.dirname(__file__), "treeDetection.pt")
        self.model = YOLO(model_path)
        QShortcut(QKeySequence("Esc"), self, self.close)
        # self.shortcut.activated.connect(self.closeEvent)

    def show_description(self, pred_label, conf):
            """Aktualisiert den Text und steuert die Sichtbarkeit des Overlays."""

            # Nur anzeigen, wenn die Konfidenz hoch genug ist (z.B. > 0.7)
            if conf > 0.7:
                # 1. Text bestimmen
                new_text = get_flammability(pred_label.lower())

                # 2. Text nur bei Änderung aktualisieren (gut für Performance)
                if self.current_overlay_text != new_text:
                    self.overlay_label.setText(new_text)
                    self.current_overlay_text = new_text

                # 3. Das Overlay zeigen und zentrieren
                self.center_description()
                self.overlay_label.show()
            else:
                # 4. Bei niedriger Konfidenz oder keinem Ergebnis: Overlay verstecken
                # Wir setzen current_overlay_text zurück, damit beim nächsten Fund der Text aktualisiert wird
                if self.overlay_label.isVisible():
                    self.overlay_label.hide()
                self.current_overlay_text = "" # Wichtig, damit der nächste Fund erkannt wird
    def center_description(self):
        """Passt die Größe des Overlays an den Text an und zentriert es auf dem Kamerabild."""

        # Größe an Text anpassen
        self.overlay_label.adjustSize()

        parent_width = self.label.width()
        parent_height = self.label.height()
        overlay_width = self.overlay_label.width()
        overlay_height = self.overlay_label.height()

        # Positionierung: Mitte horizontal, unten vertikal
        self.overlay_label.move(
            (parent_width - overlay_width) / 2,
            # Positioniere es etwas oberhalb des unteren Randes
            parent_height - overlay_height - 10
        )
        # NICHT self.overlay_label.show() hier aufrufen, da es in show_description gesteuert wird
        
    def update_frame(self):
        frame = self.picam2.capture_array()
        # frame = cv2.rotate(frame, cv2.ROTATE_270_CLOCKWISE)
        frame = cv2.rotate(frame, cv2.ROTATE_180)
        frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)

        results = self.model.predict(frame, verbose=False)
        pred_label = results[0].names[results[0].probs.top1]  # top-1 class name
        conf = results[0].probs.top1conf.item()
        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        if(conf > 0.7):
            cv2.putText(frame_bgr, f"{pred_label} ({conf:.2f})", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        else:
            pred_label = ""

        frame = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        h, w, ch = frame.shape
        bytes_per_line = ch * w
        qt_image = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
        self.show_description(pred_label, conf)
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
