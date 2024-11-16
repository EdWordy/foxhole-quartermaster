# stockpile_analyzer.py
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
import os

class StockpileAnalyzer:
    def __init__(self, mapping_file='item_mappings.csv'):
        from utils.threshold_manager import ThresholdManager
        self.threshold_manager = ThresholdManager(mapping_file)
        # Default thresholds for categories
        self.default_thresholds = {
            'Light Arms': 40,
            'Heavy Arms': 25,
            'Munitions': 40,
            'Infantry Equipment': 25,
            'Maintenance': 10,
            'Medical': 15,
            'Uniforms': 10,
            'Vehicles': 5,
            'Materials': 25,
            'Supplies': 20,
            'Logistics': 5,
            'Other': 0  # Default for uncategorized items
        }
        
        # Load mappings and build categories
        self.load_mappings(mapping_file)

    def load_mappings(self, mapping_file):
        """Load item mappings and build categories dynamically."""
        try:
            df = pd.read_csv(mapping_file)
            
            # Initialize categories based on unique categories in mappings
            self.categories = {}
            unique_categories = df['category'].unique()
            
            for category in unique_categories:
                category_items = df[df['category'] == category]
                self.categories[category] = {
                    'codes': category_items['code'].tolist(),
                    'threshold': self.default_thresholds.get(category, 5),
                    'description': f"Items: {', '.join(category_items['name'].tolist())}"
                }
                
        except Exception as e:
            print(f"Error loading mappings: {str(e)}")
            # Initialize with empty categories if file can't be loaded
            self.categories = {}

    def add_item_mapping(self, code, name, category):
        """Add or update an item mapping."""
        if category not in self.categories:
            self.categories[category] = {
                'codes': [code],
                'threshold': self.default_thresholds.get(category, 5),
                'description': f"Items: {name}"
            }
        else:
            if code not in self.categories[category]['codes']:
                self.categories[category]['codes'].append(code)
                self.categories[category]['description'] = self.categories[category]['description'] + f", {name}"

    def save_mappings(self, mapping_file='item_mappings.csv'):
        """Save current mappings back to CSV."""
        mappings = []
        for category, info in self.categories.items():
            for code in info['codes']:
                mappings.append({
                    'code': code,
                    'name': self.get_item_name(code),
                    'category': category
                })
        
        pd.DataFrame(mappings).to_csv(mapping_file, index=False)

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
    
    def get_summary(self, data):
        """Generate a text summary of the stockpile analysis."""
        try:
            # Get basic stats
            total_items = len(data['Item Code'].unique())
            total_reports = len(data['Report'].unique()) if 'Report' in data.columns else 1
            date_range = f"{data['Timestamp'].min():%Y-%m-%d %H:%M} to {data['Timestamp'].max():%Y-%m-%d %H:%M}"
            
            # Get category summaries
            category_totals = data.groupby('Category')['Quantity'].agg(['sum', 'count']).round(2)
            
            # Count critical items
            critical_items = self.get_critical_items(data)
            num_critical = len(critical_items)
            
            # Build summary text
            summary = f"""Stockpile Analysis Summary
    ========================
    Analysis Period: {date_range}
    Total Reports Analyzed: {total_reports}
    Unique Items: {total_items}
    Critical Items: {num_critical}

    Category Summary:
    ----------------"""
            
            for category, stats in category_totals.iterrows():
                summary += f"\n{category}:"
                summary += f"\n  Total Items: {int(stats['count'])}"
                summary += f"\n  Total Quantity: {int(stats['sum'])}"
                
            if num_critical > 0:
                summary += "\n\nCritical Items:"
                summary += "\n--------------"
                for item in critical_items:
                    summary += f"\n- {item['Item Name']}: {item['Current Quantity']} (Threshold: {item['Threshold']})"
            
            return summary
            
        except Exception as e:
            return f"Error generating summary: {str(e)}"

    def get_critical_items(self, data):
            """Get list of items below their threshold values."""
            critical_items = []
            latest_data = data.sort_values('Timestamp').groupby('Item Code').last()
            
            for _, row in latest_data.iterrows():
                threshold = self.threshold_manager.get_threshold(row.name)
                if row['Quantity'] < threshold:
                    critical_items.append({
                        'Category': row['Category'],
                        'Item Code': row.name,
                        'Item Name': row['Item Name'],
                        'Current Quantity': row['Quantity'],
                        'Threshold': threshold,
                        'Needed': threshold - row['Quantity']
                    })
            
            return sorted(critical_items, key=lambda x: x['Category'])

    def get_category_stats(self, data):
        """Get statistics for each category."""
        latest_data = data.sort_values('Timestamp').groupby('Item Code').last()
        stats = {}
        
        for category in self.default_thresholds.keys():
            category_items = latest_data[latest_data['Category'] == category]
            below_threshold = category_items[
                category_items['Quantity'] < self.default_thresholds[category]
            ]
            
            stats[category] = {
                'total_items': len(category_items),
                'total_quantity': int(category_items['Quantity'].sum()),
                'below_threshold': len(below_threshold)
            }
        
        return stats

    def validate_and_clean_data(self, data):
        """Validate and clean the loaded data."""
        try:
            # Convert quantity to numeric, replacing N/A and errors with 0
            data['Quantity'] = pd.to_numeric(data['Quantity'].replace('N/A', '0'), 
                                           errors='coerce').fillna(0)
            
            # Ensure timestamps are datetime
            data['Timestamp'] = pd.to_datetime(data['Timestamp'])
            
            # Remove duplicates based on Item Code and Timestamp
            data = data.drop_duplicates(subset=['Item Code', 'Timestamp'])
            
            # Sort by timestamp
            data = data.sort_values('Timestamp')
            
            return data
        except Exception as e:
            raise ValueError(f"Error validating data: {str(e)}")
