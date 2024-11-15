# detector/template_matcher.py
import cv2 as cv
import numpy as np
from pathlib import Path
import logging

class TemplateMatcher:
    def __init__(self, template_dir, threshold=0.95):
        self.template_dir = Path(template_dir)
        self.threshold = threshold
        self.templates = {}
        self.logger = self._setup_logger()
        
    def _setup_logger(self):
        logger = logging.getLogger(self.__class__.__name__)
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger

    def load_templates(self):
        self.logger.info(f"Loading templates from {self.template_dir}")
        template_files = list(self.template_dir.glob("*.png"))
        
        for template_path in template_files:
            template = cv.imread(str(template_path))
            if template is not None:
                template_gray = cv.cvtColor(template, cv.COLOR_BGR2GRAY)
                _, template_binary = cv.threshold(template_gray, 30, 255, cv.THRESH_BINARY)
                
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
        gray = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
        _, binary = cv.threshold(gray, 30, 255, cv.THRESH_BINARY)
        return gray, binary

    def detect_matches(self, image):
        img_gray, img_binary = self.preprocess_image(image)
        matches = []
        detected_locations = set()

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
                
                overlap = False
                for x, y, _, _ in detected_locations:
                    if abs(pt[0] - x) < w/2 and abs(pt[1] - y) < h/2:
                        overlap = True
                        break
                
                if not overlap:
                    matches.append({
                        "template_name": template_name,
                        "confidence": res[pt[1], pt[0]],
                        "location": (pt[0], pt[1], w, h)
                    })
                    detected_locations.add((pt[0], pt[1], w, h))

        return matches