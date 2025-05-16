# ui/analytics_window.py
"""
Analytics window for the Foxhole Quartermaster application.
Provides data analysis and visualization capabilities.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from pathlib import Path
from typing import List, Dict, Any, Optional, Union


class AnalyticsWindow(tk.Toplevel):
    """Analytics window for the Foxhole Quartermaster application."""
    
    def __init__(self, parent, app):
        """
        Initialize the analytics window.
        
        Args:
            parent: Parent window
            app: QuartermasterApp instance
        """
        super().__init__(parent)
        
        self.app = app
        
        # Set up window
        self.title("Foxhole Quartermaster - Analytics")
        self.geometry("1000x800")
        
        # Initialize variables
        self.reports_dir = None
        self.data = None
        
        # Create widgets
        self.create_widgets()
        
        # Cache for analysis results
        self._cache = {}
        
        # Handle window close
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def create_widgets(self):
        """Create widgets for the analytics window."""
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
        ttk.Button(control_frame, text="Timeline", 
                  command=lambda: self.show_visualization('trends')).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Save Charts", 
                  command=self.save_charts).pack(side=tk.LEFT, padx=5)
        
        # Frame for displaying charts
        self.chart_frame = ttk.Frame(viz_frame)
        self.chart_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    def select_reports_dir(self):
        """Open directory selection dialog."""
        directory = filedialog.askdirectory(title="Select Reports Directory")
        if directory:
            self.reports_dir = directory
            self.dir_label.config(text=f"Selected: {os.path.basename(directory)}")
    
    def analyze_reports(self):
        """Analyze reports with error logging."""
        if not self.reports_dir:
            messagebox.showwarning("Warning", "Please select reports directory first.")
            return
        
        try:
            self.status_var.set("Loading reports...")
            self.update_idletasks()
            
            # Clear cache when loading new data
            self._cache.clear()
            
            # Load and validate data
            self.data = self.app.load_reports(self.reports_dir)
            
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
            summary = self.app.inventory_manager.get_summary(self.data)
            self.summary_text.delete(1.0, tk.END)
            self.summary_text.insert(tk.END, summary)
    
    def update_critical_items_tab(self):
        """Update the critical items tab."""
        # Clear existing items
        for item in self.critical_tree.get_children():
            self.critical_tree.delete(item)
            
        if self.data is not None:
            critical_items = self.app.inventory_manager.get_critical_items(self.data)
            for item in critical_items:
                self.critical_tree.insert('', tk.END, values=(
                    item.category,
                    item.item_name,
                    item.current_quantity,
                    item.threshold,
                    item.needed
                ))
    
    def update_categories_tab(self):
        """Update the categories tab."""
        # Clear existing items
        for item in self.categories_tree.get_children():
            self.categories_tree.delete(item)
            
        if self.data is not None:
            category_stats = self.app.inventory_manager.get_category_stats(self.data)
            for category, stats in category_stats.items():
                self.categories_tree.insert('', tk.END, values=(
                    stats.name,
                    stats.total_items,
                    stats.total_quantity,
                    stats.below_threshold
                ))
    
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
            fig = plt.Figure(figsize=(10, 6))
            
            if viz_type == 'category':
                self._create_category_chart(fig)
            elif viz_type == 'critical':
                self._create_critical_chart(fig)
            elif viz_type == 'trends':
                self._create_timeline_chart(fig)
            
            # Create canvas for matplotlib figure
            canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            
            # Add navigation toolbar
            toolbar = NavigationToolbar2Tk(canvas, self.chart_frame)
            toolbar.update()
            
            self.status_var.set("Ready")
            
        except Exception as e:
            self.status_var.set("Error creating visualization")
            messagebox.showerror("Error", f"Error creating visualization: {str(e)}")
        finally:
            # Ensure figures are cleared
            plt.close('all')
    
    def _create_category_chart(self, fig):
        """Create category distribution chart."""
        # Group items by category and sum quantities
        category_totals = self.data.groupby('Category')['Quantity'].sum()
        
        # Create subplots
        ax1 = fig.add_subplot(121)
        ax2 = fig.add_subplot(122)
        
        # Pie chart
        ax1.pie(category_totals, labels=category_totals.index, autopct='%1.1f%%')
        ax1.set_title('Distribution of Items by Category')
        
        # Bar chart
        category_totals.plot(kind='bar', ax=ax2)
        ax2.set_title('Total Quantities by Category')
        ax2.set_xlabel('Category')
        ax2.set_ylabel('Total Quantity')
        plt.setp(ax2.get_xticklabels(), rotation=45, ha='right')
        
        fig.tight_layout()
    
    def _create_critical_chart(self, fig):
        """Create critical items chart."""
        critical_items = self.app.inventory_manager.get_critical_items(self.data)
        
        if not critical_items:
            ax = fig.add_subplot(111)
            ax.text(0.5, 0.5, "No critical items found", 
                   horizontalalignment='center', verticalalignment='center',
                   transform=ax.transAxes, fontsize=14)
            return
        
        # Create DataFrame from critical items
        df = pd.DataFrame([item.to_dict() for item in critical_items])
        
        # Calculate percentage of threshold
        df['Percentage'] = (df['Current Quantity'] / df['Threshold']) * 100
        
        # Sort by percentage
        df = df.sort_values('Percentage')
        
        # Create chart
        ax = fig.add_subplot(111)
        bars = ax.barh(df['Item Name'], df['Percentage'])
        
        # Color code bars based on percentage
        colors = ['#ff6b6b', '#ffd93d', '#6bff6b']  # red, yellow, green
        for i, bar in enumerate(bars):
            if df.iloc[i]['Percentage'] < 50:
                bar.set_color(colors[0])
            elif df.iloc[i]['Percentage'] < 100:
                bar.set_color(colors[1])
            else:
                bar.set_color(colors[2])
        
        # Add threshold line
        ax.axvline(x=100, color='red', linestyle='--', label='Threshold')
        
        # Customize chart
        ax.set_title('Items Near or Below Critical Thresholds')
        ax.set_xlabel('Percentage of Threshold')
        fig.tight_layout()
    
    def _create_timeline_chart(self, fig):
        """Create timeline chart."""
        # Check if we have multiple timestamps
        if len(self.data['Timestamp'].unique()) <= 1:
            ax = fig.add_subplot(111)
            ax.text(0.5, 0.5, "Insufficient data for timeline (need multiple reports)", 
                   horizontalalignment='center', verticalalignment='center',
                   transform=ax.transAxes, fontsize=14)
            return
        
        # Pivot data for timeline
        timeline = self.data.pivot(index='Timestamp', columns='Item Name', values='Quantity')
        
        # Create chart
        ax = fig.add_subplot(111)
        
        # Limit to top 10 items for readability
        top_items = self.data.groupby('Item Name')['Quantity'].sum().nlargest(10).index
        for item in top_items:
            if item in timeline.columns:
                ax.plot(timeline.index, timeline[item], marker='o', label=item)
        
        # Customize chart
        ax.set_title('Item Quantities Over Time (Top 10 Items)')
        ax.set_xlabel('Time')
        ax.set_ylabel('Quantity')
        plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
        
        # Add legend with smaller font and outside plot
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize='small')
        
        fig.tight_layout()
    
    def save_full_report(self):
        """Save complete analysis report."""
        if self.data is None:
            messagebox.showwarning("Warning", "Please analyze reports first.")
            return
            
        try:
            report_path = self.app.generate_report(self.data)
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
                fig = plt.Figure(figsize=(10, 6))
                self._create_category_chart(fig)
                fig.savefig(charts_dir / "category_distribution.png")
                plt.close(fig)
                
                # Save critical items chart
                fig = plt.Figure(figsize=(10, 6))
                self._create_critical_chart(fig)
                fig.savefig(charts_dir / "critical_items.png")
                plt.close(fig)
                
                # Save timeline chart
                fig = plt.Figure(figsize=(10, 6))
                self._create_timeline_chart(fig)
                fig.savefig(charts_dir / "timeline.png")
                plt.close(fig)
                
                self.status_var.set("Charts saved successfully")
                messagebox.showinfo("Success", f"Charts saved to: {charts_dir}")
                
        except Exception as e:
            self.status_var.set("Error saving charts")
            messagebox.showerror("Error", f"Error saving charts: {str(e)}")
    
    def on_closing(self):
        """Clean up resources before closing."""
        try:
            # Clear matplotlib figures
            plt.close('all')
            
            # Clear cache
            self._cache.clear()
            
            # Destroy window
            self.destroy()
            
        except Exception as e:
            print(f"Error during cleanup: {str(e)}")
            self.destroy()
