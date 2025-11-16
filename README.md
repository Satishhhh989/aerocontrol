# AeroControl

**Hand Gesture Mouse Control for Linux**

AeroControl is a production-ready Python application that transforms hand gestures captured via webcam into real mouse movements and desktop-switching actions on Linux. It features adaptive smoothing, velocity-based cursor control, and robust gesture recognition.

## Features

- **Natural Cursor Control**: Index finger controls cursor with adaptive smoothing based on hand distance
- **Gesture Recognition**:
  - Pinch (thumb + index): Left click
  - Two-finger pinch: Right click
  - Pinch + drag: Mouse drag
  - Spread fingers: Zoom (mouse wheel)
  - Four-finger swipe: Switch desktop/workspace
  - Palm open: Pause cursor
- **Adaptive Smoothing**: Automatically adjusts smoothing based on hand-to-camera distance
- **Velocity Control**: Non-linear sensitivity curve for precise control
- **Low Latency**: < 50ms end-to-end on mid-range hardware
- **Privacy-First**: All processing happens locally on-device

## System Requirements

- **OS**: Linux (Ubuntu 20.04+, Debian 11+, or compatible)
- **Python**: 3.10 or newer
- **Hardware**: Webcam, recommended 30 FPS or higher
- **Window Manager**: X11-based (GNOME, KDE, XFCE, etc.)

## Installation

### Quick Install
```bash
# Clone the repository
git clone https://github.com/yourusername/aerocontrol.git
cd aerocontrol

# Run setup script
chmod +x setup.sh
./setup.sh
```

### Manual Installation
```bash
# Install system dependencies (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install -y python3-pip python3-dev
sudo apt-get install -y libopencv-dev python3-opencv
sudo apt-get install -y wmctrl xdotool  # For desktop switching

# Install Python dependencies
pip3 install -r requirements.txt

# Install the package
pip3 install -e .
```

### Optional: Enable uinput (Recommended)

For low-level HID event injection (better performance):
```bash
# Load uinput kernel module
sudo modprobe uinput

# Make it persistent
echo "uinput" | sudo tee -a /etc/modules

# Set up udev rules (allows non-root access)
sudo cp 99-uinput.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules
sudo udevadm trigger

# Add yourself to the input group
sudo usermod -a -G input $USER

# Log out and back in for group changes to take effect
```

## Usage

### Basic Usage
```bash
# Start with debug overlay
python3 main.py --debug

# Start in headless mode (no UI, logs only)
python3 main.py --headless

# Use custom configuration
python3 main.py --config my_config.yaml
```

### Calibration

**Important**: Run calibration for accurate cursor mapping:
```bash
python3 main.py --calibrate
```

Follow the on-screen instructions to point at each corner of your screen. Press SPACE to confirm each point.

### Configuration

Edit `config.yaml` to customize behavior:
```yaml
camera:
  width: 640
  height: 480
  fps: 30

smoother:
  alpha_base: 0.3        # Base smoothing (lower = more smooth)
  alpha_min: 0.1         # Min smoothing (far hand)
  alpha_max: 0.7         # Max smoothing (near hand)

gestures:
  pinch_threshold: 40    # Distance for pinch detection (pixels)
  swipe_min_distance: 100  # Minimum swipe distance
  swipe_min_velocity: 200  # Minimum swipe speed
```

### Systemd Service (Auto-start)

To run AeroControl at login:
```bash
# Copy service file
cp aerocontrol.service ~/.config/systemd/user/

# Enable and start
systemctl --user enable aerocontrol.service
systemctl --user start aerocontrol.service

# Check status
systemctl --user status aerocontrol.service
```

## Gestures Guide

