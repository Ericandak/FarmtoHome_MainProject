import tensorflow as tf
from tensorflow.keras.applications import EfficientNetB0
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D, Dropout
from tensorflow.keras.preprocessing.image import ImageDataGenerator
import matplotlib.pyplot as plt
import os
import shutil
import random
import numpy as np
import cv2

class CropHealthModel:
    def __init__(self):
        self.img_size = 160  # Reduced image size
        self.samples_per_class = 500  # Limit samples per class
        self.class_names = [
            'Pepper__bell___Bacterial_spot',
            'Pepper__bell___healthy',
            'Potato___Early_blight',
            'Potato___Late_blight',
            'Potato___healthy',
            'Tomato_Bacterial_spot',
            'Tomato_Early_blight',
            'Tomato_Late_blight',
            'Tomato_Leaf_Mold',
            'Tomato_healthy',
            'Rice___Leafsmut',
            'Rice___Bacterialblight',
            'Rice___Brownspot'
        ]
        
        self.health_indicators = {
            'leaf_color': {
                'healthy_range': (35, 85),
                'weight': 0.4
            },
            'leaf_texture': {
                'uniformity_threshold': 0.7,
                'weight': 0.3
            },
            'growth_pattern': {
                'symmetry_threshold': 0.8,
                'weight': 0.3
            }
        }

    def prepare_reduced_dataset(self, source_dir, dest_dir):
        """Create a reduced dataset with balanced classes"""
        print("Preparing reduced dataset...")
        
        # Create destination directory
        if os.path.exists(dest_dir):
            shutil.rmtree(dest_dir)
        os.makedirs(dest_dir)
        
        # Copy reduced number of images for each class
        for class_name in self.class_names:
            src_class_dir = os.path.join(source_dir, class_name)
            dst_class_dir = os.path.join(dest_dir, class_name)
            
            if not os.path.exists(src_class_dir):
                print(f"Warning: {class_name} not found in source directory")
                continue
                
            os.makedirs(dst_class_dir)
            
            # Get list of all images in the class
            all_images = os.listdir(src_class_dir)
            selected_images = random.sample(all_images, 
                                         min(self.samples_per_class, len(all_images)))
            
            # Copy selected images
            for img in selected_images:
                shutil.copy2(
                    os.path.join(src_class_dir, img),
                    os.path.join(dst_class_dir, img)
                )
            
            print(f"Copied {len(selected_images)} images for {class_name}")

    def create_model(self, num_classes):
        base_model = EfficientNetB0(
            weights='imagenet',
            include_top=False,
            input_shape=(self.img_size, self.img_size, 3)
        )
        
        # Freeze most layers
        for layer in base_model.layers[:-20]:
            layer.trainable = False
        
        x = base_model.output
        x = GlobalAveragePooling2D()(x)
        x = Dense(256, activation='relu')(x)
        x = Dropout(0.5)(x)
        predictions = Dense(num_classes, activation='softmax')(x)
        
        return tf.keras.Model(inputs=base_model.input, outputs=predictions)

    def train_model(self, train_dir, validation_dir):
        print("Initializing fast training...")
        
        train_datagen = ImageDataGenerator(
            rescale=1./255,
            rotation_range=20,
            width_shift_range=0.2,
            height_shift_range=0.2,
            zoom_range=0.2,
            horizontal_flip=True,
            fill_mode='nearest',
            validation_split=0.2
        )

        train_generator = train_datagen.flow_from_directory(
            train_dir,
            target_size=(self.img_size, self.img_size),
            batch_size=128,  # Larger batch size
            class_mode='categorical',
            subset='training'
        )

        validation_generator = train_datagen.flow_from_directory(
            train_dir,
            target_size=(self.img_size, self.img_size),
            batch_size=128,
            class_mode='categorical',
            subset='validation'
        )

        num_classes = len(train_generator.class_indices)
        print(f"Training with {num_classes} classes")

        model = self.create_model(num_classes)
        model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
            loss='categorical_crossentropy',
            metrics=['accuracy']
        )

        callbacks = [
            tf.keras.callbacks.EarlyStopping(
                monitor='val_accuracy',
                patience=3,
                restore_best_weights=True,
                min_delta=0.01
            ),
            tf.keras.callbacks.ReduceLROnPlateau(
                monitor='val_loss',
                factor=0.5,
                patience=2,
                min_lr=0.00001
            ),
            tf.keras.callbacks.ModelCheckpoint(
                'best_crop_model.keras',
                monitor='val_accuracy',
                save_best_only=True
            )
        ]

        history = model.fit(
            train_generator,
            epochs=15,
            validation_data=validation_generator,
            callbacks=callbacks
        )

        model.save('crop_health_model.h5')
        print("Model saved successfully!")
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
        plt.savefig('training_history.png')
        plt.close()

    def analyze_rice_disease(self, image, prediction):
        class_index = np.argmax(prediction)
        predicted_class = self.class_names[class_index]
        confidence = prediction[0][class_index]
        
        rice_recommendations = {
            'Rice___Leafsmut': [
                "Remove infected plants immediately",
                "Improve field drainage",
                "Apply fungicide if infection is severe",
                "Use disease-resistant varieties in next planting"
            ],
            'Rice___Bacterialblight': [
                "Avoid excess nitrogen fertilization",
                "Improve air circulation between plants",
                "Apply copper-based bactericides",
                "Maintain proper field drainage"
            ],
            'Rice___Brownspot': [
                "Check soil nutrients, especially silica",
                "Maintain proper water management",
                "Apply appropriate fungicides",
                "Consider crop rotation next season"
            ]
        }
        
        return {
            'disease': predicted_class,
            'confidence': float(confidence),
            'recommendations': rice_recommendations.get(predicted_class, []),
            'severity': self.calculate_severity(image, predicted_class)
        }

    def calculate_severity(self, image, disease_class):
        hsv_img = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
        
        if 'Brownspot' in disease_class:
            mask = cv2.inRange(hsv_img, 
                              np.array([20, 50, 50]), 
                              np.array([30, 255, 255]))
        elif 'Bacterialblight' in disease_class:
            mask = cv2.inRange(hsv_img, 
                              np.array([15, 30, 200]), 
                              np.array([35, 80, 255]))
        else:
            mask = cv2.inRange(hsv_img, 
                              np.array([0, 0, 0]), 
                              np.array([180, 255, 30]))
        
        affected_ratio = np.sum(mask) / mask.size
        
        if affected_ratio < 0.1:
            return 'Low'
        elif affected_ratio < 0.3:
            return 'Moderate'
        else:
            return 'Severe'

if __name__ == "__main__":
    # Enable mixed precision
    tf.keras.mixed_precision.set_global_policy('mixed_float16')
    
    # Set paths
    original_train_dir = r'D:\ajce notes\sem8\django\New_Plant_Diseases\train'
    reduced_train_dir = r'D:\ajce notes\sem8\django\New_Plant_Diseases\reduced_train'
    
    # Initialize model
    model = CropHealthModel()
    
    # Prepare reduced dataset
    model.prepare_reduced_dataset(original_train_dir, reduced_train_dir)
    
    # Train model
    history, trained_model = model.train_model(reduced_train_dir, None)