import tensorflow as tf
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D, Dropout
from tensorflow.keras.models import Model
import numpy as np

# Path to your current .keras model
MODEL_PATH = r'D:\ajce notes\sem8\django\FarmToHomeProject\models\fruits_disease_model2.keras'

# Path where you want to save the converted model weights
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

try:
    # Load the original model
    original_model = tf.keras.models.load_model(MODEL_PATH, compile=False)
    
    # Get the number of classes
    num_classes = original_model.output_shape[-1]
    
    # Create a new model with the same architecture
    new_model = create_model(num_classes)
    
    # Copy weights from the original model to the new model
    new_model.set_weights(original_model.get_weights())
    
    # Save only the weights of the new model
    new_model.save_weights(WEIGHTS_PATH)
    
    print(f"Model weights successfully extracted and saved to {WEIGHTS_PATH}")
    
    # Test loading the saved weights
    test_model = create_model(num_classes)
    test_model.load_weights(WEIGHTS_PATH)
    print("Converted model weights loaded successfully")
    
except Exception as e:
    print(f"Error during conversion: {str(e)}")

print(f"TensorFlow version: {tf.__version__}")
print(f"Keras version: {tf.keras.__version__}")