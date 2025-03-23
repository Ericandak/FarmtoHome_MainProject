import os
import shutil
import pandas as pd

# Paths
image_folder = r"D:\ajce notes\sem8\django\FarmToHomeProject\datasets\test"  # Update with the actual path to images
csv_file = r"D:\ajce notes\sem8\django\FarmToHomeProject\datasets\test\_classes.csv"  # Update with actual path
destination_folder = r"D:\ajce notes\sem8\django\FarmToHomeProject\datasets\New_dataset\test"  # Update with actual destination

# Read CSV
df = pd.read_csv(csv_file)

# Iterate through each row
for index, row in df.iterrows():
    image_name = row["filename"]
    
    # Find the class (column with value 1)
    class_name = None
    for col in df.columns[1:]:  # Skipping 'filename' column
        if row[col] == 1:
            class_name = col
            break  # Assuming one class per image

    if class_name:
        # Create class directory if not exists
        class_dir = os.path.join(destination_folder, class_name)
        os.makedirs(class_dir, exist_ok=True)
        
        # Move image to class directory
        source_path = os.path.join(image_folder, image_name)
        destination_path = os.path.join(class_dir, image_name)
        
        if os.path.exists(source_path):  # Check if file exists
            shutil.move(source_path, destination_path)
        else:
            print(f"File not found: {image_name}")

print("Image classification completed!")
