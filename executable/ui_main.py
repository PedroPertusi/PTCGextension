from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QPainter, QColor, QImage
from screen_capture import get_video_frame, set_capture_region
from detector_mock import detect_cards_mock
from overlay_widget import ZoomDialog

class MainWindow(QMainWindow):
    def __init__(self, capture_region):
        super().__init__()
        self.setWindowTitle("PTCG Overlay")
        self.capture_region = capture_region
        set_capture_region(capture_region)

        self.setGeometry(
            capture_region["left"],
            capture_region["top"],
            capture_region["width"],
            capture_region["height"]
        )

        self.setWindowFlags(Qt.WindowStaysOnTopHint)

        self.frame = None
        self.boxes = []
        self.frame_count = 0

        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh_data)
        self.timer.start(1000 // 10)  # ~10 FPS

    def refresh_data(self):
        refresh_boxes = self.frame_count % 50 == 0

        # Only hide the window if we're refreshing detections
        was_visible = self.isVisible()
        if refresh_boxes and was_visible:
            self.setVisible(False)

        self.frame = get_video_frame(hide_window=refresh_boxes)

        if refresh_boxes and was_visible:
            self.setVisible(True)

        if self.frame is not None and refresh_boxes:
            h, w, _ = self.frame.shape
            self.boxes = detect_cards_mock(w, h)

        self.frame_count += 1
        self.update()

    def paintEvent(self, event):
        if self.frame is None:
            return

        h, w, _ = self.frame.shape
        image = QImage(self.frame.data, w, h, 3 * w, QImage.Format_RGB888)
        painter = QPainter(self)
        painter.drawImage(0, 0, image)

        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QColor(0, 255, 0, 180))

        for box in self.boxes:
            x, y, bw, bh, _ = box
            painter.drawRect(x, y, bw, bh)

        painter.end()

    def mousePressEvent(self, event):
        x_click = event.pos().x()
        y_click = event.pos().y()

        for box in self.boxes:
            x, y, w, h, name = box
            if x <= x_click <= x + w and y <= y_click <= y + h:
                dialog = ZoomDialog()
                dialog.exec_()
                break
