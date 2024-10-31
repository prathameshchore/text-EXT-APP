from skimage.metrics import structural_similarity as ssim
import cv2
import numpy as np
from flask import Flask, request, jsonify
import os

app = Flask(__name__)

# Define the path to your images
IMAGE_DIR = 'images/'

# Function to match images
def find_matching_image(id_image_path):
    # Load the ID image
    id_image = cv2.imread(id_image_path, cv2.IMREAD_GRAYSCALE)
    
    # Initialize variables
    best_match = None
    best_score = 0
    
    # Iterate through all images in the directory
    for filename in os.listdir(IMAGE_DIR):
        if filename.endswith('.jpg') or filename.endswith('.png'):
            image_path = os.path.join(IMAGE_DIR, filename)
            # Load the current image
            current_image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
            
            # Compare the images
            score = compare_images(id_image, current_image)
            if score > best_score:
                best_score = score
                best_match = filename

    return best_match, best_score

# Function to compare images using Structural Similarity Index (SSI)
def compare_images(imageA, imageB):
    # Resize images to the same size
    imageA = cv2.resize(imageA, (300, 300))
    imageB = cv2.resize(imageB, (300, 300))
    
    # Compute the structural similarity index
    score, _ = ssim(imageA, imageB, full=True)
    return score

@app.route('/match', methods=['POST'])
def match_images():
    if 'id_image' not in request.files:
        return jsonify({'error': 'ID image not provided'}), 400
    
    id_image_file = request.files['id_image']
    id_image_path = os.path.join('uploads/', id_image_file.filename)
    id_image_file.save(id_image_path)

    matched_image, score = find_matching_image(id_image_path)

    if matched_image:
        return jsonify({
            'matched_image': matched_image,
            'score': score
        }), 200
    else:
        return jsonify({'error': 'No matching image found'}), 404

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('uploads', exist_ok=True)
    os.makedirs(IMAGE_DIR, exist_ok=True)
    
    app.run(host='0.0.0.0', port=5000)
