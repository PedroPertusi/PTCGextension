import cv2
import numpy as np
import os
import uuid
from tqdm import tqdm

def rotate_image(image, angle):
    (h, w) = image.shape[:2]
    center = (w / 2, h / 2)

    # Rotation matrix
    matrix = cv2.getRotationMatrix2D(center, angle, 1.0)

    # Compute new bounding dimensions
    cos = np.abs(matrix[0, 0])
    sin = np.abs(matrix[0, 1])
    new_w = int((h * sin) + (w * cos))
    new_h = int((h * cos) + (w * sin))

    # Adjust rotation matrix to consider translation
    matrix[0, 2] += (new_w / 2) - center[0]
    matrix[1, 2] += (new_h / 2) - center[1]

    # Perform actual rotation with new bounds
    return cv2.warpAffine(image, matrix, (new_w, new_h))

def translate_image(image, tx, ty):
    matrix = np.float32([[1, 0, tx], [0, 1, ty]])
    return cv2.warpAffine(image, matrix, (image.shape[1], image.shape[0]))

def scale_image(image, fx, fy):
    return cv2.resize(image, None, fx=fx, fy=fy, interpolation=cv2.INTER_LINEAR)

def adjust_brightness_contrast(image, alpha=1.0, beta=0):
    return cv2.convertScaleAbs(image, alpha=alpha, beta=beta)

def add_gaussian_noise(image):
    row, col, ch = image.shape
    gauss = np.random.normal(0, 15, (row, col, ch)).reshape(row, col, ch)
    noisy = np.clip(image + gauss, 0, 255).astype(np.uint8)
    return noisy

def augment_image(image):
    augmentations = []

    # Rotation
    # for angle in [angle for angle in range(-90, 90, 15)]:
    #     augmentations.append(rotate_image(image, angle))
    
    # Flip
    augmentations.append(cv2.flip(image, 1))  # horizontal
    augmentations.append(cv2.flip(image, 0))  # vertical

    # Scaling
    augmentations.append(scale_image(image, 1.2, 1.2))
    augmentations.append(scale_image(image, 0.8, 0.8))

    # Brightness/contrast
    augmentations.append(adjust_brightness_contrast(image, alpha=1.5, beta=20))
    augmentations.append(adjust_brightness_contrast(image, alpha=0.7, beta=-20))

    # Noise
    augmentations.append(add_gaussian_noise(image))

    # Blur
    augmentations.append(cv2.GaussianBlur(image, (5, 5), 0))

    return augmentations

def save_augmented_images(image_path, output_dir):
    image = cv2.imread(image_path)
    if image is None:
        print(f"Failed to read {image_path}")
        return

    augmented_images = augment_image(image)
    for aug_img in augmented_images:
        aug_name = f"aug_{uuid.uuid4().hex[:8]}.jpg"
        cv2.imwrite(os.path.join(output_dir, aug_name), aug_img)

def clear_augmented_images(foldername):
    for filename in os.listdir(foldername):
        if filename.startswith("aug_"):
            os.remove(os.path.join(foldername, filename))
            print(f"Removed {filename}")

def process_all_images(root_dir='cards'):
    for foldername, _, filenames in os.walk(root_dir):
        print('iterating through folder:', foldername)
        if not os.path.exists(foldername):
            print(f"Folder {foldername} does not exist.")
            continue
        image_files = [f for f in filenames if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        if image_files:
            print(f"\nProcessing folder: {foldername}")
            for filename in tqdm(image_files, desc=f"Augmenting", unit="img"):
                image_path = os.path.join(foldername, filename)
                save_augmented_images(image_path, foldername)

def clear_augmented_images_in_all_folders(root_dir='cards'):
    for foldername, _, filenames in os.walk(root_dir):
        print('iterating through folder:', foldername)
        if not os.path.exists(foldername):
            print(f"Folder {foldername} does not exist.")
            continue
        clear_augmented_images(foldername)
        print(f"Cleared augmented images in {foldername}")

print("Starting augmentation...")
clear_augmented_images_in_all_folders('cards')
process_all_images('cards')
print("\n✅ Augmentation complete.")