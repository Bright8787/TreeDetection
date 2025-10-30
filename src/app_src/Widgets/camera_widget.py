from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QHBoxLayout, QTextEdit
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QImage, QPixmap
from picamera2 import Picamera2
from PySide6.QtGui import QShortcut, QKeySequence
import sys
from ultralytics import YOLO
import os
import cv2
import math

# NEUE DATENSTRUKTUR: Faktoren für die Brennbarkeitsformel
# V = Volatile Öle, S = Surface-to-Volume, D = Dichte
FLAMMABILITY_FACTORS = {
    "viburnum": {
        "V": 0.1, "S": 0.5, "D": 0.6,
        "description": "Sehr geringe Brennbarkeit. Hervorragend geeignet für den Brandschutz."
    },
    "quercus": {
        "V": 0.2, "S": 0.3, "D": 0.9,
        "description": "Geringe bis moderate Brennbarkeit. Sichere Wahl im grünen Zustand."
    },
    "arbutus": {
        "V": 0.4, "S": 0.5, "D": 0.5,
        "description": "Moderate Brennbarkeit. Gewachste Blätter und rissige Rinde."
    },
    "pyrancanthan": {
        "V": 0.6, "S": 0.8, "D": 0.4,
        "description": "Hohe Brennbarkeit. Dichtes, harziges Wachstum brennt schnell."
    },
    "pinus": {
        "V": 0.9, "S": 0.7, "D": 0.3,
        "description": "Sehr hohe Brennbarkeit. Harz und Nadeln entzünden sich leicht."
    }
}
# Example usage
# NEUE FUNKTION: Berechnet den Flammbarkeits-Grad (Index und Farbe)
def calculate_flammability(plant_type, moisture=0.5, k=100):
    """
    Berechnet den Flammbarkeits-Index F basierend auf der Formel: F = k * (V * S) / (sqrt(M) * D)
    Gibt Index (1-5) und zugehörige CSS-Farbe zurück.
    """
    data = FLAMMABILITY_FACTORS.get(plant_type.lower())
    if not data:
        return 0, "#7f8c8d" # Grau für unbekannt

    V = data["V"]
    S = data["S"]
    D = data["D"]

    # Sicherstellen, dass M und D > 0 sind
    if D == 0 or moisture == 0:
         F = 100
    else:
        F = k * (V * S) / (math.sqrt(moisture) * D)

    F = min(F, 100) # Beschränken auf max. 100

    # 1. Index bestimmen und 2. Farbe zuweisen
    if F < 20: index, color = 1, "#2ecc71"  # Grün (Sehr gering)
    elif F < 40: index, color = 2, "#3498db" # Blau (Gering)
    elif F < 60: index, color = 3, "#f1c40f" # Gelb (Mittel)
    elif F < 80: index, color = 4, "#e67e22" # Orange (Hoch)
    else: index, color = 5, "#e74c3c" # Rot (Sehr hoch)

    return index, color


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


        # 2. Grad-Balken (Mitte) - HIER IST DIE KORREKTUR
        self.grade_widgets = []
        grade_layout = QHBoxLayout()
        grade_layout.setSpacing(2)

        # Erstelle 5 Labels (Kacheln) für die Grade 1 bis 5
        for i in range(1, 6):
            grade_widget = QLabel(str(i))
            grade_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
            grade_widget.setFixedSize(30, 30)
            grade_widget.setStyleSheet(
                "background-color: #34495e; color: white; font-weight: bold; border: 1px solid #7f8c8d; border-radius: 4px;"
            )
            self.grade_widgets.append(grade_widget)
            grade_layout.addWidget(grade_widget)

        # Ein Container-Widget für das zentrale Layout
        self.grade_container = QWidget()
        self.grade_container.setLayout(grade_layout)

        # 3. Zurück-Button-Setup (Rechts)
        self.back_button = QPushButton("↩ Zurück")
        self.back_button.clicked.connect(self.close)
        self.back_button.setStyleSheet("padding: 5px 10px; font-size: 16px; max-width: 150px;")

        # 4. Horizontales Layout zusammenstellen
        # 4. Horizontales Layout zusammenstellen
        top_layout = QHBoxLayout()
        top_layout.addWidget(self.logo_label)  # Links
        top_layout.addStretch(1)
        top_layout.addWidget(self.grade_container) # Grad-Balken
        top_layout.addStretch(1)
        top_layout.addWidget(self.back_button) # Rechts

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
        """Steuert die Anzeige des Overlays: Nur Anweisung bei niedriger Konfidenz, ansonsten verstecken."""

        # Schwellenwert für NICHTS gefunden
        if conf <= 0.7:
            instruction_text = "Bitte bewegen Sie die Kamera oder passen Sie den Abstand zum Baum an."

            # Text nur aktualisieren und zeigen, wenn eine Änderung vorliegt
            if self.current_overlay_text != instruction_text:
                self.overlay_label.setText(instruction_text)
                self.current_overlay_text = instruction_text

            # Zeigt das Overlay mittig an
            self.center_description()
            self.overlay_label.show()

        else:
            # Bei erfolgreicher Erkennung (conf > 0.7): Overlay ausblenden
            if self.overlay_label.isVisible():
                self.overlay_label.hide()
            # current_overlay_text zurücksetzen, damit die Anweisung beim nächsten Mal sofort angezeigt wird
            self.current_overlay_text = ""

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
            (parent_height - overlay_height) / 2
        )
        # NICHT self.overlay_label.show() hier aufrufen, da es in show_description gesteuert wird

    def update_frame(self):
            frame = self.picam2.capture_array()
            frame = cv2.rotate(frame, cv2.ROTATE_180)
            frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)

            results = self.model.predict(frame, verbose=False)
            pred_label = results[0].names[results[0].probs.top1]  # top-1 class name
            conf = results[0].probs.top1conf.item()
            frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR) # Konvertierung für CV2-Text

            flam_index = 0

            # Logik zur Grad-Anzeige und Farbmarkierung
            if conf > 0.7:
                # 1. Berechne Grad und Farbe
                flam_index, flam_color = calculate_flammability(pred_label)

                # 2. Baumname auf das Video zeichnen
                cv2.putText(frame_bgr, f"{pred_label} ({conf:.2f})", (20, 40),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            else:
                pred_label = ""

            # 3. Kacheln färben: Setze alle zurück und markiere nur den aktuellen Index (falls vorhanden)
            DEFAULT_STYLE = "background-color: #34495e; color: white; font-weight: bold; border: 1px solid #7f8c8d; border-radius: 4px;"

            for i, widget in enumerate(self.grade_widgets):
                widget_grade = i + 1 # Grade sind 1 bis 5

                if widget_grade == flam_index:
                    # Aktuellen Grad markieren (hellere Farbe, dickerer Rand)
                    widget.setStyleSheet(
                        f"background-color: {flam_color}; color: black; font-weight: bold; border: 2px solid white; border-radius: 4px;"
                    )
                else:
                    # Alle anderen Kacheln zurücksetzen
                    widget.setStyleSheet(DEFAULT_STYLE)


            frame = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB) # Korrektur für Qt-Anzeige
            h, w, ch = frame.shape
            bytes_per_line = ch * w
            qt_image = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)

            self.show_description(pred_label, conf) # Steuert die Anweisung in der Mitte

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
