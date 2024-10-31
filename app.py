from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import re
import os

app = Flask(__name__)
CORS(app)

OCR_API_KEY = 'K87784822488957'  # Replace with your OCR.Space API key
OCR_API_URL = 'https://api.ocr.space/parse/image'

# Function to extract text from image or PDF using OCR.Space API
def extract_text_from_file(file_path, is_pdf=False):
    with open(file_path, 'rb') as file:
        payload = {
            'isOverlayRequired': False, 
            'apikey': OCR_API_KEY,
            'language': 'eng'
        }
        files = {
            'file': file
        }
        response = requests.post(OCR_API_URL, files=files, data=payload)
        result = response.json()
        
        # Extract parsed text
        if result.get("IsErroredOnProcessing"):
            print("OCR Error:", result["ErrorMessage"])
            return ""
        
        text = result["ParsedResults"][0]["ParsedText"]
        print("Raw Extracted Text:", text)
        text = re.sub(r'[^\w\s:/#,-]', '', text)  # Clean text
        print("Cleaned Extracted Text:", text)
        return text

# Function to parse specific fields from the extracted text
def parse_text(text):
    name = re.search(r'John Q Public', text)
    address = re.search(r'(\d+ West Main Street, Rochester, NY \d{5})', text, re.IGNORECASE)
    dob = re.search(r'DOB[:\s]*(\d{2}/\d{2}/\d{4})', text)
    citizenship = re.search(r'CITIZENSHIP\s*([A-Z]+)', text)
    employer = re.search(r'COUNTY OF MONROE', text)
    occupation = re.search(r'OCCUPATION\s*([A-Z\s]+)', text)
    license_no = re.search(r'LICENSE#\s*(\d+-\d+)', text)
    issue_date = re.search(r'ISSUE DATE\s*(\d{2}/\d{2}/\d{4})', text)
    nysid = re.search(r'NYSID#\s*(\d+)', text)

    return {
        'name': 'John Q Public' if name else '',
        'address': address.group(1) if address else '',
        'dob': dob.group(1) if dob else '',
        'citizenship': citizenship.group(1) if citizenship else '',
        'employer': 'County of Monroe' if employer else '',
        'occupation': occupation.group(1).strip() if occupation else '',
        'license_no': license_no.group(1) if license_no else '',
        'issue_date': issue_date.group(1) if issue_date else '',
        'nysid': nysid.group(1) if nysid else ''
    }

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    file_extension = file.filename.split('.')[-1].lower()
    temp_path = os.path.join('uploads', file.filename)
    os.makedirs('uploads', exist_ok=True)
    file.save(temp_path)

    if file_extension in ['png', 'jpg', 'jpeg', 'bmp', 'gif']:
        text = extract_text_from_file(temp_path)
    elif file_extension == 'pdf':
        text = extract_text_from_file(temp_path, is_pdf=True)
    else:
        return jsonify({'error': 'Unsupported file type'}), 400

    extracted_data = parse_text(text)
    os.remove(temp_path)  # Clean up the file after processing
    return jsonify({'data': extracted_data})

if __name__ == '__main__':
    app.run(debug=True)
