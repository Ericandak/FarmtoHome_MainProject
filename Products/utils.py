import tensorflow as tf
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D, Dropout
from tensorflow.keras.models import Model
import numpy as np
from django.conf import settings
from PIL import Image
import os

# Update this path to your new training directory
train_dir = os.path.join(settings.BASE_DIR.parent, 'project docs', 'Training')

def get_class_labels(train_dir):
    class_labels = sorted(os.listdir(train_dir))
    return [label for label in class_labels if os.path.isdir(os.path.join(train_dir, label))]

class_labels = get_class_labels(train_dir)
print("Class labels:", class_labels)

# Update this path to your converted model weights
WEIGHTS_PATH = r'D:\ajce notes\sem8\django\FarmToHomeProject\models\fruits_disease.weights.h5'

def create_model(num_classes, img_height=224, img_width=224):
    base_model = MobileNetV2(input_shape=(img_height, img_width, 3),
                             include_top=False,
                             weights='imagenet')
    x = base_model.output
    x = GlobalAveragePooling2D()(x)
    x = Dense(128, activation='relu')(x)
    x = Dropout(0.5)(x)
    predictions = Dense(num_classes, activation='softmax')(x)
    model = Model(inputs=base_model.input, outputs=predictions)
    return model

def load_model():
    try:
        num_classes = len(class_labels)
        model = create_model(num_classes)
        model.load_weights(WEIGHTS_PATH)
        print("Model loaded successfully")
        return model
    except Exception as e:
        print(f"Error loading model: {str(e)}")
        raise

def preprocess_image(image_path, target_size=(224, 224)):
    img = Image.open(image_path).convert('RGB')
    img = img.resize(target_size)
    img_array = np.array(img) / 255.0
    return np.expand_dims(img_array, axis=0)

def predict_fruit_disease(image_path):
    model = load_model()
    preprocessed_image = preprocess_image(image_path)
    prediction = model.predict(preprocessed_image)
    
    # Print top 5 predictions
    top_5_indices = np.argsort(prediction[0])[-5:][::-1]
    print("Top 5 predictions:")
    for i in top_5_indices:
        print(f"{class_labels[i]}: {prediction[0][i]*100:.2f}%")
    
    class_index = np.argmax(prediction)
    
    predicted_class = class_labels[class_index]
    confidence = prediction[0][class_index]
    
    is_defected_fruit = is_defected(predicted_class)
    condition = get_condition(predicted_class)

    if confidence < 0.5:  # You can adjust this threshold   
        predicted_class = "Unknown"
        is_defected_fruit = False
        condition = "Unknown"
    
    return predicted_class, confidence, is_defected_fruit, condition

def is_defected(class_name):
    defect_keywords = ['rotten', 'hit', 'diseased', 'damaged']
    return any(keyword in class_name.lower() for keyword in defect_keywords)

def get_condition(class_name):
    if 'rotten' in class_name.lower():
        return 'Rotten'
    elif 'hit' in class_name.lower() or 'damaged' in class_name.lower():
        return 'Damaged'
    elif 'diseased' in class_name.lower():
        return 'Diseased'
    else:
        return 'Healthy'

# Print TensorFlow and Keras versions
print(f"TensorFlow version: {tf.__version__}")
print(f"Keras version: {tf.keras.__version__}")

# Verify weights file exists
print(f"Weights file exists: {os.path.exists(WEIGHTS_PATH)}")