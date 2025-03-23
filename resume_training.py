import tensorflow as tf
import time
import numpy as np
from pathlib import Path

def resume_training():
    # Enable mixed precision for faster training
    tf.keras.mixed_precision.set_global_policy('mixed_float16')
    
    # Paths
    base_path = Path(r'D:\ajce notes\sem8\django\New_dataset')
    train_dir = base_path / 'Train'
    valid_dir = base_path / 'Valid'
    
    # Load the latest saved model
    model = tf.keras.models.load_model('models/phase2_best_model.keras')
    
    # IMPORTANT: Use the same image size as the original model (160x160)
    img_size = 160  # Must match the model's expected input size
    batch_size = 16  # Keep the same batch size for consistency
    
    # Set up data generators with performance optimizations
    train_datagen = tf.keras.preprocessing.image.ImageDataGenerator(
        rescale=1./255,
        rotation_range=30,
        width_shift_range=0.2,
        height_shift_range=0.2,
        shear_range=0.2,
        zoom_range=0.2,
        horizontal_flip=True,
        vertical_flip=True,
        fill_mode='nearest',
        brightness_range=[0.8, 1.2]
    )

    valid_datagen = tf.keras.preprocessing.image.ImageDataGenerator(rescale=1./255)

    train_generator = train_datagen.flow_from_directory(
        train_dir,
        target_size=(img_size, img_size),  # Must match model's input size
        batch_size=batch_size,
        class_mode='categorical',
        shuffle=True
    )

    validation_generator = valid_datagen.flow_from_directory(
        valid_dir,
        target_size=(img_size, img_size),  # Must match model's input size
        batch_size=batch_size,
        class_mode='categorical',
        shuffle=False
    )
    
    # Add timing callback to monitor step time
    class TimeHistory(tf.keras.callbacks.Callback):
        def on_train_begin(self, logs={}):
            self.times = []
            self.epoch_times = []
            
        def on_epoch_begin(self, epoch, logs={}):
            self.epoch_start_time = time.time()
            
        def on_batch_end(self, batch, logs={}):
            self.times.append(time.time())
            
        def on_epoch_end(self, epoch, logs={}):
            epoch_time = time.time() - self.epoch_start_time
            self.epoch_times.append(epoch_time)
            print(f"\nEpoch {epoch+1} took {epoch_time:.2f} seconds")
            if len(self.times) > 1:
                avg_step_time = (self.times[-1] - self.times[0]) / len(self.times)
                print(f"Average step time: {avg_step_time:.2f} seconds")
    
    time_callback = TimeHistory()
    
    # Configure TensorFlow for better performance
    physical_devices = tf.config.list_physical_devices('GPU')
    if physical_devices:
        try:
            tf.config.experimental.set_memory_growth(physical_devices[0], True)
            print("GPU memory growth enabled")
        except:
            print("Could not enable memory growth")
    
    # Callbacks
    callbacks = [
        time_callback,
        tf.keras.callbacks.EarlyStopping(
            monitor='val_accuracy',
            patience=10,
            restore_best_weights=True,
            min_delta=0.001
        ),
        tf.keras.callbacks.ReduceLROnPlateau(
            monitor='val_loss',
            factor=0.5,
            patience=5,
            min_lr=1e-6,
            verbose=1
        ),
        tf.keras.callbacks.ModelCheckpoint(
            'models/phase2_latest_model.keras',
            save_best_only=False,
            verbose=1
        ),
        tf.keras.callbacks.ModelCheckpoint(
            'models/phase2_best_model.keras',
            monitor='val_accuracy',
            save_best_only=True,
            verbose=1
        )
    ]
    
    # Resume training
    print("Resuming training...")
    history = model.fit(
        train_generator,
        epochs=30,
        initial_epoch=2,  # Start from epoch 2 (after epochs 0 and 1)
        validation_data=validation_generator,
        callbacks=callbacks
    )
    
    # Save final model
    model.save('models/final_soil_model.keras')
    print("Training complete!")

if __name__ == "__main__":
    resume_training()