"""Pattern library with pre-generated shapes for training."""

from typing import List, Tuple, Dict
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTabWidget, QWidget, QScrollArea,
                             QCheckBox, QGridLayout, QDialogButtonBox, QGroupBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class PatternGenerator:
    """Generates pattern datasets for different shapes."""
    
    def __init__(self, rows: int, cols: int):
        self.rows = rows
        self.cols = cols
        self.num_inputs = rows * cols
    
    def _create_pattern(self, grid_str: str) -> List[int]:
        """Create pattern from string representation.
        
        Args:
            grid_str: String like '1100 0110 0011 0000' (spaces separate rows)
        
        Returns:
            List of binary values
        """
        cleaned = grid_str.replace(' ', '').replace('\n', '')
        return [int(c) for c in cleaned[:self.num_inputs]]
    
    def get_basic_shapes(self) -> Dict[str, List[int]]:
        """Get basic shape patterns based on grid size."""
        if self.rows == 2 and self.cols == 2:
            return self._get_2x2_shapes()
        elif self.rows == 3 and self.cols == 3:
            return self._get_3x3_shapes()
        elif self.rows == 4 and self.cols == 4:
            return self._get_4x4_shapes()
        else:
            # For other sizes, generate simple patterns
            return self._get_generic_shapes()
    
    def _get_2x2_shapes(self) -> Dict[str, List[int]]:
        """2x2 grid patterns."""
        return {
            'Full': [1, 1, 1, 1],
            'Empty': [0, 0, 0, 0],
            'Diagonal \\': [1, 0, 0, 1],
            'Diagonal /': [0, 1, 1, 0],
            'Top': [1, 1, 0, 0],
            'Bottom': [0, 0, 1, 1],
            'Left': [1, 0, 1, 0],
            'Right': [0, 1, 0, 1],
        }
    
    def _get_3x3_shapes(self) -> Dict[str, List[int]]:
        """3x3 grid patterns."""
        return {
            'Cross +': self._create_pattern('010 111 010'),
            'X': self._create_pattern('101 010 101'),
            'T': self._create_pattern('111 010 010'),
            'L': self._create_pattern('100 100 111'),
            'I Vertical': self._create_pattern('010 010 010'),
            'I Horizontal': self._create_pattern('000 111 000'),
            'Square': self._create_pattern('111 101 111'),
            'Dot': self._create_pattern('000 010 000'),
        }
    
    def _get_4x4_shapes(self) -> Dict[str, List[int]]:
        """4x4 grid patterns."""
        return {
            # Letters
            'T': self._create_pattern('1111 0110 0110 0000'),
            'L': self._create_pattern('1000 1000 1000 1111'),
            'I': self._create_pattern('0110 0110 0110 0110'),
            'J': self._create_pattern('0111 0010 0010 1110'),
            'C': self._create_pattern('0111 1000 1000 0111'),
            'O': self._create_pattern('0110 1001 1001 0110'),
            'U': self._create_pattern('1001 1001 1001 0110'),
            'V': self._create_pattern('1001 1001 0110 0110'),
            'Z': self._create_pattern('1111 0011 1100 1111'),
            
            # Shapes
            'Cross +': self._create_pattern('0110 1111 1111 0110'),
            'X': self._create_pattern('1001 0110 0110 1001'),
            'Square': self._create_pattern('1111 1001 1001 1111'),
            'Diamond': self._create_pattern('0110 1001 1001 0110'),
            
            # Arrows
            'Arrow ↑': self._create_pattern('0110 1111 0110 0110'),
            'Arrow ↓': self._create_pattern('0110 0110 1111 0110'),
            'Arrow ←': self._create_pattern('0010 1111 1111 0010'),
            'Arrow →': self._create_pattern('0100 1111 1111 0100'),
        }
    
    def _get_generic_shapes(self) -> Dict[str, List[int]]:
        """Generic patterns for any grid size."""
        patterns = {}
        
        # Full and empty
        patterns['Full'] = [1] * self.num_inputs
        patterns['Empty'] = [0] * self.num_inputs
        
        # Edges
        top_row = [1] * self.cols + [0] * (self.num_inputs - self.cols)
        patterns['Top Edge'] = top_row
        
        bottom_row = [0] * (self.num_inputs - self.cols) + [1] * self.cols
        patterns['Bottom Edge'] = bottom_row
        
        # Center dot
        center = [0] * self.num_inputs
        center_idx = (self.rows // 2) * self.cols + (self.cols // 2)
        if center_idx < self.num_inputs:
            center[center_idx] = 1
        patterns['Center Dot'] = center
        
        return patterns


class PresetShapeDialog(QDialog):
    """Dialog for selecting preset shapes from library."""
    
    def __init__(self, rows, cols, parent=None):
        super().__init__(parent)
        self.rows = rows
        self.cols = cols
        self.generator = PatternGenerator(rows, cols)
        self.selected_patterns = []
        self.checkboxes = {}
        
        self.setWindowTitle("Load Preset Shapes")
        self.setMinimumSize(500, 400)
        
        self.setupUI()
    
    def setupUI(self):
        """Setup the dialog UI."""
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("Select Shapes for Training")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title.setStyleSheet("color: #51cf66; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Instructions
        info = QLabel(
            "Select 2+ different shapes.\n"
            "First half will be POSITIVE examples, second half NEGATIVE."
        )
        info.setStyleSheet("color: #ccc; margin-bottom: 10px;")
        layout.addWidget(info)
        
        # Shape selection area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background-color: #2b2b2b; border: 1px solid #555;")
        
        shapes_widget = QWidget()
        shapes_layout = QVBoxLayout()
        
        # Get all shapes
        all_shapes = self.generator.get_basic_shapes()
        
        # Create checkboxes for each shape
        grid = QGridLayout()
        grid.setSpacing(10)
        
        row = 0
        col = 0
        for name, pattern in all_shapes.items():
            cb = QCheckBox(name)
            cb.setStyleSheet("color: #ccc; font-size: 12px;")
            cb.setProperty('pattern', pattern)
            cb.setProperty('name', name)
            self.checkboxes[name] = cb
            
            grid.addWidget(cb, row, col)
            col += 1
            if col >= 3:  # 3 columns
                col = 0
                row += 1
        
        shapes_layout.addLayout(grid)
        shapes_widget.setLayout(shapes_layout)
        scroll.setWidget(shapes_widget)
        layout.addWidget(scroll)
        
        # Pattern count label
        self.count_label = QLabel("Selected: 0 shapes")
        self.count_label.setStyleSheet("color: #ffd43b; font-weight: bold;")
        layout.addWidget(self.count_label)
        
        # Connect checkboxes to update count
        for cb in self.checkboxes.values():
            cb.stateChanged.connect(self.updateCount)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.setStyleSheet("""
            QPushButton {
                background-color: #4c6ef5;
                color: white;
                padding: 6px 16px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #5c7cfa;
            }
        """)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
    
    def updateCount(self):
        """Update the selected count label."""
        count = sum(1 for cb in self.checkboxes.values() if cb.isChecked())
        self.count_label.setText(f"Selected: {count} shapes")
    
    def get_selected_patterns(self):
        """Get selected patterns with positive/negative labels.
        
        Returns:
            List of (inputs, target) tuples
        """
        selected = []
        for name, cb in self.checkboxes.items():
            if cb.isChecked():
                pattern = cb.property('pattern')
                selected.append((name, pattern))
        
        if len(selected) < 2:
            return []
        
        # Split into positive and negative
        mid = len(selected) // 2
        patterns = []
        
        # First half = positive (target=1)
        for name, pattern in selected[:mid]:
            patterns.append((pattern, 1))
        
        # Second half = negative (target=0)
        for name, pattern in selected[mid:]:
            patterns.append((pattern, 0))
        
        return patterns
