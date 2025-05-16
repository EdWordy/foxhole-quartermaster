# core/inventory_manager.py
"""
Inventory manager for Foxhole Quartermaster.
Handles inventory data processing, analysis, and reporting.
"""

import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
import os
import logging
from typing import List, Dict, Any, Optional, Tuple, Union

from core.models import InventoryReport, InventoryItem, CategorySummary, CriticalItem


class InventoryManager:
    """
    Manages inventory data, analysis, and reporting.
    Combines functionality from stockpile_analyzer and threshold_manager.
    """
    
    def __init__(self, config_manager):
        """
        Initialize the inventory manager.
        
        Args:
            config_manager: Configuration manager instance
        """
        self.config = config_manager
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """
        Set up logger for the inventory manager.
        
        Returns:
            Configured logger instance
        """
        logger = logging.getLogger(self.__class__.__name__)
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            # Create logs directory if it doesn't exist
            logs_path = Path(self.config.get_logs_path())
            logs_path.mkdir(exist_ok=True)
            
            # Create file handler
            log_file = logs_path / f"{self.__class__.__name__}.log"
            handler = logging.FileHandler(log_file)
            
            # Create formatter
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            
            # Add handler to logger
            logger.addHandler(handler)
        
        return logger
    
    def save_report(self, report: InventoryReport) -> str:
        """
        Save inventory report to CSV.
        
        Args:
            report: Inventory report to save
            
        Returns:
            Path to saved report file
        """
        # Create reports directory if it doesn't exist
        reports_path = Path(self.config.get_reports_path())
        reports_path.mkdir(exist_ok=True)
        
        # Generate output path
        timestamp = report.timestamp.strftime("%Y%m%d_%H%M%S")
        if report.source_image:
            base_name = os.path.splitext(os.path.basename(report.source_image))[0]
            output_path = reports_path / f"inv_report_{base_name}_{timestamp}.csv"
        else:
            output_path = reports_path / f"inv_report_{timestamp}.csv"
        
        # Save report
        output_path_str = str(output_path)
        report.save_to_csv(output_path_str)
        
        self.logger.info(f"Saved inventory report to: {output_path_str}")
        return output_path_str
    
    def load_reports(self, directory_path: Optional[str] = None) -> pd.DataFrame:
        """
        Load and combine multiple inventory reports.
        
        Args:
            directory_path: Directory containing reports (uses config if None)
            
        Returns:
            DataFrame containing combined report data
        """
        if directory_path is None:
            directory_path = self.config.get_reports_path()
            
        reports_dir = Path(directory_path)
        reports = []
        report_files = list(reports_dir.glob('inv_report_*.csv'))
        
        if not report_files:
            raise ValueError(f"No inventory reports found in {directory_path}")
            
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
                self.logger.error(f"Error loading {file.name}: {str(e)}")
                continue

        if not reports:
            raise ValueError("No valid reports could be loaded")
            
        return pd.concat(reports, ignore_index=True)
    
    def validate_and_clean_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Validate and clean the loaded data.
        
        Args:
            data: DataFrame containing report data
            
        Returns:
            Cleaned DataFrame
        """
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
            error_msg = f"Error validating data: {str(e)}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
    
    def get_critical_items(self, data: pd.DataFrame) -> List[CriticalItem]:
        """
        Get list of items below their threshold values.
        
        Args:
            data: DataFrame containing inventory data
            
        Returns:
            List of CriticalItem objects
        """
        critical_items = []
        latest_data = data.sort_values('Timestamp').groupby('Item Code').last()
        
        for idx, row in latest_data.iterrows():
            threshold = self.config.get_item_threshold(idx)
            if row['Quantity'] < threshold:
                critical_items.append(CriticalItem(
                    category=row['Category'],
                    item_code=idx,
                    item_name=row['Item Name'],
                    current_quantity=row['Quantity'],
                    threshold=threshold
                ))
        
        return sorted(critical_items, key=lambda x: x.category)
    
    def get_category_stats(self, data: pd.DataFrame) -> Dict[str, CategorySummary]:
        """
        Get statistics for each category.
        
        Args:
            data: DataFrame containing inventory data
            
        Returns:
            Dict mapping category names to CategorySummary objects
        """
        latest_data = data.sort_values('Timestamp').groupby('Item Code').last()
        stats = {}
        
        # Get unique categories
        categories = latest_data['Category'].unique()
        
        for category in categories:
            category_items = latest_data[latest_data['Category'] == category]
            threshold = self.config.get_category_threshold(category)
            
            below_threshold = category_items[
                category_items['Quantity'] < threshold
            ]
            
            stats[category] = CategorySummary(
                name=category,
                total_items=len(category_items),
                total_quantity=int(category_items['Quantity'].sum()),
                below_threshold=len(below_threshold),
                threshold=threshold
            )
        
        return stats
    
    def analyze_changes(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Analyze inventory changes between reports.
        
        Args:
            data: DataFrame containing inventory data
            
        Returns:
            DataFrame containing change analysis
        """
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
    
    def get_summary(self, data: pd.DataFrame) -> str:
        """
        Generate a text summary of the stockpile analysis.
        
        Args:
            data: DataFrame containing inventory data
            
        Returns:
            Text summary of the analysis
        """
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
                    summary += f"\n- {item.item_name}: {item.current_quantity} (Threshold: {item.threshold})"
            
            return summary
            
        except Exception as e:
            error_msg = f"Error generating summary: {str(e)}"
            self.logger.error(error_msg)
            return error_msg
    
    def generate_report(self, data: pd.DataFrame, output_path: Optional[str] = None) -> str:
        """
        Generate comprehensive analysis report.
        
        Args:
            data: DataFrame containing inventory data
            output_path: Path to save the report (auto-generated if None)
            
        Returns:
            Path to the saved report
        """
        if output_path is None:
            reports_path = Path(self.config.get_reports_path())
            reports_path.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = str(reports_path / f"inv_report_analysis_{timestamp}.xlsx")
            
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
                    len(data['Report'].unique()) if 'Report' in data.columns else 1,
                    len(data['Item Code'].unique()),
                    f"{data['Timestamp'].min():%Y-%m-%d %H:%M} to {data['Timestamp'].max():%Y-%m-%d %H:%M}",
                    len(self.get_critical_items(data))
                ]
            }
            pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)
            
            # Changes Analysis
            self.analyze_changes(data).to_excel(writer, sheet_name='Changes')
            
            # Category Analysis
            category_stats = self.get_category_stats(data)
            category_df = pd.DataFrame([stat.to_dict() for stat in category_stats.values()])
            category_df.to_excel(writer, sheet_name='Categories', index=False)
            
            # Critical Items
            critical_items = self.get_critical_items(data)
            if critical_items:
                critical_df = pd.DataFrame([item.to_dict() for item in critical_items])
                critical_df.to_excel(writer, sheet_name='Critical Items', index=False)
            
            # Format workbook
            workbook = writer.book
            for worksheet in writer.sheets.values():
                # Auto-adjust column widths
                for i, col in enumerate(category_df.columns):
                    # Find the maximum length of the column
                    max_len = max(
                        category_df[col].astype(str).apply(len).max(),
                        len(col)
                    ) + 2
                    worksheet.set_column(i, i, max_len)
                
        self.logger.info(f"Generated analysis report: {output_path}")
        return output_path
