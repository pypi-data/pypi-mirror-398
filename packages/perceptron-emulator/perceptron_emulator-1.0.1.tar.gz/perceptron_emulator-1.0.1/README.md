# ⚡ Perceptron Emulator

<div align="center">

![Perceptron Emulator](https://raw.githubusercontent.com/rexackermann/perceptron-emulator/main/screenshot.png)

**A stunning GUI-based perceptron emulator with physical hardware-style controls**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![PyQt6](https://img.shields.io/badge/GUI-PyQt6-green.svg)](https://www.riverbankcomputing.com/software/pyqt/)

[Features](#-features) • [Installation](#-installation) • [Usage](#-usage) • [Hardware Build](#-build-your-own-hardware) • [Documentation](#-documentation)

</div>

---

## ✨ Features

### 🎛️ **Physical-Style Interface**
- **Toggle Switches** - Tactile ON/OFF inputs with visual feedback
- **LED Indicators** - Real-time input state visualization
- **Rotary Knobs** - Smooth weight adjustment with labeled scales
- **Analog Meter** - Classic needle display for output visualization
- **Zero-Centered Design** - Intuitive top-centered zero position

### 🔧 **Dynamic Configuration**
- **Variable Grid Size** - Adjust from 2×2 to 8×8 inputs on the fly
- **Relative Sizing** - All widgets scale proportionally for perfect visibility
- **Responsive Layout** - Adapts to different screen sizes

### 💾 **Persistent Storage**
- **Auto-Save** - Weights and bias saved automatically (1s after changes)
- **XDG Compliant** - Configuration stored in `~/.config/perceptron-emulator/`
- **Named Presets** - Save, load, and manage multiple configurations
- **State Restoration** - Picks up exactly where you left off

### ⚙️ **Perceptron Logic**
Implements the classic perceptron calculation:
```
output = Σ(input_i × weight_i) + bias
```
- **16 Binary Inputs** (default 4×4 grid)
- **16 Adjustable Weights** (-30 to +30 range)
- **Bias Control** (-30 to +30 range)
- **Real-Time Calculation** - Instant visual feedback

---

## 📦 Installation

### From PyPI (Recommended)
```bash
pip install perceptron-emulator
```

### From Source
```bash
git clone https://github.com/rexackermann/perceptron-emulator.git
cd perceptron-emulator
pip install -r requirements.txt
```

---

## 🚀 Usage

### Launch the Application
```bash
# If installed via pip
perceptron-emulator

# If running from source
python main.py
```

### Controls
- **Toggle Switches** - Click to toggle inputs ON/OFF
- **Weight Knobs** - Click and drag to rotate (positive clockwise, negative counterclockwise)
- **Bias Knob** - Adjust the bias offset
- **Grid Size** - Use spinboxes at top to change dimensions
- **File Menu** - Save/Load/Delete presets (Ctrl+S, Ctrl+O)

### Keyboard Shortcuts
- `Ctrl+S` - Save current configuration as preset
- `Ctrl+O` - Load a saved preset

---

## 🔨 Build Your Own Hardware

Want to build a physical version? Check out [`HARDWARE.md`](HARDWARE.md) for:
- Complete component list (BOM)
- Circuit schematics and wiring diagrams
- Step-by-step assembly instructions
- Calibration procedures
- Troubleshooting guide

---

## 📚 Documentation

### Project Structure
```
perceptron-emulator/
├── main.py          # Main application and UI
├── logic.py         # Perceptron calculation engine
├── widgets.py       # Custom PyQt6 widgets
├── config.py        # XDG configuration management
├── HARDWARE.md      # Physical circuit build guide
├── README.md        # This file
└── requirements.txt # Python dependencies
```

### Configuration Files
- **Config**: `~/.config/perceptron-emulator/config.json`
- **Presets**: `~/.config/perceptron-emulator/presets/*.json`

### Requirements
- Python 3.9+
- PyQt6 >= 6.0.0
- NumPy >= 1.20.0

---

## 🎨 Screenshots

### Main Interface
![Main Interface](/home/rex/.gemini/antigravity/brain/efc0a404-36c1-420d-8e02-55d895446d89/uploaded_image_1766389879733.png)

*Dark-themed interface with physical-style controls and real-time output visualization*

---

## 🤝 Contributing

Contributions are welcome! Feel free to:
- Report bugs
- Suggest new features
- Submit pull requests

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👤 Author

**Rex Ackermann**

---

## 🌟 Acknowledgments

- Inspired by classic analog computing equipment
- Built with PyQt6 for cross-platform compatibility
- Designed for both education and experimentation

---

<div align="center">

**⭐ Star this repo if you find it useful! ⭐**

</div>
