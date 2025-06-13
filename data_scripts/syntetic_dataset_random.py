import os
import cv2
import random
import matplotlib.pyplot as plt

def load_card_dataset(dataset_path='cards/'):
    image_files = []
    for root, _, files in os.walk(dataset_path):
        for file in files:
            if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                image_files.append(os.path.join(root, file))
    return image_files

def load_image(image_path):
    image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
    if image is None:
        print(f"Failed to read {image_path}")
    return image

def save_yolo_labels(labels, image_shape, output_path, class_id=0):
    h, w = image_shape[:2]
    with open(output_path, "w") as f:
        for x1, y1, x2, y2 in labels:
            x_center = ((x1 + x2) / 2) / w
            y_center = ((y1 + y2) / 2) / h
            box_width = (x2 - x1) / w
            box_height = (y2 - y1) / h
            f.write(f"{class_id} {x_center:.6f} {y_center:.6f} {box_width:.6f} {box_height:.6f}\n")

def draw_random_cards(blank_table, cards, area, num_cards=random.randint(0,15)):
    table = blank_table.copy()
    labels = []

    x_min, y_min, x_max, y_max = area
    for _ in range(num_cards):
        card_path = random.choice(cards)
        card = load_image(card_path)
        if card is None:
            continue

        # Add alpha if missing
        if card.shape[2] == 3:
            card = cv2.cvtColor(card, cv2.COLOR_BGR2BGRA)

        # Random size
        target_w, target_h = 100, 140
        card = cv2.resize(card, (target_w, target_h), interpolation=cv2.INTER_AREA)

        # Random rotation
        angle = random.choice(range(-30, 31, 5))
        center = (target_w // 2, target_h // 2)
        rot_mat = cv2.getRotationMatrix2D(center, angle, 1.0)

        cos = abs(rot_mat[0, 0])
        sin = abs(rot_mat[0, 1])
        bound_w = int((target_h * sin) + (target_w * cos))
        bound_h = int((target_h * cos) + (target_w * sin))

        rot_mat[0, 2] += (bound_w / 2) - center[0]
        rot_mat[1, 2] += (bound_h / 2) - center[1]

        rotated_card = cv2.warpAffine(card, rot_mat, (bound_w, bound_h),
                                      flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT,
                                      borderValue=(0, 0, 0, 0))

        # Random position inside the allowed area
        max_x = x_max - bound_w
        max_y = y_max - bound_h
        if max_x <= x_min or max_y <= y_min:
            continue
        offset_x = random.randint(x_min, max_x)
        offset_y = random.randint(y_min, max_y)

        roi = table[offset_y:offset_y+bound_h, offset_x:offset_x+bound_w]

        alpha = rotated_card[:, :, 3] / 255.0
        for c in range(3):
            roi[:, :, c] = (1 - alpha) * roi[:, :, c] + alpha * rotated_card[:, :, c]
        table[offset_y:offset_y+bound_h, offset_x:offset_x+bound_w] = roi

        # Save bounding box
        labels.append((offset_x, offset_y, offset_x + bound_w, offset_y + bound_h))

    return table, labels

def main():
    cards = load_card_dataset()
    blank_table = load_image('table.png')
    area = (100, 100, blank_table.shape[1] - 100, blank_table.shape[0] - 100)  # safe margin
    table_with_cards, labels = draw_random_cards(blank_table, cards, area)

    for x1, y1, x2, y2 in labels:
        cv2.rectangle(table_with_cards, (x1, y1), (x2, y2), (0, 255, 0), 2)

    save_yolo_labels(labels, blank_table.shape, 'used_labels.txt')

    image = cv2.cvtColor(table_with_cards, cv2.COLOR_BGR2RGB)
    plt.imshow(image)
    plt.axis('off')
    plt.show()

if __name__ == "__main__":
    main()
