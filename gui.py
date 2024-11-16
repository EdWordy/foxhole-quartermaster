# gui.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import cv2
from PIL import Image, ImageTk
import pandas as pd
import sys
import os

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

from main import process_inventory_screenshot

class InventoryScanner(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Inventory Scanner")
        self.geometry("1200x800")
        
        # Set icon if available
        try:
            icon_path = resource_path("icon.ico")
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
        except:
            pass
            
        # Configure grid weight
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(1, weight=1)
        
        # Create main containers
        self.create_input_frame()
        self.create_image_frame()
        self.create_results_frame()
        
        # Initialize variables
        self.current_image = None
        self.current_image_path = None
        
    def create_input_frame(self):
        """Create frame for input controls"""
        input_frame = ttk.Frame(self, padding="5")
        input_frame.grid(row=0, column=0, columnspan=2, sticky="ew")
        
        # Add buttons
        ttk.Button(input_frame, text="Select Image", command=self.select_image).pack(side=tk.LEFT, padx=5)
        ttk.Button(input_frame, text="Process Image", command=self.process_image).pack(side=tk.LEFT, padx=5)
        ttk.Button(input_frame, text="Save Results", command=self.save_results).pack(side=tk.LEFT, padx=5)
        
        # Add checkboxes for options
        self.show_visualization = tk.BooleanVar(value=True)
        ttk.Checkbutton(input_frame, text="Show Detection Visualization", 
                       variable=self.show_visualization).pack(side=tk.LEFT, padx=5)
        
    def create_image_frame(self):
        """Create frame for image display"""
        self.image_frame = ttk.Frame(self, padding="5")
        self.image_frame.grid(row=1, column=0, sticky="nsew")
        
        # Create canvas for image
        self.image_canvas = tk.Canvas(self.image_frame, bg='gray')
        self.image_canvas.pack(fill=tk.BOTH, expand=True)
        
    def create_results_frame(self):
        """Create frame for results display"""
        results_frame = ttk.Frame(self, padding="5")
        results_frame.grid(row=1, column=1, sticky="nsew")
        
        # Create treeview for results
        columns = ("Item Name", "Quantity")
        self.results_tree = ttk.Treeview(results_frame, columns=columns, show='headings')
        
        # Set column headings
        for col in columns:
            self.results_tree.heading(col, text=col)
            self.results_tree.column(col, width=150)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.results_tree.yview)
        self.results_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack widgets
        self.results_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
    def select_image(self):
        """Open file dialog to select an image"""
        filetypes = (
            ('Image files', '*.png *.jpg *.jpeg'),
            ('All files', '*.*')
        )
        
        filename = filedialog.askopenfilename(
            title='Select Image',
            filetypes=filetypes
        )
        
        if filename:
            self.current_image_path = filename
            self.load_image(filename)
            
    def load_image(self, image_path):
        """Load and display the selected image"""
        # Load image with PIL
        image = Image.open(image_path)
        
        # Resize image to fit canvas while maintaining aspect ratio
        canvas_width = self.image_canvas.winfo_width()
        canvas_height = self.image_canvas.winfo_height()
        
        # Calculate resize ratio
        ratio = min(canvas_width/image.width, canvas_height/image.height)
        new_width = int(image.width * ratio)
        new_height = int(image.height * ratio)
        
        # Resize image
        image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Convert to PhotoImage
        self.current_image = ImageTk.PhotoImage(image)
        
        # Display image
        self.image_canvas.create_image(
            canvas_width//2, canvas_height//2,
            image=self.current_image,
            anchor='center'
        )
        
    def process_image(self):
        """Process the selected image"""
        if not self.current_image_path:
            messagebox.showwarning("Warning", "Please select an image first.")
            return
            
        try:
            # Clear previous results
            for item in self.results_tree.get_children():
                self.results_tree.delete(item)
            
            # Process image with resource paths
            inventory_data = process_inventory_screenshot(
                self.current_image_path,
                icon_template_dir=resource_path("CheckImages/Default"),
                number_template_dir=resource_path("CheckImages/Numbers"),
                item_mapping_file=resource_path("item_mappings.csv"),
                number_mapping_file=resource_path("number_mappings.csv"),
                visualize=self.show_visualization.get()
            )
            
            # Display results
            for item in inventory_data:
                self.results_tree.insert('', tk.END, values=(
                    item['Item Name'],
                    item['Quantity']
                ))
                
            messagebox.showinfo("Success", "Image processed successfully!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error processing image: {str(e)}")
            
    def save_results(self):
        """Save results to Excel file"""
        if not self.results_tree.get_children():
            messagebox.showwarning("Warning", "No results to save.")
            return
            
        file_path = filedialog.asksaveasfilename(
            defaultextension='.xlsx',
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")]
        )
        
        if file_path:
            # Get data from treeview
            data = []
            for item in self.results_tree.get_children():
                values = self.results_tree.item(item)['values']
                data.append({
                    'Item Name': values[0],
                    'Quantity': values[1]
                })
                
            # Save to Excel
            df = pd.DataFrame(data)
            df.to_excel(file_path, index=False)
            messagebox.showinfo("Success", f"Results saved to {file_path}")

if __name__ == "__main__":
    app = InventoryScanner()
    app.mainloop()