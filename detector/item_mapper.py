# detector/item_mapper.py
import pandas as pd
from pathlib import Path

class ItemMapper:
    def __init__(self, mapping_file):
        self.mapping_file = Path(mapping_file)
        self.mappings = self._load_mappings()
        
    def _load_mappings(self):
        """Load item mappings from CSV file."""
        try:
            df = pd.read_csv(self.mapping_file)
            # Convert to dictionary for faster lookups
            return dict(zip(df['code'], df['name']))
        except FileNotFoundError:
            print(f"Warning: Mapping file {self.mapping_file} not found. Using raw codes.")
            return {}
        except pd.errors.EmptyDataError:
            print(f"Warning: Mapping file {self.mapping_file} is empty. Using raw codes.")
            return {}
        except Exception as e:
            print(f"Warning: Error loading mapping file: {e}. Using raw codes.")
            return {}
    
    def get_item_name(self, code):
        """Convert item code to human-readable name."""
        return self.mappings.get(code, code)  # Return original code if no mapping exists