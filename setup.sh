
set -e

echo "==================================="
echo "  AeroControl Setup"
echo "==================================="
echo ""

# Check Python version
echo "[1/6] Checking Python version..."
python_version=$(python3 --version | awk '{print $2}')
required_version="3.10"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python 3.10+ required. Found: $python_version"
    exit 1
fi
echo "✓ Python $python_version detected"

# Install system dependencies
echo ""
echo "[2/6] Installing system dependencies..."
if command -v apt-get &> /dev/null; then
    sudo apt-get update
    sudo apt-get install -y \
        python3-pip \
        python3-dev \
        python3-opencv \
        libopencv-dev \
        wmctrl \
        xdotool \
        build-essential \
        linux-headers-$(uname -r)
    echo "✓ System dependencies installed"
else
    echo "⚠ Non-Debian system detected. Please manually install:"
    echo "  - python3-pip, python3-dev"
    echo "  - OpenCV development files"
    echo "  - wmctrl and/or xdotool"
fi

# Install Python dependencies
echo ""
echo "[3/6] Installing Python dependencies..."
pip3 install --user -r requirements.txt
echo "✓ Python dependencies installed"

# Setup uinput (optional but recommended)
echo ""
echo "[4/6] Setting up uinput (requires sudo)..."
read -p "Enable uinput for low-latency input? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Load uinput module
    sudo modprobe uinput
    
    # Make it persistent
    if ! grep -q "^uinput$" /etc/modules; then
        echo "uinput" | sudo tee -a /etc/modules
        echo "✓ uinput module will load on boot"
    fi
    
    # Install udev rules
    sudo cp 99-uinput.rules /etc/udev/rules.d/
    sudo udevadm control --reload-rules
    sudo udevadm trigger
    echo "✓ udev rules installed"
    
    # Add user to input group
    sudo usermod -a -G input $USER
    echo "✓ Added $USER to input group"
    echo "⚠ You must LOG OUT and back in for group changes to take effect"
else
    echo "⚠ Skipping uinput setup. Will use pyautogui fallback."
fi

# Install AeroControl package
echo ""
echo "[5/6] Installing AeroControl package..."
pip3 install --user -e .
echo "✓ AeroControl installed"

# Test installation
echo ""
echo "[6/6] Testing installation..."
if python3 -c "import aerocontrol; import cv2; import mediapipe" 2>/dev/null; then
    echo "✓ All imports successful"
else
    echo "❌ Import test failed. Please check error messages above."
    exit 1
fi

echo ""
echo "==================================="
echo "  Setup Complete!"
echo "==================================="
echo ""
echo "Next steps:"
echo "  1. If you enabled uinput, LOG OUT and back in"
echo "  2. Run calibration: python3 main.py --calibrate"
echo "  3. Start AeroControl: python3 main.py --debug"
echo ""
echo "For systemd auto-start:"
echo "  cp aerocontrol.service ~/.config/systemd/user/"
echo "  systemctl --user enable aerocontrol.service"
echo ""
echo "Documentation: See README.md"
EOF

chmod +x setup.sh
