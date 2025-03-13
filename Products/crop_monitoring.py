import tensorflow as tf
import cv2
import numpy as np
from pathlib import Path
from django.conf import settings

class CropMonitoringSystem:
    def __init__(self):
        self.crop_model = tf.keras.models.load_model('models/crop_health_model.h5')
        self.best_model = tf.keras.models.load_model('models/best_crop_model.keras')
        self.img_size = 160
        
        self.growth_stages = {
            'Rice': ['Seedling', 'Tillering', 'Stem Extension', 'Heading', 'Ripening'],
            'Tomato': ['Seedling', 'Vegetative', 'Flowering', 'Fruiting', 'Ripening'],
            'Potato': ['Sprouting', 'Vegetative', 'Tuber Initiation', 'Tuber Bulking', 'Maturation'],
            'Pepper': ['Seedling', 'Vegetative', 'Flowering', 'Fruiting', 'Harvesting']
        }
        
        self.health_indicators = {
            'leaf_color': {
                'healthy_range': (35, 85),
                'weight': 0.3
            },
            'growth_rate': {
                'optimal_range': (0.5, 1.0),
                'weight': 0.3
            },
            'plant_density': {
                'optimal_range': (0.6, 0.9),
                'weight': 0.2
            },
            'stress_indicators': {
                'threshold': 0.3,
                'weight': 0.2
            }
        }

    def analyze_crop(self, image_path):
        """Comprehensive crop analysis"""
        # Read and preprocess image correctly
        image = cv2.imread(str(image_path))
        if image is None:
            raise ValueError("Could not read image")
            
        # Convert BGR to RGB
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Resize image
        image = cv2.resize(image, (self.img_size, self.img_size))
        
        # Convert to float32 and normalize
        image = image.astype(np.float32) / 255.0
        
        # Make predictions
        health_pred = self.crop_model.predict(np.expand_dims(image, axis=0))
        growth_pred = self.best_model.predict(np.expand_dims(image, axis=0))
        
        # Convert back to uint8 for OpenCV operations
        image_cv = (image * 255).astype(np.uint8)
        
        # Analyze results
        health_result = self._analyze_health(image_cv, health_pred)
        growth_result = self._analyze_growth_stage(image_cv, growth_pred)
        
        return {
            'health_analysis': health_result,
            'growth_stage': growth_result,
            'recommendations': self._generate_recommendations(health_result, growth_result)
        }

    def _analyze_health(self, image, prediction):
        class_index = np.argmax(prediction)
        confidence = float(prediction[0][class_index])
        
        # Convert to HSV using uint8 image
        hsv_img = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
        
        # Calculate health score
        health_score = self._calculate_health_score(hsv_img)
        
        return {
            'condition': self._get_health_condition(health_score),
            'confidence': confidence * 100,
            'health_score': health_score
        }

    def _calculate_health_score(self, hsv_image):
        # Simple health score based on green channel in HSV
        green_mask = cv2.inRange(hsv_image, 
                                np.array([35, 50, 50]), 
                                np.array([85, 255, 255]))
        return np.sum(green_mask) / (hsv_image.shape[0] * hsv_image.shape[1] * 255)

    def _get_health_condition(self, health_score):
        if health_score > 0.7:
            return "Healthy"
        elif health_score > 0.4:
            return "Moderate"
        else:
            return "Poor"

    def _analyze_growth_stage(self, image, prediction):
        # Simplified growth stage analysis
        return {
            'current_stage': 'Vegetative',  # Placeholder
            'progress': 0.6,  # Placeholder
            'estimated_days_to_next': 15  # Placeholder
        }

    def _generate_recommendations(self, health_result, growth_result):
        recommendations = []
        
        # Health-based recommendations
        if health_result['health_score'] < 0.7:
            recommendations.extend([
                "Check for nutrient deficiencies",
                "Monitor watering schedule",
                "Inspect for pest infestations"
            ])
        
        # Growth stage recommendations
        recommendations.extend([
            "Maintain proper irrigation",
            "Monitor for disease symptoms",
            "Ensure adequate sunlight"
        ])
        
        return recommendations
