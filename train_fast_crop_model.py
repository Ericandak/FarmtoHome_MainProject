import tensorflow as tf
import os
from pathlib import Path
from fast_crop_model import FastCropHealthModel

def main():
    # Set memory growth to avoid OOM errors
    physical_devices = tf.config.list_physical_devices('GPU')
    if physical_devices:
        for device in physical_devices:
            tf.config.experimental.set_memory_growth(device, True)
    
    # Set paths
    train_dir = r'D:\ajce notes\sem8\django\New_Plant_Diseases\train'
    valid_dir = r'D:\ajce notes\sem8\django\New_Plant_Diseases\valid'
    
    # Create and train model
    model = FastCropHealthModel()
    
    # Check directories
    print(f"Training directory: {train_dir}")
    if not os.path.exists(train_dir):
        print("Error: Training directory not found!")
        return
    
    # Print class counts
    train_classes = [d for d in os.listdir(train_dir) if os.path.isdir(os.path.join(train_dir, d))]
    print(f"Found {len(train_classes)} classes in training directory")
    
    # Train the model
    history, trained_model = model.train(
        train_dir=train_dir,
        valid_dir=valid_dir
    )
    
    print("\nTraining complete! Model saved at: models/fast_crop_model.keras")

if __name__ == "__main__":
    main()