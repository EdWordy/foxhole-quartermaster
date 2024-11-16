# analytics_gui.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
from datetime import datetime
from stockpile_analyzer import StockpileAnalyzer
from visualization.stockpile_charts import StockpileVisualizer
import pandas as pd
import json
from pathlib import Path
import matplotlib.pyplot as plt
import logging
from utils.error_logger import ErrorLogger

class AnalyticsWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        
        # basic init
        self.logger = ErrorLogger()
        self.logger.log_info("Analytics window initialized")
        
        # title setup
        self.title("Foxhole Quartermaster - Analytics")
        self.geometry("1000x800")
        
        # Initialize analyzer and visualizer
        self.analyzer = StockpileAnalyzer()
        self.visualizer = StockpileVisualizer()
        self.reports_dir = None
        self.latest_report = None
        self.data = None
        
        self.create_widgets()
        self._cache = {}
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def handle_error(self, error, operation=""):
        """Handle and log an error."""
        self.error_logger.log_error(error, operation)
        self.status_var.set(f"Error during {operation}")
        messagebox.showerror("Error", f"Error during {operation}. Check logs for details.")
        
    def create_widgets(self):
        # Main container
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Controls frame
        control_frame = ttk.LabelFrame(main_frame, text="Controls", padding="5")
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(control_frame, text="Select Reports Directory", 
                  command=self.select_reports_dir).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Analyze Reports", 
                  command=self.analyze_reports).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Save Full Report", 
                  command=self.save_full_report).pack(side=tk.LEFT, padx=5)
        
        self.dir_label = ttk.Label(control_frame, text="No directory selected")
        self.dir_label.pack(side=tk.LEFT, padx=5)
        
        # Create notebook
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create and add tabs
        self.setup_summary_tab()
        self.setup_critical_items_tab()
        self.setup_categories_tab()
        self.setup_visualization_tab()
        self.setup_settings_tab()
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.pack(fill=tk.X, padx=5, pady=2)

    def setup_summary_tab(self):
        """Set up the summary tab."""
        summary_frame = ttk.Frame(self.notebook)
        self.notebook.add(summary_frame, text="Summary")
        
        # Create text widget for summary
        self.summary_text = scrolledtext.ScrolledText(summary_frame, wrap=tk.WORD)
        self.summary_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def setup_critical_items_tab(self):
        """Set up the critical items tab."""
        critical_frame = ttk.Frame(self.notebook)
        self.notebook.add(critical_frame, text="Critical Items")
        
        # Create treeview for critical items
        columns = ("Category", "Item Name", "Current Quantity", "Threshold", "Needed")
        self.critical_tree = ttk.Treeview(critical_frame, columns=columns, show='headings')
        
        # Set column headings
        for col in columns:
            self.critical_tree.heading(col, text=col)
            self.critical_tree.column(col, width=100)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(critical_frame, orient=tk.VERTICAL, 
                                command=self.critical_tree.yview)
        self.critical_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack widgets
        self.critical_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def setup_categories_tab(self):
        """Set up the categories tab."""
        categories_frame = ttk.Frame(self.notebook)
        self.notebook.add(categories_frame, text="Categories")
        
        # Create treeview for categories
        columns = ("Category", "Total Items", "Total Quantity", "Items Below Threshold")
        self.categories_tree = ttk.Treeview(categories_frame, columns=columns, show='headings')
        
        # Set column headings
        for col in columns:
            self.categories_tree.heading(col, text=col)
            self.categories_tree.column(col, width=100)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(categories_frame, orient=tk.VERTICAL, 
                                command=self.categories_tree.yview)
        self.categories_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack widgets
        self.categories_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def setup_visualization_tab(self):
        """Set up the visualization tab."""
        viz_frame = ttk.Frame(self.notebook)
        self.notebook.add(viz_frame, text="Visualization")
        
        # Controls frame
        control_frame = ttk.Frame(viz_frame)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(control_frame, text="Category Distribution", 
                  command=lambda: self.show_visualization('category')).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Critical Items Chart", 
                  command=lambda: self.show_visualization('critical')).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Historical Trends", 
                  command=lambda: self.show_visualization('trends')).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Save Charts", 
                  command=self.save_charts).pack(side=tk.LEFT, padx=5)
        
        # Canvas for charts
        self.fig_canvas = tk.Canvas(viz_frame, bg='white')
        self.fig_canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def setup_settings_tab(self):
        """Set up the settings tab with both category and item thresholds."""
        settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(settings_frame, text="Settings")
        
        # Create notebook for settings types
        settings_notebook = ttk.Notebook(settings_frame)
        settings_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Category thresholds tab
        category_frame = ttk.Frame(settings_notebook)
        settings_notebook.add(category_frame, text="Category Thresholds")
        self.setup_category_thresholds(category_frame)
        
        # Item thresholds tab
        item_frame = ttk.Frame(settings_notebook)
        settings_notebook.add(item_frame, text="Item Thresholds")
        self.setup_item_thresholds(item_frame)

    def setup_item_thresholds(self, parent):
        """Set up the item thresholds interface."""
        # Search frame
        search_frame = ttk.Frame(parent)
        search_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=5)
        search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=search_var)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Create treeview for items
        columns = ("Code", "Name", "Category", "Threshold")
        tree = ttk.Treeview(parent, columns=columns, show='headings')
        
        # Set column headings
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack tree and scrollbar
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Store references
        self.item_tree = tree
        self.item_search = search_var
        
        # Populate tree
        self.populate_item_thresholds()
        
        # Add buttons
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(button_frame, text="Update Selected", 
                  command=self.update_selected_threshold).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Reset to Defaults", 
                  command=self.reset_item_thresholds).pack(side=tk.LEFT, padx=5)
        
        # Bind search update
        search_var.trace('w', lambda *args: self.filter_items())
        
        # Bind double-click to edit
        tree.bind('<Double-1>', self.edit_threshold)

    def populate_item_thresholds(self):
        """Populate the item threshold treeview."""
        self.item_tree.delete(*self.item_tree.get_children())
        
        for code, data in self.analyzer.threshold_manager.thresholds.items():
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
        
        for code, data in self.analyzer.threshold_manager.thresholds.items():
            if (search_text in code.lower() or 
                search_text in data['name'].lower() or 
                search_text in data['category'].lower()):
                self.item_tree.insert('', tk.END, values=(
                    code,
                    data['name'],
                    data['category'],
                    data['threshold']
                ))
                
    def setup_category_thresholds(self, parent):
        """Set up the category thresholds interface."""
        # Create scrollable frame
        canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
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
        for category, threshold in sorted(self.analyzer.threshold_manager.default_category_thresholds.items()):
            frame = ttk.Frame(scrollable_frame)
            frame.pack(fill=tk.X, padx=5, pady=2)
            
            ttk.Label(frame, text=category, width=20).pack(side=tk.LEFT, padx=5)
            var = tk.StringVar(value=str(threshold))
            self.category_threshold_vars[category] = var
            ttk.Entry(frame, textvariable=var, width=10).pack(side=tk.LEFT, padx=5)
        
        # Pack canvas and scrollbar
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Add buttons
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(button_frame, text="Save Category Thresholds", 
                  command=self.save_category_thresholds).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Reset Categories to Defaults", 
                  command=self.reset_category_thresholds).pack(side=tk.LEFT, padx=5)

    def save_category_thresholds(self):
        """Save category threshold changes."""
        try:
            # Update category thresholds
            for category, var in self.category_threshold_vars.items():
                try:
                    new_threshold = int(var.get())
                    if new_threshold < 0:
                        raise ValueError(f"Threshold for {category} must be positive")
                    self.analyzer.threshold_manager.default_category_thresholds[category] = new_threshold
                except ValueError as e:
                    messagebox.showerror("Error", f"Invalid threshold for {category}: {str(e)}")
                    return
            
            # Update all items with new category defaults
            self.analyzer.threshold_manager.update_from_mappings()
            
            # Refresh item thresholds display if it exists
            if hasattr(self, 'populate_item_thresholds'):
                self.populate_item_thresholds()
                
            messagebox.showinfo("Success", "Category thresholds saved successfully!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error saving category thresholds: {str(e)}")

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
            
            # Apply changes
            self.save_category_thresholds()

    def edit_threshold(self, event):
        """Handle double-click to edit threshold."""
        item = self.item_tree.selection()[0]
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
                    self.analyzer.threshold_manager.update_threshold(code, new_val)
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
            self.analyzer.threshold_manager.update_from_mappings()
            self.populate_item_thresholds()

    def select_reports_dir(self):
        """Open directory selection dialog."""
        directory = filedialog.askdirectory(title="Select Reports Directory")
        if directory:
            self.reports_dir = directory
            self.dir_label.config(text=f"Selected: {os.path.basename(directory)}")

    def _get_cached_analysis(self, analysis_type):
        """Get cached analysis results if available."""
        cache_key = f"{analysis_type}_{self.data['Timestamp'].max()}"
        return self._cache.get(cache_key)
        
    def _cache_analysis(self, analysis_type, result):
        """Cache analysis results."""
        cache_key = f"{analysis_type}_{self.data['Timestamp'].max()}"
        self._cache[cache_key] = result
        
    def analyze_reports(self):
        """Analyze reports with error logging."""
        if not self.reports_dir:
            self.logger.log_warning("No reports directory selected")
            messagebox.showwarning("Warning", "Please select reports directory first.")
            return
        
        try:
            self.status_var.set("Loading reports...")
            self.logger.log_info(f"Starting analysis of reports in {self.reports_dir}")
            self.update_idletasks()
            
            # Clear cache when loading new data
            self._cache.clear()
            
            # Load and validate data
            self.data = self.analyzer.load_reports(self.reports_dir)
            self.data = self.analyzer.validate_and_clean_data(self.data)
            
            # Update all tabs
            self.update_summary_tab()
            self.update_critical_items_tab()
            self.update_categories_tab()
            
            self.logger.log_info("Analysis completed successfully")
            self.status_var.set("Analysis complete")
            messagebox.showinfo("Success", "Analysis complete!")
            
        except Exception as e:
            self.logger.log_error(e, "Error during report analysis")
            self.status_var.set("Error analyzing reports")
            messagebox.showerror("Error", "Error analyzing reports. Check logs for details.")

    def update_summary_tab(self):
        """Update the summary tab with analysis results."""
        if self.data is not None:
            summary = self.analyzer.get_summary(self.data)
            self.summary_text.delete(1.0, tk.END)
            self.summary_text.insert(tk.END, summary)

    def update_critical_items_tab(self):
        """Update the critical items tab."""
        # Clear existing items
        for item in self.critical_tree.get_children():
            self.critical_tree.delete(item)
            
        if self.data is not None:
            critical_items = self.analyzer.get_critical_items(self.data)
            for item in critical_items:
                self.critical_tree.insert('', tk.END, values=(
                    item['Category'],
                    item['Item Name'],
                    item['Current Quantity'],
                    item['Threshold'],
                    item['Needed']
                ))

    def update_categories_tab(self):
        """Update the categories tab."""
        # Clear existing items
        for item in self.categories_tree.get_children():
            self.categories_tree.delete(item)
            
        if self.data is not None:
            category_stats = self.analyzer.get_category_stats(self.data)
            for category, stats in category_stats.items():
                self.categories_tree.insert('', tk.END, values=(
                    category,
                    stats['total_items'],
                    stats['total_quantity'],
                    stats['below_threshold']
                ))

    def setup_visualization_tab(self):
        """Set up the visualization tab."""
        viz_frame = ttk.Frame(self.notebook)
        self.notebook.add(viz_frame, text="Visualization")
        
        # Controls frame
        control_frame = ttk.Frame(viz_frame)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(control_frame, text="Category Distribution", 
                  command=lambda: self.show_visualization('category')).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Critical Items Chart", 
                  command=lambda: self.show_visualization('critical')).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Timeline", 
                  command=lambda: self.show_visualization('trends')).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Save Charts", 
                  command=self.save_charts).pack(side=tk.LEFT, padx=5)
        
        # Frame for displaying charts
        self.chart_frame = ttk.Frame(viz_frame)
        self.chart_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def show_visualization(self, viz_type):
        """Display visualization with memory management."""
        if self.data is None:
            messagebox.showwarning("Warning", "Please analyze reports first.")
            return
            
        try:
            # Clear previous figure
            plt.close('all')
            
            # Clear previous widgets
            for widget in self.chart_frame.winfo_children():
                widget.destroy()
                
            # Create figure
            if viz_type == 'category':
                fig = self.visualizer.create_category_summary(self.data)
            elif viz_type == 'critical':
                fig = self.visualizer.create_critical_items_chart(
                    self.data, 
                    self.analyzer.default_thresholds
                )
            elif viz_type == 'trends':
                fig = self.visualizer.create_timeline_chart(self.data)
            
            # Create canvas for matplotlib figure
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            
            # Add navigation toolbar
            from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
            toolbar = NavigationToolbar2Tk(canvas, self.chart_frame)
            toolbar.update()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            
            self.status_var.set("Ready")
            
        except Exception as e:
            self.handle_error(e, "visualization")
        finally:
            # Ensure figures are cleared
            plt.close('all')

    def on_closing(self):
        """Clean up resources before closing."""
        try:
            # Clear matplotlib figures
            plt.close('all')
            
            # Clear cache
            if hasattr(self, '_cache'):
                self._cache.clear()
            
            # Close any open file handles
            logging.shutdown()
            
            self.logger.log_info("Analytics window closed")
            
            # Destroy window
            self.destroy()
            
        except Exception as e:
            print(f"Error during cleanup: {str(e)}")
            self.destroy()

    def display_figure(self, fig):
        """Display a matplotlib figure on the canvas."""
        self.fig_canvas.delete("all")
        fig.canvas.draw()
        
        self.photo = tk.PhotoImage(master=self.fig_canvas, 
                                 width=fig.canvas.get_width_height()[0],
                                 height=fig.canvas.get_width_height()[1])
        self.photo.put(fig.canvas.tostring_rgb())
        
        self.fig_canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)
        plt.close(fig)

    def save_settings(self):
        """Save the current threshold settings."""
        try:
            # Update analyzer thresholds
            for category, var in self.threshold_vars.items():
                try:
                    new_threshold = int(var.get())
                    if new_threshold < 0:
                        raise ValueError(f"Threshold for {category} must be positive")
                    self.analyzer.default_thresholds[category] = new_threshold
                except ValueError as e:
                    messagebox.showerror("Error", f"Invalid threshold for {category}: {str(e)}")
                    return
            
            # Save to file
            self.save_settings_to_file()
            messagebox.showinfo("Success", "Settings saved successfully!")
            
            # Rerun analysis if we have data
            if self.data is not None:
                self.analyze_reports()
                
        except Exception as e:
            messagebox.showerror("Error", f"Error saving settings: {str(e)}")

    def save_settings_to_file(self):
        """Save settings to configuration file."""
        config = {
            'category_thresholds': {
                category: int(var.get())
                for category, var in self.threshold_vars.items()
            }
        }
        
        with open('quartermaster_settings.json', 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4)

    def reset_settings(self):
        """Reset thresholds to default values."""
        for category, threshold in self.analyzer.default_thresholds.items():
            if category in self.threshold_vars:
                self.threshold_vars[category].set(str(threshold))
        
        if messagebox.askyesno("Save Defaults", "Do you want to save these default values?"):
            self.save_settings()

    def save_full_report(self):
        """Save complete analysis report."""
        if self.data is None:
            messagebox.showwarning("Warning", "Please analyze reports first.")
            return
            
        try:
            report_path = self.analyzer.generate_report(self.data)
            messagebox.showinfo("Success", f"Report saved to: {report_path}")
            
            if messagebox.askyesno("Open Report", "Would you like to open the report now?"):
                os.startfile(report_path)
                 
        except Exception as e:
            messagebox.showerror("Error", f"Error saving report: {str(e)}")

    def save_charts(self):
        """Save all visualization charts to files."""
        if self.data is None:
            messagebox.showwarning("Warning", "Please analyze reports first.")
            return
            
        try:
            directory = filedialog.askdirectory(title="Select Directory to Save Charts")
            if directory:
                self.status_var.set("Saving charts...")
                self.update_idletasks()
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                charts_dir = Path(directory) / f"charts_{timestamp}"
                charts_dir.mkdir(exist_ok=True)
                
                # Save category distribution
                fig = self.visualizer.create_category_summary(self.data)
                fig.savefig(charts_dir / "category_distribution.png")
                plt.close(fig)
                
                # Save critical items chart
                fig = self.visualizer.create_critical_items_chart(
                    self.data, 
                    self.analyzer.default_thresholds
                )
                fig.savefig(charts_dir / "critical_items.png")
                plt.close(fig)
                
                # Save timeline chart
                fig = self.visualizer.create_timeline_chart(self.data)
                fig.savefig(charts_dir / "timeline.png")
                plt.close(fig)
                
                self.status_var.set("Charts saved successfully")
                messagebox.showinfo("Success", f"Charts saved to: {charts_dir}")
                
        except Exception as e:
            self.status_var.set("Error saving charts")
            messagebox.showerror("Error", f"Error saving charts: {str(e)}")

if __name__ == "__main__":
    # For testing the analytics window independently
    root = tk.Tk()
    root.withdraw()  # Hide the root window
    analytics_window = AnalyticsWindow(root)
    analytics_window.mainloop()