import tensorflow as tf
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import ImageDataGenerator
import matplotlib.pyplot as plt
import numpy as np

# Load the saved model
model = load_model('models/fruits_disease.weights.h5')

# Set parameters
img_height, img_width = 100, 100
batch_size = 32
test_dir = r'D:\ajce notes\sem8\django\archive\fruits-360_dataset_100x100\fruits-360\Test'

# Create data generator for testing
test_datagen = ImageDataGenerator(rescale=1./255)
test_generator = test_datagen.flow_from_directory(
    test_dir,
    target_size=(img_height, img_width),
    batch_size=batch_size,
    class_mode='categorical',
    shuffle=False
)

# Get class mapping
class_indices = test_generator.class_indices
class_names = list(class_indices.keys())

# Evaluate model
print("Evaluating model...")
test_loss, test_acc = model.evaluate(test_generator)
print(f'Test accuracy: {test_acc:.4f}')

# Make predictions on a batch of test images
print("\nMaking predictions...")
batch_x, batch_y = next(test_generator)
predictions = model.predict(batch_x)

# Display some sample predictions
plt.figure(figsize=(15, 10))
for i in range(min(9, len(batch_x))):
    plt.subplot(3, 3, i + 1)
    plt.imshow(batch_x[i])
    true_class = class_names[np.argmax(batch_y[i])]
    pred_class = class_names[np.argmax(predictions[i])]
    color = 'green' if true_class == pred_class else 'red'
    plt.title(f'True: {true_class}\nPred: {pred_class}', color=color)
    plt.axis('off')
plt.tight_layout()
plt.show()

# Print model summary
print("\nModel Architecture:")
model.summary()