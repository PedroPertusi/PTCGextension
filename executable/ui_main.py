from PyQt5.QtWidgets import (
    QMainWindow, QPushButton, QLabel, QFileDialog, QVBoxLayout, QHBoxLayout,
    QWidget, QSlider
)
from PyQt5.QtCore import QTimer, Qt, QRect, QPoint, pyqtSignal
from PyQt5.QtGui import QPixmap, QImage, QMouseEvent
import cv2
import detector
import random
import os

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YOLO Card Detector")
        self.resize(1280, 800)
        self.detection_file_path = "detection_results.txt"
        self.output_video_path = "output_with_detections.mp4"

        self.current_frame_index = 0

        # Main video display
        self.video_label = ClickableLabel()
        self.video_label.setScaledContents(True)
        self.video_label.clicked.connect(self.on_frame_clicked)
        self.video_label.setMaximumSize(960, 540)

        # Detail view
        self.detail_label = QLabel("Click on a card to see detail")
        self.detail_label.setMinimumSize(300, 400)
        self.detail_label.setScaledContents(True)

        # Video control buttons
        self.load_button = QPushButton("Load Video")
        self.load_button.clicked.connect(self.load_video)

        # Processed video button
        self.play_processed_button = QPushButton("Play Processed Video")
        self.play_processed_button.clicked.connect(self.play_processed_video)

        self.play_pause_button = QPushButton("Pause")
        self.play_pause_button.clicked.connect(self.toggle_play)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setEnabled(False)
        self.slider.sliderReleased.connect(self.seek_video)

        # Layout setup
        layout = QVBoxLayout()
        control_layout = QHBoxLayout()
        display_layout = QHBoxLayout()

        control_layout.addWidget(self.load_button)
        control_layout.addWidget(self.play_pause_button)
        control_layout.addWidget(self.play_processed_button)
        control_layout.addWidget(self.slider)

        display_layout.addWidget(self.video_label, 4)
        display_layout.addWidget(self.detail_label, 1)

        layout.addLayout(control_layout)
        layout.addLayout(display_layout)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # Timer and state
        self.timer = QTimer()
        self.timer.timeout.connect(self.next_frame)
        self.cap = None
        self.frame_count = 0
        self.current_frame_pos = 0
        self.fps = 30

        self.processed_video = None
        self.detection_results = []

    def play_processed_video(self):
        if not os.path.exists(self.output_video_path) or not os.path.exists(self.detection_file_path):
            self.video_label.setText("Processed video or detection file not found.")
            return

        self.cap = detector.load_detection_video(self.output_video_path)
        self.detection_results = detector.load_detection_results(self.detection_file_path)

        if not self.cap or not self.cap.isOpened():
            self.video_label.setText("Failed to load processed video.")
            return

        self.frame_count = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.fps = int(self.cap.get(cv2.CAP_PROP_FPS)) or 30

        self.slider.setMaximum(self.frame_count - 1)
        self.slider.setEnabled(True)

        self.current_frame_pos = 0
        self.timer.start(1000 // self.fps)
        self.play_pause_button.setText("Pause")


    def load_video(self):
        video_path, _ = QFileDialog.getOpenFileName(self, "Select video", "", "Videos (*.mp4 *.avi *.mov)")
        if not video_path:
            return

        self.cap = cv2.VideoCapture(video_path)
        if not self.cap.isOpened():
            self.video_label.setText("Failed to load video.")
            return

        self.frame_count = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.fps = int(self.cap.get(cv2.CAP_PROP_FPS)) or 30
        width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        # Video writer for output
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(self.output_video_path, fourcc, self.fps, (width, height))

        with open(self.detection_file_path, 'w') as f:
            frame_index = 0
            while True:
                ret, frame = self.cap.read()
                if not ret:
                    break
                
                frame_with_boxes, boxes = detector.detect_on_frame(frame, return_boxes=True)
                out.write(frame_with_boxes)
                box_lines = [f"{name}, {x},{y},{w},{h}" for (name, x, y, w, h) in boxes]
                f.write(f"Frame {frame_index}: {len(boxes)} detections\n")
                for line in box_lines:
                    f.write(f"{line}\n")
                frame_index += 1

        self.cap.release()
        out.release()

        self.cap = cv2.VideoCapture(self.output_video_path)
        self.slider.setMaximum(self.frame_count - 1)
        self.slider.setEnabled(True)

        self.current_frame_pos = 0
        self.timer.start(1000 // self.fps)
        self.play_pause_button.setText("Pause")

    def display_random_card(self):
        card_path = detector.get_random_card_image_path("./cards")
        if card_path:
            pixmap = QPixmap(card_path).scaled(self.detail_label.size(), Qt.KeepAspectRatio)
            self.detail_label.setPixmap(pixmap)

    def next_frame(self):
        if self.cap is None:
            return

        ret, frame = self.cap.read()
        if not ret:
            self.timer.stop()
            self.video_label.setText("Video ended.")
            return

        boxes = self.detection_results.get(self.current_frame_pos, [])
        for (_, x, y, w, h) in boxes:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)

        self.slider.blockSignals(True)
        self.slider.setValue(self.current_frame_pos)
        self.slider.blockSignals(False)

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        q_img = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
        self.video_label.setPixmap(QPixmap.fromImage(q_img))

        self.current_frame_pos += 1

    def toggle_play(self):
        if self.timer.isActive():
            self.timer.stop()
            self.play_pause_button.setText("Play")
        else:
            self.timer.start(1000 // self.fps)
            self.play_pause_button.setText("Pause")

    def seek_video(self):
        pos = self.slider.value()
        if self.cap:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, pos)
            self.current_frame_pos = pos

    def on_frame_clicked(self, point):
        if not hasattr(self, 'detection_results') or self.cap is None:
            return

        # Obtenha dimensões reais do vídeo
        video_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        video_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        # Dimensões da QLabel
        label_width = self.video_label.width()
        label_height = self.video_label.height()

        # Redimensionar o ponto clicado
        scale_x = video_width / label_width
        scale_y = video_height / label_height

        scaled_point = QPoint(int(point.x() * scale_x), int(point.y() * scale_y))

        boxes = self.detection_results.get(self.current_frame_pos, [])
        for (name, x, y, w, h) in boxes:
            rect = QRect(x, y, w, h)
            if rect.contains(scaled_point):
                print('inside rect', name, rect, scaled_point)
                self.display_random_card()
                return
        else:
            print('outside rect', name, rect, scaled_point)


class ClickableLabel(QLabel):
    clicked = pyqtSignal(QPoint)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(event.pos())