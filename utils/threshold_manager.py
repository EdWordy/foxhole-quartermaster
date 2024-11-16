# utils/threshold_manager.py
import pandas as pd
import json
from pathlib import Path
import os

class ThresholdManager:
    def __init__(self, mappings_file='item_mappings.csv', settings_file='item_thresholds.json'):
        self.mappings_file = Path(mappings_file)
        self.settings_file = Path(settings_file)
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
        self.thresholds = self.load_thresholds()
    
    def generate_default_thresholds(self):
        """Generate default thresholds from mappings file."""
        try:
            if not self.mappings_file.exists():
                return {}
                
            df = pd.read_csv(self.mappings_file)
            thresholds = {}
            
            for _, row in df.iterrows():
                # Get default threshold from category, or use 'Other' if category not found
                category_threshold = self.default_category_thresholds.get(
                    row['category'], 
                    self.default_category_thresholds['Other']
                )
                
                thresholds[row['code']] = {
                    'name': row['name'],
                    'category': row['category'],
                    'threshold': category_threshold
                }
            
            return thresholds
            
        except Exception as e:
            print(f"Error generating default thresholds: {e}")
            return {}
    
    def load_thresholds(self):
        """Load existing thresholds or generate new ones."""
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                print("Invalid threshold file, generating new one")
        
        # Generate new thresholds if file doesn't exist or is invalid
        thresholds = self.generate_default_thresholds()
        self.save_thresholds(thresholds)
        return thresholds
    
    def save_thresholds(self, thresholds):
        """Save thresholds to file."""
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(thresholds, f, indent=4)
        except Exception as e:
            print(f"Error saving thresholds: {e}")
    
    def update_threshold(self, item_code, new_threshold):
        """Update threshold for a specific item."""
        if item_code in self.thresholds:
            self.thresholds[item_code]['threshold'] = new_threshold
            self.save_thresholds(self.thresholds)
    
    def get_threshold(self, item_code):
        """Get threshold for a specific item."""
        if item_code in self.thresholds:
            return self.thresholds[item_code]['threshold']
        return self.default_category_thresholds['Other']
    
    def update_from_mappings(self):
        """Update thresholds when mappings change."""
        new_thresholds = self.generate_default_thresholds()
        
        # Preserve existing thresholds for items that still exist
        for item_code, item_data in new_thresholds.items():
            if item_code in self.thresholds:
                item_data['threshold'] = self.thresholds[item_code]['threshold']
        
        self.thresholds = new_thresholds
        self.save_thresholds(self.thresholds)