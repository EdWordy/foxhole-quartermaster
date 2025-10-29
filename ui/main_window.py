# ui/main_window.py
"""
Main window for the Foxhole Quartermaster application.
Provides the primary user interface for the application.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import cv2
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
import pandas as pd
from datetime import datetime

from core.quartermaster import QuartermasterApp
from ui.analytics_window import AnalyticsWindow


class MainWindow(tk.Tk):
    """Main window for the Foxhole Quartermaster application."""
    
    def __init__(self, app: QuartermasterApp):
        """
        Initialize the main window.
        
        Args:
            app: QuartermasterApp instance
        """
        super().__init__()
        
        self.app = app
        
        # Set up window
        self.title("Foxhole Quartermaster")
        self.geometry('1200x800')
        
        # Try to set icon
        try:
            icon_path = self._resource_path("icon.ico")
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
        
        # Set up status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.grid(row=2, column=0, columnspan=2, sticky="ew", padx=5, pady=2)
    
    def _resource_path(self, relative_path: str) -> str:
        """
        Get absolute path to resource, works for dev and for PyInstaller.
        
        Args:
            relative_path: Relative path to the resource
            
        Returns:
            Absolute path to the resource
        """
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)
    
    def create_input_frame(self):
        """Create frame for input controls."""
        input_frame = ttk.Frame(self, padding="5")
        input_frame.grid(row=0, column=0, columnspan=2, sticky="ew")
        
        # Add buttons
        ttk.Button(input_frame, text="Select Screenshot(s)", 
                  command=self.select_images).pack(side=tk.LEFT, padx=5)
        ttk.Button(input_frame, text="Process Selected", 
                  command=self.process_images).pack(side=tk.LEFT, padx=5)
        ttk.Button(input_frame, text="Clear Selection", 
                  command=self.clear_selection).pack(side=tk.LEFT, padx=5)
        ttk.Button(input_frame, text="Save Results", 
                  command=self.save_results).pack(side=tk.LEFT, padx=5)
        ttk.Button(input_frame, text="Analytics", 
                  command=self.open_analytics).pack(side=tk.LEFT, padx=5)
        ttk.Button(input_frame, text="Settings", 
                  command=self.open_settings).pack(side=tk.LEFT, padx=5)
        
        # Add checkboxes for options
        self.show_visualization = tk.BooleanVar(value=self.app.config.get_detection_settings().get('show_visualization', False))
        ttk.Checkbutton(input_frame, text="Show Detection Visualization", 
                       variable=self.show_visualization).pack(side=tk.LEFT, padx=5)
        
        # Add selected files counter
        self.files_label = ttk.Label(input_frame, text="No files selected")
        self.files_label.pack(side=tk.RIGHT, padx=5)
    
    def create_image_frame(self):
        """Create frame for image display and file list."""
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
        """Create frame for results display."""
        results_frame = ttk.Frame(self, padding="5")
        results_frame.grid(row=1, column=1, sticky="nsew")
        
        # Create notebook for results tabs
        self.results_notebook = ttk.Notebook(results_frame)
        self.results_notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create items tab
        items_frame = ttk.Frame(self.results_notebook)
        self.results_notebook.add(items_frame, text="Items")
        
        # Create treeview for results
        columns = ("File", "Item Name", "Category", "Quantity")
        self.results_tree = ttk.Treeview(items_frame, columns=columns, show='headings')
        
        # Set column headings
        for col in columns:
            self.results_tree.heading(col, text=col)
            self.results_tree.column(col, width=150)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(items_frame, orient=tk.VERTICAL, command=self.results_tree.yview)
        self.results_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack widgets
        self.results_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Create summary tab
        summary_frame = ttk.Frame(self.results_notebook)
        self.results_notebook.add(summary_frame, text="Summary")
        
        # Create text widget for summary
        self.summary_text = tk.Text(summary_frame, wrap=tk.WORD)
        self.summary_text.pack(fill=tk.BOTH, expand=True)
    
    def select_images(self):
        """Open file dialog to select multiple images."""
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
        """Update the listbox with selected files."""
        self.file_listbox.delete(0, tk.END)
        for file in self.selected_files:
            self.file_listbox.insert(tk.END, os.path.basename(file))
    
    def on_select_file(self, event):
        """Handle file selection in listbox."""
        selection = self.file_listbox.curselection()
        if selection:
            index = selection[0]
            self.current_image_path = self.selected_files[index]
            self.load_image(self.current_image_path)
    
    def clear_selection(self):
        """Clear all selected files."""
        self.selected_files = []
        self.current_image_path = None
        self.current_image = None
        self.file_listbox.delete(0, tk.END)
        self.image_canvas.delete("all")
        self.files_label.config(text="No files selected")
        
        # Clear results
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        
        self.summary_text.delete(1.0, tk.END)
    
    def load_image(self, image_path):
        """Load and display the selected image."""
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
        """Process all selected images."""
        if not self.selected_files:
            messagebox.showwarning("Warning", "Please select images first.")
            return
            
        try:
            # Clear previous results
            for item in self.results_tree.get_children():
                self.results_tree.delete(item)
            
            self.summary_text.delete(1.0, tk.END)
            
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
            all_items = []
            
            for i, file_path in enumerate(self.selected_files):
                # Update progress
                progress_bar["value"] = (i / total_files) * 100
                progress_label.config(text=f"Processing {os.path.basename(file_path)}...")
                progress_window.update()
                
                try:
                    # Process image
                    report = self.app.process_image(
                        file_path,
                        visualize=self.show_visualization.get()
                    )
                    
                    # Add results to treeview
                    file_name = os.path.basename(file_path)
                    for item in report.items:
                        self.results_tree.insert('', tk.END, values=(
                            file_name,
                            item.name,
                            item.category,
                            item.quantity
                        ))
                        all_items.append(item)
                        
                except Exception as e:
                    messagebox.showerror("Error", f"Error processing {file_path}: {str(e)}")
            
            progress_window.destroy()
            
            # Generate summary
            if all_items:
                # Convert to DataFrame for analysis
                data = pd.DataFrame([item.to_dict() for item in all_items])
                data['Timestamp'] = datetime.now()
                
                # Generate summary
                summary = self.app.inventory_manager.get_summary(data)
                self.summary_text.insert(tk.END, summary)
                
                # Switch to summary tab
                self.results_notebook.select(1)
            
            messagebox.showinfo("Success", "All images processed successfully!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error processing images: {str(e)}")
    
    def save_results(self):
        """Save results to Excel file with image name prefix."""
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
            default_filename = f"{self.app.config.get_reports_path()}/{base_name}_inventory_{timestamp}.xlsx"
        else:
            # If multiple files, use a generic name
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_filename = f"{self.app.config.get_reports_path()}/batch_inventory_{timestamp}.xlsx"
        
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
                    'Category': values[2],
                    'Quantity': values[3]
                })
                
            # Save to Excel
            df = pd.DataFrame(data)
            
            try:
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
                
            except Exception as e:
                messagebox.showerror("Error", f"Error saving results: {str(e)}")
    
    def open_analytics(self):
        """Open the analytics window."""
        try:
            from ui.analytics_window import AnalyticsWindow
            analytics_window = AnalyticsWindow(self, self.app)
            analytics_window.grab_set()  # Make the window modal
        except Exception as e:
            messagebox.showerror("Error", f"Error opening analytics window: {str(e)}")
    
    def open_settings(self):
        """Open the settings window."""
        try:
            settings_window = SettingsWindow(self, self.app)
            settings_window.grab_set()  # Make the window modal
        except Exception as e:
            messagebox.showerror("Error", f"Error opening settings window: {str(e)}")


class SettingsWindow(tk.Toplevel):
    """Settings window for the Foxhole Quartermaster application."""
    
    def __init__(self, parent, app):
        """
        Initialize the settings window.
        
        Args:
            parent: Parent window
            app: QuartermasterApp instance
        """
        super().__init__(parent)
        
        self.app = app
        
        # Set up window
        self.title("Foxhole Quartermaster - Settings")
        self.geometry("800x600")
        
        # Create notebook for settings tabs
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create tabs
        self.create_category_tab()
        self.create_item_tab()
        self.create_general_tab()
        
        # Create buttons
        button_frame = ttk.Frame(self)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(button_frame, text="Save", command=self.save_settings).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.destroy).pack(side=tk.RIGHT, padx=5)
    
    def create_category_tab(self):
        """Create tab for category thresholds."""
        category_frame = ttk.Frame(self.notebook)
        self.notebook.add(category_frame, text="Category Thresholds")
        
        # Create scrollable frame
        canvas = tk.Canvas(category_frame)
        scrollbar = ttk.Scrollbar(category_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Store threshold variables
        self.category_threshold_vars = {}
        
        # Headers
        header_frame = ttk.Frame(scrollable_frame)
        header_frame.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(header_frame, text="Category", width=20).pack(side=tk.LEFT, padx=5)
        ttk.Label(header_frame, text="Default Threshold", width=15).pack(side=tk.LEFT, padx=5)
        
        # Create input fields for each category
        for category, threshold in sorted(self.app.config.config.get('category_thresholds', {}).items()):
            frame = ttk.Frame(scrollable_frame)
            frame.pack(fill=tk.X, padx=5, pady=2)
            
            ttk.Label(frame, text=category, width=20).pack(side=tk.LEFT, padx=5)
            var = tk.StringVar(value=str(threshold))
            self.category_threshold_vars[category] = var
            ttk.Entry(frame, textvariable=var, width=10).pack(side=tk.LEFT, padx=5)
        
        # Pack canvas and scrollbar
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Add reset button
        ttk.Button(category_frame, text="Reset to Defaults", 
                  command=self.reset_category_thresholds).pack(pady=10)
    
    def create_item_tab(self):
        """Create tab for item thresholds."""
        item_frame = ttk.Frame(self.notebook)
        self.notebook.add(item_frame, text="Item Thresholds")
        
        # Search frame
        search_frame = ttk.Frame(item_frame)
        search_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=5)
        self.item_search = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.item_search)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Create treeview for items
        columns = ("Code", "Name", "Category", "Threshold")
        self.item_tree = ttk.Treeview(item_frame, columns=columns, show='headings')
        
        # Set column headings
        for col in columns:
            self.item_tree.heading(col, text=col)
            self.item_tree.column(col, width=100)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(item_frame, orient=tk.VERTICAL, command=self.item_tree.yview)
        self.item_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack tree and scrollbar
        self.item_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Populate tree
        self.populate_item_thresholds()
        
        # Add buttons
        button_frame = ttk.Frame(item_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(button_frame, text="Update Selected", 
                  command=self.update_selected_threshold).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Reset to Defaults", 
                  command=self.reset_item_thresholds).pack(side=tk.LEFT, padx=5)
        
        # Bind search update
        self.item_search.trace('w', lambda *args: self.filter_items())
        
        # Bind double-click to edit
        self.item_tree.bind('<Double-1>', self.edit_threshold)
    
    def create_general_tab(self):
        """Create tab for general settings."""
        general_frame = ttk.Frame(self.notebook)
        self.notebook.add(general_frame, text="General Settings")
        
        # Create settings
        settings_frame = ttk.Frame(general_frame)
        settings_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # UI settings
        ui_frame = ttk.LabelFrame(settings_frame, text="UI Settings")
        ui_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Show visualization
        self.show_viz_var = tk.BooleanVar(value=self.app.config.get_ui_settings().get('show_visualization', False))
        ttk.Checkbutton(ui_frame, text="Show Detection Visualization", 
                       variable=self.show_viz_var).pack(anchor=tk.W, padx=5, pady=5)
        
        # Detection settings
        detection_frame = ttk.LabelFrame(settings_frame, text="Detection Settings")
        detection_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Confidence threshold
        ttk.Label(detection_frame, text="Confidence Threshold:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.confidence_var = tk.StringVar(value=str(self.app.config.get_detection_settings().get('confidence_threshold', 0.95)))
        ttk.Entry(detection_frame, textvariable=self.confidence_var, width=10).grid(row=0, column=1, padx=5, pady=5)
        
        # Max digit distance
        ttk.Label(detection_frame, text="Max Digit Distance:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.digit_distance_var = tk.StringVar(value=str(self.app.config.get_detection_settings().get('max_digit_distance', 150)))
        ttk.Entry(detection_frame, textvariable=self.digit_distance_var, width=10).grid(row=1, column=1, padx=5, pady=5)
        
        # Paths
        paths_frame = ttk.LabelFrame(settings_frame, text="Paths")
        paths_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Reports path
        ttk.Label(paths_frame, text="Reports Directory:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.reports_path_var = tk.StringVar(value=self.app.config.get_reports_path())
        ttk.Entry(paths_frame, textvariable=self.reports_path_var).grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)
        ttk.Button(paths_frame, text="Browse", command=lambda: self.browse_directory(self.reports_path_var)).grid(row=0, column=2, padx=5, pady=5)
        
        # Templates path
        ttk.Label(paths_frame, text="Templates Directory:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.templates_path_var = tk.StringVar(value=self.app.config.get_template_paths().get('icons', 'CheckImages/Default'))
        ttk.Entry(paths_frame, textvariable=self.templates_path_var).grid(row=1, column=1, padx=5, pady=5, sticky=tk.EW)
        ttk.Button(paths_frame, text="Browse", command=lambda: self.browse_directory(self.templates_path_var)).grid(row=1, column=2, padx=5, pady=5)
        
        # Configure grid
        paths_frame.columnconfigure(1, weight=1)
    
    def browse_directory(self, var):
        """Browse for directory and update variable."""
        directory = filedialog.askdirectory(initialdir=var.get())
        if directory:
            var.set(directory)
    
    def populate_item_thresholds(self):
        """Populate the item threshold treeview."""
        self.item_tree.delete(*self.item_tree.get_children())
        
        for code, data in self.app.config.item_thresholds.items():
            self.item_tree.insert('', tk.END, values=(
                code,
                data['name'],
                data['category'],
                data['threshold']
            ))
    
    def filter_items(self):
        """Filter items based on search text."""
        search_text = self.item_search.get().lower()
        self.item_tree.delete(*self.item_tree.get_children())
        
        for code, data in self.app.config.item_thresholds.items():
            if (search_text in code.lower() or 
                search_text in data['name'].lower() or 
                search_text in data['category'].lower()):
                self.item_tree.insert('', tk.END, values=(
                    code,
                    data['name'],
                    data['category'],
                    data['threshold']
                ))
    
    def edit_threshold(self, event):
        """Handle double-click to edit threshold."""
        selection = self.item_tree.selection()
        if not selection:
            return
            
        item = selection[0]
        code = self.item_tree.item(item)['values'][0]
        current = self.item_tree.item(item)['values'][3]
        
        dialog = tk.Toplevel(self)
        dialog.title("Edit Threshold")
        dialog.geometry("300x100")
        
        ttk.Label(dialog, text=f"Enter new threshold for {code}:").pack(padx=5, pady=5)
        
        var = tk.StringVar(value=str(current))
        entry = ttk.Entry(dialog, textvariable=var)
        entry.pack(padx=5, pady=5)
        
        def update():
            try:
                new_val = int(var.get())
                if new_val >= 0:
                    self.app.config.set_item_threshold(code, new_val)
                    self.populate_item_thresholds()
                    dialog.destroy()
                else:
                    messagebox.showwarning("Invalid Value", "Threshold must be non-negative")
            except ValueError:
                messagebox.showwarning("Invalid Value", "Please enter a valid number")
        
        ttk.Button(dialog, text="Update", command=update).pack(padx=5, pady=5)
    
    def update_selected_threshold(self):
        """Update threshold for selected item."""
        selection = self.item_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an item to update")
            return
            
        self.edit_threshold(None)
    
    def reset_item_thresholds(self):
        """Reset all item thresholds to defaults."""
        if messagebox.askyesno("Reset Thresholds", 
                              "Are you sure you want to reset all thresholds to defaults?"):
            self.app.config.update_thresholds_from_categories()
            self.populate_item_thresholds()
    
    def reset_category_thresholds(self):
        """Reset category thresholds to original defaults."""
        if messagebox.askyesno("Reset Thresholds", 
                              "Are you sure you want to reset all category thresholds to defaults?"):
            original_defaults = {
                'Light Arms': 40,
                'Heavy Arms': 25,
                'Munitions': 40,
                'Infantry Equipment': 25,
                'Maintenance': 10,
                'Medical': 15,
                'Uniforms': 10,
                'Vehicles': 5,
                'Materials': 30,
                'Supplies': 20,
                'Logistics': 5,
                'Other': 0
            }
            
            # Update variables
            for category, threshold in original_defaults.items():
                if category in self.category_threshold_vars:
                    self.category_threshold_vars[category].set(str(threshold))
    
    def save_settings(self):
        """Save all settings."""
        try:
            # Save category thresholds
            for category, var in self.category_threshold_vars.items():
                try:
                    new_threshold = int(var.get())
                    if new_threshold < 0:
                        raise ValueError(f"Threshold for {category} must be positive")
                    self.app.config.set_category_threshold(category, new_threshold)
                except ValueError as e:
                    messagebox.showerror("Error", f"Invalid threshold for {category}: {str(e)}")
                    return
            
            # Save general settings
            ui_settings = self.app.config.get_ui_settings()
            ui_settings['show_visualization'] = self.show_viz_var.get()
            
            detection_settings = self.app.config.get_detection_settings()
            try:
                detection_settings['confidence_threshold'] = float(self.confidence_var.get())
                detection_settings['max_digit_distance'] = int(self.digit_distance_var.get())
            except ValueError:
                messagebox.showerror("Error", "Invalid detection settings")
                return
            
            # Save paths
            paths = self.app.config.config.get('paths', {})
            paths['reports'] = self.reports_path_var.get()
            templates = paths.get('templates', {})
            templates['base'] = self.templates_path_var.get()
            # Keep numbers path relative to the base
            templates['numbers'] = self.app.config.get_template_paths().get('numbers', 'CheckImages/Numbers')
            paths['templates'] = templates
            
            # Save all settings
            self.app.config.save()
            
            messagebox.showinfo("Success", "Settings saved successfully!")
            self.destroy()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error saving settings: {str(e)}")
            