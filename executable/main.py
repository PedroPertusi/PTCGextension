# main.py

import sys
from PyQt5.QtWidgets import QApplication
from ui_main import MainWindow
from select_region import select_screen_region
from screen_capture import set_capture_region

if __name__ == "__main__":
    print("Please select the region where the video is playing...")
    region = select_screen_region()
    set_capture_region(region)

    app = QApplication(sys.argv)
    window = MainWindow(region)
    window.show()
    sys.exit(app.exec_())
