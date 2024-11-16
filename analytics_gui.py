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

class AnalyticsWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Foxhole Quartermaster - Analytics")
        self.geometry("1000x800")
        
        # Initialize analyzer and visualizer
        self.analyzer = StockpileAnalyzer()
        self.visualizer = StockpileVisualizer()
        self.reports_dir = None
        self.latest_report = None
        self.data = None
        
        self.create_widgets()
        
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
        """Set up the settings tab."""
        settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(settings_frame, text="Settings")
        
        # Category thresholds
        threshold_frame = ttk.LabelFrame(settings_frame, text="Category Thresholds", padding="5")
        threshold_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create scrollable frame
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
        for category, threshold in sorted(self.analyzer.default_thresholds.items()):
            frame = ttk.Frame(scrollable_frame)
            frame.pack(fill=tk.X, padx=5, pady=2)
            
            ttk.Label(frame, text=category, width=20).pack(side=tk.LEFT, padx=5)
            var = tk.StringVar(value=str(threshold))
            self.threshold_vars[category] = var
            ttk.Entry(frame, textvariable=var, width=10).pack(side=tk.LEFT, padx=5)
        
        # Pack canvas and scrollbar
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Buttons
        button_frame = ttk.Frame(settings_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(button_frame, text="Save Settings", 
                  command=self.save_settings).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Reset to Defaults", 
                  command=self.reset_settings).pack(side=tk.LEFT, padx=5)

    def select_reports_dir(self):
        """Open directory selection dialog."""
        directory = filedialog.askdirectory(title="Select Reports Directory")
        if directory:
            self.reports_dir = directory
            self.dir_label.config(text=f"Selected: {os.path.basename(directory)}")

    def analyze_reports(self):
        """Analyze the selected reports."""
        if not self.reports_dir:
            messagebox.showwarning("Warning", "Please select reports directory first.")
            return
        
        try:
            self.status_var.set("Loading reports...")
            self.update_idletasks()
            
            # Load and analyze data
            self.data = self.analyzer.load_reports(self.reports_dir)
            
            # Update all tabs
            self.update_summary_tab()
            self.update_critical_items_tab()
            self.update_categories_tab()
            
            self.status_var.set("Analysis complete")
            messagebox.showinfo("Success", "Analysis complete!")
            
        except Exception as e:
            self.status_var.set("Error analyzing reports")
            messagebox.showerror("Error", f"Error analyzing reports: {str(e)}")

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
        """Display the selected visualization."""
        if self.data is None:
            messagebox.showwarning("Warning", "Please analyze reports first.")
            return
            
        try:
            self.status_var.set(f"Generating {viz_type} visualization...")
            self.update_idletasks()
            
            # Clear previous widgets in chart frame
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
            self.status_var.set("Error generating visualization")
            messagebox.showerror("Error", f"Error creating visualization: {str(e)}")
            
        finally:
            plt.close('all')  # Clean up matplotlib figures

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