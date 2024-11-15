import cv2 as cv
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import logging

class GameInventoryDetector:
    def __init__(self, template_dir, number_dir, threshold=0.95):
        self.template_dir = Path(template_dir)
        self.number_dir = Path(number_dir)
        self.threshold = threshold
        self.templates = {}
        self.number_templates = {}
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
        """Load both icon and number templates."""
        # Load icon templates
        self.logger.info(f"Loading icon templates from {self.template_dir}")
        for template_path in self.template_dir.glob("*.png"):
            template = cv.imread(str(template_path))
            if template is not None:
                template_gray = cv.cvtColor(template, cv.COLOR_BGR2GRAY)
                _, template_binary = cv.threshold(template_gray, 30, 255, cv.THRESH_BINARY)
                
                self.templates[template_path.stem] = {
                    'gray': template_gray,
                    'binary': template_binary,
                    'size': template.shape[:2]
                }
                
        # Load number templates
        self.logger.info(f"Loading number templates from {self.number_dir}")
        for template_path in self.number_dir.glob("*.png"):
            template = cv.imread(str(template_path))
            if template is not None:
                template_gray = cv.cvtColor(template, cv.COLOR_BGR2GRAY)
                _, template_binary = cv.threshold(template_gray, 30, 255, cv.THRESH_BINARY)
                
                self.number_templates[template_path.stem] = {
                    'gray': template_gray,
                    'binary': template_binary,
                    'size': template.shape[:2]
                }

        self.logger.info(f"Loaded {len(self.templates)} icons and {len(self.number_templates)} numbers")

    def detect_number(self, img_gray, img_binary, x, y, icon_height):
        """Detect number in the region to the right of an icon."""
        # Define region to the right of the icon
        padding = 5  # Adjust based on UI spacing
        search_width = 50  # Adjust based on maximum number width
        roi_x = x + padding
        roi_y = y  # Align with icon top
        
        # Extract ROI for number detection
        roi_gray = img_gray[roi_y:roi_y+icon_height, roi_x:roi_x+search_width]
        roi_binary = img_binary[roi_y:roi_y+icon_height, roi_x:roi_x+search_width]
        
        if roi_gray.size == 0:
            return None, 0
        
        best_number = None
        best_confidence = 0
        best_x_offset = 0
        
        # Try to match each number template
        for number, template_data in self.number_templates.items():
            res_gray = cv.matchTemplate(roi_gray, template_data['gray'], cv.TM_CCOEFF_NORMED)
            res_binary = cv.matchTemplate(roi_binary, template_data['binary'], cv.TM_CCOEFF_NORMED)
            res = (res_gray + res_binary) / 2
            
            min_val, max_val, min_loc, max_loc = cv.minMaxLoc(res)
            
            if max_val > best_confidence:
                best_confidence = max_val
                best_number = number
                best_x_offset = max_loc[0]
        
        if best_confidence >= self.threshold:
            return best_number, best_x_offset
        
        return None, 0

    def detect_icons(self, image_path, visualize=True):
        """Detect icons and their quantities in the given image."""
        img = cv.imread(str(image_path))
        if img is None:
            raise FileNotFoundError(f"Could not read image: {image_path}")
        
        img_gray, img_binary = self.preprocess_image(img)
        matches = []
        detected_locations = set()

        # Sort templates by size
        sorted_templates = sorted(
            self.templates.items(),
            key=lambda x: x[1]['size'][0] * x[1]['size'][1],
            reverse=True
        )

        for template_name, template_data in sorted_templates:
            res_gray = cv.matchTemplate(img_gray, template_data['gray'], cv.TM_CCOEFF_NORMED)
            res_binary = cv.matchTemplate(img_binary, template_data['binary'], cv.TM_CCOEFF_NORMED)
            res = (res_gray + res_binary) / 2
            
            locations = np.where(res >= self.threshold)
            for pt in zip(*locations[::-1]):
                h, w = template_data['size']
                
                # Check for overlap
                overlap = False
                for x, y, _, _ in detected_locations:
                    if abs(pt[0] - x) < w/2 and abs(pt[1] - y) < h/2:
                        overlap = True
                        break
                
                if not overlap:
                    # Detect number next to icon
                    number, x_offset = self.detect_number(img_gray, img_binary, pt[0], pt[1], h)
                    
                    matches.append({
                        "template_name": template_name,
                        "confidence": res[pt[1], pt[0]],
                        "location": (pt[0], pt[1], w, h),
                        "quantity": number,
                        "quantity_offset": x_offset
                    })
                    detected_locations.add((pt[0], pt[1], w, h))

        if visualize:
            self._visualize_matches(img, matches)

        return matches

    def preprocess_image(self, image):
        """Preprocess the input image for better matching."""
        gray = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
        _, binary = cv.threshold(gray, 30, 255, cv.THRESH_BINARY)
        return gray, binary

    def _visualize_matches(self, img, matches):
        """Visualize the detected matches and quantities."""
        fig, ax = plt.subplots(figsize=(15, 10))
        ax.imshow(cv.cvtColor(img, cv.COLOR_BGR2RGB))
        ax.set_title("Detection Results")

        for match in matches:
            x, y, w, h = match["location"]
            confidence = match["confidence"]
            quantity = match["quantity"]
            
            # Draw rectangle around icon
            rect = plt.Rectangle((x, y), w, h, fill=False, edgecolor='g', linewidth=2)
            ax.add_patch(rect)
            
            # Label with icon name, confidence, and quantity
            label = f"{match['template_name']}\n{confidence:.2f}"
            if quantity:
                label += f"\nQty: {quantity}"
            ax.text(x, y-5, label, color='white', fontsize=8, 
                   bbox=dict(facecolor='green', alpha=0.5))
            
            # If quantity was detected, highlight it
            if quantity:
                quantity_x = x + match["quantity_offset"] + 5  # Adjust based on UI spacing
                rect_q = plt.Rectangle((quantity_x, y), 20, h, fill=False, edgecolor='blue', linewidth=1)
                ax.add_patch(rect_q)

        ax.axis('off')
        plt.tight_layout()
        plt.show()

# Example usage
if __name__ == "__main__":
    detector = GameInventoryDetector(
        template_dir="CheckImages/Default",
        number_dir="CheckImages/Numbers",  # Directory containing number templates
        threshold=0.95
    )
    detector.load_templates()
    matches = detector.detect_icons("test_image.png")