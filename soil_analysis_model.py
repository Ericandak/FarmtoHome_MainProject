import tensorflow as tf
from tensorflow.keras.applications import EfficientNetB0
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D, Dropout, BatchNormalization
from tensorflow.keras.preprocessing.image import ImageDataGenerator
import matplotlib.pyplot as plt
import os
import shutil
import random
import numpy as np
import cv2
import time

class SoilAnalysisModel:
    def __init__(self):
        self.img_size = 128
        self.batch_size = 32
        self.samples_per_class = 500

        # Updated soil classes based on your classifications
        self.soil_classes = [
            'Alluvial',
            'Black',
            'Cinder',
            'Clay',
            'Laterite',
            'Loamy',
            'Peat',
            'Red',
            'Sandy',
            'Yellow'
        ]
        
        # Updated characteristics for each soil type
        self.soil_characteristics = {
            'Alluvial': {
                'fertility': 'High',
                'water_retention': 'Good',
                'suitable_crops': ['Rice', 'Wheat', 'Sugarcane', 'Vegetables'],
                'recommendations': [
                    "Maintain organic matter content",
                    "Regular crop rotation recommended",
                    "Moderate irrigation needed"
                ]
            },
            'Black': {
                'fertility': 'Very High',
                'water_retention': 'Excellent',
                'suitable_crops': ['Cotton', 'Soybean', 'Wheat', 'Chickpeas'],
                'recommendations': [
                    "Ensure proper drainage",
                    "Deep ploughing recommended",
                    "Add organic matter to improve structure"
                ]
            },
            'Cinder': {
                'fertility': 'Low',
                'water_retention': 'Poor',
                'suitable_crops': ['Drought-resistant crops', 'Cacti', 'Succulents'],
                'recommendations': [
                    "Add organic matter to improve fertility",
                    "Use mulching to retain moisture",
                    "Consider container gardening"
                ]
            },
            'Clay': {
                'fertility': 'Medium to High',
                'water_retention': 'High',
                'suitable_crops': ['Rice', 'Wheat', 'Maize', 'Sugarcane'],
                'recommendations': [
                    "Improve drainage",
                    "Add organic matter",
                    "Avoid overwatering"
                ]
            },
            'Laterite': {
                'fertility': 'Low to Medium',
                'water_retention': 'Poor',
                'suitable_crops': ['Cashew', 'Rubber', 'Tea', 'Coffee'],
                'recommendations': [
                    "Regular liming needed",
                    "Add organic matter",
                    "Implement soil conservation measures"
                ]
            },
            'Loamy': {
                'fertility': 'High',
                'water_retention': 'Good',
                'suitable_crops': ['Most crops', 'Vegetables', 'Fruits'],
                'recommendations': [
                    "Maintain organic content",
                    "Regular crop rotation",
                    "Balanced fertilization"
                ]
            },
            'Peat': {
                'fertility': 'High in nitrogen',
                'water_retention': 'Very High',
                'suitable_crops': ['Vegetables', 'Berries', 'Root crops'],
                'recommendations': [
                    "Manage water table",
                    "Add mineral supplements",
                    "Monitor pH levels"
                ]
            },
            'Red': {
                'fertility': 'Medium',
                'water_retention': 'Medium',
                'suitable_crops': ['Groundnut', 'Millets', 'Pulses'],
                'recommendations': [
                    "Regular liming to control acidity",
                    "Add organic matter",
                    "Proper irrigation scheduling"
                ]
            },
            'Sandy': {
                'fertility': 'Low',
                'water_retention': 'Poor',
                'suitable_crops': ['Carrots', 'Potatoes', 'Watermelon'],
                'recommendations': [
                    "Add organic matter regularly",
                    "Frequent but light irrigation",
                    "Use mulching techniques"
                ]
            },
            'Yellow': {
                'fertility': 'Low to Medium',
                'water_retention': 'Medium',
                'suitable_crops': ['Pineapple', 'Cassava', 'Sweet Potatoes'],
                'recommendations': [
                    "Add organic amendments",
                    "pH correction if needed",
                    "Proper nutrient management"
                ]
            }
        }

    def create_model(self):
        """Improved model architecture for better accuracy"""
        # Use a larger EfficientNet model
        base_model = tf.keras.applications.EfficientNetB3(
            weights='imagenet',
            include_top=False,
            input_shape=(self.img_size, self.img_size, 3)
        )
        
        # Unfreeze more layers for better feature learning
        base_model.trainable = True
        
        # Create a more robust architecture
        x = base_model.output
        x = GlobalAveragePooling2D()(x)
        
        # Add L2 regularization to all dense layers
        x = Dense(2048, activation='relu', kernel_regularizer=tf.keras.regularizers.l2(0.001))(x)
        x = BatchNormalization()(x)
        x = Dropout(0.6)(x)  # Increased dropout
        
        x = Dense(1024, activation='relu', kernel_regularizer=tf.keras.regularizers.l2(0.001))(x)
        x = BatchNormalization()(x)
        x = Dropout(0.5)(x)  # Increased dropout
        
        x = Dense(512, activation='relu', kernel_regularizer=tf.keras.regularizers.l2(0.001))(x)
        x = BatchNormalization()(x)
        x = Dropout(0.4)(x)  # Increased dropout
        
        predictions = Dense(len(self.soil_classes), activation='softmax')(x)
        
        return tf.keras.Model(inputs=base_model.input, outputs=predictions)

    def create_faster_model(self):
        """Create a lightweight model for faster training"""
        # Use MobileNetV2 instead of EfficientNet
        base_model = tf.keras.applications.MobileNetV2(
            weights='imagenet',
            include_top=False,
            input_shape=(128, 128, 3)  # Reduced image size
        )
        
        # Freeze base model layers
        base_model.trainable = False
        
        x = base_model.output
        x = GlobalAveragePooling2D()(x)
        x = Dense(256, activation='relu', kernel_regularizer=tf.keras.regularizers.l2(0.001))(x)
        x = BatchNormalization()(x)
        x = Dropout(0.4)(x)
        predictions = Dense(len(self.soil_classes), activation='softmax')(x)
        
        return tf.keras.Model(inputs=base_model.input, outputs=predictions)

    def create_balanced_model(self):
        """Create a model less prone to overfitting"""
        base_model = tf.keras.applications.EfficientNetB0(  # B0 instead of B3
            weights='imagenet',
            include_top=False,
            input_shape=(self.img_size, self.img_size, 3)
        )
        
        # Freeze more layers
        for layer in base_model.layers[:-10]:
            layer.trainable = False
        
        x = base_model.output
        x = GlobalAveragePooling2D()(x)
        
        # Simpler architecture with regularization
        x = Dense(512, activation='relu', kernel_regularizer=tf.keras.regularizers.l2(0.001))(x)
        x = BatchNormalization()(x)
        x = Dropout(0.5)(x)
        
        x = Dense(256, activation='relu', kernel_regularizer=tf.keras.regularizers.l2(0.001))(x)
        x = BatchNormalization()(x)
        x = Dropout(0.4)(x)
        
        predictions = Dense(len(self.soil_classes), activation='softmax')(x)
        
        return tf.keras.Model(inputs=base_model.input, outputs=predictions)

    def train(self, train_dir, valid_dir, test_dir=None):
        """Faster training process"""
        # Update image size
        self.img_size = 128  # Reduced from 160
        
        # More aggressive data augmentation for better generalization
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
        
        valid_datagen = ImageDataGenerator(rescale=1./255)
        test_datagen = ImageDataGenerator(rescale=1./255)
        
        # Increase batch size for faster training
        train_generator = train_datagen.flow_from_directory(
            train_dir,
            target_size=(self.img_size, self.img_size),
            batch_size=64,  # Increased from 32
            class_mode='categorical'
        )
        
        validation_generator = valid_datagen.flow_from_directory(
            valid_dir,
            target_size=(self.img_size, self.img_size),
            batch_size=64,
            class_mode='categorical'
        )
        
        # Use the faster model
        model = self.create_faster_model()
        
        # Single training phase with higher learning rate
        model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
            loss='categorical_crossentropy',
            metrics=['accuracy']
        )
        
        callbacks = [
            tf.keras.callbacks.EarlyStopping(
                monitor='val_accuracy',
                patience=5,
                restore_best_weights=True
            ),
            tf.keras.callbacks.ModelCheckpoint(
                'models/best_model.keras',
                monitor='val_accuracy',
                save_best_only=True,
                verbose=1
            )
        ]
        
        history = model.fit(
            train_generator,
            epochs=15,  # Reduced number of epochs
            validation_data=validation_generator,
            callbacks=callbacks
        )
        
        # Save final model
        model.save('models/final_soil_model.keras')
        return history, model