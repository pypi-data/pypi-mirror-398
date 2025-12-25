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

## Features

### Hardware-Style Interface
- **Realistic toggle switches** for binary inputs with satisfying click animations
- **Glowing LED indicators** that respond to input states
- **Rotary potentiometer knobs** for adjusting weights and bias (±1 range)
- **Analog meter** displaying the perceptron's output value
- **Configurable knob sizes** (Small/Medium/Large/XLarge) for optimal display on any grid size
- **Scrollable, adaptive UI** that works on any screen size

### Perceptron Logic
- Adjustable grid size from **2×2 to 8×8** (including non-square grids like 2×4, 4×2, etc.)
- Real-time computation and visualization
- Interactive weight and bias adjustment
- Visual feedback through LED indicators and analog meter
- Automatic state saving and loading

### Training Mode
- **Automatic training** with visual progress tracking
- Pre-defined patterns: **AND**, **OR**, **NAND**
- **Pattern Library** with 100+ preset shapes:
  - Works for ALL grid sizes (2×2 to 8×8, including non-square)
  - Visual previews for every pattern
  - Individual +/- labeling for positive/negative examples
  - Categories: Letters, Numbers, Shapes, Arrows, Basic patterns
- **Save/Load custom pattern sets** for reuse
- Adjustable learning rate (0.01 to 1.0)
- Real-time error and weight evolution plots
- Step-by-step or continuous training modes
- Weights and bias saved automatically (1s after changes)
- **XDG Compliant** - Configuration stored in `~/.config/perceptron-emulator/`
- **Named Presets** - Save, load, and manage multiple configurations
- **State Restoration** - Picks up exactly where you left off

### ⚙️ **Perceptron Logic**
Implements the classic perceptron calculation:
```
output = Σ(input_i × weight_i) + bias
```
- **Up to 64 Binary Inputs** (2×2 to 8×8 grid)
- **Adjustable Weights** (-1 to +1 range)
- **Bias Control** (-1 to +1 range)
- **Real-Time Calculation** - Instant visual feedback

### 🎓 **Automatic Training Mode**
- **Predefined Patterns**: AND, OR, NAND logic gates
- **Custom Pattern Recognition**: Train on YOUR shapes (T vs J, + vs -, etc.)
- **Real-Time Visualization**: 
  - Error plot showing convergence
  - Weight evolution trajectories
- **Delta Rule Learning**: Classic perceptron algorithm
- **Adjustable Learning Rate**: 0.01 to 0.50
- **Live Updates**: Watch knobs rotate as weights adjust

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

### Training Mode

#### Predefined Patterns (AND, OR, NAND)
1. Select pattern from dropdown
2. Adjust learning rate (0.01-0.50)
3. Click "Start Training"
4. Watch convergence in real-time

#### Custom Pattern Recognition 🎨 NEW!
Train the perceptron to recognize YOUR shapes:

**Example: T vs J Recognition**
```
1. Select "CUSTOM" from pattern dropdown
2. Draw a T shape using toggle switches:
   [1][1][1][0]
   [0][1][0][0]
   [0][1][0][0]
   [0][0][0][0]
3. Click "Add as Positive (+)" (green button)
4. Repeat with 3-5 variations of T
5. Draw a J shape:
   [0][1][1][0]
   [0][0][1][0]
   [0][0][1][0]
   [1][1][0][0]
6. Click "Add as Negative (-)" (red button)
7. Repeat with 3-5 variations of J
8. Click "Start Training"
9. Watch the perceptron learn to distinguish T from J!
```

**Other Pattern Ideas:**
- + vs - (plus vs minus)
- L vs I (letters)
- Vertical vs Horizontal lines
- Any two distinct shapes!

**Tips:**
- Add 3-5 examples of each type for better learning
- Make patterns clearly different
- Use "Clear All Patterns" to start over

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

## 🎓 How Training Works

### The Perceptron Learning Algorithm

The perceptron learns through **supervised learning** using the **delta rule**:

```
For each training pattern:
  1. Calculate output = Σ(input_i × weight_i) + bias
  2. Compare output to target (expected value)
  3. If wrong, adjust weights:
     - weight_i = weight_i + η × error × input_i
     - bias = bias + η × error
     - where error = (target - predicted)
```

### Training Patterns

**Important**: You train on **ALL possible input combinations**, not just one pattern!

#### Example: 2x2 Grid (4 inputs) AND Pattern

The trainer generates **16 total patterns** (2^4 combinations):

| Inputs | Target | Type |
|--------|--------|------|
| [0,0,0,0] | 0 | Negative example |
| [1,0,0,0] | 0 | Negative example |
| [0,1,0,0] | 0 | Negative example |
| ... (12 more) | 0 | Negative examples |
| [1,1,1,1] | 1 | **Positive example** |

**Pattern Breakdown:**
- **AND**: 15 negative (output 0) + 1 positive (output 1) = All inputs must be ON
- **OR**: 1 negative (output 0) + 15 positive (output 1) = Any input ON
- **NAND**: 15 positive (output 1) + 1 negative (output 0) = NOT all inputs ON

### Training Process

1. **Select Pattern**: Choose AND, OR, or NAND
2. **Set Learning Rate** (η): Controls how fast weights change
   - Low (0.01-0.05): Slow, stable learning
   - Medium (0.10-0.20): Balanced
   - High (0.30-0.50): Fast but may oscillate

3. **Training Loop**: For each epoch:
   - Test ALL patterns (e.g., all 16 for 2x2 grid)
   - Count errors (misclassified patterns)
   - Update weights for each wrong prediction
   - Plot error count

4. **Convergence**: Training stops when:
   - All patterns are correctly classified (0 errors), OR
   - Maximum epochs reached (1000)

### Grid Size Impact

| Grid | Inputs | Patterns | Complexity |
|------|--------|----------|------------|
| 2x2 | 4 | 16 | Fast (~20-50 epochs) |
| 3x3 | 9 | 512 | Moderate (~50-200 epochs) |
| 4x4 | 16 | 65,536 | Slow (may not converge) |

**Note**: Larger grids have exponentially more patterns (2^n), making training slower.

### Visualizations

**Error Plot Tab**: Shows convergence progress
- X-axis: Epoch number
- Y-axis: Number of misclassified patterns
- Goal: Reach 0 errors (green line)

**Weight Evolution Tab**: Shows individual weight trajectories
- Each colored line = one weight's journey
- Watch weights adjust to find the decision boundary
- Final values determine the learned function

### Example Training Session

```
1. Set grid to 2x2 (4 inputs, 16 patterns)
2. Select "AND" pattern
3. Set learning rate to 0.10
4. Click "Start Training"
5. Observe:
   - Epoch counter increasing
   - Error count decreasing
   - Knobs rotating to new values
   - Weight evolution plot showing convergence
6. After ~30 epochs: "Status: Converged ✓"
7. Test manually: Toggle all 4 switches ON → output should be high
```

### Why It Works

The perceptron finds a **linear decision boundary** that separates positive from negative examples:

- **AND**: Boundary requires ALL inputs active
- **OR**: Boundary requires ANY input active  
- **NAND**: Boundary is the inverse of AND

The weights determine the boundary's position and orientation, while the bias shifts it.

## 🎨 Screenshots

### Main Interface
![Main Interface](https://raw.githubusercontent.com/rexackermann/perceptron-emulator/main/screenshot.png)

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
