# main.py
import cv2 as cv
from pathlib import Path
from detector.template_matcher import TemplateMatcher
from detector.visualizer import MatchVisualizer
from detector.data_processor import DataProcessor
from detector.item_mapper import ItemMapper
from detector.number_mapper import NumberMapper, QuantityComposer

def process_inventory_screenshot(
    image_path,
    icon_template_dir="CheckImages/Default",
    number_template_dir="CheckImages/Numbers",
    item_mapping_file="item_mappings.csv",
    number_mapping_file="number_mappings.csv",
    visualize=True,
    save_excel=True
):
    """Process inventory screenshot with item name mapping."""
    # Initialize detectors and mapper
    icon_detector = TemplateMatcher(icon_template_dir, threshold=0.95)
    number_detector = TemplateMatcher(number_template_dir, threshold=0.95)
    item_mapper = ItemMapper(item_mapping_file)
    number_mapper = NumberMapper(number_mapping_file)
    data_processor = DataProcessor(item_mapper, number_mapper)
    
    # Load templates
    icon_detector.load_templates()
    number_detector.load_templates()
    
    # Read image
    img = cv.imread(str(image_path))
    if img is None:
        raise FileNotFoundError(f"Could not read image: {image_path}")
    
    # Detect icons and numbers
    icon_matches = icon_detector.detect_matches(img)
    number_matches = number_detector.detect_matches(img)
    
    # Visualize if requested
    if visualize:
        MatchVisualizer.visualize_matches(img, icon_matches, "Icon Detections")
        MatchVisualizer.visualize_matches(img, number_matches, "Number Detections")
    
    # Process and save data
    inventory_data = data_processor.process_inventory_data(icon_matches, number_matches)
    
    if save_excel:
        excel_path = data_processor.save_to_excel(inventory_data, image_path=image_path)
        print(f"Saved inventory report to: {excel_path}")
    
    return inventory_data


if __name__ == "__main__":
    inventory_data = process_inventory_screenshot(
        "test_image.png",
        icon_template_dir="CheckImages/Default",
        number_template_dir="CheckImages/Numbers",
        item_mapping_file="item_mappings.csv",
        number_mapping_file="number_mappings.csv"
    )
    
    # Print results
    for item in inventory_data:
        print(f"Item: {item['Item Name']} ({item['Item Code']}), Quantity: {item['Quantity']}")