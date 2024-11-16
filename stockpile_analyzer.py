# stockpile_analyzer.py
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
import os

class StockpileAnalyzer:
    def __init__(self):
        # Define categories with default thresholds
        self.categories = {
            'Infantry Equipment': {
                'codes': ['23C'],
                'threshold': 50,
                'description': 'Rifles and basic infantry weapons'
            },
            'Ammunition': {
                'codes': ['24C', '31C', '36C'],
                'threshold': 100,
                'description': '7.62mm, 9mm, 20mm rounds'
            },
            'Uniforms': {
                'codes': ['107C', '110C'],
                'threshold': 10,
                'description': 'Sapper and Medic uniforms'
            },
            'Vehicles': {
                'codes': ['128', '145'],
                'threshold': 2,
                'description': 'APCs and other vehicles'
            },
            'Construction': {
                'codes': ['208C', '232C'],
                'threshold': 10,
                'description': 'Building materials'
            },
            'Logistics': {
                'codes': ['205'],
                'threshold': 5,
                'description': 'Logistics and transport items'
            },
            'Supplies': {
                'codes': ['76C', '80C', '85C', '86C', '93C'],
                'threshold': 10,
                'description': 'Various supplies and equipment'
            }
        }

    def set_threshold(self, category, threshold):
        """Set threshold for a specific category."""
        if category in self.categories:
            self.categories[category]['threshold'] = threshold

    def get_threshold(self, category):
        """Get threshold for a specific category."""
        return self.categories.get(category, {}).get('threshold', 0)

    def load_reports(self, directory_path):
        """Load and combine multiple inventory reports."""
        reports = []
        report_files = list(Path(directory_path).glob('inv_report_*.csv'))
        
        if not report_files:
            raise ValueError("No inventory reports found")
            
        for file in report_files:
            try:
                # Extract timestamp from filename
                timestamp_str = file.stem.split('_')[-2] + '_' + file.stem.split('_')[-1]
                timestamp = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
                
                # Read CSV
                df = pd.read_csv(file)
                df['Timestamp'] = timestamp
                df['Report'] = file.name
                reports.append(df)
                
            except Exception as e:
                print(f"Error loading {file.name}: {str(e)}")
                continue

        if not reports:
            raise ValueError("No valid reports could be loaded")
            
        return pd.concat(reports, ignore_index=True)

    def analyze_changes(self, data):
        """Analyze inventory changes between reports."""
        changes = {}
        
        # Get earliest and latest reports for each item
        latest = data.sort_values('Timestamp').groupby('Item Code').last()
        earliest = data.sort_values('Timestamp').groupby('Item Code').first()
        
        for item_code in latest.index:
            current_qty = latest.loc[item_code, 'Quantity']
            initial_qty = earliest.loc[item_code, 'Quantity']
            item_name = latest.loc[item_code, 'Item Name']
            
            changes[item_code] = {
                'Item Name': item_name,
                'Initial Quantity': initial_qty,
                'Current Quantity': current_qty,
                'Change': current_qty - initial_qty,
                'Percent Change': ((current_qty - initial_qty) / initial_qty * 100) if initial_qty != 0 else 0
            }
            
        return pd.DataFrame.from_dict(changes, orient='index')

    def analyze_categories(self, data):
        """Analyze inventory by category."""
        latest_data = data.sort_values('Timestamp').groupby('Item Code').last()
        
        category_analysis = {}
        for category, info in self.categories.items():
            category_items = latest_data[latest_data.index.isin(info['codes'])]
            
            total_qty = category_items['Quantity'].sum()
            below_threshold = category_items[category_items['Quantity'] < info['threshold']]
            
            category_analysis[category] = {
                'Total Quantity': total_qty,
                'Items Below Threshold': len(below_threshold),
                'Items': ', '.join(f"{row['Item Name']}: {row['Quantity']}" 
                                 for _, row in category_items.iterrows())
            }
            
        return pd.DataFrame.from_dict(category_analysis, orient='index')

    def identify_critical_items(self, data):
        """Identify items below threshold levels."""
        latest_data = data.sort_values('Timestamp').groupby('Item Code').last()
        critical_items = []
        
        for category, info in self.categories.items():
            threshold = info['threshold']
            for code in info['codes']:
                if code in latest_data.index:
                    qty = latest_data.loc[code, 'Quantity']
                    if qty < threshold:
                        critical_items.append({
                            'Category': category,
                            'Item Code': code,
                            'Item Name': latest_data.loc[code, 'Item Name'],
                            'Current Quantity': qty,
                            'Threshold': threshold,
                            'Needed': threshold - qty
                        })
                        
        return pd.DataFrame(critical_items)

    def generate_report(self, data, output_path=None):
        """Generate comprehensive analysis report."""
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"inv_report_analysis_{timestamp}.xlsx"
            
        with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
            # Summary
            summary_data = {
                'Metric': [
                    'Total Reports Analyzed',
                    'Total Unique Items',
                    'Date Range',
                    'Critical Items Count'
                ],
                'Value': [
                    len(data['Report'].unique()),
                    len(data['Item Code'].unique()),
                    f"{data['Timestamp'].min():%Y-%m-%d %H:%M} to {data['Timestamp'].max():%Y-%m-%d %H:%M}",
                    len(self.identify_critical_items(data))
                ]
            }
            pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)
            
            # Changes Analysis
            self.analyze_changes(data).to_excel(writer, sheet_name='Changes')
            
            # Category Analysis
            self.analyze_categories(data).to_excel(writer, sheet_name='Categories')
            
            # Critical Items
            critical_items = self.identify_critical_items(data)
            if not critical_items.empty:
                critical_items.to_excel(writer, sheet_name='Critical Items', index=False)
            
            # Format workbook
            workbook = writer.book
            for worksheet in writer.sheets.values():
                worksheet.autofit()
                
        return output_path

    def get_quick_summary(self, data):
        """Get a quick text summary of the analysis."""
        critical_items = self.identify_critical_items(data)
        category_analysis = self.analyze_categories(data)
        
        summary = f"""Stockpile Analysis Summary
------------------------
Reports Analyzed: {len(data['Report'].unique())}
Time Period: {data['Timestamp'].min():%Y-%m-%d %H:%M} to {data['Timestamp'].max():%Y-%m-%d %H:%M}
Total Unique Items: {len(data['Item Code'].unique())}
Critical Items: {len(critical_items)}

Category Totals:
"""
        
        for category, row in category_analysis.iterrows():
            summary += f"\n{category}:"
            summary += f"\n  Total Quantity: {row['Total Quantity']}"
            summary += f"\n  Items Below Threshold: {row['Items Below Threshold']}"
            
        if not critical_items.empty:
            summary += "\n\nCritical Items Needing Attention:"
            for _, item in critical_items.iterrows():
                summary += f"\n- {item['Item Name']}: {item['Current Quantity']} (Need {item['Needed']} more)"
                
        return summary