# core/quartermaster.py
"""
Main controller for the Foxhole Quartermaster application.
Coordinates all functionality between components.
"""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
import pandas as pd
import logging

from core.models import InventoryReport, InventoryItem
from core.image_recognition import ImageRecognizer
from core.inventory_manager import InventoryManager
from utils.config_manager import ConfigManager


class QuartermasterApp:
    """
    Main controller for the Foxhole Quartermaster application.
    Coordinates all functionality between components.
    """
    
    def __init__(self, config_file: str = 'config.yaml'):
        """
        Initialize the Quartermaster application.
        
        Args:
            config_file: Path to configuration file
        """
        # Initialize configuration
        self.config = ConfigManager(config_file)
        
        # Initialize components
        self.image_recognizer = ImageRecognizer(self.config)
        self.inventory_manager = InventoryManager(self.config)
        
        # Set up logging
        self.logger = self._setup_logger()
        self.logger.info("Foxhole Quartermaster initialized")
        
        # Create necessary directories
        self._create_directories()
    
    def _setup_logger(self) -> logging.Logger:
        """
        Set up logger for the application.
        
        Returns:
            Configured logger instance
        """
        logger = logging.getLogger("FoxholeQuartermaster")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            # Create logs directory if it doesn't exist
            logs_path = Path(self.config.get_logs_path())
            logs_path.mkdir(exist_ok=True)
            
            # Create file handler
            log_file = logs_path / "quartermaster.log"
            handler = logging.FileHandler(log_file)
            
            # Create formatter
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            
            # Add handler to logger
            logger.addHandler(handler)
        
        return logger
    
    def _create_directories(self) -> None:
        """Create necessary directories for the application."""
        # Create reports directory
        reports_path = Path(self.config.get_reports_path())
        reports_path.mkdir(exist_ok=True)
        
        # Create logs directory
        logs_path = Path(self.config.get_logs_path())
        logs_path.mkdir(exist_ok=True)
    
    def process_image(self, image_path: str, visualize: bool = False, save_report: bool = True) -> InventoryReport:
        """
        Process an image to detect inventory items.
        
        Args:
            image_path: Path to the image file
            visualize: Whether to show visualization of detections
            save_report: Whether to save the report to file
            
        Returns:
            InventoryReport containing detected items
        """
        self.logger.info(f"Processing image: {image_path}")
        
        try:
            # Process image
            report = self.image_recognizer.process_image(image_path, visualize)
            
            # Save report if requested
            if save_report:
                self.inventory_manager.save_report(report)
            
            self.logger.info(f"Processed image: {image_path}, detected {len(report.items)} items")
            return report
            
        except Exception as e:
            self.logger.error(f"Error processing image {image_path}: {str(e)}")
            raise
    
    def process_multiple_images(self, image_paths: List[str], visualize: bool = False) -> List[InventoryReport]:
        """
        Process multiple images to detect inventory items.
        
        Args:
            image_paths: List of paths to image files
            visualize: Whether to show visualization of detections
            
        Returns:
            List of InventoryReport objects
        """
        self.logger.info(f"Processing {len(image_paths)} images")
        
        reports = []
        for image_path in image_paths:
            try:
                report = self.process_image(image_path, visualize)
                reports.append(report)
            except Exception as e:
                self.logger.error(f"Error processing image {image_path}: {str(e)}")
                # Continue with next image
        
        self.logger.info(f"Processed {len(reports)} images successfully")
        return reports
    
    def load_reports(self, directory_path: Optional[str] = None) -> pd.DataFrame:
        """
        Load and combine multiple inventory reports.
        
        Args:
            directory_path: Directory containing reports (uses config if None)
            
        Returns:
            DataFrame containing combined report data
        """
        self.logger.info(f"Loading reports from {directory_path or self.config.get_reports_path()}")
        
        try:
            data = self.inventory_manager.load_reports(directory_path)
            data = self.inventory_manager.validate_and_clean_data(data)
            
            self.logger.info(f"Loaded {len(data)} records from reports")
            return data
            
        except Exception as e:
            self.logger.error(f"Error loading reports: {str(e)}")
            raise
    
    def analyze_inventory(self, data: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        """
        Analyze inventory data.
        
        Args:
            data: DataFrame containing inventory data (loads from reports if None)
            
        Returns:
            Dict containing analysis results
        """
        self.logger.info("Analyzing inventory data")
        
        try:
            # Load data if not provided
            if data is None:
                data = self.load_reports()
            
            # Get critical items
            critical_items = self.inventory_manager.get_critical_items(data)
            
            # Get category stats
            category_stats = self.inventory_manager.get_category_stats(data)
            
            # Get changes
            changes = self.inventory_manager.analyze_changes(data)
            
            # Create analysis results
            analysis = {
                'critical_items': critical_items,
                'category_stats': category_stats,
                'changes': changes,
                'summary': self.inventory_manager.get_summary(data)
            }
            
            self.logger.info("Inventory analysis complete")
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing inventory: {str(e)}")
            raise
    
    def generate_report(self, data: Optional[pd.DataFrame] = None, 
                       output_path: Optional[str] = None) -> str:
        """
        Generate comprehensive analysis report.
        
        Args:
            data: DataFrame containing inventory data (loads from reports if None)
            output_path: Path to save the report (auto-generated if None)
            
        Returns:
            Path to the saved report
        """
        self.logger.info("Generating analysis report")
        
        try:
            # Load data if not provided
            if data is None:
                data = self.load_reports()
            
            # Generate report
            report_path = self.inventory_manager.generate_report(data, output_path)
            
            self.logger.info(f"Generated analysis report: {report_path}")
            return report_path
            
        except Exception as e:
            self.logger.error(f"Error generating report: {str(e)}")
            raise
    
    def update_category_threshold(self, category: str, threshold: int) -> None:
        """
        Update threshold for a category.
        
        Args:
            category: Category name
            threshold: New threshold value
        """
        self.logger.info(f"Updating threshold for category {category} to {threshold}")
        
        try:
            self.config.set_category_threshold(category, threshold)
            self.config.save()
            
            self.logger.info(f"Updated threshold for category {category}")
            
        except Exception as e:
            self.logger.error(f"Error updating category threshold: {str(e)}")
            raise
    
    def update_item_threshold(self, item_code: str, threshold: int) -> None:
        """
        Update threshold for a specific item.
        
        Args:
            item_code: Item code
            threshold: New threshold value
        """
        self.logger.info(f"Updating threshold for item {item_code} to {threshold}")
        
        try:
            self.config.set_item_threshold(item_code, threshold)
            self.config.save()
            
            self.logger.info(f"Updated threshold for item {item_code}")
            
        except Exception as e:
            self.logger.error(f"Error updating item threshold: {str(e)}")
            raise
