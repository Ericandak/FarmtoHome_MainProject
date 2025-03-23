import tensorflow as tf
import cv2
import numpy as np
from pathlib import Path
from django.conf import settings

class CropMonitoringSystem:
    def __init__(self):
        # Load models with fallbacks

        try:
                self.crop_model = tf.keras.models.load_model('models/crop_health_model.h5')
                self.img_size = 160  # Changed from 160 to 128
                print("Loaded original crop model")
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
        
        self.best_model = tf.keras.models.load_model('models/best_crop_model.keras')
        
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

    def analyze_crop(self, image_path):
        """Analyze crop health"""
        try:
            # Load and preprocess image using TensorFlow instead of OpenCV
            img = tf.keras.preprocessing.image.load_img(
                image_path, 
                target_size=(160, 160)  # Use 160x160 as that's what we set in __init__
            )
            img_array = tf.keras.preprocessing.image.img_to_array(img)
            img_array = img_array / 255.0
            img_array = np.expand_dims(img_array, axis=0)
            
            # Make prediction
            prediction = self.crop_model.predict(img_array)
            
            # Process results using the disease analysis logic
            class_index = np.argmax(prediction[0])
            confidence = float(prediction[0][class_index])
            
            # Get disease name if available
            if hasattr(self, 'class_names') and class_index < len(self.class_names):
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
            
            # Calculate severity based on confidence
            severity = 'High' if confidence < 0.3 else 'Medium' if confidence < 0.7 else 'Low'
            
            return {
                'health_analysis': {
                    'crop_type': crop_type,
                    'disease': disease,
                    'confidence': confidence * 100,  # Convert to percentage
                    'severity': severity
                },
                'recommendations': [
                    f"Detected {disease} with {confidence*100:.1f}% confidence",
                    f"Disease severity: {severity}",
                    "Consider consulting with an agricultural expert for specific treatment options"
                ]
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
                'recommendations': ['Unable to analyze crop due to an error']
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

    def _get_recommendations(self, soil_type, crop_health_score):
        """Generate recommendations based on soil type and crop health"""
        recommendations = []
        
        # Add soil-specific recommendations
        if soil_type in self.soil_characteristics:
            soil_info = self.soil_characteristics[soil_type]
            recommendations.append(f"Soil Type: {soil_type} - Best suited for: {', '.join(soil_info['suitable_crops'])}")
            
            if soil_info['fertility'] == 'Low':
                recommendations.append("Consider adding organic fertilizers to improve soil fertility")
            if soil_info['water_retention'] == 'Poor':
                recommendations.append("Implement mulching to improve water retention")
        
        # Add crop health recommendations
        if crop_health_score < 0.7:
            recommendations.append("Crop health needs attention - Consider increasing monitoring frequency")
        
        return recommendations

def analyze_farm_condition(crop_image_path, soil_image_path):
    monitoring_system = CropMonitoringSystem()
    
    # Get comprehensive analysis
    analysis = monitoring_system.comprehensive_analysis(
        crop_image_path=crop_image_path,
        soil_image_path=soil_image_path
    )
    
    # Get recommendations
    recommendations = monitoring_system._get_recommendations(analysis['soil_analysis']['soil_type'], analysis['crop_analysis']['health_score'])
    
    return {
        'analysis': analysis,
        'recommendations': recommendations
    }
