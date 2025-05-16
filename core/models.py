# core/models.py
"""
Core data models for the Foxhole Quartermaster application.
These models provide standardized data structures used throughout the application.
"""

from datetime import datetime
from dataclasses import dataclass
from typing import List, Dict, Optional, Union, Tuple
import pandas as pd

@dataclass
class InventoryItem:
    """Represents a single item in the inventory."""
    code: str
    name: str
    category: str
    quantity: int
    confidence: float = 1.0
    location: Optional[Tuple[int, int, int, int]] = None  # (x, y, width, height)
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "Item Code": self.code,
            "Item Name": self.name,
            "Category": self.category,
            "Quantity": self.quantity,
            "Confidence": f"{self.confidence:.3f}",
            "X": self.location[0] if self.location else None,
            "Y": self.location[1] if self.location else None,
            "Timestamp": self.timestamp
        }


@dataclass
class InventoryReport:
    """Represents a complete inventory report from a single screenshot."""
    items: List[InventoryItem]
    source_image: Optional[str] = None
    timestamp: datetime = None
    report_id: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.report_id is None:
            self.report_id = f"report_{self.timestamp.strftime('%Y%m%d_%H%M%S')}"
    
    def to_dataframe(self) -> pd.DataFrame:
        """Convert report to pandas DataFrame."""
        data = [item.to_dict() for item in self.items]
        df = pd.DataFrame(data)
        if not df.empty:
            df["Report"] = self.report_id
            if "Timestamp" not in df.columns:
                df["Timestamp"] = self.timestamp
        return df
    
    def save_to_csv(self, output_path: Optional[str] = None) -> str:
        """Save report to CSV file."""
        if output_path is None:
            timestamp = self.timestamp.strftime("%Y%m%d_%H%M%S")
            if self.source_image:
                base_name = os.path.splitext(os.path.basename(self.source_image))[0]
                output_path = f"Reports/inv_report_{base_name}_{timestamp}.csv"
            else:
                output_path = f"Reports/inv_report_{timestamp}.csv"
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Save as CSV
        df = self.to_dataframe()
        df.to_csv(output_path, index=False)
        
        return output_path


@dataclass
class CategorySummary:
    """Summary statistics for an item category."""
    name: str
    total_items: int
    total_quantity: int
    below_threshold: int
    threshold: int
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "Category": self.name,
            "Total Items": self.total_items,
            "Total Quantity": self.total_quantity,
            "Items Below Threshold": self.below_threshold,
            "Threshold": self.threshold
        }


@dataclass
class CriticalItem:
    """Represents an item that is below its threshold level."""
    category: str
    item_code: str
    item_name: str
    current_quantity: int
    threshold: int
    
    @property
    def needed(self) -> int:
        """Calculate how many items are needed to reach threshold."""
        return max(0, self.threshold - self.current_quantity)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "Category": self.category,
            "Item Code": self.item_code,
            "Item Name": self.item_name,
            "Current Quantity": self.current_quantity,
            "Threshold": self.threshold,
            "Needed": self.needed
        }


import os  # Added for os.makedirs
