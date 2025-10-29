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
        self.confidence_threshold = detection_settings.get('confidence_threshold', 0.90)
        self.max_digit_distance = detection_settings.get('max_digit_distance', 150)
        
        # Get template paths
        template_paths = self.config.get_template_paths()
        self.base_template_dir = Path(template_paths.get('base', 'data/processed_templates'))
        self.number_template_dir = Path(template_paths.get('numbers', 'data/numbers'))
        
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
        import time
        start_time = time.time()
        
        self.logger.info(f"Loading icon templates from {self.base_template_dir}")
        self.icon_templates = self._load_item_templates()
        icon_load_time = time.time() - start_time
        
        self.logger.info(f"Loading number templates from {self.number_template_dir}")
        number_start = time.time()
        self.number_templates = self._load_templates_from_dir(self.number_template_dir)
        number_load_time = time.time() - number_start
        
        total_time = time.time() - start_time
        self.logger.info(f"Loaded {len(self.icon_templates)} icon templates in {icon_load_time:.2f}s")
        self.logger.info(f"Loaded {len(self.number_templates)} number templates in {number_load_time:.2f}s")
        self.logger.info(f"Total template loading time: {total_time:.2f}s")
        
        # Print to console for user feedback
        print(f"Loaded {len(self.icon_templates)} icon templates and {len(self.number_templates)} number templates ({total_time:.2f}s)")
    
    def _load_item_templates(self) -> Dict[str, Dict[str, Any]]:
        """
        Load item templates from the catalog-based directory structure.
        Each item has its own folder under base_template_dir, named by CodeName.
        Multiple variations of the same item (different angles/states) are loaded.
        
        Returns:
            Dict mapping template names to template data
        """
        templates = {}
        
        if not self.base_template_dir.exists():
            self.logger.warning(f"Base template directory not found: {self.base_template_dir}")
            return templates
        
        # Get all item directories first for progress tracking
        item_dirs = [d for d in self.base_template_dir.iterdir() if d.is_dir()]
        total_items = len(item_dirs)
        
        print(f"Loading templates from {total_items} item folders...")
        
        templates_loaded = 0
        last_progress = -1
        
        # Iterate through each item folder
        for idx, item_dir in enumerate(item_dirs):
            item_code = item_dir.name
            
            # Show progress every 10%
            progress = int((idx / total_items) * 100)
            if progress >= last_progress + 10:
                print(f"  Progress: {progress}% ({idx}/{total_items} items)")
                last_progress = progress
            
            # Find PNG files in the item directory
            template_files = list(item_dir.glob("*.png"))
            
            if not template_files:
                self.logger.debug(f"No templates found for item: {item_code}")
                continue
            
            # Load ALL variations of this item
            for template_path in template_files:
                template = cv.imread(str(template_path), cv.IMREAD_GRAYSCALE)
                if template is not None:
                    # Process template directly as grayscale (already loaded that way)
                    _, template_binary = cv.threshold(template, 30, 255, cv.THRESH_BINARY)
                    
                    # Use the item code (folder name) as the template name
                    # Create unique key for this specific variation
                    variation_key = f"{item_code}_{template_path.stem}"
                    
                    templates[variation_key] = {
                        'gray': template,  # Already grayscale
                        'binary': template_binary,
                        'size': template.shape[:2],
                        'path': template_path,
                        'item_code': item_code  # Store the actual item code
                    }
                    templates_loaded += 1
                    self.logger.debug(f"Loaded template variation: {variation_key}")
                else:
                    self.logger.warning(f"Failed to load template: {template_path}")
        
        print(f"  Complete: Loaded {templates_loaded} template variations from {total_items} items")
        return templates
    
    def _load_templates_from_dir(self, template_dir: Path) -> Dict[str, Dict[str, Any]]:
        """
        Load templates from a flat directory (used for number templates).
        
        Args:
            template_dir: Directory containing template images
            
        Returns:
            Dict mapping template names to template data
        """
        templates = {}
        
        if not template_dir.exists():
            self.logger.warning(f"Template directory not found: {template_dir}")
            return templates
        
        template_files = list(template_dir.glob("*.png"))
        
        for template_path in template_files:
            # Load directly as grayscale for better performance
            template = cv.imread(str(template_path), cv.IMREAD_GRAYSCALE)
            if template is not None:
                _, template_binary = cv.threshold(template, 30, 255, cv.THRESH_BINARY)
                
                templates[template_path.stem] = {
                    'gray': template,  # Already grayscale
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
        Detect items in the image with ultra-optimized performance.
        Uses early termination once item is found with high confidence.
        
        Args:
            image: Input image
            
        Returns:
            List of detected items with their locations and confidence scores
        """
        import time
        from concurrent.futures import ThreadPoolExecutor, as_completed
        import multiprocessing
        
        start_time = time.time()
        
        img_gray, img_binary = self.preprocess_image(image)
        detected_items = {}  # Track best match per item_code
        detected_locations = set()
        items_found = set()  # Track which items we've found with high confidence

        # Group templates by item_code for smarter processing
        templates_by_item = {}
        for template_name, template_data in self.icon_templates.items():
            item_code = template_data.get('item_code', template_name)
            if item_code not in templates_by_item:
                templates_by_item[item_code] = []
            templates_by_item[item_code].append((template_name, template_data))
        
        print(f"Detecting items ({len(templates_by_item)} unique items, {len(self.icon_templates)} total variations)...")
        
        # CRITICAL OPTIMIZATION: Process items, not individual templates
        # Once we find an item with high confidence, skip its other variations
        
        def match_item_variations(item_code, variations):
            """Match all variations of an item, stopping early if high confidence found."""
            # Skip if we already found this item with excellent confidence
            if item_code in items_found:
                return []
            
            best_match = None
            
            # Sort variations by size (try larger templates first)
            variations = sorted(variations, 
                              key=lambda x: x[1]['size'][0] * x[1]['size'][1], 
                              reverse=True)
            
            for template_name, template_data in variations:
                # Quick grayscale check first
                res_gray = cv.matchTemplate(img_gray, template_data['gray'], cv.TM_CCOEFF_NORMED)
                max_val = np.max(res_gray)
                
                # Skip if no promising matches
                if max_val < self.confidence_threshold - 0.05:
                    continue
                
                # Do full matching
                res_binary = cv.matchTemplate(img_binary, template_data['binary'], cv.TM_CCOEFF_NORMED)
                res = (res_gray + res_binary) / 2
                
                # Find matches above threshold
                locations = np.where(res >= self.confidence_threshold)
                
                for pt in zip(*locations[::-1]):
                    h, w = template_data['size']
                    confidence = float(res[pt[1], pt[0]])
                    
                    match = {
                        'item_code': item_code,
                        'confidence': confidence,
                        'location': (int(pt[0]), int(pt[1]), w, h)
                    }
                    
                    # Keep best match
                    if best_match is None or confidence > best_match['confidence']:
                        best_match = match
                    
                    # CRITICAL: If we found a great match (>0.97), stop checking other variations
                    if confidence > 0.97:
                        return [best_match]
            
            return [best_match] if best_match else []
        
        # Process items in parallel
        num_workers = max(1, multiprocessing.cpu_count() - 1)
        all_results = []
        
        # Convert to list for progress tracking
        items_list = list(templates_by_item.items())
        
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = {executor.submit(match_item_variations, item_code, variations): item_code 
                      for item_code, variations in items_list}
            
            completed = 0
            for future in as_completed(futures):
                item_results = future.result()
                all_results.extend(item_results)
                
                # Mark high-confidence items as found
                for result in item_results:
                    if result['confidence'] > 0.97:
                        items_found.add(result['item_code'])
                
                completed += 1
                if completed % 50 == 0:
                    progress = int((completed / len(items_list)) * 100)
                    print(f"  Progress: {progress}% ({completed}/{len(items_list)} items checked, {len(all_results)} matches)")
        
        # Filter results to avoid overlaps
        for result in all_results:
            item_code = result['item_code']
            location = result['location']
            confidence = result['confidence']
            x, y, w, h = location
            
            # Check for overlap with existing detections
            overlap = False
            for dx, dy, dw, dh in detected_locations:
                if abs(x - dx) < w/2 and abs(y - dy) < h/2:
                    overlap = True
                    break
            
            if not overlap:
                # Keep best match per item at each location
                if item_code not in detected_items or confidence > detected_items[item_code]['confidence']:
                    if item_code in detected_items:
                        old_loc = detected_items[item_code]['location']
                        detected_locations.discard(old_loc)
                    
                    detected_items[item_code] = {
                        "template_name": item_code,
                        "confidence": confidence,
                        "location": location
                    }
                    detected_locations.add(location)
        
        matches = list(detected_items.values())
        
        elapsed = time.time() - start_time
        print(f"✓ Detection complete: {len(matches)} items found in {elapsed:.2f}s")
        self.logger.info(f"Item detection: found {len(matches)} items in {elapsed:.2f}s "
                        f"(checked {len(items_list)} item types, stopped early on {len(items_found)} high-confidence matches)")

        return matches
    
    def detect_numbers(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """
        Detect numbers in the image with optimized performance.
        
        Args:
            image: Input image
            
        Returns:
            List of detected numbers with their locations and confidence scores
        """
        import time
        start_time = time.time()
        
        img_gray, img_binary = self.preprocess_image(image)
        matches = []
        detected_locations = set()

        for template_name, template_data in self.number_templates.items():
            # OPTIMIZATION: Use only grayscale first, check if worth doing binary
            res_gray = cv.matchTemplate(img_gray, template_data['gray'], cv.TM_CCOEFF_NORMED)
            
            # Quick check: if no matches above threshold, skip binary
            max_gray = np.max(res_gray)
            if max_gray < self.confidence_threshold - 0.05:
                continue
            
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
        
        elapsed = time.time() - start_time
        self.logger.debug(f"Number detection: found {len(matches)} digits in {elapsed:.2f}s")

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
        import time
        start_time = time.time()
        
        # Read image
        img = cv.imread(image_path)
        if img is None:
            raise FileNotFoundError(f"Could not read image: {image_path}")
        
        # Detect items and numbers
        detect_start = time.time()
        icon_matches = self.detect_items(img)
        detect_time = time.time() - detect_start
        
        number_start = time.time()
        number_matches = self.detect_numbers(img)
        number_time = time.time() - number_start
        
        # Visualize if requested
        if visualize:
            self.visualize_matches(img, icon_matches, "Item Detections")
            self.visualize_matches(img, number_matches, "Number Detections")
        
        # Process matches into inventory items
        process_start = time.time()
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
        
        process_time = time.time() - process_start
        
        # Create inventory report
        report = InventoryReport(
            items=inventory_items,
            source_image=image_path
        )
        
        total_time = time.time() - start_time
        
        # Log performance metrics
        self.logger.info(f"Image processing complete: {len(inventory_items)} items detected")
        self.logger.info(f"  Item detection: {detect_time:.2f}s")
        self.logger.info(f"  Number detection: {number_time:.2f}s")
        self.logger.info(f"  Item creation: {process_time:.2f}s")
        self.logger.info(f"  Total time: {total_time:.2f}s")
        
        # Print summary to console
        print(f"Processed image: {len(inventory_items)} items detected in {total_time:.2f}s")
        
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