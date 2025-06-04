# detector_mock.py

import random

CARD_NAMES = ["charizard", "pikachu", "mewtwo", "bulbasaur", "gengar"]

def detect_cards_mock(frame_width, frame_height):
    """
    Returns mocked bounding boxes with fake card names.
    Each box = (x, y, width, height, card_name)
    """
    boxes = []
    for _ in range(random.randint(1, 3)):
        x = random.randint(50, frame_width - 150)
        y = random.randint(50, frame_height - 200)
        w = 120
        h = 180
        name = random.choice(CARD_NAMES)
        boxes.append((x, y, w, h, name))
    return boxes
