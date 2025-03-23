import tensorflow as tf
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import ImageDataGenerator
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import classification_report, confusion_matrix

def plot_class_accuracies(y_true, y_pred, class_names):
    """Plot per-class accuracies"""
    # Calculate per-class accuracy
    class_accuracies = {}
    for i, class_name in enumerate(class_names):
        mask = (y_true == i)
        if np.sum(mask) > 0:  # Ensure we have samples for this class
            class_acc = np.mean(y_pred[mask] == y_true[mask])
            class_accuracies[class_name] = class_acc
    
    # Sort accuracies
    sorted_items = sorted(class_accuracies.items(), key=lambda x: x[1])
    classes, accuracies = zip(*sorted_items)
    
    # Create figure with two subplots
    plt.figure(figsize=(15, 10))
    
    # Bottom classes
    plt.subplot(2, 1, 1)
    bottom_classes = classes[:5]  # Show bottom 5 classes
    bottom_accuracies = accuracies[:5]
    
    plt.barh(range(len(bottom_classes)), bottom_accuracies, color='salmon')
    plt.yticks(range(len(bottom_classes)), bottom_classes)
    plt.xlabel('Accuracy')
    plt.title('Bottom 5 Classes by Accuracy')
    
    # Top classes
    plt.subplot(2, 1, 2)
    top_classes = classes[-5:]  # Show top 5 classes
    top_accuracies = accuracies[-5:]
    
    plt.barh(range(len(top_classes)), top_accuracies, color='skyblue')
    plt.yticks(range(len(top_classes)), top_classes)
    plt.xlabel('Accuracy')
    plt.title('Top 5 Classes by Accuracy')
    
    plt.tight_layout()
    plt.savefig('soil_class_accuracy.png')
    plt.close()

def evaluate_model(test_dir):
    """Evaluate the soil model and generate visualizations"""
    try:
        # Load the saved model
        model = load_model('models/fast_soil_model.keras')
        
        # Create test generator
        test_datagen = ImageDataGenerator(rescale=1./255)
        test_generator = test_datagen.flow_from_directory(
            test_dir,
            target_size=(128, 128),
            batch_size=1,
            class_mode='categorical',
            shuffle=False
        )
        
        # Get predictions
        predictions = model.predict(test_generator)
        y_pred = np.argmax(predictions, axis=1)
        y_true = test_generator.classes
        
        # Get class names
        class_names = list(test_generator.class_indices.keys())
        
        # Print classification report
        print("\nClassification Report:")
        print(classification_report(y_true, y_pred, target_names=class_names))
        
        # Plot confusion matrix
        plt.figure(figsize=(12, 8))
        cm = confusion_matrix(y_true, y_pred)
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                    xticklabels=class_names,
                    yticklabels=class_names)
        plt.title('Soil Analysis Confusion Matrix')
        plt.ylabel('True Label')
        plt.xlabel('Predicted Label')
        plt.xticks(rotation=45)
        plt.yticks(rotation=45)
        plt.tight_layout()
        plt.savefig('soil_confusion_matrix.png')
        plt.close()
        
        # Generate class accuracy plot
        plot_class_accuracies(y_true, y_pred, class_names)
        
        print("\nEvaluation completed successfully!")
        print("Generated visualizations:")
        print("1. soil_confusion_matrix.png")
        print("2. soil_class_accuracy.png")
        
    except Exception as e:
        print(f"Error during evaluation: {str(e)}")

if __name__ == "__main__":
    test_dir = r'D:\ajce notes\sem8\django\New_dataset\Test'
    evaluate_model(test_dir)