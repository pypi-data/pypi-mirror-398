"""Enhanced pattern library with visual previews and more variations."""

from typing import List, Tuple, Dict
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTabWidget, QWidget, QScrollArea,
                             QCheckBox, QGridLayout, QDialogButtonBox, QGroupBox,
                             QFrame)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QPainter, QColor, QPen


class PatternPreviewWidget(QWidget):
    """Visual preview of a pattern as a mini grid."""
    
    def __init__(self, pattern: List[int], rows: int, cols: int, parent=None):
        super().__init__(parent)
        self.pattern = pattern
        self.rows = rows
        self.cols = cols
        self.setFixedSize(60, 60)
    
    def paintEvent(self, event):
        """Draw the pattern as a grid."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Calculate cell size
        cell_width = 60 / self.cols
        cell_height = 60 / self.rows
        
        # Draw grid
        for row in range(self.rows):
            for col in range(self.cols):
                idx = row * self.cols + col
                if idx < len(self.pattern):
                    x = col * cell_width
                    y = row * cell_height
                    
                    # Fill cell if pattern is 1
                    if self.pattern[idx] == 1:
                        painter.fillRect(int(x), int(y), int(cell_width), int(cell_height), QColor("#51cf66"))
                    else:
                        painter.fillRect(int(x), int(y), int(cell_width), int(cell_height), QColor("#333"))
                    
                    # Draw border
                    painter.setPen(QPen(QColor("#555"), 1))
                    painter.drawRect(int(x), int(y), int(cell_width), int(cell_height))


class PatternGenerator:
    """Generates pattern datasets with variations."""
    
    def __init__(self, rows: int, cols: int):
        self.rows = rows
        self.cols = cols
        self.num_inputs = rows * cols
    
    def _create_pattern(self, grid_str: str) -> List[int]:
        """Create pattern from string representation."""
        cleaned = grid_str.replace(' ', '').replace('\n', '')
        return [int(c) for c in cleaned[:self.num_inputs]]
    
    def _rotate_90(self, pattern: List[int]) -> List[int]:
        """Rotate pattern 90 degrees clockwise."""
        grid = [pattern[i:i+self.cols] for i in range(0, len(pattern), self.cols)]
        rotated = [[grid[self.rows-1-j][i] for j in range(self.rows)] for i in range(self.cols)]
        return [cell for row in rotated for cell in row]
    
    def _generate_variations(self, base_pattern: List[int], count: int = 3) -> List[List[int]]:
        """Generate variations of a pattern (rotations, flips)."""
        variations = [base_pattern]
        
        # Add rotations
        current = base_pattern
        for _ in range(min(count - 1, 3)):
            current = self._rotate_90(current)
            if current != base_pattern and current not in variations:
                variations.append(current)
        
        return variations[:count]
    
    def get_all_patterns(self) -> Dict[str, Dict[str, List[Tuple[str, List[int]]]]]:
        """Get all patterns organized by category - works for ANY grid size."""
        # Use specific libraries for common square sizes if available
        if self.rows == self.cols:
            if self.rows == 2:
                return self._get_2x2_library()
            elif self.rows == 3:
                return self._get_3x3_library()
            elif self.rows == 4:
                return self._get_4x4_library()
            elif self.rows == 5:
                return self._get_5x5_library()
            elif self.rows == 6:
                return self._get_6x6_library()
            elif self.rows == 7:
                return self._get_7x7_library()
            elif self.rows == 8:
                return self._get_8x8_library()
        
        # For all other sizes (including non-square), use universal generator
        return self._get_universal_library()
    
    def _get_universal_library(self) -> Dict[str, Dict[str, List[Tuple[str, List[int]]]]]:
        """Universal pattern library that works for ANY grid size."""
        library = {}
        
        # Basic patterns - always available
        library['Basic'] = {}
        
        # Full and empty
        library['Basic']['Full'] = [('Full', [1] * self.num_inputs)]
        library['Basic']['Empty'] = [('Empty', [0] * self.num_inputs)]
        
        # Edges
        top_row = [1] * self.cols + [0] * (self.num_inputs - self.cols)
        library['Basic']['Top Edge'] = [('Top Edge', top_row)]
        
        bottom_row = [0] * (self.num_inputs - self.cols) + [1] * self.cols
        library['Basic']['Bottom Edge'] = [('Bottom Edge', bottom_row)]
        
        left_col = []
        for r in range(self.rows):
            left_col.extend([1] + [0] * (self.cols - 1))
        library['Basic']['Left Edge'] = [('Left Edge', left_col)]
        
        right_col = []
        for r in range(self.rows):
            right_col.extend([0] * (self.cols - 1) + [1])
        library['Basic']['Right Edge'] = [('Right Edge', right_col)]
        
        # Corners
        top_left = [1] + [0] * (self.num_inputs - 1)
        library['Basic']['Top-Left'] = [('Top-Left', top_left)]
        
        top_right = [0] * (self.cols - 1) + [1] + [0] * (self.num_inputs - self.cols)
        library['Basic']['Top-Right'] = [('Top-Right', top_right)]
        
        bottom_left = [0] * (self.num_inputs - self.cols) + [1] + [0] * (self.cols - 1)
        library['Basic']['Bottom-Left'] = [('Bottom-Left', bottom_left)]
        
        bottom_right = [0] * (self.num_inputs - 1) + [1]
        library['Basic']['Bottom-Right'] = [('Bottom-Right', bottom_right)]
        
        # Shapes - if grid is large enough
        if self.rows >= 3 and self.cols >= 3:
            library['Shapes'] = {}
            
            # Center dot
            center = [0] * self.num_inputs
            center_idx = (self.rows // 2) * self.cols + (self.cols // 2)
            center[center_idx] = 1
            library['Shapes']['Center Dot'] = [('Center Dot', center)]
            
            # Cross (if grid is big enough)
            if self.rows >= 3 and self.cols >= 3:
                cross = [0] * self.num_inputs
                # Vertical line
                for r in range(self.rows):
                    cross[r * self.cols + self.cols // 2] = 1
                # Horizontal line
                for c in range(self.cols):
                    cross[(self.rows // 2) * self.cols + c] = 1
                library['Shapes']['Cross +'] = [('Cross +', cross)]
            
            # Diagonals (if square or nearly square)
            if abs(self.rows - self.cols) <= 1:
                # Diagonal \
                diag1 = [0] * self.num_inputs
                for i in range(min(self.rows, self.cols)):
                    diag1[i * self.cols + i] = 1
                library['Shapes']['Diagonal \\'] = [('Diagonal \\', diag1)]
                
                # Diagonal /
                diag2 = [0] * self.num_inputs
                for i in range(min(self.rows, self.cols)):
                    diag2[i * self.cols + (self.cols - 1 - i)] = 1
                library['Shapes']['Diagonal /'] = [('Diagonal /', diag2)]
        
        # Letters - if grid is large enough
        if self.rows >= 4 and self.cols >= 3:
            library['Letters'] = {}
            
            # Simple T pattern
            t_pattern = [0] * self.num_inputs
            # Top row
            for c in range(self.cols):
                t_pattern[c] = 1
            # Vertical stem (center column)
            for r in range(1, self.rows):
                t_pattern[r * self.cols + self.cols // 2] = 1
            library['Letters']['T'] = [('T', t_pattern)]
            
            # Simple L pattern
            l_pattern = [0] * self.num_inputs
            # Left column
            for r in range(self.rows):
                l_pattern[r * self.cols] = 1
            # Bottom row
            for c in range(self.cols):
                l_pattern[(self.rows - 1) * self.cols + c] = 1
            library['Letters']['L'] = [('L', l_pattern)]
            
            # Simple I pattern (vertical line in center)
            i_pattern = [0] * self.num_inputs
            for r in range(self.rows):
                i_pattern[r * self.cols + self.cols // 2] = 1
            library['Letters']['I'] = [('I', i_pattern)]
        
        return library
    
    def _get_4x4_library(self) -> Dict[str, Dict[str, List[Tuple[str, List[int]]]]]:
        """Comprehensive 4x4 pattern library with variations."""
        library = {}
        
        # Letters
        library['Letters'] = {}
        letter_patterns = {
            'T': '1111 0110 0110 0000',
            'L': '1000 1000 1000 1111',
            'I': '0110 0110 0110 0110',
            'J': '0111 0010 0010 1110',
            'C': '0111 1000 1000 0111',
            'O': '0110 1001 1001 0110',
            'U': '1001 1001 1001 0110',
            'V': '1001 1001 0110 0110',
            'Z': '1111 0011 1100 1111',
            'H': '1001 1111 1111 1001',
            'F': '1111 1000 1110 1000',
            'E': '1111 1000 1110 1000 1111',
            'A': '0110 1001 1111 1001',
        }
        
        for name, pattern_str in letter_patterns.items():
            base = self._create_pattern(pattern_str)
            variations = self._generate_variations(base, 2)
            library['Letters'][name] = [(f"{name}", var) for var in variations]
        
        # Shapes
        library['Shapes'] = {}
        shape_patterns = {
            'Cross +': '0110 1111 1111 0110',
            'X': '1001 0110 0110 1001',
            'Square': '1111 1001 1001 1111',
            'Diamond': '0110 1001 1001 0110',
            'Filled Square': '0000 0110 0110 0000',
            'Corners': '1001 0000 0000 1001',
            'Checkerboard': '1010 0101 1010 0101',
            'Stripes H': '1111 0000 1111 0000',
            'Stripes V': '1010 1010 1010 1010',
            'Spiral': '1111 0001 0101 1111',
            'Frame': '1111 1001 1001 1111',
            'Dots': '1010 0000 0000 1010',
        }
        
        for name, pattern_str in shape_patterns.items():
            base = self._create_pattern(pattern_str)
            variations = self._generate_variations(base, 3)
            library['Shapes'][name] = [(f"{name}", var) for var in variations]
        
        # Arrows
        library['Arrows'] = {}
        arrow_patterns = {
            'Up ↑': '0110 1111 0110 0110',
            'Down ↓': '0110 0110 1111 0110',
            'Left ←': '0010 1111 1111 0010',
            'Right →': '0100 1111 1111 0100',
        }
        
        for name, pattern_str in arrow_patterns.items():
            base = self._create_pattern(pattern_str)
            variations = self._generate_variations(base, 4)
            library['Arrows'][name] = [(f"{name}", var) for var in variations]
        
        # Numbers
        library['Numbers'] = {}
        number_patterns = {
            '0': '0110 1001 1001 0110',
            '1': '0010 0110 0010 0111',
            '2': '0110 0001 0110 1111',
            '3': '1110 0011 0011 1110',
            '4': '1001 1001 1111 0001',
            '5': '1111 1110 0001 1110',
            '6': '0110 1000 1110 0110',
            '7': '1111 0001 0010 0100',
            '8': '0110 0110 0110 0110',
            '9': '0110 1111 0001 0110',
        }
        
        for name, pattern_str in number_patterns.items():
            base = self._create_pattern(pattern_str)
            variations = self._generate_variations(base, 2)  # Add variations for numbers
            library['Numbers'][name] = [(f"{name}", var) for var in variations]
        
        return library
    
    def _get_3x3_library(self) -> Dict[str, Dict[str, List[Tuple[str, List[int]]]]]:
        """3x3 pattern library."""
        library = {}
        
        library['Shapes'] = {}
        shapes = {
            'Cross +': '010 111 010',
            'X': '101 010 101',
            'T': '111 010 010',
            'L': '100 100 111',
            'Square': '111 101 111',
        }
        
        for name, pattern_str in shapes.items():
            base = self._create_pattern(pattern_str)
            variations = self._generate_variations(base, 4)
            library['Shapes'][name] = [(f"{name}", var) for var in variations]
        
        return library
    
    def _get_2x2_library(self) -> Dict[str, Dict[str, List[Tuple[str, List[int]]]]]:
        """2x2 pattern library."""
        library = {}
        
        library['Basic'] = {}
        basic_patterns = {
            'Full': '11 11',
            'Empty': '00 00',
            'Diagonal \\': '10 01',
            'Diagonal /': '01 10',
            'Top': '11 00',
            'Bottom': '00 11',
            'Left': '10 10',
            'Right': '01 01',
            'Top-Left': '10 00',
            'Top-Right': '01 00',
            'Bottom-Left': '00 10',
            'Bottom-Right': '00 01',
        }
        
        for name, pattern_str in basic_patterns.items():
            base = self._create_pattern(pattern_str)
            library['Basic'][name] = [(name, [base])]
        
        return library
    
    def _get_5x5_library(self) -> Dict[str, Dict[str, List[Tuple[str, List[int]]]]]:
        """5x5 pattern library."""
        library = {}
        
        # Letters
        library['Letters'] = {}
        letter_patterns = {
            'T': '11111 00100 00100 00100 00000',
            'L': '10000 10000 10000 10000 11111',
            'I': '01110 00100 00100 00100 01110',
            'C': '01110 10000 10000 10000 01110',
            'O': '01110 10001 10001 10001 01110',
            'H': '10001 10001 11111 10001 10001',
            'F': '11111 10000 11110 10000 10000',
            'E': '11111 10000 11110 10000 11111',
        }
        
        for name, pattern_str in letter_patterns.items():
            base = self._create_pattern(pattern_str)
            variations = self._generate_variations(base, 2)
            library['Letters'][name] = [(f"{name}", var) for var in variations]
        
        # Shapes
        library['Shapes'] = {}
        shape_patterns = {
            'Cross +': '00100 00100 11111 00100 00100',
            'X': '10001 01010 00100 01010 10001',
            'Square': '11111 10001 10001 10001 11111',
            'Diamond': '00100 01010 10001 01010 00100',
        }
        
        for name, pattern_str in shape_patterns.items():
            base = self._create_pattern(pattern_str)
            variations = self._generate_variations(base, 3)
            library['Shapes'][name] = [(f"{name}", var) for var in variations]
        
        return library
    
    def _get_6x6_library(self) -> Dict[str, Dict[str, List[Tuple[str, List[int]]]]]:
        """6x6 pattern library."""
        library = {}
        
        # Letters
        library['Letters'] = {}
        letter_patterns = {
            'T': '111111 001100 001100 001100 001100 000000',
            'L': '110000 110000 110000 110000 110000 111111',
            'I': '011110 001100 001100 001100 001100 011110',
            'C': '011110 110000 110000 110000 110000 011110',
            'O': '011110 110011 110011 110011 110011 011110',
        }
        
        for name, pattern_str in letter_patterns.items():
            base = self._create_pattern(pattern_str)
            variations = self._generate_variations(base, 2)
            library['Letters'][name] = [(f"{name}", var) for var in variations]
        
        # Shapes
        library['Shapes'] = {}
        shape_patterns = {
            'Cross +': '001100 001100 111111 111111 001100 001100',
            'X': '110011 011110 001100 001100 011110 110011',
            'Square': '111111 110011 110011 110011 110011 111111',
        }
        
        for name, pattern_str in shape_patterns.items():
            base = self._create_pattern(pattern_str)
            variations = self._generate_variations(base, 3)
            library['Shapes'][name] = [(f"{name}", var) for var in variations]
        
        return library
    
    def _get_7x7_library(self) -> Dict[str, Dict[str, List[Tuple[str, List[int]]]]]:
        """7x7 pattern library."""
        library = {}
        
        # Letters
        library['Letters'] = {}
        letter_patterns = {
            'T': '1111111 0011100 0011100 0011100 0011100 0011100 0000000',
            'L': '1100000 1100000 1100000 1100000 1100000 1100000 1111111',
            'I': '0111110 0011100 0011100 0011100 0011100 0011100 0111110',
        }
        
        for name, pattern_str in letter_patterns.items():
            base = self._create_pattern(pattern_str)
            variations = self._generate_variations(base, 2)
            library['Letters'][name] = [(f"{name}", var) for var in variations]
        
        # Shapes
        library['Shapes'] = {}
        shape_patterns = {
            'Cross +': '0011100 0011100 1111111 1111111 1111111 0011100 0011100',
            'Square': '1111111 1100011 1100011 1100011 1100011 1100011 1111111',
        }
        
        for name, pattern_str in shape_patterns.items():
            base = self._create_pattern(pattern_str)
            variations = self._generate_variations(base, 3)
            library['Shapes'][name] = [(f"{name}", var) for var in variations]
        
        return library
    
    def _get_8x8_library(self) -> Dict[str, Dict[str, List[Tuple[str, List[int]]]]]:
        """8x8 pattern library."""
        library = {}
        
        # Letters
        library['Letters'] = {}
        letter_patterns = {
            'T': '11111111 00111100 00111100 00111100 00111100 00111100 00111100 00000000',
            'L': '11000000 11000000 11000000 11000000 11000000 11000000 11000000 11111111',
            'I': '01111110 00111100 00111100 00111100 00111100 00111100 00111100 01111110',
            'C': '01111110 11000011 11000000 11000000 11000000 11000000 11000011 01111110',
            'O': '01111110 11000011 11000011 11000011 11000011 11000011 11000011 01111110',
        }
        
        for name, pattern_str in letter_patterns.items():
            base = self._create_pattern(pattern_str)
            variations = self._generate_variations(base, 2)
            library['Letters'][name] = [(f"{name}", var) for var in variations]
        
        # Shapes
        library['Shapes'] = {}
        shape_patterns = {
            'Cross +': '00111100 00111100 11111111 11111111 11111111 11111111 00111100 00111100',
            'X': '11000011 01100110 00111100 00011000 00011000 00111100 01100110 11000011',
            'Square': '11111111 11000011 11000011 11000011 11000011 11000011 11000011 11111111',
            'Diamond': '00011000 00111100 01100110 11000011 11000011 01100110 00111100 00011000',
        }
        
        for name, pattern_str in shape_patterns.items():
            base = self._create_pattern(pattern_str)
            variations = self._generate_variations(base, 3)
            library['Shapes'][name] = [(f"{name}", var) for var in variations]
        
        return library
    
    def _get_generic_library(self) -> Dict[str, Dict[str, List[Tuple[str, List[int]]]]]:
        """Generic patterns for any grid size."""
        library = {}
        library['Basic'] = {}
        
        # Simple patterns
        library['Basic']['Full'] = [('Full', [1] * self.num_inputs)]
        library['Basic']['Empty'] = [('Empty', [0] * self.num_inputs)]
        
        return library


class PresetShapeDialog(QDialog):
    """Enhanced dialog with visual previews and better organization."""
    
    def __init__(self, rows, cols, parent=None):
        super().__init__(parent)
        self.rows = rows
        self.cols = cols
        self.generator = PatternGenerator(rows, cols)
        self.selected_patterns = []
        self.checkboxes = {}
        
        self.setWindowTitle("Pattern Library - Select Shapes")
        self.setMinimumSize(700, 600)
        
        self.setupUI()
    
    def setupUI(self):
        """Setup the enhanced dialog UI."""
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("📚 Pattern Library")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #51cf66; margin-bottom: 5px;")
        layout.addWidget(title)
        
        # Instructions
        info = QLabel(
            "Click + for POSITIVE examples, - for NEGATIVE examples.\n"
            "Select at least one of each type for training."
        )
        info.setStyleSheet("color: #ccc; margin-bottom: 10px; font-size: 11px;")
        info.setWordWrap(True)
        layout.addWidget(info)
        
        # Category tabs
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #555;
                background-color: #2b2b2b;
            }
            QTabBar::tab {
                background-color: #333;
                color: #ccc;
                padding: 8px 16px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #4c6ef5;
                color: white;
            }
        """)
        
        # Get all patterns
        all_patterns = self.generator.get_all_patterns()
        
        # Create tab for each category
        for category_name, patterns_dict in all_patterns.items():
            tab = self.create_category_tab(category_name, patterns_dict)
            self.tabs.addTab(tab, f"{category_name} ({len(patterns_dict)})")
        
        layout.addWidget(self.tabs)
        
        # Selection info
        self.count_label = QLabel("Selected: 0 patterns")
        self.count_label.setStyleSheet("color: #ffd43b; font-weight: bold; font-size: 13px;")
        layout.addWidget(self.count_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        select_all_btn = QPushButton("Select All in Tab")
        select_all_btn.clicked.connect(self.selectAllInCurrentTab)
        select_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #4c6ef5;
                color: white;
                padding: 6px 12px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #5c7cfa;
            }
        """)
        button_layout.addWidget(select_all_btn)
        
        deselect_all_btn = QPushButton("Deselect All")
        deselect_all_btn.clicked.connect(self.deselectAll)
        deselect_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #555;
                color: white;
                padding: 6px 12px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #666;
            }
        """)
        button_layout.addWidget(deselect_all_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # OK/Cancel
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.setStyleSheet("""
            QPushButton {
                background-color: #37b24d;
                color: white;
                padding: 8px 20px;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #40c057;
            }
        """)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
    
    def create_category_tab(self, category_name, patterns_dict):
        """Create tab for a pattern category with visual previews."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background-color: #2b2b2b; border: none;")
        
        container = QWidget()
        grid = QGridLayout()
        grid.setSpacing(15)
        
        row = 0
        col = 0
        
        for pattern_name, variations in patterns_dict.items():
            for var_idx, (var_name, pattern) in enumerate(variations):
                # Create frame for each pattern
                frame = QFrame()
                frame.setFrameStyle(QFrame.Shape.Box)
                frame.setStyleSheet("""
                    QFrame {
                        background-color: #333;
                        border: 1px solid #555;
                        border-radius: 5px;
                        padding: 5px;
                    }
                    QFrame:hover {
                        border: 1px solid #4c6ef5;
                    }
                """)
                
                frame_layout = QVBoxLayout()
                frame_layout.setSpacing(5)
                
                # Preview
                preview = PatternPreviewWidget(pattern, self.rows, self.cols)
                frame_layout.addWidget(preview, alignment=Qt.AlignmentFlag.AlignCenter)
                
                # Pattern name label
                cb_name = f"{pattern_name}" if var_idx == 0 else f"{pattern_name} #{var_idx+1}"
                name_label = QLabel(cb_name)
                name_label.setStyleSheet("color: #ccc; font-size: 10px; font-weight: bold;")
                name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                frame_layout.addWidget(name_label)
                
                # +/- button group
                button_layout = QHBoxLayout()
                button_layout.setSpacing(3)
                
                plus_btn = QPushButton("+")
                plus_btn.setFixedSize(25, 25)
                plus_btn.setCheckable(True)
                plus_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #333;
                        color: #51cf66;
                        border: 1px solid #555;
                        border-radius: 3px;
                        font-weight: bold;
                        font-size: 14px;
                    }
                    QPushButton:checked {
                        background-color: #51cf66;
                        color: #000;
                        border: 1px solid #51cf66;
                    }
                    QPushButton:hover {
                        border: 1px solid #51cf66;
                    }
                """)
                plus_btn.setProperty('pattern', pattern)
                plus_btn.setProperty('category', category_name)
                plus_btn.setProperty('target', 1)
                plus_btn.setProperty('partner', None)  # Will set after creating minus button
                plus_btn.clicked.connect(lambda checked, btn=plus_btn: self.onButtonClicked(btn, checked))
                
                minus_btn = QPushButton("-")
                minus_btn.setFixedSize(25, 25)
                minus_btn.setCheckable(True)
                minus_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #333;
                        color: #ff6b6b;
                        border: 1px solid #555;
                        border-radius: 3px;
                        font-weight: bold;
                        font-size: 14px;
                    }
                    QPushButton:checked {
                        background-color: #ff6b6b;
                        color: #fff;
                        border: 1px solid #ff6b6b;
                    }
                    QPushButton:hover {
                        border: 1px solid #ff6b6b;
                    }
                """)
                minus_btn.setProperty('pattern', pattern)
                minus_btn.setProperty('category', category_name)
                minus_btn.setProperty('target', 0)
                minus_btn.setProperty('partner', None)
                minus_btn.clicked.connect(lambda checked, btn=minus_btn: self.onButtonClicked(btn, checked))
                
                # Link buttons as partners (only one can be checked)
                plus_btn.setProperty('partner', minus_btn)
                minus_btn.setProperty('partner', plus_btn)
                
                button_layout.addWidget(plus_btn)
                button_layout.addWidget(minus_btn)
                
                unique_key = f"{category_name}_{pattern_name}_{var_idx}"
                self.checkboxes[unique_key] = (plus_btn, minus_btn)
                
                frame_layout.addLayout(button_layout)
                frame.setLayout(frame_layout)
                
                grid.addWidget(frame, row, col)
                
                col += 1
                if col >= 4:  # 4 columns
                    col = 0
                    row += 1
        
        container.setLayout(grid)
        scroll.setWidget(container)
        return scroll
    
    def onButtonClicked(self, button, checked):
        """Handle +/- button clicks (only one can be active)."""
        if checked:
            # Uncheck partner button
            partner = button.property('partner')
            if partner and partner.isChecked():
                partner.setChecked(False)
        self.updateCount()
    
    def updateCount(self):
        """Update the selected count label."""
        positive = 0
        negative = 0
        for buttons in self.checkboxes.values():
            plus_btn, minus_btn = buttons
            if plus_btn.isChecked():
                positive += 1
            elif minus_btn.isChecked():
                negative += 1
        
        total = positive + negative
        self.count_label.setText(f"Selected: {total} patterns (+ {positive} / - {negative})")
    
    def selectAllInCurrentTab(self):
        """Select all patterns in current tab as positive."""
        current_tab_name = self.tabs.tabText(self.tabs.currentIndex()).split(' (')[0]
        for key, buttons in self.checkboxes.items():
            plus_btn, minus_btn = buttons
            if plus_btn.property('category') == current_tab_name:
                plus_btn.setChecked(True)
    
    def deselectAll(self):
        """Deselect all patterns."""
        for buttons in self.checkboxes.values():
            plus_btn, minus_btn = buttons
            plus_btn.setChecked(False)
            minus_btn.setChecked(False)
    
    def get_selected_patterns(self):
        """Get selected patterns with their explicit positive/negative labels."""
        patterns = []
        
        for buttons in self.checkboxes.values():
            plus_btn, minus_btn = buttons
            if plus_btn.isChecked():
                pattern = plus_btn.property('pattern')
                patterns.append((pattern, 1))  # Positive
            elif minus_btn.isChecked():
                pattern = minus_btn.property('pattern')
                patterns.append((pattern, 0))  # Negative
        
        return patterns
