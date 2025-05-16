# utils/config_manager.py
"""
Configuration manager for the Foxhole Quartermaster application.
Provides a centralized system for managing all application settings.
"""

import json
import yaml
import os
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Optional, Union


class ConfigManager:
    """Manages all configuration settings for the application."""
    
    def __init__(self, config_file: str = 'config.yaml'):
        """
        Initialize the configuration manager.
        
        Args:
            config_file: Path to the configuration file
        """
        self.config_file = Path(config_file)
        
        # Default thresholds for categories - moved this BEFORE loading config
        self.default_category_thresholds = {
            'Light Arms': 40,
            'Heavy Arms': 25,
            'Munitions': 40,
            'Infantry Equipment': 25,
            'Maintenance': 10,
            'Medical': 15,
            'Uniforms': 10,
            'Vehicles': 5,
            'Materials': 30,
            'Supplies': 20,
            'Logistics': 5,
            'Other': 0
        }
        
        # Now load the config
        self.config = self._load_config()
        
        # Initialize item mappings and thresholds
        self._initialize_mappings()
    
    def _load_config(self) -> Dict[str, Any]:
        """
        Load configuration from file.
        
        Returns:
            Dict containing configuration settings
        """
        if not self.config_file.exists():
            return self._create_default_config()
        
        try:
            if self.config_file.suffix.lower() == '.yaml':
                with open(self.config_file, 'r') as f:
                    return yaml.safe_load(f)
            else:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading configuration: {e}")
            return self._create_default_config()
    
    def _create_default_config(self) -> Dict[str, Any]:
        """
        Create default configuration.
        
        Returns:
            Dict containing default configuration settings
        """
        default_config = {
            'paths': {
                'templates': {
                    'icons': 'CheckImages/Default',
                    'numbers': 'CheckImages/Numbers'
                },
                'reports': 'Reports',
                'logs': 'logs'
            },
            'detection': {
                'confidence_threshold': 0.95,
                'max_digit_distance': 150
            },
            'ui': {
                'show_visualization': False,
                'default_window_size': '1200x800'
            },
            'category_thresholds': self.default_category_thresholds
        }
        
        self._save_config(default_config)
        return default_config
    
    def _save_config(self, config: Dict[str, Any] = None) -> None:
        """
        Save configuration to file.
        
        Args:
            config: Configuration to save (uses self.config if None)
        """
        if config is None:
            config = self.config
            
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
        
        try:
            if self.config_file.suffix.lower() == '.yaml':
                with open(self.config_file, 'w') as f:
                    yaml.dump(config, f, default_flow_style=False)
            else:
                with open(self.config_file, 'w') as f:
                    json.dump(config, f, indent=4)
        except Exception as e:
            print(f"Error saving configuration: {e}")
    
    def _initialize_mappings(self) -> None:
        """Initialize item mappings and thresholds from files."""
        # Load item mappings
        mapping_file = Path(self.config.get('paths', {}).get('item_mappings', 'item_mappings.csv'))
        if mapping_file.exists():
            try:
                self.item_mappings = pd.read_csv(mapping_file).set_index('code').to_dict('index')
            except Exception as e:
                print(f"Error loading item mappings: {e}")
                self.item_mappings = {}
        else:
            self.item_mappings = {}
        
        # Load item thresholds
        threshold_file = Path(self.config.get('paths', {}).get('item_thresholds', 'item_thresholds.json'))
        if threshold_file.exists():
            try:
                with open(threshold_file, 'r') as f:
                    self.item_thresholds = json.load(f)
            except Exception as e:
                print(f"Error loading item thresholds: {e}")
                self.item_thresholds = self._generate_default_thresholds()
        else:
            self.item_thresholds = self._generate_default_thresholds()
    
    def _generate_default_thresholds(self) -> Dict[str, Dict[str, Any]]:
        """
        Generate default thresholds from mappings.
        
        Returns:
            Dict containing default thresholds for each item
        """
        thresholds = {}
        
        for code, item_data in self.item_mappings.items():
            category = item_data.get('category', 'Other')
            category_threshold = self.get_category_threshold(category)
            
            thresholds[code] = {
                'name': item_data.get('name', code),
                'category': category,
                'threshold': category_threshold
            }
        
        return thresholds
    
    def save(self) -> None:
        """Save all configuration to files."""
        # Save main configuration
        self._save_config()
        
        # Save item thresholds
        threshold_file = Path(self.config.get('paths', {}).get('item_thresholds', 'item_thresholds.json'))
        os.makedirs(os.path.dirname(threshold_file), exist_ok=True)
        
        try:
            with open(threshold_file, 'w') as f:
                json.dump(self.item_thresholds, f, indent=4)
        except Exception as e:
            print(f"Error saving item thresholds: {e}")
    
    def get_category_threshold(self, category: str) -> int:
        """
        Get threshold for a category.
        
        Args:
            category: Category name
            
        Returns:
            Threshold value for the category
        """
        return self.config.get('category_thresholds', {}).get(
            category, 
            self.default_category_thresholds.get(category, 0)
        )
    
    def set_category_threshold(self, category: str, threshold: int) -> None:
        """
        Set threshold for a category.
        
        Args:
            category: Category name
            threshold: New threshold value
        """
        if 'category_thresholds' not in self.config:
            self.config['category_thresholds'] = {}
            
        self.config['category_thresholds'][category] = threshold
        
        # Update thresholds for all items in this category
        self.update_thresholds_from_categories()
    
    def get_item_threshold(self, item_code: str) -> int:
        """
        Get threshold for a specific item.
        
        Args:
            item_code: Item code
            
        Returns:
            Threshold value for the item
        """
        if item_code in self.item_thresholds:
            return self.item_thresholds[item_code]['threshold']
        
        # If item not found, try to get category threshold
        category = self.get_item_category(item_code)
        return self.get_category_threshold(category)
    
    def set_item_threshold(self, item_code: str, threshold: int) -> None:
        """
        Set threshold for a specific item.
        
        Args:
            item_code: Item code
            threshold: New threshold value
        """
        if item_code in self.item_thresholds:
            self.item_thresholds[item_code]['threshold'] = threshold
        else:
            # Create new entry if item doesn't exist
            name = self.get_item_name(item_code)
            category = self.get_item_category(item_code)
            
            self.item_thresholds[item_code] = {
                'name': name,
                'category': category,
                'threshold': threshold
            }
    
    def get_item_name(self, item_code: str) -> str:
        """
        Get name for an item.
        
        Args:
            item_code: Item code
            
        Returns:
            Name of the item
        """
        if item_code in self.item_mappings:
            return self.item_mappings[item_code].get('name', item_code)
        return item_code
    
    def get_item_category(self, item_code: str) -> str:
        """
        Get category for an item.
        
        Args:
            item_code: Item code
            
        Returns:
            Category of the item
        """
        if item_code in self.item_mappings:
            return self.item_mappings[item_code].get('category', 'Other')
        return 'Other'
    
    def update_thresholds_from_categories(self) -> None:
        """Update all item thresholds based on their categories."""
        for code, item_data in self.item_thresholds.items():
            category = item_data['category']
            item_data['threshold'] = self.get_category_threshold(category)
    
    def get_template_paths(self) -> Dict[str, str]:
        """
        Get paths to template directories.
        
        Returns:
            Dict containing paths to icon and number templates
        """
        return self.config.get('paths', {}).get('templates', {
            'icons': 'CheckImages/Default',
            'numbers': 'CheckImages/Numbers'
        })
    
    def get_detection_settings(self) -> Dict[str, Any]:
        """
        Get detection settings.
        
        Returns:
            Dict containing detection settings
        """
        return self.config.get('detection', {
            'confidence_threshold': 0.95,
            'max_digit_distance': 150
        })
    
    def get_ui_settings(self) -> Dict[str, Any]:
        """
        Get UI settings.
        
        Returns:
            Dict containing UI settings
        """
        return self.config.get('ui', {
            'show_visualization': False,
            'default_window_size': '1200x800'
        })
    
    def get_reports_path(self) -> str:
        """
        Get path to reports directory.
        
        Returns:
            Path to reports directory
        """
        return self.config.get('paths', {}).get('reports', 'Reports')
    
    def get_logs_path(self) -> str:
        """
        Get path to logs directory.
        
        Returns:
            Path to logs directory
        """
        return self.config.get('paths', {}).get('logs', 'logs')
