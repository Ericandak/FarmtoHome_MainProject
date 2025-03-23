import tensorflow as tf
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import ImageDataGenerator
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import classification_report, confusion_matrix
import os
import time

def evaluate_model(test_dir):
    """Evaluate crop model on test dataset"""
    start_time = time.time()
    
    # Load model
    model_path = 'models/fast_crop_model.keras'
    if not os.path.exists(model_path):
        print(f"Error: Model not found at {model_path}")
        return
    
    print(f"Loading model from {model_path}...")
    model = load_model(model_path)
    
    # Set up test data generator
    test_datagen = ImageDataGenerator(rescale=1./255)
    img_size = 128  # Same as training
    
    print(f"Processing test data from {test_dir}...")
    test_generator = test_datagen.flow_from_directory(
        test_dir,
        target_size=(img_size, img_size),
        batch_size=32,  # Larger batch for faster evaluation
        class_mode='categorical',
        shuffle=False
    )
    
    # Get class names and count
    class_names = list(test_generator.class_indices.keys())
    num_classes = len(class_names)
    print(f"Found {num_classes} classes in test dataset")
    
    # Evaluate model
    print("\nEvaluating model performance...")
    scores = model.evaluate(test_generator, verbose=1)
    print(f"Test Loss: {scores[0]:.4f}")
    print(f"Test Accuracy: {scores[1]:.4f}")
    
    # Get predictions
    print("\nGenerating predictions for detailed analysis...")
    predictions = model.predict(test_generator)
    y_pred = np.argmax(predictions, axis=1)
    y_true = test_generator.classes
    
    # Print classification report
    print("\nClassification Report:")
    report = classification_report(y_true, y_pred, target_names=class_names, output_dict=True)
    print(classification_report(y_true, y_pred, target_names=class_names))
    
    # Plot and save confusion matrix
    print("\nGenerating confusion matrix visualization...")
    plt.figure(figsize=(20, 15))
    cm = confusion_matrix(y_true, y_pred)
    
    # If we have too many classes, plot normalized confusion matrix
    if num_classes > 20:
        cm_normalized = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]
        sns.heatmap(cm_normalized, annot=False, cmap='Blues',
                    xticklabels=class_names, yticklabels=class_names)
        plt.title('Normalized Confusion Matrix (too many classes for detailed view)')
    else:
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                    xticklabels=class_names, yticklabels=class_names)
        plt.title('Confusion Matrix')
        
    plt.ylabel('True Label')
    plt.xlabel('Predicted Label')
    plt.xticks(rotation=90)
    plt.yticks(rotation=0)
    plt.tight_layout()
    plt.savefig('crop_confusion_matrix.png')
    plt.close()
    
    # Plot class accuracies as bar chart
    print("\nAnalyzing per-class performance...")
    class_accuracies = [report[name]['recall'] for name in class_names]
    
    # Sort by accuracy
    sorted_indices = np.argsort(class_accuracies)
    sorted_classes = [class_names[i] for i in sorted_indices]
    sorted_accuracies = [class_accuracies[i] for i in sorted_indices]
    
    # Plot top 10 and bottom 10 classes
    plt.figure(figsize=(15, 10))
    
    # Bottom 10
    plt.subplot(2, 1, 1)
    bottom_n = min(10, len(sorted_classes))
    plt.barh(range(bottom_n), sorted_accuracies[:bottom_n], color='salmon')
    plt.yticks(range(bottom_n), sorted_classes[:bottom_n])
    plt.xlim(0, 1.0)
    plt.title(f'Bottom {bottom_n} Classes by Accuracy')
    plt.xlabel('Accuracy')
    
    # Top 10
    plt.subplot(2, 1, 2)
    top_n = min(10, len(sorted_classes))
    plt.barh(range(top_n), sorted_accuracies[-top_n:][::-1], color='skyblue')
    plt.yticks(range(top_n), sorted_classes[-top_n:][::-1])
    plt.xlim(0, 1.0)
    plt.title(f'Top {top_n} Classes by Accuracy')
    plt.xlabel('Accuracy')
    
    plt.tight_layout()
    plt.savefig('crop_class_accuracy.png')
    plt.close()
    
    # Visualize sample predictions
    print("\nGenerating sample prediction visualizations...")
    test_generator.reset()
    batch_x, batch_y = next(test_generator)
    
    predictions = model.predict(batch_x)
    
    plt.figure(figsize=(20, 20))
    for i in range(min(25, len(batch_x))):
        plt.subplot(5, 5, i+1)
        plt.imshow(batch_x[i])
        
        true_idx = np.argmax(batch_y[i])
        pred_idx = np.argmax(predictions[i])
        
        true_class = class_names[true_idx]
        pred_class = class_names[pred_idx]
        confidence = predictions[i][pred_idx] * 100
        
        title = f"True: {true_class}\nPred: {pred_class}\nConf: {confidence:.1f}%"
        color = 'green' if true_idx == pred_idx else 'red'
        
        plt.title(title, color=color, fontsize=8)
        plt.axis('off')
    
    plt.tight_layout()
    plt.savefig('crop_sample_predictions.png')
    plt.close()
    
    # Calculate and print class distribution
    print("\nClass distribution in test set:")
    counts = [np.sum(y_true == i) for i in range(len(class_names))]
    for i, (name, count) in enumerate(zip(class_names, counts)):
        accuracy = np.sum((y_true == i) & (y_pred == i)) / max(count, 1)
        print(f"{name}: {count} samples, Accuracy: {accuracy:.4f}")
    
    # Print execution time
    elapsed_time = time.time() - start_time
    print(f"\nEvaluation completed in {elapsed_time:.2f} seconds")
    print(f"Results saved to crop_confusion_matrix.png, crop_class_accuracy.png, and crop_sample_predictions.png")

if __name__ == "__main__":
    test_dir = r'D:\ajce notes\sem8\django\New_Plant_Diseases\valid'
    evaluate_model(test_dir)