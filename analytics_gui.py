# analytics_gui.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
from datetime import datetime
from stockpile_analyzer import StockpileAnalyzer
import pandas as pd
import json

class AnalyticsWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Foxhole Quartermaster - Analytics")
        self.geometry("1000x800")
        
        # Initialize analyzer
        self.analyzer = StockpileAnalyzer()
        self.reports_dir = None
        self.latest_report = None
        self.data = None
        
        self.create_widgets()
        
        # Load saved settings
        self.load_settings_from_file()
        
    def create_widgets(self):
        # Main container
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Top control panel
        control_frame = ttk.LabelFrame(main_frame, text="Controls", padding="5")
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Directory selection
        ttk.Button(control_frame, text="Select Reports Directory", 
                  command=self.select_reports_dir).pack(side=tk.LEFT, padx=5)
        self.dir_label = ttk.Label(control_frame, text="No directory selected")
        self.dir_label.pack(side=tk.LEFT, padx=5)
        
        # Analysis buttons
        ttk.Button(control_frame, text="Analyze Reports", 
                  command=self.analyze_reports).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Save Full Report", 
                  command=self.save_full_report).pack(side=tk.LEFT, padx=5)
        
        # Create notebook for different views
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Summary tab
        summary_frame = ttk.Frame(self.notebook)
        self.notebook.add(summary_frame, text="Summary")
        self.summary_text = scrolledtext.ScrolledText(summary_frame, wrap=tk.WORD, 
                                                    width=80, height=20)
        self.summary_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Critical Items tab
        critical_frame = ttk.Frame(self.notebook)
        self.notebook.add(critical_frame, text="Critical Items")
        
        # Create treeview for critical items
        columns = ("Category", "Item Name", "Current Quantity", "Threshold", "Needed")
        self.critical_tree = ttk.Treeview(critical_frame, columns=columns, show='headings')
        
        # Set column headings
        for col in columns:
            self.critical_tree.heading(col, text=col)
            self.critical_tree.column(col, width=100)
            
        # Add scrollbar to critical items
        critical_scroll = ttk.Scrollbar(critical_frame, orient=tk.VERTICAL, 
                                      command=self.critical_tree.yview)
        self.critical_tree.configure(yscrollcommand=critical_scroll.set)
        
        # Pack critical items widgets
        self.critical_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        critical_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Category Analysis tab
        category_frame = ttk.Frame(self.notebook)
        self.notebook.add(category_frame, text="Categories")
        
        # Create treeview for categories
        cat_columns = ("Category", "Total Quantity", "Below Threshold", "Items")
        self.category_tree = ttk.Treeview(category_frame, columns=cat_columns, show='headings')
        
        # Set column headings
        for col in cat_columns:
            self.category_tree.heading(col, text=col)
            self.category_tree.column(col, width=100)
            
        # Add scrollbar to categories
        category_scroll = ttk.Scrollbar(category_frame, orient=tk.VERTICAL, 
                                      command=self.category_tree.yview)
        self.category_tree.configure(yscrollcommand=category_scroll.set)
        
        # Pack category widgets
        self.category_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        category_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.pack(fill=tk.X, padx=5, pady=5)
        
        # Add Settings tab
        settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(settings_frame, text="Settings")
        
        # Create settings interface
        self.create_settings_interface(settings_frame)
        
    def select_reports_dir(self):
        directory = filedialog.askdirectory(title="Select Reports Directory")
        if directory:
            self.reports_dir = directory
            self.dir_label.config(text=f"Selected: {os.path.basename(directory)}")
            
    def analyze_reports(self):
        if not self.reports_dir:
            messagebox.showwarning("Warning", "Please select reports directory first.")
            return
            
        try:
            self.status_var.set("Loading reports...")
            self.update_idletasks()
            
            # Load and analyze data
            self.data = self.analyzer.load_reports(self.reports_dir)
            
            # Update summary tab
            self.status_var.set("Updating summary...")
            self.update_idletasks()
            self.summary_text.delete(1.0, tk.END)
            self.summary_text.insert(tk.END, self.analyzer.get_quick_summary(self.data))
            
            # Update critical items tab
            self.status_var.set("Updating critical items...")
            self.update_idletasks()
            self.update_critical_items()
            
            # Update category analysis tab
            self.status_var.set("Updating categories...")
            self.update_idletasks()
            self.update_category_analysis()
            
            self.status_var.set("Analysis complete")
            messagebox.showinfo("Success", "Analysis complete!")
            
        except Exception as e:
            self.status_var.set("Error during analysis")
            messagebox.showerror("Error", f"Error analyzing reports: {str(e)}")
            
    def update_critical_items(self):
        # Clear existing items
        for item in self.critical_tree.get_children():
            self.critical_tree.delete(item)
            
        # Add new items
        critical_items = self.analyzer.identify_critical_items(self.data)
        for _, item in critical_items.iterrows():
            self.critical_tree.insert('', tk.END, values=(
                item['Category'],
                item['Item Name'],
                item['Current Quantity'],
                item['Threshold'],
                item['Needed']
            ))
            
    def update_category_analysis(self):
        # Clear existing items
        for item in self.category_tree.get_children():
            self.category_tree.delete(item)
            
        # Add new items
        category_analysis = self.analyzer.analyze_categories(self.data)
        for category, row in category_analysis.iterrows():
            self.category_tree.insert('', tk.END, values=(
                category,
                row['Total Quantity'],
                row['Items Below Threshold'],
                row['Items']
            ))
            
    def save_full_report(self):
        if self.data is None:
            messagebox.showwarning("Warning", "Please analyze reports first.")
            return
            
        try:
            report_path = self.analyzer.generate_report(self.data)
            self.latest_report = report_path
            messagebox.showinfo("Success", f"Report saved to: {report_path}")
            
            # Ask if user wants to open the report
            if messagebox.askyesno("Open Report", "Would you like to open the report now?"):
                os.startfile(report_path)
                
        except Exception as e:
            messagebox.showerror("Error", f"Error saving report: {str(e)}")
            
    def create_settings_interface(self, parent):
        """Create the settings interface for category thresholds."""
        # Main settings container
        settings_container = ttk.Frame(parent)
        settings_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Category thresholds section
        threshold_frame = ttk.LabelFrame(settings_container, text="Category Thresholds", padding="5")
        threshold_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create scrollable frame for thresholds
        canvas = tk.Canvas(threshold_frame)
        scrollbar = ttk.Scrollbar(threshold_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Store threshold variables
        self.threshold_vars = {}
        
        # Create input fields for each category
        for i, (category, info) in enumerate(self.analyzer.categories.items()):
            category_frame = ttk.Frame(scrollable_frame)
            category_frame.pack(fill=tk.X, padx=5, pady=2)
            
            # Category label
            ttk.Label(category_frame, text=category, width=20).pack(side=tk.LEFT, padx=5)
            
            # Threshold input
            threshold_var = tk.StringVar(value=str(info['threshold']))
            self.threshold_vars[category] = threshold_var
            threshold_entry = ttk.Entry(category_frame, textvariable=threshold_var, width=10)
            threshold_entry.pack(side=tk.LEFT, padx=5)
            
            # Items in category (for reference)
            items_text = ", ".join(info['codes'])
            ttk.Label(category_frame, text=f"Items: {items_text}").pack(side=tk.LEFT, padx=5)
        
        # Pack canvas and scrollbar
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Buttons frame
        button_frame = ttk.Frame(settings_container)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(button_frame, text="Save Settings", 
                  command=self.save_settings).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Reset to Defaults", 
                  command=self.reset_settings).pack(side=tk.LEFT, padx=5)

    def save_settings(self):
        """Save the current threshold settings."""
        try:
            # Update analyzer thresholds
            for category, var in self.threshold_vars.items():
                try:
                    new_threshold = int(var.get())
                    if new_threshold < 0:
                        raise ValueError(f"Threshold for {category} must be positive")
                    self.analyzer.categories[category]['threshold'] = new_threshold
                except ValueError as e:
                    messagebox.showerror("Error", f"Invalid threshold for {category}: {str(e)}")
                    return
            
            # Save to configuration file
            self.save_settings_to_file()
            
            messagebox.showinfo("Success", "Settings saved successfully!")
            
            # Rerun analysis if we have data loaded
            if self.data is not None:
                self.analyze_reports()
                
        except Exception as e:
            messagebox.showerror("Error", f"Error saving settings: {str(e)}")


    def save_settings_to_file(self):
        """Save current settings to a configuration file."""
        config = {
            'category_thresholds': {}
        }
        
        # Collect all threshold values
        for category, var in self.threshold_vars.items():
            try:
                config['category_thresholds'][category] = int(var.get())
            except ValueError:
                config['category_thresholds'][category] = self.analyzer.categories[category]['threshold']
        
        try:
            # Ensure the file is written with proper encoding
            with open('quartermaster_settings.json', 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            messagebox.showerror("Error", f"Could not save settings file: {str(e)}")

    def load_settings_from_file(self):
        """Load settings from configuration file with proper error handling."""
        try:
            # Try to read existing settings
            if os.path.exists('quartermaster_settings.json'):
                with open('quartermaster_settings.json', 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    
                # Update threshold variables
                thresholds = config.get('category_thresholds', {})
                for category, threshold in thresholds.items():
                    if category in self.threshold_vars:
                        self.threshold_vars[category].set(str(threshold))
                        self.analyzer.categories[category]['threshold'] = threshold
            else:
                # If no file exists, create one with default values
                default_config = {
                    'category_thresholds': {
                        category: info['threshold']
                        for category, info in self.analyzer.categories.items()
                    }
                }
                with open('quartermaster_settings.json', 'w', encoding='utf-8') as f:
                    json.dump(default_config, f, indent=4)
                    
        except json.JSONDecodeError:
            # Handle corrupted settings file
            print("Settings file corrupted, creating new one with defaults")
            os.remove('quartermaster_settings.json')
            self.reset_settings()
            self.save_settings_to_file()
        except Exception as e:
            print(f"Error loading settings: {str(e)}")
            # Continue with default values
            self.reset_settings()

    def reset_settings(self):
        """Reset thresholds to default values."""
        for category, info in self.analyzer.categories.items():
            if category in self.threshold_vars:
                default_threshold = info['threshold']
                self.threshold_vars[category].set(str(default_threshold))
                
        # Ask if user wants to save these defaults
        if messagebox.askyesno("Save Defaults", "Do you want to save these default values?"):
            self.save_settings()