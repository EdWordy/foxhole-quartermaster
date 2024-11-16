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
        # Extract the number if it's in the format 'numX'
        if template_name.startswith('num') and len(template_name) > 3:
            try:
                return str(int(template_name[3:]))
            except ValueError:
                pass
        return self.mappings.get(template_name, template_name)

class QuantityComposer:
    def __init__(self, number_mapper):
        self.number_mapper = number_mapper
    
    def compose_quantity(self, number_matches, reference_x, reference_y, max_distance=150):
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
                abs(y - reference_y) < h * 1.5):  # Vertical tolerance
                relevant_numbers.append({
                    **match,
                    "distance_from_ref": x - reference_x
                })
        
        if not relevant_numbers:
            return None
        
        # Sort by x coordinate to get correct digit order
        relevant_numbers.sort(key=lambda m: m["location"][0])
        
        # Group digits that are close to each other
        digit_groups = []
        current_group = [relevant_numbers[0]]
        
        for i in range(1, len(relevant_numbers)):
            curr = relevant_numbers[i]
            prev = relevant_numbers[i-1]
            curr_x = curr["location"][0]
            prev_x = prev["location"][0]
            
            # If digits are close enough, add to current group
            if curr_x - prev_x <= 40:  # Increased maximum gap between digits
                current_group.append(curr)
            else:
                # Start new group if gap is too large
                digit_groups.append(current_group)
                current_group = [curr]
        
        digit_groups.append(current_group)
        
        # Use the group closest to the reference point
        if digit_groups:
            best_group = min(digit_groups, 
                           key=lambda group: min(d["distance_from_ref"] for d in group))
            
            # Compose the number from the best group
            composed_number = ''
            for match in best_group:
                digit = self.number_mapper.get_number_value(match["template_name"])
                composed_number += str(digit)
                
            try:
                return int(composed_number)
            except ValueError:
                return None
                
        return None