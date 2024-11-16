# gui.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import cv2
from PIL import Image, ImageTk
import pandas as pd
import sys
import os
from datetime import datetime

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

from main import process_inventory_screenshot

class InventoryScanner(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Foxhole Quartermaster")
        self.geometry("1200x800")
        
        # Try to set icon
        try:
            icon_path = resource_path("icon.ico")
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
        except:
            pass
            
        # Configure grid weight
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(1, weight=1)
        
        # Initialize variables
        self.current_image = None
        self.current_image_path = None
        self.selected_files = []
        
        # Create main containers
        self.create_input_frame()
        self.create_image_frame()
        self.create_results_frame()
        
    def create_input_frame(self):
        """Create frame for input controls"""
        input_frame = ttk.Frame(self, padding="5")
        input_frame.grid(row=0, column=0, columnspan=2, sticky="ew")
        
        # Add buttons
        ttk.Button(input_frame, text="Select Image(s)", command=self.select_images).pack(side=tk.LEFT, padx=5)
        ttk.Button(input_frame, text="Process Selected", command=self.process_images).pack(side=tk.LEFT, padx=5)
        ttk.Button(input_frame, text="Clear Selection", command=self.clear_selection).pack(side=tk.LEFT, padx=5)
        ttk.Button(input_frame, text="Save Results", command=self.save_results).pack(side=tk.LEFT, padx=5)
        
        # Add checkboxes for options
        self.show_visualization = tk.BooleanVar(value=False)
        ttk.Checkbutton(input_frame, text="Show Detection Visualization", 
                       variable=self.show_visualization).pack(side=tk.LEFT, padx=5)
        
        # Add selected files counter
        self.files_label = ttk.Label(input_frame, text="No files selected")
        self.files_label.pack(side=tk.RIGHT, padx=5)
        
    def create_image_frame(self):
        """Create frame for image display and file list"""
        self.image_frame = ttk.Frame(self, padding="5")
        self.image_frame.grid(row=1, column=0, sticky="nsew")
        
        # Create file listbox
        self.file_listbox = tk.Listbox(self.image_frame, selectmode=tk.SINGLE)
        self.file_listbox.pack(fill=tk.X, pady=5)
        self.file_listbox.bind('<<ListboxSelect>>', self.on_select_file)
        
        # Create canvas for image preview
        self.image_canvas = tk.Canvas(self.image_frame, bg='gray')
        self.image_canvas.pack(fill=tk.BOTH, expand=True)
        
    def create_results_frame(self):
        """Create frame for results display"""
        results_frame = ttk.Frame(self, padding="5")
        results_frame.grid(row=1, column=1, sticky="nsew")
        
        # Create treeview for results
        columns = ("File", "Item Name", "Quantity")
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
        
    def select_images(self):
        """Open file dialog to select multiple images"""
        filetypes = (
            ('Image files', '*.png *.jpg *.jpeg'),
            ('All files', '*.*')
        )
        
        filenames = filedialog.askopenfilenames(
            title='Select Images',
            filetypes=filetypes
        )
        
        if filenames:
            self.selected_files = list(filenames)
            self.update_file_list()
            self.files_label.config(text=f"{len(self.selected_files)} files selected")
            
    def update_file_list(self):
        """Update the listbox with selected files"""
        self.file_listbox.delete(0, tk.END)
        for file in self.selected_files:
            self.file_listbox.insert(tk.END, os.path.basename(file))
            
    def on_select_file(self, event):
        """Handle file selection in listbox"""
        selection = self.file_listbox.curselection()
        if selection:
            index = selection[0]
            self.current_image_path = self.selected_files[index]
            self.load_image(self.current_image_path)
            
    def clear_selection(self):
        """Clear all selected files"""
        self.selected_files = []
        self.current_image_path = None
        self.current_image = None
        self.file_listbox.delete(0, tk.END)
        self.image_canvas.delete("all")
        self.files_label.config(text="No files selected")
        
    def load_image(self, image_path):
        """Load and display the selected image"""
        image = Image.open(image_path)
        
        # Resize image to fit canvas while maintaining aspect ratio
        canvas_width = self.image_canvas.winfo_width()
        canvas_height = self.image_canvas.winfo_height()
        
        ratio = min(canvas_width/image.width, canvas_height/image.height)
        new_width = int(image.width * ratio)
        new_height = int(image.height * ratio)
        
        image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        self.current_image = ImageTk.PhotoImage(image)
        
        self.image_canvas.delete("all")
        self.image_canvas.create_image(
            canvas_width//2, canvas_height//2,
            image=self.current_image,
            anchor='center'
        )
        
    def process_images(self):
        """Process all selected images"""
        if not self.selected_files:
            messagebox.showwarning("Warning", "Please select images first.")
            return
            
        try:
            # Clear previous results
            for item in self.results_tree.get_children():
                self.results_tree.delete(item)
            
            # Create progress bar
            progress_window = tk.Toplevel(self)
            progress_window.title("Processing Images")
            progress_window.geometry("300x150")
            
            progress_label = ttk.Label(progress_window, text="Processing...")
            progress_label.pack(pady=10)
            
            progress_bar = ttk.Progressbar(
                progress_window, 
                orient="horizontal", 
                length=200, 
                mode="determinate"
            )
            progress_bar.pack(pady=10)
            
            # Process each image
            total_files = len(self.selected_files)
            for i, file_path in enumerate(self.selected_files):
                # Update progress
                progress_bar["value"] = (i / total_files) * 100
                progress_label.config(text=f"Processing {os.path.basename(file_path)}...")
                progress_window.update()
                
                # Process image
                inventory_data = process_inventory_screenshot(
                    file_path,
                    icon_template_dir=resource_path("CheckImages/Default"),
                    number_template_dir=resource_path("CheckImages/Numbers"),
                    visualize=self.show_visualization.get()
                )
                
                # Add results to treeview
                file_name = os.path.basename(file_path)
                for item in inventory_data:
                    self.results_tree.insert('', tk.END, values=(
                        file_name,
                        item['Item Name'],
                        item['Quantity']
                    ))
            
            progress_window.destroy()
            messagebox.showinfo("Success", "All images processed successfully!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error processing images: {str(e)}")
            
    def save_results(self):
        """Save results to Excel file with image name prefix"""
        if not self.results_tree.get_children():
            messagebox.showwarning("Warning", "No results to save.")
            return
            
        # Get unique filenames from results
        files = set()
        for item in self.results_tree.get_children():
            values = self.results_tree.item(item)['values']
            files.add(values[0])  # First column contains filename
        
        # If there's only one file, use it as prefix
        if len(files) == 1:
            filename = list(files)[0]
            base_name = os.path.splitext(filename)[0]  # Remove extension
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_filename = f"Reports/{base_name}_inventory_{timestamp}.xlsx"
        else:
            # If multiple files, use a generic name
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_filename = f"Reports/batch_inventory_{timestamp}.xlsx"
        
        file_path = filedialog.asksaveasfilename(
            defaultextension='.xlsx',
            initialfile=default_filename,
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")]
        )
        
        if file_path:
            # Get data from treeview
            data = []
            for item in self.results_tree.get_children():
                values = self.results_tree.item(item)['values']
                data.append({
                    'File': values[0],
                    'Item Name': values[1],
                    'Quantity': values[2]
                })
                
            # Save to Excel
            df = pd.DataFrame(data)
            
            # If multiple files, create separate sheets for each file
            with pd.ExcelWriter(file_path, engine='xlsxwriter') as writer:
                if len(files) > 1:
                    # Create summary sheet with all data
                    df.to_excel(writer, sheet_name='All Results', index=False)
                    
                    # Create individual sheets for each file
                    for filename in files:
                        file_data = df[df['File'] == filename]
                        sheet_name = os.path.splitext(filename)[0][:31]  # Excel limits sheet names to 31 chars
                        file_data.to_excel(writer, sheet_name=sheet_name, index=False)
                else:
                    # Single file - just one sheet
                    df.to_excel(writer, sheet_name='Inventory', index=False)
                
                # Format each worksheet
                for worksheet in writer.sheets.values():
                    workbook = writer.book
                    header_format = workbook.add_format({
                        'bold': True,
                        'bg_color': '#D8E4BC',
                        'border': 1
                    })
                    
                    # Apply header format
                    for col_num, value in enumerate(df.columns.values):
                        worksheet.write(0, col_num, value, header_format)
                        
                    # Auto-adjust column widths
                    for i, col in enumerate(df.columns):
                        max_length = max(
                            df[col].astype(str).apply(len).max(),
                            len(col)
                        ) + 2
                        worksheet.set_column(i, i, max_length)
            
            messagebox.showinfo("Success", f"Results saved to {file_path}")

if __name__ == "__main__":
    app = InventoryScanner()
    app.mainloop()
