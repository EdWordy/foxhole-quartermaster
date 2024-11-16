# detector/item_mapper.py
import pandas as pd
from pathlib import Path

class ItemMapper:
    def __init__(self, mapping_file):
        self.mapping_file = Path(mapping_file)
        self.mappings = {}
        self.categories = {}
        self._load_mappings()
        
    def _load_mappings(self):
        """Load item mappings from CSV file."""
        try:
            df = pd.read_csv(self.mapping_file)
            # Create mappings dictionary
            for _, row in df.iterrows():
                self.mappings[row['code']] = row['name']
                self.categories[row['code']] = row['category']
        except FileNotFoundError:
            print(f"Warning: Mapping file {self.mapping_file} not found. Using raw codes.")
        except Exception as e:
            print(f"Warning: Error loading mapping file: {e}. Using raw codes.")
            
    def get_item_name(self, code):
        """Get item name from code."""
        return self.mappings.get(code, code)
    
    def get_item_category(self, code):
        """Get item category from code."""
        return self.categories.get(code, "Unknown")
        
    def get_all_categories(self):
        """Get list of all unique categories."""
        return list(set(self.categories.values()))