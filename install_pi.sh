#!/usr/bin/env bash
# Raspberry Pi 7" Touch Display 2 Setup Script for Weather & News Dashboard

set -e

echo "=========================================================="
echo "Installing Pi Smart Weather & News Dashboard"
echo "=========================================================="

# Update and install system dependencies
sudo apt update
sudo apt install -y python3 python3-pip python3-pygame python3-requests git

# Create virtual environment if requested
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Create config.json if missing
if [ ! -f "config.json" ]; then
    cp config.json.example config.json
    echo "Created default config.json."
fi

# Install Desktop Shortcut & Start Menu Entry
echo "Installing Desktop Shortcut & Start Menu Entry..."
mkdir -p ~/.local/share/applications
cp pi-smart-dashboard.desktop ~/.local/share/applications/
cp pi-smart-dashboard.desktop ~/Desktop/
chmod +x ~/Desktop/pi-smart-dashboard.desktop
sudo cp pi-smart-dashboard.desktop /usr/share/applications/ 2>/dev/null || true

# Install Systemd Service (Optional)
echo "Installing Systemd Service (Optional)..."
sudo cp pi-smart-dashboard.service /etc/systemd/system/
sudo systemctl daemon-reload

echo "=========================================================="
echo "Installation Complete!"
echo "To run on Pi:"
echo " - Double click the 'Smart Dashboard' icon on your desktop."
echo " - Launch from Accessories / System Start Menu."
echo " - Or enable on boot: sudo systemctl enable pi-smart-dashboard.service"
echo "=========================================================="
