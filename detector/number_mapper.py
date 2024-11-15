# detector/number_mapper.py
import pandas as pd
from pathlib import Path

class NumberMapper:
    def __init__(self, mapping_file=None):
        self.mapping_file = Path(mapping_file) if mapping_file else None
        self.mappings = self._load_mappings()
    
    def _load_mappings(self):
        """Load number template mappings from CSV file."""
        if not self.mapping_file:
            # Default mappings if no file provided
            return {f'num{i}': str(i) for i in range(10)}
        
        try:
            df = pd.read_csv(self.mapping_file)
            return dict(zip(df['template'], df['value']))
        except Exception as e:
            print(f"Warning: Using default number mappings. Error: {e}")
            return {f'num{i}': str(i) for i in range(10)}
    
    def get_number_value(self, template_name):
        """Convert number template name to actual value."""
        return self.mappings.get(template_name, template_name)

class QuantityComposer:
    def __init__(self, number_mapper):
        self.number_mapper = number_mapper
    
    def compose_quantity(self, number_matches, reference_x, reference_y, max_distance=100):
        """
        Compose multi-digit numbers from individual digit matches.
        Args:
            number_matches: List of number template matches
            reference_x: X coordinate to measure distance from (usually icon position)
            reference_y: Y coordinate for vertical alignment
            max_distance: Maximum horizontal distance to consider for digit matching
        """
        relevant_numbers = []
        
        # Filter numbers that are close enough horizontally and vertically aligned
        for match in number_matches:
            x, y, w, h = match["location"]
            if (x > reference_x and 
                x < reference_x + max_distance and 
                abs(y - reference_y) < h):
                relevant_numbers.append(match)
        
        if not relevant_numbers:
            return None
        
        # Sort by x coordinate to get correct digit order
        relevant_numbers.sort(key=lambda m: m["location"][0])
        
        # Compose the number from individual digits
        composed_number = ''
        for match in relevant_numbers:
            digit = self.number_mapper.get_number_value(match["template_name"])
            composed_number += str(digit)
            
        try:
            return int(composed_number)
        except ValueError:
            return None