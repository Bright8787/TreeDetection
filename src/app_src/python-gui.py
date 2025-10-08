'''from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QPushButton, QLabel, QSizePolicy
)'''
from PySide6.QtCore import Qt, Slot, Signal, QThread
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QPushButton, QLabel, QSizePolicy, QTextEdit
)
from PySide6.QtGui import QImage, QPixmap
from Widgets.camera_widget import CameraWindow
from Widgets.droidcam_widget import CameraWindowDroidCam, CameraWorker
import sys
import threading
import webbrowser
import socket
import cv2
from flask import Flask, request, render_template_string

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tree Category Detection Model")
        self.resize(320, 100)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main vertical layout
        self.main_layout = QVBoxLayout()
        central_widget.setLayout(self.main_layout)

        # Top label
        top_widget = QLabel("Tree Category Detection")
        top_widget.setStyleSheet("font-size: 24px; font-weight: bold;")
        top_widget.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.main_layout.addWidget(top_widget)

        # Buttons layout
        button_layout = QHBoxLayout()
        self.button_picam = QPushButton("Connect via PI Camera")
        self.button_droidcam = QPushButton("Connect via Droid Camera")
        button_layout.addWidget(self.button_picam)
        button_layout.addWidget(self.button_droidcam)
        self.main_layout.addLayout(button_layout)

        # Connect buttons to methods
        self.button_picam.clicked.connect(self.connect_pi_camera)
        self.button_droidcam.clicked.connect(self.connect_droid_camera)
        # Info box (for messages)
        self.info_box = QTextEdit()
        self.info_box.setReadOnly(True)
        self.info_box.setPlaceholderText("Status messages will appear here...")
        self.main_layout.addWidget(self.info_box)

        self.cam_window_droid = CameraWindowDroidCam()

        # layout = QVBoxLayout()
        # self.label = QLabel("No feed yet")
        # self.label.setScaledContents(True)
        # layout.addWidget(self.label)
        # self.setLayout(layout)
        # self.main_layout.addWidget(self.label)

        # Thread + worker
        self.worker_thread = None
        self.worker = None

    # Methods for buttons
    def connect_pi_camera(self):
        print("PI Camera clicked")
        # TODO: Open Pi Camera in a new window or start stream
        # Camera feed
        self.cam_window = CameraWindow()
        self.cam_window.show()

    def log_to_gui(self, text):
        """Append text messages to the info box on the GUI."""
        self.info_box.append(text)

    def connect_droid_camera(self):

        HTML_PAGE = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Connect DroidCam</title>
            <style>
                body { font-family: sans-serif; text-align: center; margin-top: 100px; }
                input { padding: 10px; font-size: 18px; }
                button { padding: 10px 20px; font-size: 18px; margin-top: 10px; }
            </style>
        </head>
        <body>
            <h2>Enter DroidCam IP Address</h2>
            <form method="post">
                <input name="ip" placeholder="192.168.x.x" required>
                <br><button type="submit">Connect</button>
            </form>
        </body>
        </html>
        """

        app = Flask(__name__)
        self.droid_ip = None

        @app.route("/", methods=["GET", "POST"])
        def index():
            if request.method == "POST":
                ip = request.form.get("ip", "").strip()
                if ip:
                    self.droid_ip = ip
                    threading.Thread(target=self._connect_to_droidcam, args=(ip,), daemon=True).start()
                    return "<h3>✅ Connected! You can close this page now.</h3>"
            return render_template_string(HTML_PAGE)

        self.log_to_gui("🌐 Starting DroidCam setup via web interface...")
     
        def run_server():
            app.run(host="0.0.0.0", port=8080, debug=False)

        threading.Thread(target=run_server, daemon=True).start()

        # Get local IP address of Raspberry Pi
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
        except Exception:
            local_ip = socket.gethostbyname(socket.gethostname())

        # GUI feedback instead of terminal print
        message = (
            "<b>DroidCam Setup Server Started</b><br>"
            f"👉 From your phone, open: <b>http://{local_ip}:8080</b><br>"
            "Make sure both the Raspberry Pi and phone are on the same Wi-Fi.<br>"
            "After entering your DroidCam IP on the phone, the stream will appear here."
        )
        self.log_to_gui(message)
        



    def _connect_to_droidcam(self, ip):
        self.log_to_gui(f"🔗 Connecting to DroidCam at {ip} ...")
        # url = f"http://{ip}:4747/video?640x480"
        url = f"http://{ip}:4747/video"

        cap = cv2.VideoCapture(url)
        if not cap.isOpened():
            self.log_to_gui(f"❌ Could not connect to {url}")
            return
    
        cap.release()

        self.cam_window_droid.show()
        # Thread + worker
        self.thread = QThread()
        self.worker = CameraWorker(url)
        self.worker.moveToThread(self.thread)

        # Signals
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.worker.frame_ready.connect(lambda f: print("Frame emitted:", f.shape))
        self.worker.frame_ready.connect(self.update_frame)
        self.worker.frame_ready.connect(self.cam_window_droid.update_frame)

        # Start
        self.thread.start()
        self.log_to_gui("✅ Connection successful — opening camera window.")

    @Slot(object)
    def update_frame(self, frame):
        print("Updating Frame")
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        bytes_per_line = ch * w
        qt_img = QImage(rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
        self.label.setPixmap(QPixmap.fromImage(qt_img))

    def closeEvent(self, event):
        if self.worker:
            self.worker.stop()
        if self.thread:
            self.thread.quit()
            self.thread.wait()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
