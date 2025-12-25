import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                              QHBoxLayout, QGridLayout, QLabel, QGroupBox, QSpinBox,
                              QMenuBar, QMenu, QInputDialog, QMessageBox, QPushButton,
                              QComboBox, QSlider, QSplitter)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QAction
from .logic import Perceptron
from .widgets import ToggleSwitch, LEDBulb, RotaryKnob, AnalogMeter
from .config import ConfigManager
from .training import PerceptronTrainer
from .plotting import TrainingPlotWidget
import numpy as np


class PerceptronEmulator(QMainWindow):
    def __init__(self, rows=4, cols=4):
        super().__init__()
        self.rows = rows
        self.cols = cols
        self.perceptron = Perceptron(rows, cols)
        
        # Initialize config manager
        self.config_manager = ConfigManager()
        
        # Initialize trainer (matches current grid size)
        self.trainer = PerceptronTrainer(num_inputs=rows * cols)
        self.training_active = False
        self.training_timer = QTimer()
        self.training_timer.timeout.connect(self.trainingStep)
        
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
        
        # Add training panel at the bottom
        training_panel = self.createTrainingPanel()
        main_layout.addWidget(training_panel)
    
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
        self.knob_labels = []  # Store labels for updating
        for row in range(self.rows):
            for col in range(self.cols):
                # Create container for knob + label
                knob_container = QWidget()
                knob_layout = QVBoxLayout()
                knob_layout.setSpacing(5)
                knob_layout.setContentsMargins(0, 0, 0, 0)
                
                # Create knob
                knob = RotaryKnob(min_value=-30.0, max_value=30.0)
                index = row * self.cols + col
                knob.valueChanged.connect(lambda val, idx=index: self.onWeightChanged(idx, val))
                knob_layout.addWidget(knob, alignment=Qt.AlignmentFlag.AlignCenter)
                
                # Create value label
                value_label = QLabel("0.00")
                value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                value_label.setStyleSheet("color: #51cf66; font-size: 11px; font-family: monospace; font-weight: bold;")
                knob_layout.addWidget(value_label)
                
                knob_container.setLayout(knob_layout)
                grid.addWidget(knob_container, row, col)
                
                self.knobs.append(knob)
                self.knob_labels.append(value_label)
        
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
        
        # Bias value label
        self.bias_value_label = QLabel("0.00")
        self.bias_value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.bias_value_label.setStyleSheet("color: #51cf66; font-size: 12px; font-family: monospace; font-weight: bold;")
        layout.addWidget(self.bias_value_label)
        
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
    
    def createTrainingPanel(self):
        """Create the training control panel with plot."""
        widget = QWidget()
        main_layout = QHBoxLayout()
        
        # Left side - Controls
        controls_widget = QWidget()
        controls_layout = QVBoxLayout()
        
        # Pattern selection
        pattern_label = QLabel("Training Pattern:")
        pattern_label.setStyleSheet("color: #ccc; font-weight: bold;")
        controls_layout.addWidget(pattern_label)
        
        self.pattern_combo = QComboBox()
        self.pattern_combo.addItems(['AND', 'OR', 'NAND', 'CUSTOM'])
        self.pattern_combo.currentTextChanged.connect(self.onPatternTypeChanged)
        self.pattern_combo.setStyleSheet("""
            QComboBox {
                background-color: #333;
                color: #ccc;
                border: 1px solid #555;
                padding: 5px;
                border-radius: 3px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #333;
                color: #ccc;
                selection-background-color: #555;
            }
        """)
        controls_layout.addWidget(self.pattern_combo)
        
        # Learning rate slider
        lr_label = QLabel("Learning Rate: 0.10")
        lr_label.setStyleSheet("color: #ccc; font-weight: bold;")
        controls_layout.addWidget(lr_label)
        
        self.lr_slider = QSlider(Qt.Orientation.Horizontal)
        self.lr_slider.setRange(1, 50)  # 0.01 to 0.50
        self.lr_slider.setValue(10)  # 0.10
        self.lr_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                background: #333;
                height: 8px;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #51cf66;
                width: 16px;
                margin: -4px 0;
                border-radius: 8px;
            }
        """)
        self.lr_slider.valueChanged.connect(
            lambda v: lr_label.setText(f"Learning Rate: {v/100:.2f}")
        )
        controls_layout.addWidget(self.lr_slider)
        
        # Training buttons
        button_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("Start Training")
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #51cf66;
                color: #000;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #69db7c;
            }
            QPushButton:disabled {
                background-color: #555;
                color: #888;
            }
        """)
        self.start_btn.clicked.connect(self.startTraining)
        button_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff6b6b;
                color: #fff;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ff8787;
            }
            QPushButton:disabled {
                background-color: #555;
                color: #888;
            }
        """)
        self.stop_btn.clicked.connect(self.stopTraining)
        button_layout.addWidget(self.stop_btn)
        
        self.reset_btn = QPushButton("Reset")
        self.reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffd43b;
                color: #000;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ffe066;
            }
        """)
        self.reset_btn.clicked.connect(self.resetTraining)
        button_layout.addWidget(self.reset_btn)
        
        controls_layout.addLayout(button_layout)
        
        # Status labels
        self.epoch_label = QLabel("Epoch: 0")
        self.epoch_label.setStyleSheet("color: #ccc; font-size: 14px; font-family: monospace;")
        controls_layout.addWidget(self.epoch_label)
        
        self.error_label = QLabel("Errors: 0")
        self.error_label.setStyleSheet("color: #ccc; font-size: 14px; font-family: monospace;")
        controls_layout.addWidget(self.error_label)
        
        self.status_label = QLabel("Status: Ready")
        self.status_label.setStyleSheet("color: #51cf66; font-size: 14px; font-weight: bold;")
        controls_layout.addWidget(self.status_label)
        
        # Info label showing pattern count
        self.info_label = QLabel(f"Patterns: {2 ** (self.rows * self.cols)} combinations")
        self.info_label.setStyleSheet("color: #51cf66; font-size: 12px;")
        controls_layout.addWidget(self.info_label)
        
        # Custom pattern capture panel (initially hidden)
        self.custom_pattern_panel = QWidget()
        custom_layout = QVBoxLayout()
        custom_layout.setSpacing(8)
        custom_layout.setContentsMargins(0, 10, 0, 0)
        
        # Pattern count label
        self.custom_count_label = QLabel("Positive: 0, Negative: 0")
        self.custom_count_label.setStyleSheet("color: #ffd43b; font-size: 12px; font-weight: bold;")
        custom_layout.addWidget(self.custom_count_label)
        
        # Button container
        button_container = QWidget()
        button_layout = QHBoxLayout()
        button_layout.setSpacing(5)
        button_layout.setContentsMargins(0, 0, 0, 0)
        
        # Add as positive button
        self.add_positive_btn = QPushButton("Add as Positive (+)")
        self.add_positive_btn.setStyleSheet("""
            QPushButton {
                background-color: #51cf66;
                color: #000;
                border: none;
                padding: 6px 12px;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #69db7c;
            }
        """)
        self.add_positive_btn.clicked.connect(self.addPositivePattern)
        button_layout.addWidget(self.add_positive_btn)
        
        # Add as negative button
        self.add_negative_btn = QPushButton("Add as Negative (-)")
        self.add_negative_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff6b6b;
                color: #fff;
                border: none;
                padding: 6px 12px;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ff8787;
            }
        """)
        self.add_negative_btn.clicked.connect(self.addNegativePattern)
        button_layout.addWidget(self.add_negative_btn)
        
        button_container.setLayout(button_layout)
        custom_layout.addWidget(button_container)
        
        # Clear patterns button
        self.clear_patterns_btn = QPushButton("Clear All Patterns")
        self.clear_patterns_btn.setStyleSheet("""
            QPushButton {
                background-color: #444;
                color: #ccc;
                border: 1px solid #666;
                padding: 4px 8px;
                border-radius: 3px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #555;
            }
        """)
        self.clear_patterns_btn.clicked.connect(self.clearCustomPatterns)
        custom_layout.addWidget(self.clear_patterns_btn)
        
        self.custom_pattern_panel.setLayout(custom_layout)
        self.custom_pattern_panel.setVisible(False)  # Hidden by default
        controls_layout.addWidget(self.custom_pattern_panel)
        
        controls_layout.addStretch()
        controls_widget.setLayout(controls_layout)
        controls_widget.setMinimumWidth(250)
        
        # Right side - Plot
        self.plot_widget = TrainingPlotWidget()
        
        # Add to main layout
        main_layout.addWidget(controls_widget)
        main_layout.addWidget(self.plot_widget, stretch=1)
        
        widget.setLayout(main_layout)
        
        # Wrap in a panel
        return self.createPanel("TRAINING MODE", widget)

    
    def onInputToggled(self, index, state):
        """Handle input switch toggle."""
        self.perceptron.set_input(index, state)
        self.leds[index].setState(state)
        self.updateOutput()
    
    def onWeightChanged(self, index, value):
        """Handle weight knob change."""
        self.perceptron.set_weight(index, value)
        # Update the label
        if index < len(self.knob_labels):
            self.knob_labels[index].setText(f"{value:.2f}")
        self.updateOutput()
    
    def onBiasChanged(self, value):
        """Handle bias knob change."""
        self.perceptron.set_bias(value)
        self.bias_value_label.setText(f"{value:.2f}")
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
    
    def startTraining(self):
        """Start the training process."""
        # Warn for large grids (exponential pattern count)
        num_inputs = self.rows * self.cols
        num_patterns = 2 ** num_inputs
        
        if num_inputs > 6:  # More than 64 patterns
            reply = QMessageBox.question(
                self,
                "Large Grid Warning",
                f"Training on {self.rows}x{self.cols} grid requires {num_patterns} patterns.\n"
                f"This may take a long time to converge.\n\n"
                "Continue anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
        
        # Preserve custom patterns before reinitializing trainer
        saved_custom_patterns = self.trainer.custom_patterns.copy() if self.pattern_combo.currentText() == 'CUSTOM' else []
        
        # Reinitialize trainer with current grid size
        self.trainer = PerceptronTrainer(num_inputs=num_inputs)
        
        # Restore custom patterns if in CUSTOM mode
        if saved_custom_patterns:
            self.trainer.custom_patterns = saved_custom_patterns
        
        # Set pattern and learning rate
        pattern_name = self.pattern_combo.currentText()
        learning_rate = self.lr_slider.value() / 100.0
        
        # Validate custom patterns
        if pattern_name == 'CUSTOM':
            positive, negative = self.trainer.get_custom_pattern_count()
            if positive == 0 or negative == 0:
                QMessageBox.warning(
                    self,
                    "Insufficient Patterns",
                    f"Custom training requires both positive and negative examples.\n"
                    f"Current: {positive} positive, {negative} negative\n\n"
                    "Please add at least one example of each type."
                )
                return
        
        self.trainer.set_pattern(pattern_name)
        self.trainer.set_learning_rate(learning_rate)
        
        # Update UI state
        self.training_active = True
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.pattern_combo.setEnabled(False)
        self.lr_slider.setEnabled(False)
        self.status_label.setText("Status: Training...")
        self.status_label.setStyleSheet("color: #ffd43b; font-size: 14px; font-weight: bold;")
        
        # Start training timer (100ms interval for smooth updates)
        self.training_timer.start(100)
    
    def stopTraining(self):
        """Stop the training process."""
        self.training_active = False
        self.training_timer.stop()
        
        # Update UI state
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.pattern_combo.setEnabled(True)
        self.lr_slider.setEnabled(True)
        
        if self.trainer.has_converged():
            self.status_label.setText("Status: Converged ✓")
            self.status_label.setStyleSheet("color: #51cf66; font-size: 14px; font-weight: bold;")
        else:
            self.status_label.setText("Status: Stopped")
            self.status_label.setStyleSheet("color: #ff6b6b; font-size: 14px; font-weight: bold;")
    
    def resetTraining(self):
        """Reset the training state."""
        # Stop if running
        if self.training_active:
            self.stopTraining()
        
        # Reset trainer
        self.trainer.reset()
        
        # Clear plot
        self.plot_widget.clear_plot()
        
        # Reset labels
        self.epoch_label.setText("Epoch: 0")
        self.error_label.setText("Errors: 0")
        self.status_label.setText("Status: Ready")
        self.status_label.setStyleSheet("color: #51cf66; font-size: 14px; font-weight: bold;")
    
    def onPatternTypeChanged(self, pattern_type):
        """Handle pattern type change - show/hide custom panel."""
        is_custom = (pattern_type == 'CUSTOM')
        self.custom_pattern_panel.setVisible(is_custom)
        
        # Update info label
        if is_custom:
            self.updateCustomPatternCount()
        else:
            self.info_label.setText(f"Patterns: {2 ** (self.rows * self.cols)} combinations")
    
    def addPositivePattern(self):
        """Capture current switch state as positive example."""
        inputs = [1 if sw.state else 0 for sw in self.switches]
        self.trainer.add_custom_pattern(inputs, 1)
        self.updateCustomPatternCount()
    
    def addNegativePattern(self):
        """Capture current switch state as negative example."""
        inputs = [1 if sw.state else 0 for sw in self.switches]
        self.trainer.add_custom_pattern(inputs, 0)
        self.updateCustomPatternCount()
    
    def clearCustomPatterns(self):
        """Clear all custom patterns."""
        self.trainer.clear_custom_patterns()
        self.updateCustomPatternCount()
    
    def updateCustomPatternCount(self):
        """Update the custom pattern count label."""
        positive, negative = self.trainer.get_custom_pattern_count()
        self.custom_count_label.setText(f"Positive: {positive}, Negative: {negative}")
        total = positive + negative
        self.info_label.setText(f"Patterns: {total} custom")
    
    def trainingStep(self):
        """Execute one training epoch."""
        if not self.training_active:
            return
        
        # Run one epoch
        errors = self.trainer.train_epoch()
        
        # Update labels
        self.epoch_label.setText(f"Epoch: {self.trainer.epoch_count}")
        self.error_label.setText(f"Errors: {errors}")
        
        # Update plot with weight history
        epochs = list(range(1, len(self.trainer.error_history) + 1))
        self.plot_widget.update_plot(
            epochs, 
            self.trainer.error_history,
            self.trainer.weight_history
        )
        
        # Sync weights to UI (all weights for current grid)
        for i in range(min(len(self.trainer.weights), len(self.knobs))):
            self.knobs[i].blockSignals(True)
            self.knobs[i].setValue(self.trainer.weights[i])
            self.knobs[i].blockSignals(False)
            self.perceptron.set_weight(i, self.trainer.weights[i])
            # Update label
            if i < len(self.knob_labels):
                self.knob_labels[i].setText(f"{self.trainer.weights[i]:.2f}")
        
        # Sync bias
        self.bias_knob.blockSignals(True)
        self.bias_knob.setValue(self.trainer.bias)
        self.bias_knob.blockSignals(False)
        self.perceptron.set_bias(self.trainer.bias)
        self.bias_value_label.setText(f"{self.trainer.bias:.2f}")
        
        # Update output display
        self.updateOutput()
        
        # Check for convergence
        if self.trainer.has_converged():
            self.stopTraining()
        
        # Stop after 1000 epochs max
        if self.trainer.epoch_count >= 1000:
            self.stopTraining()
            self.status_label.setText("Status: Max epochs reached")
            self.status_label.setStyleSheet("color: #ff6b6b; font-size: 14px; font-weight: bold;")

    
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
        
        # Rebuild training panel
        training_panel = self.createTrainingPanel()
        self.main_layout.addWidget(training_panel)
        
        # Update trainer with new grid size
        self.trainer = PerceptronTrainer(num_inputs=self.rows * self.cols)
        
        # Update info label
        self.info_label.setText(f"Patterns: {2 ** (self.rows * self.cols)} combinations")
    
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
