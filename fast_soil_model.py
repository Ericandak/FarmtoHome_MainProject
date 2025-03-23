import tensorflow as tf
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D, Dropout, BatchNormalization
import os
import matplotlib.pyplot as plt


import tensorflow as tf
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D, Dropout
from tensorflow.keras.preprocessing.image import ImageDataGenerator

class FastSoilModel:
    def __init__(self):
        self.img_size = 128
        self.soil_classes = None  # Will be set automatically from the dataset
        
    def create_model(self, num_classes):
        """Create a lightweight model using MobileNetV2"""
        base_model = MobileNetV2(
            weights='imagenet',
            include_top=False,
            input_shape=(self.img_size, self.img_size, 3)
        )
        
        # Freeze base model
        base_model.trainable = False
        
        x = base_model.output
        x = GlobalAveragePooling2D()(x)
        x = Dense(256, activation='relu', kernel_regularizer=tf.keras.regularizers.l2(0.001))(x)
        x = BatchNormalization()(x)
        x = Dropout(0.4)(x)
        predictions = Dense(num_classes, activation='softmax')(x)
        
        return tf.keras.Model(inputs=base_model.input, outputs=predictions)
    
    def train(self, train_dir, valid_dir, test_dir=None):
        """Fast training process"""
        # Ensure models directory exists
        os.makedirs('models', exist_ok=True)
        
        # Data augmentation for training
        train_datagen = ImageDataGenerator(
            rescale=1./255,
            rotation_range=20,
            width_shift_range=0.2,
            height_shift_range=0.2,
            shear_range=0.2,
            zoom_range=0.2,
            horizontal_flip=True,
            fill_mode='nearest'
        )
        
        # Only rescaling for validation/test
        valid_datagen = ImageDataGenerator(rescale=1./255)
        
        # Create generators
        train_generator = train_datagen.flow_from_directory(
            train_dir,
            target_size=(self.img_size, self.img_size),
            batch_size=64,
            class_mode='categorical'
        )
        
        validation_generator = valid_datagen.flow_from_directory(
            valid_dir,
            target_size=(self.img_size, self.img_size),
            batch_size=64,
            class_mode='categorical'
        )
        
        # Get number of classes from the dataset
        num_classes = len(train_generator.class_indices)
        self.soil_classes = list(train_generator.class_indices.keys())
        print(f"\nDetected {num_classes} soil classes: {self.soil_classes}")
        
        # Create and compile model with correct number of classes
        model = self.create_model(num_classes)
        model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
            loss='categorical_crossentropy',
            metrics=['accuracy']
        )
        
        # Training callbacks
        callbacks = [
            tf.keras.callbacks.EarlyStopping(
                monitor='val_accuracy',
                patience=5,
                restore_best_weights=True,
                verbose=1
            ),
            tf.keras.callbacks.ReduceLROnPlateau(
                monitor='val_loss',
                factor=0.5,
                patience=3,
                min_lr=0.00001,
                verbose=1
            ),
            tf.keras.callbacks.ModelCheckpoint(
                'models/fast_model_best.keras',
                monitor='val_accuracy',
                save_best_only=True,
                verbose=1
            )
        ]
        
        # Train the model
        print("\nStarting training...")
        history = model.fit(
            train_generator,
            epochs=15,
            validation_data=validation_generator,
            callbacks=callbacks,
            verbose=1
        )
        
        # Save final model
        model.save('models/fast_soil_model.keras')
        
        # Plot training history
        self.plot_training_history(history)
        
        return history, model
    
    def plot_training_history(self, history):
        plt.figure(figsize=(12, 4))
        
        # Plot accuracy
        plt.subplot(1, 2, 1)
        plt.plot(history.history['accuracy'], label='Training Accuracy')
        plt.plot(history.history['val_accuracy'], label='Validation Accuracy')
        plt.title('Model Accuracy')
        plt.xlabel('Epoch')
        plt.ylabel('Accuracy')
        plt.legend()
        
        # Plot loss
        plt.subplot(1, 2, 2)
        plt.plot(history.history['loss'], label='Training Loss')
        plt.plot(history.history['val_loss'], label='Validation Loss')
        plt.title('Model Loss')
        plt.xlabel('Epoch')
        plt.ylabel('Loss')
        plt.legend()
        
        plt.tight_layout()
        plt.savefig('fast_model_training_history.png')
        plt.close()