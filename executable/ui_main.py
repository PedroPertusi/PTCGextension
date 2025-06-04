# ui_main.py

from PyQt5.QtWidgets import QLabel, QMainWindow, QVBoxLayout, QWidget, QDialog, QHBoxLayout
from PyQt5.QtCore import QTimer, QRect
from PyQt5.QtGui import QImage, QPixmap, QPainter, QColor
import cv2
from screen_capture import get_video_frame
from detector_mock import detect_cards_mock

class ZoomDialog(QDialog):
    def __init__(self, card_path):
        super().__init__()
        self.setWindowTitle("Card Viewer")
        layout = QHBoxLayout()
        label = QLabel()
        pixmap = QPixmap(card_path).scaled(300, 450)
        label.setPixmap(pixmap)
        layout.addWidget(label)
        self.setLayout(layout)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pokémon Card Inspector (Mock)")
        self.setGeometry(100, 100, 1280, 720)

        self.label = QLabel()
        layout = QVBoxLayout()
        layout.addWidget(self.label)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(1000 // 10)  # ~10 FPS

        self.boxes = []

    def update_frame(self):
        frame = get_video_frame()
        if frame is None:
            return

        h, w, _ = frame.shape
        self.boxes = detect_cards_mock(w, h)

        qt_img = QImage(frame.data, w, h, 3 * w, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_img)

        painter = QPainter(pixmap)
        painter.setPen(QColor(0, 255, 0))
        for box in self.boxes:
            x, y, bw, bh, name = box
            painter.drawRect(x, y, bw, bh)
        painter.end()

        self.label.setPixmap(pixmap)
        self.label.mousePressEvent = self.on_click

    def on_click(self, event):
        x_click = event.pos().x()
        y_click = event.pos().y()

        for box in self.boxes:
            x, y, w, h, name = box
            if x <= x_click <= x + w and y <= y_click <= y + h:
                dialog = ZoomDialog(f"cards/{name}.jpg")
                dialog.exec_()
                break
