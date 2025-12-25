from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, pyqtSignal, QPointF
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QRadialGradient, QConicalGradient, QPainterPath, QFont
import math


class ToggleSwitch(QWidget):
    """A physical-looking toggle switch widget."""
    toggled = pyqtSignal(bool)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.state = False
        self.setFixedSize(40, 40)
        self.setStyleSheet("background: transparent;")
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw switch base (dark circle)
        painter.setPen(QPen(QColor(40, 40, 40), 2))
        painter.setBrush(QBrush(QColor(60, 60, 60)))
        painter.drawEllipse(2, 2, 36, 36)
        
        # Draw switch toggle
        if self.state:
            # ON state - red/orange glow
            gradient = QRadialGradient(20, 20, 15)
            gradient.setColorAt(0, QColor(255, 100, 50))
            gradient.setColorAt(1, QColor(180, 50, 20))
            painter.setBrush(QBrush(gradient))
        else:
            # OFF state - dark gray
            painter.setBrush(QBrush(QColor(80, 80, 80)))
        
        painter.drawEllipse(8, 8, 24, 24)
    
    def mousePressEvent(self, event):
        self.state = not self.state
        self.toggled.emit(self.state)
        self.update()


class LEDBulb(QWidget):
    """A physical-looking LED indicator."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.state = False
        self.setFixedSize(30, 30)
        self.setStyleSheet("background: transparent;")
    
    def setState(self, state):
        self.state = state
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw LED housing
        painter.setPen(QPen(QColor(30, 30, 30), 1))
        painter.setBrush(QBrush(QColor(40, 40, 40)))
        painter.drawEllipse(2, 2, 26, 26)
        
        # Draw LED light
        if self.state:
            # ON - bright red glow
            gradient = QRadialGradient(15, 15, 12)
            gradient.setColorAt(0, QColor(255, 80, 80, 255))
            gradient.setColorAt(0.5, QColor(255, 40, 40, 200))
            gradient.setColorAt(1, QColor(180, 20, 20, 100))
            painter.setBrush(QBrush(gradient))
        else:
            # OFF - dark red
            painter.setBrush(QBrush(QColor(60, 20, 20)))
        
        painter.drawEllipse(5, 5, 20, 20)


class RotaryKnob(QWidget):
    """A physical-looking rotary potentiometer/knob."""
    valueChanged = pyqtSignal(float)
    
    def __init__(self, min_value=-30.0, max_value=30.0, parent=None):
        super().__init__(parent)
        self.min_value = min_value
        self.max_value = max_value
        self.value = 0.0
        self.angle = -90.0  # Zero at top: -90° (with range from -225° to +45°)
        self.dragging = False
        self.setMinimumSize(100, 100)
        self.setStyleSheet("background: transparent;")
    
    def sizeHint(self):
        from PyQt6.QtCore import QSize
        return QSize(100, 100)
    
    def setValue(self, value):
        self.value = max(self.min_value, min(self.max_value, value))
        # Map value to angle: 0 at -90° (top), negative CCW, positive CW
        # Range: -225° (min) to +45° (max), with 0 at -90°
        value_range = self.max_value - self.min_value
        normalized = (self.value - self.min_value) / value_range
        self.angle = -225 + (normalized * 270)
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Use relative sizing based on widget size
        width = self.width()
        height = self.height()
        center_x, center_y = width / 2, height / 2
        radius = min(width, height) * 0.28  # 28% of smallest dimension
        
        # Draw knob body (metallic look)
        gradient = QRadialGradient(center_x, center_y, radius)
        gradient.setColorAt(0, QColor(120, 120, 120))
        gradient.setColorAt(0.7, QColor(80, 80, 80))
        gradient.setColorAt(1, QColor(50, 50, 50))
        painter.setBrush(QBrush(gradient))
        painter.setPen(QPen(QColor(30, 30, 30), 2))
        painter.drawEllipse(int(center_x - radius), int(center_y - radius), 
                          int(radius * 2), int(radius * 2))
        
        # Draw tick marks and value labels around the knob
        font_size = max(7, int(height * 0.08))
        painter.setFont(QFont("Arial", font_size, QFont.Weight.Bold))
        
        # Key positions with zero at top (-90°)
        labels = [
            (-225, str(int(self.min_value))),  # -30 (bottom left)
            (-157.5, str(int(self.min_value / 2))),  # -15 (left)
            (-90, "0"),  # 0 (top)
            (-22.5, str(int(self.max_value / 2))),  # +15 (right)
            (45, str(int(self.max_value)))  # +30 (bottom right)
        ]
        
        for angle, label in labels:
            rad = math.radians(angle)
            
            # Draw tick mark
            if label == "0":
                painter.setPen(QPen(QColor(255, 200, 100), 2))
                tick_length = radius * 0.4
            else:
                painter.setPen(QPen(QColor(200, 200, 200), 1))
                tick_length = radius * 0.32
            
            x1 = center_x + (radius + 3) * math.cos(rad)
            y1 = center_y + (radius + 3) * math.sin(rad)
            x2 = center_x + (radius + 3 + tick_length) * math.cos(rad)
            y2 = center_y + (radius + 3 + tick_length) * math.sin(rad)
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))
            
            # Draw value label - positioned further out
            label_distance = radius + tick_length + 12
            label_x = center_x + label_distance * math.cos(rad)
            label_y = center_y + label_distance * math.sin(rad)
            
            if label == "0":
                painter.setPen(QPen(QColor(255, 200, 100)))
            else:
                painter.setPen(QPen(QColor(220, 220, 220)))
            
            # Center the text
            fm = painter.fontMetrics()
            text_width = fm.horizontalAdvance(label)
            text_height = fm.height()
            painter.drawText(
                int(label_x - text_width / 2),
                int(label_y + text_height / 4),
                label
            )
        
        # Draw pointer indicator
        painter.setPen(QPen(QColor(255, 100, 50), 3))
        rad = math.radians(self.angle)
        pointer_x = center_x + (radius - 5) * math.cos(rad)
        pointer_y = center_y + (radius - 5) * math.sin(rad)
        painter.drawLine(int(center_x), int(center_y), int(pointer_x), int(pointer_y))
        
        # Draw center cap
        cap_radius = radius * 0.2
        painter.setBrush(QBrush(QColor(60, 60, 60)))
        painter.setPen(QPen(QColor(40, 40, 40), 1))
        painter.drawEllipse(int(center_x - cap_radius), int(center_y - cap_radius), 
                          int(cap_radius * 2), int(cap_radius * 2))
    
    def mousePressEvent(self, event):
        self.dragging = True
        self.updateFromMouse(event.pos())
    
    def mouseMoveEvent(self, event):
        if self.dragging:
            self.updateFromMouse(event.pos())
    
    def mouseReleaseEvent(self, event):
        self.dragging = False
    
    def updateFromMouse(self, pos):
        # Calculate angle from center (using relative position)
        center_x = self.width() / 2
        center_y = self.height() / 2
        dx = pos.x() - center_x
        dy = pos.y() - center_y
        angle_rad = math.atan2(dy, dx)
        angle_deg = math.degrees(angle_rad)
        
        # Constrain to -225° to +45° (270° range with zero at -90°)
        # Normalize to -180 to +180 range first
        while angle_deg > 180:
            angle_deg -= 360
        while angle_deg < -180:
            angle_deg += 360
        
        # Constrain to valid range
        if angle_deg < -225:
            angle_deg = -225
        elif angle_deg > 45:
            angle_deg = 45
        
        self.angle = angle_deg
        
        # Map angle back to value (-225° = min, -90° = 0, +45° = max)
        normalized = (angle_deg + 225) / 270
        self.value = self.min_value + (normalized * (self.max_value - self.min_value))
        
        self.valueChanged.emit(self.value)
        self.update()


class AnalogMeter(QWidget):
    """A physical-looking analog meter with a needle."""
    
    def __init__(self, min_value=-100.0, max_value=100.0, parent=None):
        super().__init__(parent)
        self.min_value = min_value
        self.max_value = max_value
        self.value = 0.0
        self.setMinimumSize(240, 160)
        self.setStyleSheet("background: transparent;")
    
    def sizeHint(self):
        from PyQt6.QtCore import QSize
        return QSize(240, 160)
    
    def setValue(self, value):
        self.value = max(self.min_value, min(self.max_value, value))
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Use relative sizing
        width = self.width()
        height = self.height()
        
        # Draw meter face (beige/cream background)
        margin = width * 0.04
        painter.setPen(QPen(QColor(40, 40, 40), 3))
        painter.setBrush(QBrush(QColor(240, 235, 220)))
        painter.drawRoundedRect(int(margin), int(margin), 
                              int(width - 2 * margin), int(height - 2 * margin), 5, 5)
        
        # Draw scale arc
        center_x = width / 2
        center_y = height * 0.7  # Position center lower for better arc visibility
        radius = min(width, height) * 0.48
        
        # Draw tick marks and labels
        painter.setPen(QPen(QColor(0, 0, 0), 2))
        font_size = max(8, int(height * 0.065))
        painter.setFont(QFont("Arial", font_size, QFont.Weight.Bold))
        
        # Create labels for the scale with zero at top
        # -135° = min value, -90° = zero (top), -45° = max value
        num_ticks = 11
        for i in range(num_ticks):
            # Zero at top: -135° (min) to -45° (max), with -90° at center (zero)
            angle = -135 + (i * 9)  # 90 degree arc
            rad = math.radians(angle)
            
            # Calculate the value this tick represents
            normalized = i / (num_ticks - 1)
            tick_value = self.min_value + (normalized * (self.max_value - self.min_value))
            
            # Tick mark
            if i == num_ticks // 2:  # Center (zero) at -90°
                painter.setPen(QPen(QColor(200, 0, 0), 3))
                tick_length = radius * 0.24
            elif i % 2 == 0:  # Major ticks
                painter.setPen(QPen(QColor(0, 0, 0), 2))
                tick_length = radius * 0.19
            else:  # Minor ticks
                painter.setPen(QPen(QColor(0, 0, 0), 1))
                tick_length = radius * 0.13
            
            x1 = center_x + (radius - tick_length) * math.cos(rad)
            y1 = center_y + (radius - tick_length) * math.sin(rad)
            x2 = center_x + radius * math.cos(rad)
            y2 = center_y + radius * math.sin(rad)
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))
            
            # Draw value labels only for min, zero, and max to avoid overlap
            if i == 0 or i == num_ticks // 2 or i == num_ticks - 1:
                label = str(int(tick_value))
                label_distance = radius - tick_length - height * 0.15
                label_x = center_x + label_distance * math.cos(rad)
                label_y = center_y + label_distance * math.sin(rad)
                
                if i == num_ticks // 2:  # Zero
                    painter.setPen(QPen(QColor(200, 0, 0)))
                else:
                    painter.setPen(QPen(QColor(0, 0, 0)))
                
                fm = painter.fontMetrics()
                text_width = fm.horizontalAdvance(label)
                text_height = fm.height()
                painter.drawText(
                    int(label_x - text_width / 2),
                    int(label_y + text_height / 4),
                    label
                )
        
        # Calculate needle angle based on value
        # Map value to angle: min=-135°, zero=-90°, max=-45°
        value_range = self.max_value - self.min_value
        normalized = (self.value - self.min_value) / value_range if value_range != 0 else 0.5
        needle_angle = -135 + (normalized * 90)  # Map to -135° to -45°
        
        # Draw needle
        painter.setPen(QPen(QColor(180, 0, 0), 3))
        rad = math.radians(needle_angle)
        needle_length = radius - tick_length - height * 0.05
        needle_x = center_x + needle_length * math.cos(rad)
        needle_y = center_y + needle_length * math.sin(rad)
        painter.drawLine(int(center_x), int(center_y), int(needle_x), int(needle_y))
        
        # Draw center pivot
        pivot_radius = radius * 0.065
        painter.setBrush(QBrush(QColor(60, 60, 60)))
        painter.setPen(QPen(QColor(40, 40, 40), 1))
        painter.drawEllipse(int(center_x - pivot_radius), int(center_y - pivot_radius), 
                          int(pivot_radius * 2), int(pivot_radius * 2))
