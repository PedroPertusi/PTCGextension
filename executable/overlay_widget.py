# overlay_widget.py

from PyQt5.QtWidgets import QDialog, QLabel, QHBoxLayout
from PyQt5.QtGui import QPixmap
import os
import random

CARDS_DIR = "cards"

class ZoomDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Card Viewer")

        # Choose a random image from the cards directory
        images = [img for img in os.listdir(CARDS_DIR) if img.lower().endswith(('.jpg', '.png'))]
        if not images:
            raise FileNotFoundError("No images found in 'cards' folder.")
        
        card_path = os.path.join(CARDS_DIR, random.choice(images))

        layout = QHBoxLayout()
        label = QLabel()
        pixmap = QPixmap(card_path).scaled(300, 450)
        label.setPixmap(pixmap)
        layout.addWidget(label)
        self.setLayout(layout)