| Gesture | Action | How To |
|---------|--------|--------|
| Point | Move cursor | Extend index finger, move hand |
| Pinch | Left click | Touch thumb and index finger together |
| Two-finger pinch | Right click | Touch thumb and middle finger |
| Pinch + hold | Drag | Pinch and move hand |
| Spread fingers | Zoom | Spread all fingers apart |
| Four-finger swipe ↑ | Previous desktop | Four fingers together, swipe up |
| Four-finger swipe ↓ | Next desktop | Four fingers together, swipe down |
| Open palm | Pause | Open hand flat |

## Troubleshooting

### Camera Not Found
```bash
# List available cameras
ls /dev/video*

# Try a different camera index
python3 main.py --camera 1
```

### Permission Denied (uinput)

If you see permission errors:
```bash
# Check uinput permissions
ls -l /dev/uinput

# Should show: crw-rw---- 1 root input

# Ensure you're in the input group
groups | grep input

# If not, add yourself and re-login
sudo usermod -a -G input $USER
```

### Fallback Mode (No uinput)

AeroControl automatically falls back to `pyautogui` + `wmctrl/xdotool` if uinput is unavailable. Install fallback tools:
```bash
sudo apt-get install wmctrl xdotool
pip3 install pyautogui
```

### Low FPS / High Latency
```bash
# Reduce camera resolution
python3 main.py --config low_res_config.yaml

# In config file:
# camera:
#   width: 320
#   height: 240
#   fps: 15
```

### Cursor Too Jittery

Increase smoothing in `config.yaml`:
```yaml
smoother:
  alpha_base: 0.2  # Lower = more smoothing
  alpha_min: 0.05
```

### Desktop Switching Not Working

Ensure a desktop tool is installed:
```bash
# Check which is available
which wmctrl
which xdotool

# Install if missing
sudo apt-get install wmctrl xdotool
```

## Testing

Run the test suite:
```bash
# Install test dependencies
pip3 install pytest

# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_smoother.py -v

# Run with coverage
pytest --cov=aerocontrol tests/
```

## Performance Tuning

### For Low-End Hardware
```yaml
camera:
  width: 320
  height: 240
  fps: 15

smoother:
  alpha_base: 0.4  # Less smoothing = less computation
```

### For High-Precision Work
```yaml
camera:
  width: 1280
  height: 720
  fps: 60

smoother:
  alpha_base: 0.2
  alpha_min: 0.05
  alpha_max: 0.8
```

## Development

### Project Structure
aerocontrol/
├── aerocontrol/        # Main package
│   ├── capture.py      # Camera capture
│   ├── detector.py     # Hand detection (MediaPipe)
│   ├── tracker.py      # Hand tracking
│   ├── gesture.py      # Gesture recognition
│   ├── smoother.py     # Adaptive smoothing
│   ├── hidemitter.py   # HID event emission
│   ├── calibrate.py    # Calibration wizard
│   ├── ui_debug.py     # Debug UI
│   ├── cli.py          # CLI interface
│   └── main.py         # Main controller
├── tests/              # Test suite
├── config.yaml         # Configuration
└── README.md          # This file

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## FAQ

**Q: Does this work on Wayland?**  
A: Desktop switching may have limited support on Wayland. Mouse control works via pyautogui fallback.

**Q: Can I use this without calibration?**  
A: Yes, but cursor accuracy will be reduced. Calibration is highly recommended.

**Q: How much CPU does it use?**  
A: Approximately 5-15% on a modern quad-core CPU at 30 FPS.

**Q: Is my camera data sent anywhere?**  
A: No. All processing is local. No network calls are made.

**Q: Can I customize gestures?**  
A: Yes, edit thresholds in `config.yaml` or modify `gesture.py` for custom gestures.

## License

MIT License - see LICENSE file for details.

## Acknowledgments

- Built with [MediaPipe](https://mediapipe.dev/) for hand tracking
- Uses [OpenCV](https://opencv.org/) for camera capture
- Desktop control via `wmctrl` and `xdotool`

## Support

For issues, questions, or feature requests, please open an issue on GitHub or check the [troubleshooting guide](#troubleshooting).

---

**Made with ❤️ for the Linux community**