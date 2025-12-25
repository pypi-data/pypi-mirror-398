"""Plotting module for training visualization."""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTabWidget
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import numpy as np


class TrainingPlotWidget(QWidget):
    """Widget for displaying training progress plots."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Create matplotlib figure with tabs
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #444;
                background: #2b2b2b;
            }
            QTabBar::tab {
                background: #333;
                color: #ccc;
                padding: 8px 16px;
                margin: 2px;
                border-radius: 4px;
            }
            QTabBar::tab:selected {
                background: #51cf66;
                color: #000;
                font-weight: bold;
            }
        """)
        
        # Error plot tab
        self.error_widget = QWidget()
        self.error_figure = Figure(figsize=(6, 4), facecolor='#2b2b2b')
        self.error_canvas = FigureCanvasQTAgg(self.error_figure)
        self.ax_error = self.error_figure.add_subplot(111)
        error_layout = QVBoxLayout()
        error_layout.addWidget(self.error_canvas)
        error_layout.setContentsMargins(0, 0, 0, 0)
        self.error_widget.setLayout(error_layout)
        
        # Weight evolution plot tab
        self.weight_widget = QWidget()
        self.weight_figure = Figure(figsize=(6, 4), facecolor='#2b2b2b')
        self.weight_canvas = FigureCanvasQTAgg(self.weight_figure)
        self.ax_weights = self.weight_figure.add_subplot(111)
        weight_layout = QVBoxLayout()
        weight_layout.addWidget(self.weight_canvas)
        weight_layout.setContentsMargins(0, 0, 0, 0)
        self.weight_widget.setLayout(weight_layout)
        
        # Add tabs
        self.tab_widget.addTab(self.error_widget, "Error Plot")
        self.tab_widget.addTab(self.weight_widget, "Weight Evolution")
        
        # Style the plots
        self._style_error_plot()
        self._style_weight_plot()
        
        # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.tab_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        
        # Data
        self.epochs = []
        self.errors = []
        self.weight_history = []
        
        # Color palette for weights
        self.colors = [
            '#ff6b6b', '#51cf66', '#339af0', '#ffd43b', 
            '#ff8787', '#69db7c', '#4dabf7', '#ffe066',
            '#fa5252', '#40c057', '#228be6', '#fcc419',
            '#f03e3e', '#37b24d', '#1c7ed6', '#fab005'
        ]
        
    def _style_error_plot(self):
        """Apply dark theme styling to the error plot."""
        self.ax_error.set_facecolor('#1e1e1e')
        self.ax_error.tick_params(colors='#cccccc', which='both')
        self.ax_error.spines['bottom'].set_color('#cccccc')
        self.ax_error.spines['top'].set_color('#cccccc')
        self.ax_error.spines['left'].set_color('#cccccc')
        self.ax_error.spines['right'].set_color('#cccccc')
        self.ax_error.set_xlabel('Epoch', color='#cccccc', fontsize=10)
        self.ax_error.set_ylabel('Errors', color='#cccccc', fontsize=10)
        self.ax_error.set_title('Training Progress', color='#cccccc', fontsize=12, pad=10)
        self.ax_error.grid(True, alpha=0.2, color='#666666')
        self.error_figure.tight_layout()
        
    def _style_weight_plot(self):
        """Apply dark theme styling to the weight evolution plot."""
        self.ax_weights.set_facecolor('#1e1e1e')
        self.ax_weights.tick_params(colors='#cccccc', which='both')
        self.ax_weights.spines['bottom'].set_color('#cccccc')
        self.ax_weights.spines['top'].set_color('#cccccc')
        self.ax_weights.spines['left'].set_color('#cccccc')
        self.ax_weights.spines['right'].set_color('#cccccc')
        self.ax_weights.set_xlabel('Epoch', color='#cccccc', fontsize=10)
        self.ax_weights.set_ylabel('Weight Value', color='#cccccc', fontsize=10)
        self.ax_weights.set_title('Weight Evolution', color='#cccccc', fontsize=12, pad=10)
        self.ax_weights.grid(True, alpha=0.2, color='#666666')
        self.weight_figure.tight_layout()
        
    def update_plot(self, epochs, errors, weight_history=None):
        """Update both plots with new data.
        
        Args:
            epochs: List of epoch numbers
            errors: List of error counts
            weight_history: List of weight arrays (one per epoch)
        """
        self.epochs = epochs
        self.errors = errors
        if weight_history is not None:
            self.weight_history = weight_history
        
        # Update error plot
        self._update_error_plot()
        
        # Update weight evolution plot
        if self.weight_history:
            self._update_weight_plot()
        
    def _update_error_plot(self):
        """Update the error plot."""
        self.ax_error.clear()
        
        if len(self.epochs) > 0:
            # Plot error line
            self.ax_error.plot(self.epochs, self.errors, 'o-', color='#ff6b6b', 
                              linewidth=2, markersize=4, label='Errors')
            
            # Add convergence line
            self.ax_error.axhline(y=0, color='#51cf66', linestyle='--', 
                                 linewidth=1, alpha=0.7, label='Converged')
            
            # Set limits
            self.ax_error.set_xlim(0, max(self.epochs) + 1)
            max_error = max(self.errors) if self.errors else 1
            self.ax_error.set_ylim(-0.5, max_error + 1)
            
            # Legend
            self.ax_error.legend(loc='upper right', facecolor='#2b2b2b', 
                                edgecolor='#666666', labelcolor='#cccccc')
        
        # Reapply styling
        self._style_error_plot()
        
        # Redraw canvas
        self.error_canvas.draw()
    
    def _update_weight_plot(self):
        """Update the weight evolution plot."""
        self.ax_weights.clear()
        
        if len(self.epochs) > 0 and len(self.weight_history) > 0:
            # Convert weight history to numpy array for easier indexing
            weights_array = np.array(self.weight_history)
            num_weights = weights_array.shape[1]
            
            # Plot each weight's evolution
            for i in range(num_weights):
                color = self.colors[i % len(self.colors)]
                self.ax_weights.plot(
                    self.epochs, 
                    weights_array[:, i], 
                    '-', 
                    color=color, 
                    linewidth=2, 
                    alpha=0.8,
                    label=f'W{i}'
                )
            
            # Add zero reference line
            self.ax_weights.axhline(y=0, color='#666666', linestyle=':', 
                                   linewidth=1, alpha=0.5)
            
            # Set limits
            self.ax_weights.set_xlim(0, max(self.epochs) + 1)
            
            # Auto-scale y-axis with some padding
            all_weights = weights_array.flatten()
            if len(all_weights) > 0:
                min_w = np.min(all_weights)
                max_w = np.max(all_weights)
                padding = (max_w - min_w) * 0.1 if max_w != min_w else 1
                self.ax_weights.set_ylim(min_w - padding, max_w + padding)
            
            # Legend (show only if not too many weights)
            if num_weights <= 16:
                self.ax_weights.legend(
                    loc='center left', 
                    bbox_to_anchor=(1, 0.5),
                    facecolor='#2b2b2b', 
                    edgecolor='#666666', 
                    labelcolor='#cccccc',
                    ncol=1 if num_weights <= 8 else 2,
                    fontsize=8
                )
        
        # Reapply styling
        self._style_weight_plot()
        
        # Redraw canvas
        self.weight_canvas.draw()
        
    def clear_plot(self):
        """Clear both plots."""
        self.epochs = []
        self.errors = []
        self.weight_history = []
        
        self.ax_error.clear()
        self._style_error_plot()
        self.error_canvas.draw()
        
        self.ax_weights.clear()
        self._style_weight_plot()
        self.weight_canvas.draw()
