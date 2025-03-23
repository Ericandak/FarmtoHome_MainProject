import tensorflow as tf
from pathlib import Path
from fast_soil_model import FastSoilModel
import os

def main():
    # Enable mixed precision for faster training
    tf.keras.mixed_precision.set_global_policy('mixed_float16')
    
    # Set up paths
    base_path = Path(r'D:\ajce notes\sem8\django\New_dataset')
    train_dir = base_path / 'Train'
    valid_dir = base_path / 'Valid'  # Using Test set as validation
    
    # Print dataset information
    print("\nChecking dataset structure...")
    for directory in [train_dir, valid_dir]:
        print(f"\n{directory.name} directory contents:")
        for soil_type in os.listdir(directory):
            num_images = len(os.listdir(directory / soil_type))
            print(f"{soil_type}: {num_images} images")
    
    # Initialize and train model
    print("\nInitializing fast soil analysis model...")
    soil_model = FastSoilModel()
    
    print("\nStarting model training...")
    history, model = soil_model.train(
        train_dir=str(train_dir),
        valid_dir=str(valid_dir)
    )
    
    print("\nTraining complete!")
    print("Model saved as 'models/fast_soil_model.keras'")
    print("Training history plot saved as 'fast_model_training_history.png'")

if __name__ == "__main__":
    main()