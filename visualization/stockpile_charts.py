# visualization/stockpile_charts.py
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from datetime import datetime
import os

class StockpileVisualizer:
    def __init__(self):
        # Use a built-in style instead of seaborn
        plt.style.use('bmh')  # or try 'ggplot', 'classic', 'fivethirtyeight'
        
    def create_category_summary(self, data):
        """Create pie and bar charts showing item distribution by category."""
        # Group items by category and sum quantities
        category_totals = data.groupby('Category')['Quantity'].sum()
        
        # Create figure with two subplots
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 7))
        
        # Pie chart
        ax1.pie(category_totals, labels=category_totals.index, autopct='%1.1f%%')
        ax1.set_title('Distribution of Items by Category')
        
        # Bar chart
        category_totals.plot(kind='bar', ax=ax2)
        ax2.set_title('Total Quantities by Category')
        ax2.set_xlabel('Category')
        ax2.set_ylabel('Total Quantity')
        plt.xticks(rotation=45)
        
        plt.tight_layout()
        return fig

    def create_critical_items_chart(self, data, thresholds):
        """Create visualization of items near or below critical thresholds."""
        items_vs_threshold = []
        
        for _, row in data.iterrows():
            category = row['Category']
            threshold = thresholds.get(category, thresholds['Other'])
            if threshold > 0:  # Avoid division by zero
                percentage = (row['Quantity'] / threshold) * 100
                items_vs_threshold.append({
                    'Item': row['Item Name'],
                    'Percentage': percentage,
                    'Actual': row['Quantity'],
                    'Threshold': threshold
                })
        
        df = pd.DataFrame(items_vs_threshold)
        
        # Sort by percentage and get items below 150% of threshold
        df = df[df['Percentage'] < 150].sort_values('Percentage')
        
        # Create chart
        fig, ax = plt.subplots(figsize=(12, 6))
        bars = ax.barh(df['Item'], df['Percentage'])
        
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
        plt.tight_layout()
        
        return fig

    def create_timeline_chart(self, data):
        """Create timeline showing quantity changes over time."""
        # Pivot data for timeline
        timeline = data.pivot(index='Timestamp', columns='Item Name', values='Quantity')
        
        # Create figure
        fig, ax = plt.subplots(figsize=(15, 8))
        
        # Plot each item
        colors = plt.cm.tab20(np.linspace(0, 1, len(timeline.columns)))
        for item, color in zip(timeline.columns, colors):
            ax.plot(timeline.index, timeline[item], marker='o', label=item, color=color)
        
        # Customize chart
        ax.set_title('Item Quantities Over Time')
        ax.set_xlabel('Time')
        ax.set_ylabel('Quantity')
        plt.xticks(rotation=45)
        
        # Add legend with smaller font and outside plot
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize='small')
        
        plt.tight_layout()
        return fig

    def create_category_heatmap(self, data):
        """Create heatmap showing quantity changes over time."""
        # Pivot data for heatmap
        pivot = data.pivot_table(
            index='Category', 
            columns='Timestamp', 
            values='Quantity',
            aggfunc='sum'
        )
        
        # Create figure
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Create heatmap using matplotlib
        im = ax.imshow(pivot, aspect='auto', cmap='YlOrRd')
        
        # Add colorbar
        plt.colorbar(im, ax=ax, label='Quantity')
        
        # Set labels
        ax.set_title('Category Quantities Over Time')
        ax.set_yticks(range(len(pivot.index)))
        ax.set_yticklabels(pivot.index)
        ax.set_xticks(range(len(pivot.columns)))
        ax.set_xticklabels([t.strftime('%Y-%m-%d %H:%M') for t in pivot.columns], 
                          rotation=45, ha='right')
        
        plt.tight_layout()
        return fig

    def save_all_charts(self, data, historical_data, thresholds, output_dir):
        """Generate and save all visualization charts."""
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Category summary
        fig = self.create_category_summary(data)
        fig.savefig(os.path.join(output_dir, f"category_summary_{timestamp}.png"))
        plt.close(fig)
        
        # Critical items
        fig = self.create_critical_items_chart(data, thresholds)
        fig.savefig(os.path.join(output_dir, f"critical_items_{timestamp}.png"))
        plt.close(fig)
        
        # Timeline chart
        fig = self.create_timeline_chart(historical_data)
        fig.savefig(os.path.join(output_dir, f"timeline_{timestamp}.png"))
        plt.close(fig)
        
        # Category heatmap
        fig = self.create_category_heatmap(historical_data)
        fig.savefig(os.path.join(output_dir, f"category_heatmap_{timestamp}.png"))
        plt.close(fig)