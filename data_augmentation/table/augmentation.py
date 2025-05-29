import os
import cv2
import random
import matplotlib.pyplot as plt

def load_card_dataset(dataset_path = 'cards/'):
    """
    Load the card dataset from the specified path.
    Args:
        dataset_path (str): Path to the dataset folder.
    Returns:
        list: List of image file paths.
    """
    image_files = []
    for root, _, files in os.walk(dataset_path):
        for file in files:
            if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                image_files.append(os.path.join(root, file))
    return image_files

def load_table_dataset_labels(dataset_path = 'predict/'):
    """
    Load the table dataset from the specified path add return the labels.
    Args:
        dataset_path (str): Path to the dataset folder.
    Returns:
        list: List of Label Tuples.
    """
    labels = []
    for root, _, files in os.walk(dataset_path):
        print("Current root:", root)
        for file in files:
            if 'labels' in root:
                label_file = os.path.join(root, file.replace('.png', '.txt').replace('.jpg', '.txt').replace('.jpeg', '.txt'))
                if os.path.exists(label_file):
                    labels += load_labels(label_file)
    return labels

def load_image(image_path):
    """
    Load an image from the specified path.
    Args:
        image_path (str): Path to the image file.
    Returns:
        numpy.ndarray: Loaded image.
    """

    image = cv2.imread(image_path)
    if image is None:
        print(f"Failed to read {image_path}")
    return image

def load_labels(label_path):
    """
    Load a label file from the specified path.
    Args:
        label_path (str): Path to the label file.
    Returns:
        list: List of labels.
    """
    labels = []
    with open(label_path, 'r') as f:
        # format: 0 0.544132 0.301534 0.0664062 0.0865143
        # ignore first number (class id)
        # and convert string to float in format: (x, y, w, h)
        for line in f:
            parts = line.strip().split()
            if len(parts) == 5:
                x, y, w, h = map(float, parts[1:])
                labels.append((x, y, w, h))
    return labels

def reformat_labels(labels, blank_table):
    """
    Reformat labels to match the blank table size.
    Args:
        labels (list): List of labels.
        blank_table (numpy.ndarray): Blank table image.
    Returns:
        list: Reformatted labels.
    """
    reformatted_labels = []
    for label in labels:
        x, y, w, h = label
        # Convert to pixel coordinates
        x1 = int((x - w / 2) * blank_table.shape[1])
        y1 = int((y - h / 2) * blank_table.shape[0])
        x2 = int((x + w / 2) * blank_table.shape[1])
        y2 = int((y + h / 2) * blank_table.shape[0])
        reformatted_labels.append((x1, y1, x2, y2))
    return reformatted_labels

def save_reformatted_labels(reformatted_labels, image_shape, output_path, class_id=0):
    """
    Save reformatted labels back into YOLO format.
    Args:
        reformatted_labels (list): List of (x1, y1, x2, y2) pixel coords.
        image_shape (tuple): Shape of the image (height, width).
        output_path (str): File path to save the txt file.
        class_id (int): Class ID to write (default: 0).
    """
    h, w = image_shape[:2]
    with open(output_path, "w") as f:
        for x1, y1, x2, y2 in reformatted_labels:
            x_center = ((x1 + x2) / 2) / w
            y_center = ((y1 + y2) / 2) / h
            box_width = (x2 - x1) / w
            box_height = (y2 - y1) / h
            f.write(f"{class_id} {x_center:.6f} {y_center:.6f} {box_width:.6f} {box_height:.6f}\n")

def draw_cards_in_table(blank_table, labels, cards):
    """
    Draw cards in the table image based on the labels, all resized to the same average size.
    Returns:
        numpy.ndarray: Table image with drawn cards.
    """
    table = blank_table.copy()
    random_labels = random.sample(labels, random.randint(10, 15))

    # Calculate average box size
    total_w = sum(x2 - x1 for x1, y1, x2, y2 in random_labels)
    total_h = sum(y2 - y1 for x1, y1, x2, y2 in random_labels)
    avg_w = total_w / len(random_labels) 
    avg_h = total_h / len(random_labels) 

    for label in random_labels:
        x1, y1, x2, y2 = label
        card_image_path = random.choice(cards)
        card_image = load_image(card_image_path)

        card_h, card_w = card_image.shape[:2]

        # Scale image to average size (keeping aspect ratio)
        scale = min(avg_w / card_w, avg_h / card_h)
        new_w = int(card_w * scale)
        new_h = int(card_h * scale)

        # Resize image
        resized_card = cv2.resize(card_image, (new_w, new_h), interpolation=cv2.INTER_AREA)

        # Add alpha channel if not present
        if resized_card.shape[2] == 3:
            resized_card = cv2.cvtColor(resized_card, cv2.COLOR_BGR2BGRA)

        # Rotation
        angle = random.choice(range(-90, 91, 15))
        center = (new_w // 2, new_h // 2)
        rot_mat = cv2.getRotationMatrix2D(center, angle, 1.0)

        # Compute bounding box for rotated image
        cos = abs(rot_mat[0, 0])
        sin = abs(rot_mat[0, 1])
        bound_w = int((new_h * sin) + (new_w * cos))
        bound_h = int((new_h * cos) + (new_w * sin))

        # Adjust transformation matrix
        rot_mat[0, 2] += (bound_w / 2) - center[0]
        rot_mat[1, 2] += (bound_h / 2) - center[1]

        # Rotate with transparent background
        rotated_card = cv2.warpAffine(
            resized_card,
            rot_mat,
            (bound_w, bound_h),
            flags=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_CONSTANT,
            borderValue=(0, 0, 0, 0)  # Transparent
        )

        # Compute top-left corner to center rotated image in label box
        box_w = x2 - x1
        box_h = y2 - y1
        offset_x = x1 + (box_w - bound_w) // 2
        offset_y = y1 + (box_h - bound_h) // 2

        # Clip offsets to image bounds
        if offset_x < 0 or offset_y < 0 or offset_x + bound_w > table.shape[1] or offset_y + bound_h > table.shape[0]:
            continue  # Skip if rotated card does not fit

        # Define region of interest on table
        roi = table[offset_y:offset_y+bound_h, offset_x:offset_x+bound_w]

        # Create masks from alpha channel
        alpha = rotated_card[:, :, 3] / 255.0
        for c in range(3):  # For BGR channels
            roi[:, :, c] = (1 - alpha) * roi[:, :, c] + alpha * rotated_card[:, :, c]

        # Update table with blended ROI
        table[offset_y:offset_y+bound_h, offset_x:offset_x+bound_w] = roi

    return table, random_labels

def main():
    labels = load_table_dataset_labels()
    cards = load_card_dataset()
    blank_table_path = 'table.png'
    blank_table = load_image(blank_table_path)
    labels = reformat_labels(labels, blank_table)

    table_with_cards, used_labels = draw_cards_in_table(blank_table, labels, cards)

    for x1, y1, x2, y2 in used_labels:
        cv2.rectangle(table_with_cards, (x1, y1), (x2, y2), (0, 255, 0), 2)

    # Save only the used labels in YOLO format
    save_reformatted_labels(used_labels, blank_table.shape, "used_labels.txt")

    image = cv2.cvtColor(table_with_cards, cv2.COLOR_BGR2RGB)
    plt.imshow(image)
    plt.axis('off')
    plt.show()
    return image

if __name__ == "__main__": 
    main()