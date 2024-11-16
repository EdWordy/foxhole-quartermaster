# detector/data_processor.py
import pandas as pd
from datetime import datetime
from pathlib import Path
import os
from detector.number_mapper import QuantityComposer  # Added this import

class DataProcessor:
    def __init__(self, item_mapper=None, number_mapper=None):
        self.item_mapper = item_mapper
        self.quantity_composer = QuantityComposer(number_mapper) if number_mapper else None
        
    def process_inventory_data(self, icon_matches, number_matches):
        """Process matches and associate numbers with icons."""
        inventory_data = []
        
        for icon in icon_matches:
            icon_x, icon_y, icon_w, icon_h = icon["location"]
            icon_code = icon["template_name"]
            
            # Get human-readable name and category if mapper exists
            item_name, category = None, None
            if self.item_mapper:
                item_name = self.item_mapper.get_item_name(icon_code)
                category = self.item_mapper.get_item_category(icon_code)
            else:
                item_name = icon_code
                category = "Unknown"
            
            # Get composed quantity if number mapper exists
            quantity = (self.quantity_composer.compose_quantity(
                number_matches, 
                icon_x + icon_w,
                icon_y
            ) if self.quantity_composer else None)
            
            inventory_data.append({
                "Item Code": icon_code,
                "Item Name": item_name,
                "Category": category,
                "Quantity": quantity if quantity is not None else "N/A",
                "Confidence": f"{icon['confidence']:.3f}",
                "X": icon_x,
                "Y": icon_y
            })
            
        return inventory_data

    def save_to_excel(self, inventory_data, output_path=None, image_path=None):
        """Save inventory data to CSV file."""
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if image_path:
                base_name = os.path.splitext(os.path.basename(image_path))[0]
                output_path = f"Reports/inv_report_{base_name}_{timestamp}.csv"
            else:
                output_path = f"Reports/inv_report_{timestamp}.csv"
        else:
            output_path = output_path.replace('.xlsx', '.csv')

        # Save as CSV
        df = pd.DataFrame(inventory_data)
        df.to_csv(output_path, index=False)
        
        return output_path