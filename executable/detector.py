import cv2
import os
import random
from ultralytics import YOLO

# Load the actual YOLO model
model = YOLO("my_model/my_model.pt")

# Label list based on your model training classes
CARD_NAMES = ["charizard", "pikachu", "mewtwo", "bulbasaur", "gengar"]

def load_yolo_detections(txt_path, frame_width, frame_height):
    boxes = []
    with open(txt_path, 'r') as file:
        for line in file:
            parts = line.strip().split()
            if len(parts) != 5:
                continue
            class_id, x_center, y_center, width, height = map(float, parts)
            class_id = int(class_id)
            x_center *= frame_width
            y_center *= frame_height
            width *= frame_width
            height *= frame_height
            x = int(x_center - width / 2)
            y = int(y_center - height / 2)
            w = int(width)
            h = int(height)
            card_name = CARD_NAMES[class_id] if 0 <= class_id < len(CARD_NAMES) else f"class_{class_id}"
            boxes.append((card_name, x, y, w, h))
    return boxes

def load_detection_video(video_path):
    return cv2.VideoCapture(video_path)

def load_detection_results(txt_path):
    detection_data = {}
    current_frame = None
    with open(txt_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith("Frame"):
                parts = line.split(":")
                current_frame = int(parts[0].split()[1])
                detection_data[current_frame] = []
            elif current_frame is not None and ',' in line:
                parts = line.split(",")
                if len(parts) == 5:
                    name, x, y, w, h = parts
                    detection_data[current_frame].append((name, int(x), int(y), int(w), int(h)))
    return detection_data

def detect_on_frame(frame, return_boxes=False):
    height, width = frame.shape[:2]
    results = model.predict(source=frame, imgsz=640, conf=0.25, verbose=False)

    boxes = []
    for r in results:
        for box in r.boxes:
            cls_id = int(box.cls.item())
            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
            w = x2 - x1
            h = y2 - y1
            name = CARD_NAMES[cls_id] if 0 <= cls_id < len(CARD_NAMES) else f"class_{cls_id}"
            boxes.append((name, x1, y1, w, h))

    image = draw_detections(frame.copy(), boxes)
    if return_boxes:
        return image, boxes
    return image

def draw_detections(image, boxes):
    for (name, x, y, w, h) in boxes:
        cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.putText(image, name, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    return image

def preprocess_video(video_path):
    results = []
    cap = cv2.VideoCapture(video_path)
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        frame_with_boxes, boxes = detect_on_frame(frame, return_boxes=True)
        results.append((frame_with_boxes, boxes))
    cap.release()
    return results

def get_random_card_image_path(cards_root="./cards"):
    print(f"Looking for card images in: {cards_root}")
    if not os.path.exists(cards_root):
        print(f"Cards root directory does not exist: {cards_root}")
        return None
    folders = [f for f in os.listdir(cards_root) if os.path.isdir(os.path.join(cards_root, f))]
    if not folders:
        print(f"No card folders found in: {cards_root}")
        return None
    selected_folder = random.choice(folders)
    folder_path = os.path.join(cards_root, selected_folder)
    images = [img for img in os.listdir(folder_path)
              if os.path.isfile(os.path.join(folder_path, img)) and img.lower().endswith((".png", ".jpg", ".jpeg"))]
    if not images:
        print(f"No card images found in: {folder_path}")
        return None
    selected_image = random.choice(images)
    print(f"Selected card image: {selected_image} from folder: {folder_path}")
    return os.path.join(folder_path, selected_image)