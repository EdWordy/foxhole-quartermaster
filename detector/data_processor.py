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
            
            # Get human-readable name if mapper exists
            item_name = (self.item_mapper.get_item_name(icon_code) 
                        if self.item_mapper else icon_code)
            
            # Get composed quantity if number mapper exists
            quantity = (self.quantity_composer.compose_quantity(
                number_matches, 
                icon_x + icon_w,  # Look for numbers to the right of the icon
                icon_y           # Align vertically with icon top
            ) if self.quantity_composer else None)
            
            inventory_data.append({
                "Item Code": icon_code,
                "Item Name": item_name,
                "Quantity": quantity if quantity is not None else "N/A",
                #"Confidence": f"{icon['confidence']:.3f}",
                #"X": icon_x,
                #"Y": icon_y
            })
            
        return inventory_data

    def save_to_excel(self, inventory_data, output_path=None, image_path=None):
        """Save inventory data to formatted Excel file."""
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            # If image path is provided, use its name in the output filename
            if image_path:
                base_name = os.path.splitext(os.path.basename(image_path))[0]
                output_path = f"Reports/inv_report_{base_name}_{timestamp}.xlsx"
            else:
                output_path = f"Reports/inv_report_{timestamp}.xlsx"
        
        output_path = Path(output_path)
        df = pd.DataFrame(inventory_data)
        
        # Create Excel writer with formatting
        with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Inventory', index=False)
            
            # Get workbook and worksheet objects
            workbook = writer.book
            worksheet = writer.sheets['Inventory']
            
            # Add formats
            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#D8E4BC',
                'border': 1
            })
            
            cell_format = workbook.add_format({
                'border': 1
            })
            
            # Apply formats
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)
            
            # Color alternate rows for better readability
            row_format_alt = workbook.add_format({
                'border': 1,
                'bg_color': '#F2F2F2'
            })
            
            for row in range(1, len(df) + 1):
                format_to_use = row_format_alt if row % 2 == 0 else cell_format
                for col in range(len(df.columns)):
                    worksheet.write(row, col, df.iloc[row-1, col], format_to_use)
            
            # Auto-adjust column widths
            for i, col in enumerate(df.columns):
                max_length = max(
                    df[col].astype(str).apply(len).max(),
                    len(col)
                ) + 2
                worksheet.set_column(i, i, max_length)
        
        return output_path