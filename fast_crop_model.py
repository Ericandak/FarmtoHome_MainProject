import tensorflow as tf
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D, Dropout, BatchNormalization
import matplotlib.pyplot as plt
import os
import shutil
import random
import numpy as np
import cv2

class FastCropHealthModel:
    def __init__(self):
        self.img_size = 128  # Reduced image size for faster processing
        self.samples_per_class = 700  # Limit samples per class
        self.class_names = None  # Will be set automatically from dataset
        self.model = None
        
    def create_model(self, num_classes):
        """Create a lightweight model using MobileNetV2"""
        base_model = MobileNetV2(
            weights='imagenet',
            include_top=False,
            input_shape=(self.img_size, self.img_size, 3)
        )
        
        # Freeze base model layers
        base_model.trainable = False
        
        x = base_model.output
        x = GlobalAveragePooling2D()(x)
        x = Dense(256, activation='relu', kernel_regularizer=tf.keras.regularizers.l2(0.001))(x)
        x = BatchNormalization()(x)
        x = Dropout(0.4)(x)
        predictions = Dense(num_classes, activation='softmax')(x)
        
        return tf.keras.Model(inputs=base_model.input, outputs=predictions)
    
    def prepare_reduced_dataset(self, source_dir, dest_dir):
        """Create a reduced dataset with balanced classes"""
        print("Preparing reduced dataset...")
        
        # Create destination directory
        if os.path.exists(dest_dir):
            shutil.rmtree(dest_dir)
        os.makedirs(dest_dir)
        
        # Get all class directories from source
        class_dirs = [d for d in os.listdir(source_dir) if os.path.isdir(os.path.join(source_dir, d))]
        
        # Copy reduced number of images for each class
        for class_name in class_dirs:
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
        self.class_names = list(train_generator.class_indices.keys())
        print(f"\nDetected {num_classes} crop classes: {self.class_names}")
        
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
                'models/fast_crop_model_best.keras',
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
        model.save('models/fast_crop_model.keras')
        self.model = model
        
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
        plt.savefig('fast_crop_training_history.png')
        plt.close()
    
    def analyze_crop(self, image_path):
        """Analyze a crop image"""
        if self.model is None:
            raise ValueError("Model not trained or loaded. Call train() first or load a model.")
        
        # Load and preprocess image
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Could not read image at {image_path}")
        
        # Convert BGR to RGB
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # Resize image
        img = cv2.resize(img, (self.img_size, self.img_size))
        
        # Normalize pixel values
        img = img.astype(np.float32) / 255.0
        
        # Make prediction
        prediction = self.model.predict(np.expand_dims(img, axis=0))
        
        # Convert back to uint8 for OpenCV operations
        
        img_cv = (img * 255).astype(np.uint8)
        
        # Get results
        result = self._analyze_disease(img_cv, prediction)
        
        return result
    
    def _analyze_disease(self, image, prediction):
        """Analyze disease based on prediction"""
        class_index = np.argmax(prediction)
        confidence = float(prediction[0][class_index])
        
        if self.class_names and class_index < len(self.class_names):
            disease = self.class_names[class_index]
        else:
            disease = f"Unknown (Class {class_index})"
        
        # Get crop type from disease name
        if 'Rice' in disease:
            crop_type = 'Rice'
        elif 'Tomato' in disease:
            crop_type = 'Tomato'
        elif 'Potato' in disease:
            crop_type = 'Potato'
        elif 'Pepper' in disease:
            crop_type = 'Pepper'
        else:
            crop_type = 'Unknown'
        
        # Generate recommendations based on disease
        recommendations = self._get_recommendations(disease)
        
        # Calculate severity
        severity = self._calculate_severity(image, disease)
        
        return {
            'crop_type': crop_type,
            'disease': disease,
            'confidence': confidence * 100,  # Convert to percentage
            'severity': severity,
            'recommendations': recommendations
        }
    
    def _get_recommendations(self, disease):
        """Get recommendations based on disease"""
        recommendations = []
        
        disease_recommendations = {
            'Bacterial_spot': [
                "Remove infected plants",
                "Apply copper-based bactericides",
                "Ensure proper spacing for air circulation",
                "Avoid overhead irrigation"
            ],
            'Early_blight': [
                "Remove infected leaves",
                "Apply fungicide treatments",
                "Ensure proper plant spacing",
                "Water at the base to keep foliage dry"
            ],
            'Late_blight': [
                "Remove infected plants immediately",
                "Apply preventative fungicides",
                "Improve drainage",
                "Rotate crops in future seasons"
            ],
            'Leaf_Mold': [
                "Improve air circulation",
                "Reduce humidity",
                "Apply appropriate fungicides",
                "Remove affected leaves"
            ],
            'Leafsmut': [
                "Remove infected plants",
                "Improve field drainage",
                "Apply fungicide if infection is severe",
                "Use disease-resistant varieties in next planting"
            ],
            'Bacterialblight': [
                "Avoid excess nitrogen fertilization",
                "Improve air circulation between plants",
                "Apply copper-based bactericides",
                "Maintain proper field drainage"
            ],
            'Brownspot': [
                "Check soil nutrients, especially silica",
                "Maintain proper water management",
                "Apply appropriate fungicides",
                "Consider crop rotation next season"
            ],
            'healthy': [
                "Continue with regular maintenance",
                "Monitor for early signs of disease",
                "Maintain proper irrigation",
                "Follow fertilization schedule"
            ]
        }
        
        # Find matching recommendations
        for disease_key, recs in disease_recommendations.items():
            if disease_key in disease:
                recommendations.extend(recs)
                return recommendations
        
        # Default recommendations if no match found
        return [
            "Maintain proper irrigation",
            "Monitor for disease symptoms",
            "Ensure adequate sunlight",
            "Check soil nutrition levels"
        ]
    
    def _calculate_severity(self, image, disease):
        """Calculate disease severity"""
        # Convert to HSV for better color analysis
        hsv_img = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
        
        # Different masks for different diseases
        if 'Brownspot' in disease:
            mask = cv2.inRange(hsv_img, 
                              np.array([20, 50, 50]), 
                              np.array([30, 255, 255]))
        elif 'Bacterialblight' in disease or 'Bacterial_spot' in disease:
            mask = cv2.inRange(hsv_img, 
                              np.array([15, 30, 200]), 
                              np.array([35, 80, 255]))
        elif 'Early_blight' in disease or 'Late_blight' in disease:
            mask = cv2.inRange(hsv_img, 
                              np.array([0, 40, 40]), 
                              np.array([20, 255, 255]))
        elif 'healthy' in disease:
            # For healthy plants, calculate green percentage
            mask = cv2.inRange(hsv_img, 
                              np.array([35, 50, 50]), 
                              np.array([85, 255, 255]))
            # Invert the ratio to get 'non-green' for consistency with disease severity
            affected_ratio = 1.0 - (np.sum(mask) / mask.size / 255.0)
            
            if affected_ratio < 0.1:
                return 'Low'
            elif affected_ratio < 0.3:
                return 'Moderate'
            else:
                return 'Severe'
        else:
            mask = cv2.inRange(hsv_img, 
                              np.array([0, 0, 0]), 
                              np.array([180, 255, 30]))
        
        affected_ratio = np.sum(mask) / mask.size / 255.0
        
        if affected_ratio < 0.1:
            return 'Low'
        elif affected_ratio < 0.3:
            return 'Moderate'
        else:
            return 'Severe'