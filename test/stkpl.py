import cv2 as cv
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import logging

class GameInventoryDetector:
    def __init__(self, template_dir, threshold=0.95):
        self.template_dir = Path(template_dir)
        self.threshold = threshold
        self.templates = {}
        self.logger = self._setup_logger()
        
    def _setup_logger(self):
        logger = logging.getLogger('GameInventoryDetector')
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger

    def load_templates(self):
        """Load all template images from the template directory."""
        self.logger.info(f"Loading templates from {self.template_dir}")
        template_files = list(self.template_dir.glob("*.png"))
        
        for template_path in template_files:
            template = cv.imread(str(template_path))
            if template is not None:
                # Convert template to grayscale
                template_gray = cv.cvtColor(template, cv.COLOR_BGR2GRAY)
                
                # Threshold the template to create a binary mask
                _, template_binary = cv.threshold(template_gray, 30, 255, cv.THRESH_BINARY)
                
                # Store both grayscale and binary versions
                self.templates[template_path.stem] = {
                    'gray': template_gray,
                    'binary': template_binary,
                    'size': template.shape[:2]
                }
                self.logger.debug(f"Loaded template: {template_path.stem}")
            else:
                self.logger.warning(f"Failed to load template: {template_path}")
                
        self.logger.info(f"Loaded {len(self.templates)} templates")

    def preprocess_image(self, image):
        """Preprocess the input image for better matching."""
        # Convert to grayscale
        gray = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
        
        # Apply threshold to create binary image
        _, binary = cv.threshold(gray, 30, 255, cv.THRESH_BINARY)
        
        return gray, binary

    def detect_icons(self, image_path, visualize=True):
        """Detect icons in the given image using template matching."""
        # Read the main image
        img = cv.imread(str(image_path))
        if img is None:
            raise FileNotFoundError(f"Could not read image: {image_path}")
        
        # Preprocess the image
        img_gray, img_binary = self.preprocess_image(img)
        matches = []
        detected_locations = set()

        # Sort templates by size (larger first to prevent multiple detections)
        sorted_templates = sorted(
            self.templates.items(),
            key=lambda x: x[1]['size'][0] * x[1]['size'][1],
            reverse=True
        )

        for template_name, template_data in sorted_templates:
            # Match using both grayscale and binary images
            res_gray = cv.matchTemplate(img_gray, template_data['gray'], cv.TM_CCOEFF_NORMED)
            res_binary = cv.matchTemplate(img_binary, template_data['binary'], cv.TM_CCOEFF_NORMED)
            
            # Combine results
            res = (res_gray + res_binary) / 2
            
            # Find all matches above threshold
            locations = np.where(res >= self.threshold)
            for pt in zip(*locations[::-1]):  # Switch columns and rows
                h, w = template_data['size']
                
                # Check if this location overlaps with previously detected icons
                overlap = False
                for x, y, _, _ in detected_locations:
                    if abs(pt[0] - x) < w/2 and abs(pt[1] - y) < h/2:
                        overlap = True
                        break
                
                if not overlap:
                    # Extract region and check for quantity
                    roi = img_gray[pt[1]:pt[1]+h, pt[0]+w:pt[0]+w+30]  # Look for quantity to the right
                    quantity = None
                    if roi.size > 0:
                        # You might want to add OCR here for quantity detection
                        pass

                    matches.append({
                        "template_name": template_name,
                        "confidence": res[pt[1], pt[0]],
                        "location": (pt[0], pt[1], w, h),
                        "quantity": quantity
                    })
                    detected_locations.add((pt[0], pt[1], w, h))

        if visualize:
            self._visualize_matches(img, matches)

        return matches

    def _visualize_matches(self, img, matches):
        """Visualize the detected matches on the image."""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 8))
        
        # Original image
        ax1.imshow(cv.cvtColor(img, cv.COLOR_BGR2RGB))
        ax1.set_title("Original Image")
        ax1.axis('off')
        
        # Detection results
        ax2.imshow(cv.cvtColor(img, cv.COLOR_BGR2RGB))
        ax2.set_title("Detection Results")

        for match in matches:
            x, y, w, h = match["location"]
            confidence = match["confidence"]
            
            # Draw rectangle around match
            rect = plt.Rectangle((x, y), w, h, fill=False, edgecolor='g', linewidth=2)
            ax2.add_patch(rect)
            
            # Add label with template name and confidence
            label = f"{match['template_name']}\n{confidence:.2f}"
            if match['quantity']:
                label += f"\nQty: {match['quantity']}"
            ax2.text(x, y-5, label, color='white', fontsize=8, 
                    bbox=dict(facecolor='green', alpha=0.5))

        ax2.axis('off')
        plt.tight_layout()
        plt.show()

# Example usage
if __name__ == "__main__":
    detector = GameInventoryDetector("CheckImages/Default", threshold=0.95)
    detector.load_templates()
    matches = detector.detect_icons("test_image.png")