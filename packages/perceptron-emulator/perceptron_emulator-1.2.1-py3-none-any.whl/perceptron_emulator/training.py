"""Training module for the perceptron emulator."""

import numpy as np
from typing import List, Tuple, Dict, Optional


class PerceptronTrainer:
    """Handles perceptron training with the delta rule learning algorithm."""
    
    def __init__(self, num_inputs: int = 4):
        """Initialize the trainer.
        
        Args:
            num_inputs: Number of inputs (e.g., 4 for 2x2 grid, 9 for 3x3, etc.)
        """
        self.num_inputs = num_inputs
        self.weights = np.zeros(num_inputs)
        self.bias = 0.0
        self.learning_rate = 0.1
        
        # Training history
        self.error_history: List[int] = []
        self.weight_history: List[np.ndarray] = []
        self.bias_history: List[float] = []
        self.epoch_count = 0
        
        # Current pattern
        self.current_pattern: Optional[str] = None
        self.patterns: List[Tuple[List[int], int]] = []
        
        # Custom patterns (user-drawn shapes)
        self.custom_patterns: List[Tuple[List[int], int]] = []
    
    def add_custom_pattern(self, inputs: List[int], target: int):
        """Add a custom pattern (user-drawn shape).
        
        Args:
            inputs: Binary input pattern
            target: 1 for positive, 0 for negative
        """
        self.custom_patterns.append((inputs.copy(), target))
    
    def clear_custom_patterns(self):
        """Clear all custom patterns."""
        self.custom_patterns = []
    
    def get_custom_pattern_count(self) -> tuple[int, int]:
        """Get count of positive and negative custom patterns.
        
        Returns:
            Tuple of (positive_count, negative_count)
        """
        positive = sum(1 for _, target in self.custom_patterns if target == 1)
        negative = len(self.custom_patterns) - positive
        return (positive, negative)
    
    def _generate_and_pattern(self) -> List[Tuple[List[int], int]]:
        """Generate AND pattern: output 1 only when ALL inputs are 1.
        
        Returns:
            List of (inputs, target) tuples
        """
        patterns = []
        # Generate all possible binary combinations
        for i in range(2 ** self.num_inputs):
            inputs = [(i >> j) & 1 for j in range(self.num_inputs)]
            target = 1 if all(inputs) else 0
            patterns.append((inputs, target))
        return patterns
    
    def _generate_or_pattern(self) -> List[Tuple[List[int], int]]:
        """Generate OR pattern: output 1 when ANY input is 1.
        
        Returns:
            List of (inputs, target) tuples
        """
        patterns = []
        for i in range(2 ** self.num_inputs):
            inputs = [(i >> j) & 1 for j in range(self.num_inputs)]
            target = 1 if any(inputs) else 0
            patterns.append((inputs, target))
        return patterns
    
    def _generate_nand_pattern(self) -> List[Tuple[List[int], int]]:
        """Generate NAND pattern: output 0 only when ALL inputs are 1.
        
        Returns:
            List of (inputs, target) tuples
        """
        patterns = []
        for i in range(2 ** self.num_inputs):
            inputs = [(i >> j) & 1 for j in range(self.num_inputs)]
            target = 0 if all(inputs) else 1
            patterns.append((inputs, target))
        return patterns
        
    def set_pattern(self, pattern_name: str):
        """Set the training pattern.
        
        Args:
            pattern_name: Name of the pattern ('AND', 'OR', 'NAND', 'CUSTOM')
        """
        if pattern_name == 'CUSTOM':
            self.current_pattern = 'CUSTOM'
            self.patterns = self.custom_patterns
            return
        
        pattern_generators = {
            'AND': self._generate_and_pattern,
            'OR': self._generate_or_pattern,
            'NAND': self._generate_nand_pattern,
        }
        
        if pattern_name not in pattern_generators:
            raise ValueError(f"Unknown pattern: {pattern_name}")
        
        self.current_pattern = pattern_name
        self.patterns = pattern_generators[pattern_name]()
        
    def set_learning_rate(self, rate: float):
        """Set the learning rate.
        
        Args:
            rate: Learning rate (0.01 - 0.5)
        """
        self.learning_rate = max(0.01, min(0.5, rate))
        
    def reset(self):
        """Reset weights, bias, and training history."""
        self.weights = np.zeros(self.num_inputs)
        self.bias = 0.0
        self.error_history = []
        self.weight_history = []
        self.bias_history = []
        self.epoch_count = 0
        
    def compute_output(self, inputs: List[int]) -> float:
        """Compute perceptron output for given inputs.
        
        Args:
            inputs: List of binary inputs
            
        Returns:
            Raw output value (before activation)
        """
        return np.dot(inputs, self.weights) + self.bias
    
    def train_epoch(self) -> int:
        """Train for one epoch on all patterns.
        
        Returns:
            Number of misclassified patterns
        """
        if not self.patterns:
            raise ValueError("No pattern set. Call set_pattern() first.")
        
        errors = 0
        
        for inputs, target in self.patterns:
            # Compute output
            output = self.compute_output(inputs)
            
            # Apply step activation for classification
            predicted = 1 if output > 0 else 0
            
            # Calculate error
            error = target - predicted
            if error != 0:
                errors += 1
            
            # Update weights using delta rule
            # w_i = w_i + η * error * input_i
            for i in range(self.num_inputs):
                self.weights[i] += self.learning_rate * error * inputs[i]
            
            # Update bias
            self.bias += self.learning_rate * error
        
        # Record history
        self.epoch_count += 1
        self.error_history.append(errors)
        self.weight_history.append(self.weights.copy())
        self.bias_history.append(self.bias)
        
        return errors
    
    def has_converged(self) -> bool:
        """Check if training has converged (no errors).
        
        Returns:
            True if last epoch had zero errors
        """
        return len(self.error_history) > 0 and self.error_history[-1] == 0
    
    def get_weights_dict(self) -> Dict[str, float]:
        """Get current weights and bias as a dictionary.
        
        Returns:
            Dictionary with weights and bias
        """
        result = {f'w{i}': float(self.weights[i]) for i in range(self.num_inputs)}
        result['bias'] = float(self.bias)
        return result
