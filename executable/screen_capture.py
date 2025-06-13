# screen_capture.py

import mss
import numpy as np
import cv2
import pygetwindow as gw
import time

CAPTURE_REGION = None
OVERLAY_WINDOW_TITLE = "PTCG Overlay"  # must match self.setWindowTitle

def set_capture_region(region_dict):
    global CAPTURE_REGION
    CAPTURE_REGION = region_dict

def get_video_frame(hide_window=False):
    global CAPTURE_REGION
    if CAPTURE_REGION is None:
        return None

    try:
        moved = False
        original_position = None

        if hide_window:
            overlay_win = next((w for w in gw.getWindowsWithTitle(OVERLAY_WINDOW_TITLE) if w.isVisible), None)
            if overlay_win:
                ox1, oy1 = overlay_win.left, overlay_win.top
                ow, oh = overlay_win.width, overlay_win.height

                rx1, ry1 = CAPTURE_REGION["left"], CAPTURE_REGION["top"]
                rx2, ry2 = rx1 + CAPTURE_REGION["width"], ry1 + CAPTURE_REGION["height"]
                if (ox1 < rx2 and ox1 + ow > rx1 and oy1 < ry2 and oy1 + oh > ry1):
                    original_position = (overlay_win.left, overlay_win.top)
                    overlay_win.moveTo(-2000, -2000)
                    moved = True
                    time.sleep(0.05)

        with mss.mss() as sct:
            screenshot = sct.grab(CAPTURE_REGION)
            frame = np.array(screenshot)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2RGB)

        if moved and original_position:
            overlay_win.moveTo(*original_position)

        return frame

    except Exception as e:
        print(f"Capture error: {e}")
        return None

