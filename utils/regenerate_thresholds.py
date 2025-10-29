#!/usr/bin/env python3
"""
Script to regenerate item_thresholds.json from catalog.json
This creates default thresholds based on item categories from the catalog.

IMPORTANT: This generates keys that match the template filenames WITHOUT suffixes.
For templates named "vanilla_Aluminum_19", "vanilla_Aluminum_21", etc.,
this will create a single key "vanilla_Aluminum" that matches all variants.
"""

import json
from pathlib import Path

# Default thresholds by category
DEFAULT_THRESHOLDS = {
    "Light Arms": 40,
    "Heavy Arms": 40,
    "Heavy Ammunition": 30,
    "Utility": 20,
    "Medical": 15,
    "Supplies": 20,
    "Materials": 30,
    "Uniforms": 10,
    "Vehicles": 5,
    "Shippables": 5,
    "Logistics": 5,
    "Infantry Equipment": 0,
    "Maintenance": 10,
    "Other": 0
}

def get_category_from_item(item):
    """Extract and normalize category from catalog item"""
    # Try ItemCategory first
    if "ItemCategory" in item:
        category = item["ItemCategory"].replace("EItemCategory::", "")
        # Map some specific categories
        if category == "Supplies":
            # Check if it's medical supplies
            display_name = item.get("DisplayName", "").lower()
            if any(med in display_name for med in ["bandage", "medical", "trauma", "blood", "plasma"]):
                return "Medical"
            # Check if it's fuel
            if any(fuel in display_name for fuel in ["diesel", "petrol", "fuel"]):
                return "Supplies"
            # Check if it's materials
            if any(mat in display_name for mat in ["material", "alloy", "explosive"]):
                return "Materials"
        return category
    
    # For vehicles, use VehicleProfileType
    if "VehicleProfileType" in item:
        return "Vehicles"
    
    # For shippables (containers)
    if "ShippableInfo" in item:
        shippable_type = item["ShippableInfo"]
        if "Container" in item.get("DisplayName", ""):
            return "Logistics"
        return "Shippables"
    
    return "Other"

def map_to_standard_category(raw_category):
    """Map raw categories to standardized threshold categories"""
    category_map = {
        "SmallArms": "Light Arms",
        "HeavyArms": "Heavy Arms",
        "HeavyAmmo": "Heavy Ammunition",
        "Utility": "Utility",
        "Medical": "Medical",
        "Resource": "Supplies",
        "Supplies": "Supplies",
        "Uniforms": "Uniforms",
        "Vehicles": "Vehicles",
        "Shippables": "Shippables",
        "Logistics": "Logistics",
        "Materials": "Materials",
        "Other": "Other"
    }
    return category_map.get(raw_category, "Other")

def generate_item_code(code_name):
    """Return the item's CodeName with vanilla_ prefix to match template filenames"""
    return f"vanilla_{code_name}"

def generate_crate_code(code_name):
    """Generate crate code from CodeName (e.g., 'Aluminum' -> 'vanilla_AluminumCrate')"""
    return f"vanilla_{code_name}Crate"

def should_include_item(item):
    """Determine if an item should be included in thresholds"""
    # Skip items that are typically not stockpiled
    display_name = item.get("DisplayName", "")
    code_name = item.get("CodeName", "")
    
    # Skip structure blueprints and deployed items
    if "Blueprint" in code_name or "Deployed" in code_name:
        return False
    
    # Check if item is stockpilable
    if "ItemProfileData" in item:
        if not item["ItemProfileData"].get("bIsStockpilable", False):
            return False
    
    # Include vehicles that can be shipped
    if "VehicleProfileType" in item:
        return True
    
    # Include items with ItemCategory
    if "ItemCategory" in item:
        return True
    
    return False

def main():
    # Load catalog.json
    catalog_path = Path(r"E:\Github Local Library\foxhole-quartemaster\data\catalog.json")
    with open(catalog_path, 'r', encoding='utf-8') as f:
        catalog = json.load(f)
    
    thresholds = {}
    
    for item in catalog:
        if not should_include_item(item):
            continue
        
        code_name = item.get("CodeName")
        if not code_name:
            continue  # Skip items without CodeName
        
        display_name = item.get("DisplayName", code_name)
        raw_category = get_category_from_item(item)
        category = map_to_standard_category(raw_category)
        
        # Get default threshold for this category
        threshold = DEFAULT_THRESHOLDS.get(category, 0)
        
        # Check if item can be crated
        can_be_crated = False
        if "ItemProfileData" in item:
            can_be_crated = item["ItemProfileData"].get("bIsCratable", False)
        elif "VehicleProfileType" in item:
            can_be_crated = True  # Vehicles can be crated
        
        # Add single item entry
        item_code = generate_item_code(code_name)
        thresholds[item_code] = {
            "name": display_name,
            "category": category,
            "threshold": threshold
        }
        
        # Add crate entry if item can be crated
        if can_be_crated:
            crate_code = generate_crate_code(code_name)
            thresholds[crate_code] = {
                "name": f"{display_name} (crate)",
                "category": category,
                "threshold": threshold
            }
    
    # Write to output file
    output_path = Path(r"E:\Github Local Library\foxhole-quartemaster\data\item_thresholds.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(thresholds, f, indent=2, ensure_ascii=True)
    
    print(f"Generated {len(thresholds)} threshold entries")
    print(f"Output written to: {output_path}")

if __name__ == "__main__":
    main()