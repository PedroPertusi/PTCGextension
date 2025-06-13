from PyQt5.QtWidgets import (
    QMainWindow, QPushButton, QLabel, QFileDialog, QVBoxLayout, QHBoxLayout,
    QWidget, QSlider, QProgressBar, QInputDialog
)
from PyQt5.QtCore import QTimer, Qt, QRect, QPoint, pyqtSignal, QObject, QThread
from PyQt5.QtGui import QPixmap, QImage, QMouseEvent
import cv2
import detector
import random
import os

class VideoProcessor(QObject):
    frame_ready = pyqtSignal(QImage)
    finished = pyqtSignal()
    update_slider = pyqtSignal(int)
    update_progress = pyqtSignal(int)

    def __init__(self, video_path, output_path, result_path, fps):
        super().__init__()
        self.video_path = video_path
        self.output_path = output_path
        self.result_path = result_path
        self.fps = fps

    def run(self):
        cap = cv2.VideoCapture(self.video_path)
        if not cap.isOpened():
            self.finished.emit()
            return

        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(self.output_path, fourcc, self.fps, (width, height))

        with open(self.result_path, 'w') as f:
            frame_index = 0
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                frame_with_boxes, boxes = detector.detect_on_frame(frame, return_boxes=True)
                out.write(frame_with_boxes)

                # Save detection results
                box_lines = [f"{int(name)}, {x},{y},{w},{h}" for (name, x, y, w, h) in boxes]

                f.write(f"Frame {frame_index}: {len(boxes)} detections\n")
                for line in box_lines:
                    f.write(f"{line}\n")

                self.update_progress.emit(int((frame_index / frame_count) * 100))
                frame_index += 1

        cap.release()
        out.release()
        self.finished.emit()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YOLO Card Detector")
        self.resize(1280, 800)

        self.__init_video__()

        self.static_image_mode = False
        self.static_detections = []

        os.makedirs("results", exist_ok=True)

        # UI Elements

        self.video_label = ClickableLabel()
        self.video_label.setScaledContents(True)
        self.video_label.clicked.connect(self.on_frame_clicked)
        self.video_label.setMaximumSize(960, 540)

        self.detail_label = QLabel("Click on a card to see detail")
        self.detail_label.setMinimumSize(300, 400)
        self.detail_label.setScaledContents(True)

        self.load_button = QPushButton("Process Video")
        self.load_button.clicked.connect(self.load_video)
    
        self.detect_image_button = QPushButton("Detect on Image")
        self.detect_image_button.clicked.connect(self.detect_on_image)

        self.play_processed_button = QPushButton("Play Processed Video")
        self.play_processed_button.clicked.connect(self.select_processed_video)

        self.play_pause_button = QPushButton("Pause")
        self.play_pause_button.clicked.connect(self.toggle_play)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setEnabled(False)
        self.slider.sliderReleased.connect(self.seek_video)

        self.progress = QProgressBar()
        self.progress.setValue(0)

        # Ui base visibility
        self.slider.setVisible(False)
        self.play_pause_button.setVisible(False)
        self.progress.setVisible(False)


        # Layout

        layout = QVBoxLayout()
        control_layout = QHBoxLayout()
        display_layout = QHBoxLayout()

        control_layout.addWidget(self.load_button)
        control_layout.addWidget(self.detect_image_button)
        control_layout.addWidget(self.play_pause_button)
        control_layout.addWidget(self.play_processed_button)
        control_layout.addWidget(self.slider)
        
        display_layout.addWidget(self.video_label, 4)
        display_layout.addWidget(self.detail_label, 1)

        layout.addLayout(control_layout)
        layout.addWidget(self.progress)
        layout.addLayout(display_layout)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.timer = QTimer()
        self.timer.timeout.connect(self.next_frame)

    def __init_video__(self):
        
        self.cap = None
        self.detection_results = []
        self.frame_count = 0
        self.current_frame_pos = 0
        self.fps = 30
        # Ensure results directory exists
        os.makedirs("results", exist_ok=True)

    def next_available_index(self):
        existing = [f for f in os.listdir("results") if f.startswith("output_") and f.endswith(".mp4")]
        indices = [int(f.split('_')[1].split('.')[0]) for f in existing if f.split('_')[1].split('.')[0].isdigit()]
        return max(indices + [0]) + 1

    def load_video(self):
        self.progress.setVisible(True)
        self.static_image_mode = False
        video_path, _ = QFileDialog.getOpenFileName(self, "Select video", "", "Videos (*.mp4 *.avi *.mov)")
        if not video_path:
            return

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            self.video_label.setText("Failed to load video.")
            return
        

        self.frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.fps = int(cap.get(cv2.CAP_PROP_FPS)) or 30
        cap.release()

        self.slider.setMaximum(self.frame_count - 1)
        self.slider.setEnabled(True)
        self.current_frame_pos = 0

        index = self.next_available_index()
        output_path = os.path.join("results", f"output_{index}.mp4")
        result_path = os.path.join("results", f"results_{index}.txt")

        self.processor_thread = QThread()
        self.static_image_mode = False
        self.processor = VideoProcessor(video_path, output_path, result_path, self.fps)
        self.processor.moveToThread(self.processor_thread)

        self.processor.update_slider.connect(self.slider.setValue)
        self.processor.update_progress.connect(self.progress.setValue)
        self.processor.finished.connect(self.processor_thread.quit)
        self.processor.finished.connect(self.on_processing_finished)

        self.processor_thread.started.connect(self.processor.run)
        self.processor_thread.start()

    def select_processed_video(self):
        self.__init_video__()
        self.static_image_mode = False
        self.detail_label.setText("Click on a card to see detail")
        self.detail_label.setPixmap(QPixmap())
        
        files = sorted([
            f for f in os.listdir("results")
            if f.startswith("output_") and f.endswith(".mp4")
        ])

        if not files:
            self.video_label.setText("No processed videos found in 'results' folder.")
            return

        items = [f.replace("output_", "").replace(".mp4", "") for f in files]
        item, ok = QInputDialog.getItem(self, "Choose Processed Video", "Video:", items, 0, False)
        if not ok or not item:
            return

        output_video = os.path.join("results", f"output_{item}.mp4")
        result_file = os.path.join("results", f"results_{item}.txt")

        self.cap = detector.load_detection_video(output_video)
        self.detection_results = detector.load_detection_results(result_file)

        if not self.cap or not self.cap.isOpened():
            self.video_label.setText("Failed to load processed video.")
            return

        self.frame_count = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.fps = int(self.cap.get(cv2.CAP_PROP_FPS)) or 30

        self.slider.setMaximum(self.frame_count - 1)
        self.slider.setEnabled(True)
        self.current_frame_pos = 0
        self.slider.setVisible(True)
        self.play_pause_button.setVisible(True)
        self.timer.start(1000 // self.fps)
        self.play_pause_button.setText("Pause")

    def on_processing_finished(self):
        self.progress.setValue(100)
        self.static_image_mode = False
        # Find the latest processed file
        index = self.next_available_index() - 1  # Because we incremented before
        output_video = os.path.join("results", f"output_{index}.mp4")
        result_file = os.path.join("results", f"results_{index}.txt")

        self.cap = detector.load_detection_video(output_video)
        self.detection_results = detector.load_detection_results(result_file)

        if not self.cap or not self.cap.isOpened():
            self.video_label.setText("Failed to load processed video.")
            return

        self.frame_count = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.fps = int(self.cap.get(cv2.CAP_PROP_FPS)) or 30
        self.slider.setMaximum(self.frame_count - 1)
        self.slider.setEnabled(True)
        self.current_frame_pos = 0

        # Show controls and start video
        self.slider.setVisible(True)
        self.play_pause_button.setVisible(True)
        self.timer.start(1000 // self.fps)
        self.play_pause_button.setText("Pause")
        # remove progress bar
        self.progress.setValue(0)
        self.progress.setVisible(False)

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
   
    def detect_on_image(self):
        self.static_image_mode = True
        self.__init_video__()
        self.detail_label.setText("Click on a card to see detail")
        self.detail_label.setPixmap(QPixmap())
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Image", "", "Images (*.png *.jpg *.jpeg *.bmp)")
        if not file_path:
            return

        img = cv2.imread(file_path)
        if img is None:
            self.video_label.setText("Failed to load image.")
            return

        frame_with_boxes, boxes = detector.detect_on_frame(img, return_boxes=True)

        # Store detections for click interaction
        self.static_image_mode = True
        self.static_detections = [(int(name), x, y, w, h) for (name, x, y, w, h) in boxes]

        # Convert to QImage and show
        rgb = cv2.cvtColor(frame_with_boxes, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        q_img = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
        self.video_label.setPixmap(QPixmap.fromImage(q_img))

    def on_frame_clicked(self, point):
        if self.static_image_mode:
            # Click on static image with detections
            pixmap = self.video_label.pixmap()
            if not pixmap:
                return
            label_width = self.video_label.width()
            label_height = self.video_label.height()
            img_width = pixmap.width()
            img_height = pixmap.height()

            scale_x = img_width / label_width
            scale_y = img_height / label_height
            scaled_point = QPoint(int(point.x() * scale_x), int(point.y() * scale_y))

            for (idx, x, y, w, h) in self.static_detections:
                rect = QRect(x, y, w, h)
                if rect.contains(scaled_point):
                    self.load_card_by_index(idx)
                    return

        elif hasattr(self, 'detection_results') and self.cap:
            video_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            video_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

            label_width = self.video_label.width()
            label_height = self.video_label.height()

            scale_x = video_width / label_width
            scale_y = video_height / label_height

            scaled_point = QPoint(int(point.x() * scale_x), int(point.y() * scale_y))

            boxes = self.detection_results.get(self.current_frame_pos, [])
            for (name, x, y, w, h) in boxes:
                rect = QRect(x, y, w, h)
                if rect.contains(scaled_point):
                    try:
                        idx = int(name)
                        self.load_card_by_index(idx)
                    except ValueError:
                        print(f"Invalid index: {name}")
                    return

    def load_card_by_index(self, idx):
        card_path = f"./cards/sv1-{idx+1}/sv1-{idx+1}.png"
        if os.path.exists(card_path):
            pixmap = QPixmap(card_path).scaled(self.detail_label.size(), Qt.KeepAspectRatio)
            self.detail_label.setPixmap(pixmap)
        else:
            self.detail_label.setText(f"Card image not found for index {idx}")


class ClickableLabel(QLabel):
    clicked = pyqtSignal(QPoint)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(event.pos())
