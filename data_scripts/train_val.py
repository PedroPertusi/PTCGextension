import os
import random
import shutil
from pathlib import Path

# Set paths
base_dir = Path("train_data_colored")  # Replace with actual path
images_dir = base_dir / "images"
labels_dir = base_dir / "labels"

output_images_train = images_dir / "train"
output_images_val = images_dir / "val"
output_labels_train = labels_dir / "train"
output_labels_val = labels_dir / "val"

# Create output folders
for folder in [output_images_train, output_images_val, output_labels_train, output_labels_val]:
    folder.mkdir(parents=True, exist_ok=True)

# Get all image files
image_files = list(images_dir.glob("*.jpg")) + list(images_dir.glob("*.png"))
random.shuffle(image_files)

# Train/Val split
split_ratio = 0.8
split_index = int(len(image_files) * split_ratio)
train_files = image_files[:split_index]
val_files = image_files[split_index:]

# Copy files
def move_files(files, target_img_dir, target_lbl_dir):
    for img_path in files:
        label_path = labels_dir / f"{img_path.stem}.txt"
        shutil.move(str(img_path), target_img_dir / img_path.name)
        if label_path.exists():
            shutil.move(str(label_path), target_lbl_dir / label_path.name)

move_files(train_files, output_images_train, output_labels_train)
move_files(val_files, output_images_val, output_labels_val)

print("Dataset successfully split into train and val.")