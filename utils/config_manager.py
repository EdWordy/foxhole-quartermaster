# utils/config_manager.py
"""
Configuration manager for the Foxhole Quartermaster application.
Provides a centralized system for managing all application settings.
"""

import json
import yaml
import os
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
        
        # Default thresholds for categories
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
        
        # Category mapping from game categories to our categories
        self.category_map = {
            'EItemCategory::SmallArms': 'Light Arms',
            'EItemCategory::HeavyArms': 'Heavy Arms',
            'EItemCategory::HeavyAmmo': 'Heavy Arms',
            'EItemCategory::Utility': 'Infantry Equipment',
            'EItemCategory::Medical': 'Medical',
            'EItemCategory::Supplies': 'Supplies',
            'EItemCategory::Resource': 'Materials',
            'EItemCategory::Uniforms': 'Uniforms',
            'EItemCategory::Ammunition': 'Munitions',
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
                'catalog': 'data/catalog.json',
                'templates': {
                    'base': 'data/processed_templates',
                    'numbers': 'data/numbers'
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
        os.makedirs(os.path.dirname(self.config_file) or '.', exist_ok=True)
        
        try:
            if self.config_file.suffix.lower() == '.yaml':
                with open(self.config_file, 'w') as f:
                    yaml.dump(config, f, default_flow_style=False)
            else:
                with open(self.config_file, 'w') as f:
                    json.dump(config, f, indent=4)
        except Exception as e:
            print(f"Error saving configuration: {e}")
    
    def _load_catalog(self) -> List[Dict[str, Any]]:
        """
        Load the game catalog file.
        
        Returns:
            List of catalog entries
        """
        catalog_path = Path(self.config.get('paths', {}).get('catalog', 'data/catalog.json'))
        
        if not catalog_path.exists():
            print(f"Warning: Catalog file not found at {catalog_path}")
            return []
        
        try:
            with open(catalog_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading catalog: {e}")
            return []
    
    def _map_category(self, item_category: str) -> str:
        """
        Map game category to application category.
        
        Args:
            item_category: Game category string (e.g., 'EItemCategory::Supplies')
            
        Returns:
            Mapped category name
        """
        return self.category_map.get(item_category, 'Other')
    
    def _extract_icon_filename(self, icon_path: str) -> str:
        """
        Extract the filename from the icon path.
        
        Args:
            icon_path: Full icon path from catalog (e.g., 'War/Content/Textures/UI/ItemIcons/ResouceAluminumIcon.0')
            
        Returns:
            Clean filename for template matching
        """
        if not icon_path:
            return ""
        
        # Extract filename without path and extension
        parts = icon_path.split('/')
        if parts:
            filename = parts[-1]
            # Remove .0 suffix if present
            if filename.endswith('.0'):
                filename = filename[:-2]
            return filename
        
        return ""
    
    def _initialize_mappings(self) -> None:
        """Initialize item mappings and thresholds from catalog."""
        # Load catalog
        catalog = self._load_catalog()
        
        # Build item mappings from catalog
        self.item_mappings = {}
        
        for entry in catalog:
            code_name = entry.get('CodeName')
            if not code_name:
                continue
            
            # Determine category
            item_category = entry.get('ItemCategory', '')
            vehicle_profile = entry.get('VehicleProfileType', '')
            
            # Map to our category system
            if vehicle_profile:
                category = 'Vehicles'
            else:
                category = self._map_category(item_category)
            
            # Extract icon filename for template matching
            icon_path = entry.get('Icon', '')
            icon_filename = self._extract_icon_filename(icon_path)
            
            # Store mapping
            self.item_mappings[code_name] = {
                'name': entry.get('DisplayName', code_name),
                'category': category,
                'description': entry.get('Description', ''),
                'icon': icon_path,
                'icon_filename': icon_filename,
                'encumbrance': entry.get('Encumbrance', 0)
            }
        
        # Load item thresholds
        threshold_file = Path(self.config.get('paths', {}).get('item_thresholds', 'data/item_thresholds.json'))
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
    
    def get_template_path_for_item(self, item_code: str) -> Optional[Path]:
        """
        Get the template image path for an item.
        
        Args:
            item_code: Item code name
            
        Returns:
            Path to the template image, or None if not found
        """
        if item_code not in self.item_mappings:
            return None
        
        icon_filename = self.item_mappings[item_code].get('icon_filename', '')
        if not icon_filename:
            return None
        
        base_path = Path(self.config.get('paths', {}).get('templates', {}).get('base', 'data/processed_templates'))
        template_path = base_path / item_code / f"{icon_filename}.png"
        
        return template_path if template_path.exists() else None
    
    def save(self) -> None:
        """Save all configuration to files."""
        # Save main configuration
        self._save_config()
        
        # Save item thresholds
        threshold_file = Path(self.config.get('paths', {}).get('item_thresholds', 'data/item_thresholds.json'))
        os.makedirs(os.path.dirname(threshold_file) or '.', exist_ok=True)
        
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
            Name of the item (with "(crate)" suffix for crated items)
        """
        # Check if it's a crated item
        if item_code.endswith('_crated'):
            # Get the base item name
            base_code = item_code.replace('_crated', '')
            if base_code in self.item_mappings:
                base_name = self.item_mappings[base_code].get('name', base_code)
                return f"{base_name} (crate)"
            return item_code
        elif item_code.endswith('C') and len(item_code) > 1:
            # Try alternate crated format (e.g., "207C")
            base_code = item_code[:-1]
            if base_code in self.item_mappings:
                base_name = self.item_mappings[base_code].get('name', base_code)
                return f"{base_name} (crate)"
            return item_code
        
        # Regular item
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
        # Check if it's a crated item
        if item_code.endswith('_crated'):
            # Get the base item category
            base_code = item_code.replace('_crated', '')
            if base_code in self.item_mappings:
                return self.item_mappings[base_code].get('category', 'Other')
            return 'Other'
        elif item_code.endswith('C') and len(item_code) > 1:
            # Try alternate crated format
            base_code = item_code[:-1]
            if base_code in self.item_mappings:
                return self.item_mappings[base_code].get('category', 'Other')
            return 'Other'
        
        # Regular item
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
            Dict containing paths to base templates and number templates
        """
        templates = self.config.get('paths', {}).get('templates', {})
        return {
            'base': templates.get('base', 'data/processed_templates'),
            'numbers': templates.get('numbers', 'data/numbers')
        }
    
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