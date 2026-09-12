# TreeDetection (BotanIdent)

A Raspberry Pi 5 desktop application that identifies tree species from a live camera feed and estimates the tree's flammability. It runs full-screen on an LCD touchscreen and uses a YOLO model trained to classify four species: **Pinus**, **Quercus**, **Arbutus**, **Pyracantha** and **Viburnum**.

## How it works

1. A camera feed (Raspberry Pi Camera via Picamera2, or a phone camera via DroidCam over Wi-Fi) is streamed into the GUI.
2. Each frame is run through a custom-trained YOLO classification model ([treeDetection.pt](src/app_src/Widgets/treeDetection.pt)).
3. When the model's top prediction confidence exceeds `0.7`, the detected species and confidence are overlaid on the video.
4. A flammability index (1–5) is computed from per-species factors (volatile oils, surface-to-volume ratio, density) and shown as a color-coded gauge next to the video.

## Project structure

```
src/
  app_src/
    python-gui.py          # Main window: entry point, camera source selection, DroidCam pairing
    run.sh / run_me.sh      # Launch scripts (activate venv, start GUI)
    Widgets/
      camera_widget.py      # Pi Camera feed window, YOLO inference, flammability gauge UI
      droidcam_widget.py    # DroidCam feed window + capture/detect flow, background stream worker
      treeDetection.pt      # Trained YOLO classification model weights
    Window/
      Main.qml, logo.png    # QML/logo assets
requirement.txt             # Full pip freeze from the Raspberry Pi environment
```

## Requirements

- Raspberry Pi 5 with Raspberry Pi OS
- Pi Camera Module (via `picamera2`)
- Python 3 with a virtual environment containing the packages in [requirement.txt](requirement.txt) — key ones: `PySide6`, `ultralytics`, `opencv-python`, `picamera2`, `flask`, `torch`

## Running the app

On the Raspberry Pi, with the virtual environment set up (The path is hardcoded and should be adjusted):

```bash
cd src/app_src
./run_venv.sh
# or
./run_me.sh
```

This launches the full-screen GUI, from which you can choose to connect via the Pi Camera or pair a phone as a DroidCam source (the app spins up a small local web page for entering the phone's DroidCam IP address).

## Controls

- **Esc** — close the active camera window
- **↩ Zurück** button — return to the main menu from the Pi Camera view
- **📸 Capture and Detect** / **▶ Continue Stream** — in the DroidCam view, freeze a frame to run detection, then resume the live stream

## Tree species and flammability

| Species | Relative flammability |
|---|---|
| Pinus | Very high — resin and needles ignite easily |
| Pyracantha | High — dense, resinous growth burns quickly |
| Arbutus | Moderate — waxy leaves, fissured bark |
| Quercus | Low to moderate — safe choice in green condition |
| Viburnum | Low — excellent for fire protection |
The flammability index is computed as `F = k * (V * S) / (sqrt(M) * D)`, where `V` (volatile oils), `S` (surface-to-volume ratio), and `D` (density) are per-species constants and `M` is moisture (see [camera_widget.py](src/app_src/Widgets/camera_widget.py)).
