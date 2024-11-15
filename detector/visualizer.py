# detector/visualizer.py
import matplotlib.pyplot as plt
import cv2 as cv

class MatchVisualizer:
    @staticmethod
    def visualize_matches(img, matches, title="Detection Results"):
        fig, ax = plt.subplots(figsize=(15, 10))
        ax.imshow(cv.cvtColor(img, cv.COLOR_BGR2RGB))
        ax.set_title(title)

        for match in matches:
            x, y, w, h = match["location"]
            confidence = match["confidence"]
            
            rect = plt.Rectangle((x, y), w, h, fill=False, edgecolor='g', linewidth=2)
            ax.add_patch(rect)
            
            label = f"{match['template_name']}\n{confidence:.2f}"
            ax.text(x, y-5, label, color='white', fontsize=8, 
                    bbox=dict(facecolor='green', alpha=0.5))

        ax.axis('off')
        plt.tight_layout()
        plt.show()