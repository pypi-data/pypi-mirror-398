import numpy as np

class Perceptron:
    def __init__(self, rows=4, cols=4):
        """
        Initialize perceptron with variable grid size.
        
        Args:
            rows: Number of rows in the input grid
            cols: Number of columns in the input grid
        """
        self.rows = rows
        self.cols = cols
        self.input_count = rows * cols
        # Initialize inputs to 0 (OFF)
        self.inputs = np.zeros(self.input_count, dtype=int)
        # Initialize weights to 0.0
        self.weights = np.zeros(self.input_count, dtype=float)
        # Initialize bias to 0.0
        self.bias = 0.0

    def set_input(self, index, value):
        """Sets the input at index to 1 (ON) or 0 (OFF)."""
        if 0 <= index < self.input_count:
            self.inputs[index] = 1 if value else 0

    def set_weight(self, index, value):
        """Sets the weight at index. Value should be between -30 and 30."""
        if 0 <= index < self.input_count:
            self.weights[index] = value

    def set_bias(self, value):
        """Sets the bias. Value should be between -30 and 30."""
        self.bias = value

    def calculate_output(self):
        """Calculates the dot product of inputs and weights, adds bias."""
        # y = sum(x_i * w_i) + b
        weighted_sum = np.dot(self.inputs, self.weights) + self.bias
        return weighted_sum
