import tensorflow as tf
import os

# Ensure models directory exists
os.makedirs('models', exist_ok=True)

# Path to the best model from the current training
best_model_path = 'models/phase2_best_model.keras'
final_model_path = 'models/final_soil_model.keras'

# Load the best model
model = tf.keras.models.load_model(best_model_path)

# Save it as the final model
model.save(final_model_path)

print(f"Best model copied to {final_model_path}")