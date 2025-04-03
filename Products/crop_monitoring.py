import tensorflow as tf
import cv2
import numpy as np
from pathlib import Path
from django.conf import settings

class CropMonitoringSystem:
    def __init__(self):
        try:
            self.crop_model = tf.keras.models.load_model('models/fast_crop_model.keras')
            self.img_size = 128  # Changed to 128x128 to match model's expected input
            print("Loaded fast crop model")
        except:
            self.crop_model = None
            print("WARNING: No crop model found")
        
        try:
            self.soil_model = tf.keras.models.load_model('models/fast_soil_model.keras')
            self.soil_img_size = 128
            print("Loaded soil model")
        except:
            self.soil_model = None
            print("No soil model found")

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

        self.soil_characteristics = {
            'Alluvial': {
                'fertility': 'High',
                'water_retention': 'Good',
                'suitable_crops': ['Rice', 'Wheat', 'Sugarcane', 'Vegetables'],
                'ph_range': '6.5-7.5'
            },
            'Black': {
                'fertility': 'Very High',
                'water_retention': 'Excellent',
                'suitable_crops': ['Cotton', 'Soybean', 'Wheat', 'Chickpeas'],
                'ph_range': '7.0-8.5'
            },
            'Cinder': {
                'fertility': 'Low',
                'water_retention': 'Poor',
                'suitable_crops': ['Drought-resistant crops', 'Cacti', 'Succulents'],
                'ph_range': '6.0-7.0'
            },
            'Clay': {
                'fertility': 'Medium to High',
                'water_retention': 'High',
                'suitable_crops': ['Rice', 'Wheat', 'Maize', 'Sugarcane'],
                'ph_range': '6.0-7.0'
            },
            'Laterite': {
                'fertility': 'Low to Medium',
                'water_retention': 'Poor',
                'suitable_crops': ['Cashew', 'Rubber', 'Tea', 'Coffee'],
                'ph_range': '5.5-6.5'
            },
            'Loamy': {
                'fertility': 'High',
                'water_retention': 'Good',
                'suitable_crops': ['Vegetables', 'Fruits', 'Grains', 'Pulses'],
                'ph_range': '6.0-7.0'
            },
            'Peat': {
                'fertility': 'High in Nitrogen',
                'water_retention': 'Very High',
                'suitable_crops': ['Vegetables', 'Berries', 'Root Crops'],
                'ph_range': '4.5-5.5'
            },
            'Red': {
                'fertility': 'Medium',
                'water_retention': 'Medium',
                'suitable_crops': ['Groundnut', 'Potato', 'Rice'],
                'ph_range': '6.0-6.5'
            },
            'Sandy': {
                'fertility': 'Low',
                'water_retention': 'Poor',
                'suitable_crops': ['Potato', 'Carrot', 'Radish'],
                'ph_range': '5.5-7.0'
            },
            'Yellow': {
                'fertility': 'Low to Medium',
                'water_retention': 'Medium',
                'suitable_crops': ['Rice', 'Vegetables', 'Citrus Fruits'],
                'ph_range': '5.5-6.5'
            }
        }

        # Define crop types and their diseases
        self.crop_diseases = {
            'Tomato': [
                'Tomato_Bacterial_spot',
                'Tomato_Early_blight',
                'Tomato_Late_blight',
                'Tomato_Leaf_Mold',
                'Tomato_Septoria_leaf_spot',
                'Tomato_Spider_mites',
                'Tomato_Target_Spot',
                'Tomato_Yellow_Leaf_Curl_Virus',
                'Tomato_mosaic_virus',
                'Tomato_healthy'
            ],
            'Potato': [
                'Potato_Early_blight',
                'Potato_Late_blight',
                'Potato_healthy'
            ],
            'Pepper': [
                'Pepper_Bacterial_spot',
                'Pepper_healthy'
            ],
            'Rice': [
                'Rice_Bacterial_leaf_blight',
                'Rice_Brown_spot',
                'Rice_Leaf_smut',
                'Rice_healthy'
            ]
        }

        # Disease recommendations dictionary
        self.disease_recommendations = {
            'Bacterial_spot': [
                "Remove infected plants immediately",
                "Apply copper-based bactericides",
                "Ensure proper plant spacing for air circulation",
                "Avoid overhead irrigation to prevent spread"
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
            'healthy': [
                "Continue regular maintenance",
                "Monitor for early signs of disease",
                "Maintain proper irrigation",
                "Follow fertilization schedule"
            ]
        }

    def analyze_crop(self, image_path):
        """Analyze crop health"""
        try:
            # Load and preprocess image with correct size (128x128)
            img = tf.keras.preprocessing.image.load_img(
                image_path, 
                target_size=(128, 128)  # Changed to 128x128
            )
            img_array = tf.keras.preprocessing.image.img_to_array(img)
            img_array = img_array / 255.0
            img_array = np.expand_dims(img_array, axis=0)
            
            # Get prediction
            prediction = self.crop_model.predict(img_array)
            class_index = np.argmax(prediction[0])
            confidence = float(prediction[0][class_index])
            
            # Define disease classes
            disease_classes = [
                'Tomato_Bacterial_spot',
                'Tomato_Early_blight',
                'Tomato_Late_blight',
                'Tomato_Leaf_Mold',
                'Tomato_Septoria_leaf_spot',
                'Tomato_Spider_mites',
                'Tomato_Target_Spot',
                'Tomato_Yellow_Leaf_Curl_Virus',
                'Tomato_mosaic_virus',
                'Tomato_healthy'
            ]
            
            # Get disease name
            disease = disease_classes[class_index] if class_index < len(disease_classes) else "Unknown"
            
            # Extract crop type and clean disease name
            crop_type = disease.split('_')[0]
            clean_disease = '_'.join(disease.split('_')[1:])
            
            # Determine severity
            if confidence > 0.8:
                severity = 'Low'
            elif confidence > 0.6:
                severity = 'Moderate'
            else:
                severity = 'High'
            
            # Get recommendations
            recommendations = self._get_recommendations(clean_disease)
            
            return {
                'health_analysis': {
                    'crop_type': crop_type,
                    'disease': clean_disease,
                    'confidence': confidence * 100,
                    'severity': severity
                },
                'recommendations': recommendations
            }
            
        except Exception as e:
            print(f"Error in crop analysis: {str(e)}")
            return {
                'health_analysis': {
                    'crop_type': 'Unknown',
                    'disease': 'Error in analysis',
                    'confidence': 0,
                    'severity': 'Unknown'
                },
                'recommendations': [
                    'Unable to analyze crop. Please ensure:',
                    '- The image is clear and well-lit',
                    '- The leaf is centered in the image',
                    '- The image shows typical disease symptoms'
                ]
            }

    def analyze_soil(self, image_path):
        """Analyze soil type and its characteristics"""
        try:
            # Load and preprocess image
            img = tf.keras.preprocessing.image.load_img(
                image_path, 
                target_size=(128, 128)  # Make sure this matches the model's input size
            )
            img_array = tf.keras.preprocessing.image.img_to_array(img)
            img_array = img_array / 255.0
            img_array = np.expand_dims(img_array, axis=0)
            
            # Define soil types in the same order as model training
            soil_types = [
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
            
            # Get soil prediction
            prediction = self.soil_model.predict(img_array)
            predicted_index = np.argmax(prediction[0])
            
            # Safety check to prevent index out of range
            if predicted_index >= len(soil_types):
                raise ValueError(f"Model predicted class index {predicted_index} which is out of range")
            
            soil_type = soil_types[predicted_index]
            confidence = float(prediction[0][predicted_index])
            
            # Get soil characteristics
            characteristics = self.soil_characteristics.get(soil_type, {})
            
            return {
                'soil_type': soil_type,
                'confidence': confidence * 100,  # Convert to percentage
                'characteristics': characteristics
            }
            
        except Exception as e:
            print(f"Error in soil analysis: {str(e)}")
            # Return a default response in case of error
            return {
                'soil_type': 'Unknown',
                'confidence': 0,
                'characteristics': {
                    'fertility': 'Unknown',
                    'water_retention': 'Unknown',
                    'suitable_crops': [],
                    'ph_range': 'Unknown'
                }
            }

    def _get_recommendations(self, disease):
        """Get recommendations based on disease"""
        # Find matching recommendations
        for disease_key, recs in self.disease_recommendations.items():
            if disease_key.lower() in disease.lower():
                return recs
        
        # Default recommendations if no match found
        return [
            "Consult with an agricultural expert",
            "Monitor the affected area closely",
            "Consider soil testing",
            "Review irrigation practices"
        ]

def analyze_farm_condition(crop_image_path, soil_image_path):
    monitoring_system = CropMonitoringSystem()
    
    # Get comprehensive analysis
    analysis = monitoring_system.comprehensive_analysis(
        crop_image_path=crop_image_path,
        soil_image_path=soil_image_path
    )
    
    # Get recommendations
    recommendations = monitoring_system._get_recommendations(analysis['crop_analysis']['disease'])
    
    return {
        'analysis': analysis,
        'recommendations': recommendations
    }
