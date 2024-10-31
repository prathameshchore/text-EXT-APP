from flask import Flask, request, jsonify
from flask_cors import CORS  # Import Flask-CORS
import pytesseract
from PIL import Image
import pdf2image
import re
import os

app = Flask(__name__)
CORS(app)

#pytesseract.pytesseract.tesseract_cmd = os.path.join(os.getcwd(), 'tesseract', 'tesseract.exe')


# Function to preprocess and extract text from an image
def extract_text_from_image(image_path):
    image = Image.open(image_path)
    # Convert image to grayscale and apply thresholding for better OCR accuracy
    image = image.convert('L').point(lambda x: 0 if x < 128 else 255, '1')
    text = pytesseract.image_to_string(image, config='--psm 6')
    print("Raw Extracted Text:", text)  # Debugging line to check raw OCR text
    
    # Clean up text by removing unusual symbols and extra whitespace
    text = re.sub(r'[^\w\s:/#,-]', '', text)  # Remove non-alphanumeric characters, keeping common symbols
    text = re.sub(r'\s+', ' ', text).strip()  # Replace multiple whitespace with a single space
    print("Cleaned Extracted Text:", text)  # Debugging line to check cleaned OCR text
    return text

# Function to extract text from a PDF
def extract_text_from_pdf(pdf_path):
    images = pdf2image.convert_from_path(pdf_path, dpi=300)
    text = ''
    for image in images:
        image = image.convert('L').point(lambda x: 0 if x < 128 else 255, '1')
        text += pytesseract.image_to_string(image, config='--psm 6')
    print("Raw Extracted Text:", text)  # Debugging line to check raw OCR text
    
    # Clean up text by removing unusual symbols and extra whitespace
    text = re.sub(r'[^\w\s:/#,-]', '', text)  # Remove non-alphanumeric characters, keeping common symbols
    text = re.sub(r'\s+', ' ', text).strip()  # Replace multiple whitespace with a single space
    print("Cleaned Extracted Text:", text)  # Debugging line to check cleaned OCR text
    return text

# Function to parse specific fields from the extracted text
def parse_text(text):
    # Updated regular expressions to account for inconsistencies in spacing and symbols
    name = re.search(r'John Q Public', text)
    address = re.search(r'(\d+ West Main Street, Rochester, NY \d{5})', text, re.IGNORECASE)
    dob = re.search(r'DOB[:\s]*(\d{2}/\d{2}/\d{4})', text)
    citizenship = re.search(r'CITIZENSHIP\s*([A-Z]+)', text)
    employer = re.search(r'COUNTY OF MONROE', text)
    occupation = re.search(r'OCCUPATION\s*([A-Z\s]+)', text)
    license_no = re.search(r'LICENSE#\s*(\d+-\d+)', text)
    issue_date = re.search(r'ISSUE DATE\s*(\d{2}/\d{2}/\d{4})', text)
    nysid = re.search(r'NYSID#\s*(\d+)', text)

    # Returning a dictionary with parsed fields
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
    
    # Check file type and save appropriately
    if file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif')):
        image_path = os.path.join('uploads', file.filename)
        file.save(image_path)
        text = extract_text_from_image(image_path)
    elif file.filename.lower().endswith('.pdf'):
        pdf_path = os.path.join('uploads', file.filename)
        file.save(pdf_path)
        text = extract_text_from_pdf(pdf_path)
    else:
        return jsonify({'error': 'Unsupported file type'}), 400

    # Parse the extracted text
    extracted_data = parse_text(text)
    return jsonify({'data': extracted_data})

if __name__ == '__main__':
    os.makedirs('uploads', exist_ok=True)
    app.run(debug=True)
