# core/image_recognition.py
"""
Image recognition module for Foxhole Quartermaster.
Handles detection of items and quantities in screenshots.
"""

import cv2 as cv
import numpy as np
from pathlib import Path
import logging
from typing import List, Dict, Tuple, Any, Optional
import matplotlib.pyplot as plt

from core.models import InventoryItem, InventoryReport


class ImageRecognizer:
    """
    Handles detection of items and quantities in screenshots.
    Combines functionality from the original template_matcher, visualizer, and number_mapper.
    """
    
    def __init__(self, config_manager):
        """
        Initialize the image recognizer.
        
        Args:
            config_manager: Configuration manager instance
        """
        self.config = config_manager
        self.logger = self._setup_logger()
        
        # Get detection settings
        detection_settings = self.config.get_detection_settings()
        self.confidence_threshold = detection_settings.get('confidence_threshold', 0.95)
        self.max_digit_distance = detection_settings.get('max_digit_distance', 150)
        
        # Get template paths
        template_paths = self.config.get_template_paths()
        self.icon_template_dir = Path(template_paths.get('icons', 'CheckImages/Default'))
        self.number_template_dir = Path(template_paths.get('numbers', 'CheckImages/Numbers'))
        
        # Initialize templates
        self.icon_templates = {}
        self.number_templates = {}
        self.load_templates()
    
    def _setup_logger(self) -> logging.Logger:
        """
        Set up logger for the image recognizer.
        
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
    
    def load_templates(self) -> None:
        """Load icon and number templates from directories."""
        self.logger.info(f"Loading icon templates from {self.icon_template_dir}")
        self.icon_templates = self._load_templates_from_dir(self.icon_template_dir)
        
        self.logger.info(f"Loading number templates from {self.number_template_dir}")
        self.number_templates = self._load_templates_from_dir(self.number_template_dir)
        
        self.logger.info(f"Loaded {len(self.icon_templates)} icon templates and {len(self.number_templates)} number templates")
    
    def _load_templates_from_dir(self, template_dir: Path) -> Dict[str, Dict[str, Any]]:
        """
        Load templates from a directory.
        
        Args:
            template_dir: Directory containing template images
            
        Returns:
            Dict mapping template names to template data
        """
        templates = {}
        template_files = list(template_dir.glob("*.png"))
        
        for template_path in template_files:
            template = cv.imread(str(template_path))
            if template is not None:
                template_gray = cv.cvtColor(template, cv.COLOR_BGR2GRAY)
                _, template_binary = cv.threshold(template_gray, 30, 255, cv.THRESH_BINARY)
                
                templates[template_path.stem] = {
                    'gray': template_gray,
                    'binary': template_binary,
                    'size': template.shape[:2]
                }
                self.logger.debug(f"Loaded template: {template_path.stem}")
            else:
                self.logger.warning(f"Failed to load template: {template_path}")
        
        return templates
    
    def preprocess_image(self, image: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Preprocess image for template matching.
        
        Args:
            image: Input image
            
        Returns:
            Tuple of (grayscale image, binary image)
        """
        gray = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
        _, binary = cv.threshold(gray, 30, 255, cv.THRESH_BINARY)
        return gray, binary
    
    def detect_items(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """
        Detect items in the image.
        
        Args:
            image: Input image
            
        Returns:
            List of detected items with their locations and confidence scores
        """
        img_gray, img_binary = self.preprocess_image(image)
        matches = []
        detected_locations = set()

        # Sort templates by size (largest first) to prioritize larger templates
        sorted_templates = sorted(
            self.icon_templates.items(),
            key=lambda x: x[1]['size'][0] * x[1]['size'][1],
            reverse=True
        )

        for template_name, template_data in sorted_templates:
            # Match using both grayscale and binary images for better results
            res_gray = cv.matchTemplate(img_gray, template_data['gray'], cv.TM_CCOEFF_NORMED)
            res_binary = cv.matchTemplate(img_binary, template_data['binary'], cv.TM_CCOEFF_NORMED)
            res = (res_gray + res_binary) / 2
            
            # Find locations where confidence exceeds threshold
            locations = np.where(res >= self.confidence_threshold)
            
            for pt in zip(*locations[::-1]):  # Convert from (y,x) to (x,y)
                h, w = template_data['size']
                
                # Check for overlap with existing detections
                overlap = False
                for x, y, _, _ in detected_locations:
                    if abs(pt[0] - x) < w/2 and abs(pt[1] - y) < h/2:
                        overlap = True
                        break
                
                if not overlap:
                    matches.append({
                        "template_name": template_name,
                        "confidence": float(res[pt[1], pt[0]]),
                        "location": (int(pt[0]), int(pt[1]), w, h)
                    })
                    detected_locations.add((pt[0], pt[1], w, h))

        return matches
    
    def detect_numbers(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """
        Detect numbers in the image.
        
        Args:
            image: Input image
            
        Returns:
            List of detected numbers with their locations and confidence scores
        """
        img_gray, img_binary = self.preprocess_image(image)
        matches = []
        detected_locations = set()

        for template_name, template_data in self.number_templates.items():
            res_gray = cv.matchTemplate(img_gray, template_data['gray'], cv.TM_CCOEFF_NORMED)
            res_binary = cv.matchTemplate(img_binary, template_data['binary'], cv.TM_CCOEFF_NORMED)
            res = (res_gray + res_binary) / 2
            
            locations = np.where(res >= self.confidence_threshold)
            
            for pt in zip(*locations[::-1]):
                h, w = template_data['size']
                
                # Check for overlap with existing detections
                overlap = False
                for x, y, _, _ in detected_locations:
                    if abs(pt[0] - x) < w/2 and abs(pt[1] - y) < h/2:
                        overlap = True
                        break
                
                if not overlap:
                    matches.append({
                        "template_name": template_name,
                        "confidence": float(res[pt[1], pt[0]]),
                        "location": (int(pt[0]), int(pt[1]), w, h)
                    })
                    detected_locations.add((pt[0], pt[1], w, h))

        return matches
    
    def compose_quantity(self, number_matches: List[Dict[str, Any]], 
                         reference_x: int, reference_y: int) -> Optional[int]:
        """
        Compose multi-digit numbers from individual digit matches.
        
        Args:
            number_matches: List of number template matches
            reference_x: X coordinate to measure distance from (usually icon position)
            reference_y: Y coordinate for vertical alignment
            
        Returns:
            Composed quantity or None if no digits found
        """
        relevant_numbers = []
        
        # Filter numbers that are close enough horizontally and vertically aligned
        for match in number_matches:
            x, y, w, h = match["location"]
            if (x > reference_x and 
                x < reference_x + self.max_digit_distance and 
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
            if curr_x - prev_x <= 40:  # Maximum gap between digits
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
                digit = self._get_number_value(match["template_name"])
                composed_number += str(digit)
                
            try:
                return int(composed_number)
            except ValueError:
                return None
                
        return None
    
    def _get_number_value(self, template_name: str) -> str:
        """
        Convert number template name to actual value.
        
        Args:
            template_name: Template name
            
        Returns:
            String representation of the number
        """
        # Extract the number if it's in the format 'numX'
        if template_name.startswith('num') and len(template_name) > 3:
            try:
                return template_name[3:]
            except ValueError:
                pass
        
        # Default mapping for special cases
        number_mapping = {
            'num0': '0',
            'num1': '1',
            'num2': '2',
            'num3': '3',
            'num4': '4',
            'num5': '5',
            'num6': '6',
            'num7': '7',
            'num8': '8',
            'num9': '9',
            'numk': 'k'
        }
        
        return number_mapping.get(template_name, template_name)
    
    def process_image(self, image_path: str, visualize: bool = False) -> InventoryReport:
        """
        Process an image to detect inventory items.
        
        Args:
            image_path: Path to the image file
            visualize: Whether to show visualization of detections
            
        Returns:
            InventoryReport containing detected items
        """
        # Read image
        img = cv.imread(image_path)
        if img is None:
            raise FileNotFoundError(f"Could not read image: {image_path}")
        
        # Detect items and numbers
        icon_matches = self.detect_items(img)
        number_matches = self.detect_numbers(img)
        
        # Visualize if requested
        if visualize:
            self.visualize_matches(img, icon_matches, "Item Detections")
            self.visualize_matches(img, number_matches, "Number Detections")
        
        # Process matches into inventory items
        inventory_items = []
        
        for icon in icon_matches:
            icon_x, icon_y, icon_w, icon_h = icon["location"]
            icon_code = icon["template_name"]
            
            # Get item name and category
            item_name = self.config.get_item_name(icon_code)
            category = self.config.get_item_category(icon_code)
            
            # Get quantity
            quantity = self.compose_quantity(number_matches, icon_x + icon_w, icon_y)
            
            # Create inventory item
            inventory_items.append(InventoryItem(
                code=icon_code,
                name=item_name,
                category=category,
                quantity=quantity if quantity is not None else 0,
                confidence=icon["confidence"],
                location=icon["location"]
            ))
        
        # Create inventory report
        report = InventoryReport(
            items=inventory_items,
            source_image=image_path
        )
        
        return report
    
    def visualize_matches(self, img: np.ndarray, matches: List[Dict[str, Any]], 
                         title: str = "Detection Results") -> None:
        """
        Visualize matches on the image.
        
        Args:
            img: Input image
            matches: List of matches to visualize
            title: Title for the visualization
        """
        fig, ax = plt.subplots(figsize=(15, 10))
        ax.imshow(cv.cvtColor(img, cv.COLOR_BGR2RGB))
        ax.set_title(title)

        for match in matches:
            x, y, w, h = match["location"]
            confidence = match["confidence"]
            
            rect = plt.Rectangle((x, y), w, h, fill=False, edgecolor='g', linewidth=2)
            ax.add_patch(rect)
            
            label = f"{match['template_name']}\n{confidence:.2f}"
            ax.text(x, y-5, label, color='white', fontsize=8, 
                    bbox=dict(facecolor='green', alpha=0.5))

        ax.axis('off')
        plt.tight_layout()
        plt.show()
