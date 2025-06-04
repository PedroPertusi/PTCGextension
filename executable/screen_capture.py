# screen_capture.py

import mss
import numpy as np
import cv2

# Define the region where the browser video is playing (adjust as needed)
MONITOR_REGION = {
    "top": 100,
    "left": 100,
    "width": 1280,
    "height": 720
}

def get_video_frame():
    with mss.mss() as sct:
        try:
            screenshot = sct.grab(MONITOR_REGION)
            frame = np.array(screenshot)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2RGB)
            return frame
        except Exception:
            return None
