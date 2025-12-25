"""Configuration management for Perceptron Emulator using XDG directories."""
import json
import os
from pathlib import Path


class ConfigManager:
    """Manages saving and loading of perceptron weights and bias."""
    
    def __init__(self, app_name="perceptron-emulator"):
        self.app_name = app_name
        self.config_dir = self._get_config_dir()
        self.config_file = self.config_dir / "config.json"
        self.presets_dir = self.config_dir / "presets"
        
        # Ensure directories exist
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.presets_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_config_dir(self):
        """Get XDG config directory for the application."""
        xdg_config_home = os.environ.get('XDG_CONFIG_HOME')
        if xdg_config_home:
            base_dir = Path(xdg_config_home)
        else:
            base_dir = Path.home() / '.config'
        
        return base_dir / self.app_name
    
    def save_current_state(self, rows, cols, weights, bias):
        """Save current grid size, weights, and bias to config file."""
        config = {
            'grid': {
                'rows': rows,
                'cols': cols
            },
            'weights': weights.tolist(),
            'bias': bias
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
    
    def load_current_state(self):
        """Load the last saved state from config file."""
        if not self.config_file.exists():
            return None
        
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
            return config
        except (json.JSONDecodeError, KeyError):
            return None
    
    def save_preset(self, name, rows, cols, weights, bias):
        """Save a named preset configuration."""
        preset = {
            'grid': {
                'rows': rows,
                'cols': cols
            },
            'weights': weights.tolist(),
            'bias': bias
        }
        
        preset_file = self.presets_dir / f"{name}.json"
        with open(preset_file, 'w') as f:
            json.dump(preset, f, indent=2)
    
    def load_preset(self, name):
        """Load a named preset configuration."""
        preset_file = self.presets_dir / f"{name}.json"
        if not preset_file.exists():
            return None
        
        try:
            with open(preset_file, 'r') as f:
                preset = json.load(f)
            return preset
        except (json.JSONDecodeError, KeyError):
            return None
    
    def list_presets(self):
        """List all available preset names."""
        presets = []
        for file in self.presets_dir.glob("*.json"):
            presets.append(file.stem)
        return sorted(presets)
    
    def delete_preset(self, name):
        """Delete a named preset."""
        preset_file = self.presets_dir / f"{name}.json"
        if preset_file.exists():
            preset_file.unlink()
            return True
        return False
