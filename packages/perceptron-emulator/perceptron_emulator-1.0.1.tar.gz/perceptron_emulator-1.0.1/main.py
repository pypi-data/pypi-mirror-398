import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                              QHBoxLayout, QGridLayout, QLabel, QGroupBox, QSpinBox,
                              QMenuBar, QMenu, QInputDialog, QMessageBox)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QAction
from logic import Perceptron
from widgets import ToggleSwitch, LEDBulb, RotaryKnob, AnalogMeter
from config import ConfigManager
import numpy as np


class PerceptronEmulator(QMainWindow):
    def __init__(self, rows=4, cols=4):
        super().__init__()
        self.rows = rows
        self.cols = cols
        self.perceptron = Perceptron(rows, cols)
        
        # Initialize config manager
        self.config_manager = ConfigManager()
        
        # Auto-save timer (save 1 second after last change)
        self.autosave_timer = QTimer()
        self.autosave_timer.setSingleShot(True)
        self.autosave_timer.timeout.connect(self.autosave)
        
        self.setWindowTitle("Perceptron Emulator")
        self.setStyleSheet("background-color: #2b2b2b;")
        
        # Storage for widgets
        self.switches = []
        self.leds = []
        self.knobs = []
        
        self.initUI()
        self.createMenuBar()
        self.resize(1200, 700)
        
        # Load last saved state
        self.loadState()
    
    def initUI(self):
        # Main layout container
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Top controls for grid size
        controls_layout = QHBoxLayout()
        controls_layout.addWidget(QLabel("Grid Size:"))
        
        self.rows_spin = QSpinBox()
        self.rows_spin.setRange(2, 8)
        self.rows_spin.setValue(self.rows)
        self.rows_spin.valueChanged.connect(self.changeGridSize)
        controls_layout.addWidget(QLabel("Rows:"))
        controls_layout.addWidget(self.rows_spin)
        
        self.cols_spin = QSpinBox()
        self.cols_spin.setRange(2, 8)
        self.cols_spin.setValue(self.cols)
        self.cols_spin.valueChanged.connect(self.changeGridSize)
        controls_layout.addWidget(QLabel("Cols:"))
        controls_layout.addWidget(self.cols_spin)
        
        controls_layout.addStretch()
        main_layout.addLayout(controls_layout)
        
        # Store the main layout for rebuilding
        self.main_layout = main_layout
        self.controls_layout = controls_layout
        
        # Main panel layout (horizontal)
        panel_layout = QHBoxLayout()
        
        # Left panel - Input switches
        input_panel = self.createPanel("INPUT SWITCHES", self.createInputGrid())
        panel_layout.addWidget(input_panel)
        
        # Middle-left panel - LED indicators
        led_panel = self.createPanel("LED INDICATORS", self.createLEDGrid())
        panel_layout.addWidget(led_panel)
        
        # Middle-right panel - Weight knobs
        weight_panel = self.createPanel("WEIGHTS", self.createWeightGrid())
        panel_layout.addWidget(weight_panel)
        
        # Right panel - Bias and Meter
        bias_panel = self.createPanel("BIAS & OUTPUT", self.createBiasAndMeter())
        panel_layout.addWidget(bias_panel)
        
        main_layout.addLayout(panel_layout)
    
    def createMenuBar(self):
        """Create menu bar with save/load options."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        # Save preset
        save_action = QAction("&Save Preset...", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.savePreset)
        file_menu.addAction(save_action)
        
        # Load preset
        load_action = QAction("&Load Preset...", self)
        load_action.setShortcut("Ctrl+O")
        load_action.triggered.connect(self.loadPreset)
        file_menu.addAction(load_action)
        
        file_menu.addSeparator()
        
        # Delete preset
        delete_action = QAction("&Delete Preset...", self)
        delete_action.triggered.connect(self.deletePreset)
        file_menu.addAction(delete_action)
    
    def createPanel(self, title, content_widget):
        """Create a styled panel with title."""
        group = QGroupBox(title)
        group.setStyleSheet("""
            QGroupBox {
                background-color: #1a1a1a;
                border: 2px solid #444;
                border-radius: 8px;
                margin-top: 10px;
                padding: 15px;
                font-weight: bold;
                color: #ccc;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 5px 10px;
                background-color: #333;
                border-radius: 4px;
            }
        """)
        
        layout = QVBoxLayout()
        layout.addWidget(content_widget)
        group.setLayout(layout)
        return group
    
    def createInputGrid(self):
        """Create the grid of input toggle switches."""
        widget = QWidget()
        grid = QGridLayout()
        grid.setSpacing(10)
        
        self.switches = []
        for row in range(self.rows):
            for col in range(self.cols):
                switch = ToggleSwitch()
                index = row * self.cols + col
                switch.toggled.connect(lambda state, idx=index: self.onInputToggled(idx, state))
                grid.addWidget(switch, row, col)
                self.switches.append(switch)
        
        widget.setLayout(grid)
        return widget
    
    def createLEDGrid(self):
        """Create the grid of LED indicators."""
        widget = QWidget()
        grid = QGridLayout()
        grid.setSpacing(10)
        
        self.leds = []
        for row in range(self.rows):
            for col in range(self.cols):
                led = LEDBulb()
                grid.addWidget(led, row, col)
                self.leds.append(led)
        
        widget.setLayout(grid)
        return widget
    
    def createWeightGrid(self):
        """Create the grid of weight knobs."""
        widget = QWidget()
        grid = QGridLayout()
        grid.setSpacing(15)
        
        self.knobs = []
        for row in range(self.rows):
            for col in range(self.cols):
                knob = RotaryKnob(min_value=-30.0, max_value=30.0)
                index = row * self.cols + col
                knob.valueChanged.connect(lambda val, idx=index: self.onWeightChanged(idx, val))
                grid.addWidget(knob, row, col)
                self.knobs.append(knob)
        
        widget.setLayout(grid)
        return widget
    
    def createBiasAndMeter(self):
        """Create the bias knob and output meter."""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Bias knob
        bias_label = QLabel("BIAS")
        bias_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bias_label.setStyleSheet("color: #ccc; font-weight: bold;")
        layout.addWidget(bias_label)
        
        self.bias_knob = RotaryKnob(min_value=-30.0, max_value=30.0)
        self.bias_knob.valueChanged.connect(self.onBiasChanged)
        layout.addWidget(self.bias_knob, alignment=Qt.AlignmentFlag.AlignCenter)
        
        layout.addSpacing(30)
        
        # Output meter
        meter_label = QLabel("OUTPUT")
        meter_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        meter_label.setStyleSheet("color: #ccc; font-weight: bold;")
        layout.addWidget(meter_label)
        
        self.meter = AnalogMeter(min_value=-100.0, max_value=100.0)
        layout.addWidget(self.meter, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Value display
        self.value_label = QLabel("0.00")
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.value_label.setStyleSheet("color: #0f0; font-size: 18px; font-family: monospace;")
        layout.addWidget(self.value_label)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def onInputToggled(self, index, state):
        """Handle input switch toggle."""
        self.perceptron.set_input(index, state)
        self.leds[index].setState(state)
        self.updateOutput()
    
    def onWeightChanged(self, index, value):
        """Handle weight knob change."""
        self.perceptron.set_weight(index, value)
        self.updateOutput()
    
    def onBiasChanged(self, value):
        """Handle bias knob change."""
        self.perceptron.set_bias(value)
        self.updateOutput()
    
    def updateOutput(self):
        """Calculate and display the output."""
        output = self.perceptron.calculate_output()
        self.meter.setValue(output)
        self.value_label.setText(f"{output:.2f}")
        
        # Trigger auto-save
        self.autosave_timer.start(1000)
    
    def autosave(self):
        """Auto-save current state."""
        self.config_manager.save_current_state(
            self.rows, 
            self.cols,
            self.perceptron.weights,
            self.perceptron.bias
        )
    
    def loadState(self):
        """Load last saved state on startup."""
        state = self.config_manager.load_current_state()
        if state:
            # Check if grid size matches
            if state['grid']['rows'] == self.rows and state['grid']['cols'] == self.cols:
                # Restore weights and bias
                weights = np.array(state['weights'])
                self.perceptron.weights = weights
                self.perceptron.bias = state['bias']
                
                # Update UI
                for i, knob in enumerate(self.knobs):
                    if i < len(weights):
                        knob.setValue(weights[i])
                
                self.bias_knob.setValue(state['bias'])
                self.updateOutput()
    
    def savePreset(self):
        """Save current configuration as a named preset."""
        name, ok = QInputDialog.getText(self, "Save Preset", "Enter preset name:")
        if ok and name:
            self.config_manager.save_preset(
                name,
                self.rows,
                self.cols,
                self.perceptron.weights,
                self.perceptron.bias
            )
            QMessageBox.information(self, "Success", f"Preset '{name}' saved!")
    
    def loadPreset(self):
        """Load a saved preset."""
        presets = self.config_manager.list_presets()
        if not presets:
            QMessageBox.information(self, "No Presets", "No saved presets found.")
            return
        
        name, ok = QInputDialog.getItem(self, "Load Preset", "Select preset:", presets, 0, False)
        if ok and name:
            preset = self.config_manager.load_preset(name)
            if preset:
                # Check if grid size matches
                if preset['grid']['rows'] != self.rows or preset['grid']['cols'] != self.cols:
                    QMessageBox.warning(
                        self, 
                        "Grid Mismatch", 
                        f"Preset is for {preset['grid']['rows']}x{preset['grid']['cols']} grid. "
                        f"Current grid is {self.rows}x{self.cols}."
                    )
                    return
                
                # Restore weights and bias
                weights = np.array(preset['weights'])
                self.perceptron.weights = weights
                self.perceptron.bias = preset['bias']
                
                # Update UI
                for i, knob in enumerate(self.knobs):
                    if i < len(weights):
                        knob.setValue(weights[i])
                
                self.bias_knob.setValue(preset['bias'])
                self.updateOutput()
    
    def deletePreset(self):
        """Delete a saved preset."""
        presets = self.config_manager.list_presets()
        if not presets:
            QMessageBox.information(self, "No Presets", "No saved presets found.")
            return
        
        name, ok = QInputDialog.getItem(self, "Delete Preset", "Select preset to delete:", presets, 0, False)
        if ok and name:
            reply = QMessageBox.question(
                self,
                "Confirm Delete",
                f"Are you sure you want to delete preset '{name}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                if self.config_manager.delete_preset(name):
                    QMessageBox.information(self, "Success", f"Preset '{name}' deleted!")
                else:
                    QMessageBox.warning(self, "Error", f"Failed to delete preset '{name}'.")
    
    def changeGridSize(self, value):
        """Handle grid size change by rebuilding the UI."""
        # Get new dimensions
        new_rows = self.rows_spin.value()
        new_cols = self.cols_spin.value()
        
        # Only rebuild if dimensions actually changed
        if new_rows == self.rows and new_cols == self.cols:
            return
        
        # Update dimensions
        self.rows = new_rows
        self.cols = new_cols
        
        # Create new perceptron with new dimensions
        self.perceptron = Perceptron(self.rows, self.cols)
        
        # Clear existing panels (everything except controls)
        # Remove all items from main_layout except the first one (controls)
        while self.main_layout.count() > 1:
            item = self.main_layout.takeAt(1)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self.clearLayout(item.layout())
        
        # Rebuild the panel layout
        panel_layout = QHBoxLayout()
        
        # Left panel - Input switches
        input_panel = self.createPanel("INPUT SWITCHES", self.createInputGrid())
        panel_layout.addWidget(input_panel)
        
        # Middle-left panel - LED indicators
        led_panel = self.createPanel("LED INDICATORS", self.createLEDGrid())
        panel_layout.addWidget(led_panel)
        
        # Middle-right panel - Weight knobs
        weight_panel = self.createPanel("WEIGHTS", self.createWeightGrid())
        panel_layout.addWidget(weight_panel)
        
        # Right panel - Bias and Meter
        bias_panel = self.createPanel("BIAS & OUTPUT", self.createBiasAndMeter())
        panel_layout.addWidget(bias_panel)
        
        self.main_layout.addLayout(panel_layout)
    
    def clearLayout(self, layout):
        """Recursively clear a layout."""
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self.clearLayout(item.layout())


def main():
    """Main entry point for the application."""
    app = QApplication(sys.argv)
    
    # Set application-wide font
    font = QFont("Arial", 10)
    app.setFont(font)
    
    window = PerceptronEmulator(rows=4, cols=4)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
