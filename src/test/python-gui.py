from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QSizePolicy
import sys
from PySide6.QtCore import Qt
from Widgets.camera_widget import CameraWindow
app = QApplication(sys.argv)

window = QMainWindow()
window.setWindowTitle("Tree Category Detection Model")
window.resize(800, 600)

# Central widget
central_widget = QWidget()
window.setCentralWidget(central_widget)

# Main vertical layout
main_layout = QVBoxLayout()
central_widget.setLayout(main_layout)

# Top widget (label)
top_widget = QLabel("Tree Category Detection")
top_widget.setStyleSheet("font-size: 24px; font-weight: bold;")
top_widget.setAlignment(Qt.AlignmentFlag.AlignHCenter)
main_layout.addWidget(top_widget)


# Camera feed
camera_widget = CameraWindow()
camera_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
main_layout.addWidget(camera_widget, stretch=1)  # stretch=1 makes it take remaining space

# Buttons layout
button_layout = QHBoxLayout()
button_picam = QPushButton("Connect via PI Camera")
button_droidcam = QPushButton("Connect via Droid Camera")
button_layout.addWidget(button_picam)
button_layout.addWidget(button_droidcam)

main_layout.addLayout(button_layout)



window.show()
sys.exit(app.exec())
