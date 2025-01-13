# OCR Image Upload and Processing

This project provides a simple web application for uploading images and processing them using Optical Character Recognition (OCR). It extracts specific information from the uploaded image, such as PLN name, date, time, duration, and affected area, and displays the results on the web page.

## Overview

The application consists of two parts:
1. **Frontend (HTML, CSS, JavaScript)**: A simple web interface that allows users to upload images and view the OCR results.
2. **Backend (Python Flask)**: A server that processes the uploaded image using OCR and returns the extracted data as a JSON response.

The frontend sends the uploaded image to the backend, where the OCR processing occurs, and the results are displayed back to the user.

### Features
- Upload images in `.jpg` or `.jpeg` format.
- Extracts specific data such as PLN name, date, time, duration, and affected area.
- Displays the processed results directly on the webpage.

## Requirements

- Python 3.x
- Flask
- Tesseract (for OCR processing)
- `pytesseract` Python library
- Image file (JPG/JPEG)

## Project Structure

The project contains the following files:

/frontend ├── index.html # HTML structure for the upload page 

/backend ├── OCR PLN Flask fixed.py # Flask backend for handling image upload and OCR processing └── Utils.py # All of the function

## How to run the Code
Step 1 : Make sure you have installed all necessary libraries

Step 2: Running the Flask Backend

    Start the Flask Server:

    In your terminal, navigate to the directory where your OCR PLN Flask fixed.py file is located. Run the Flask app by executing:

    python OCR PLN Flask fixed.py

    The Flask server should now be running locally at http://127.0.0.1:5000/.

Step 3: Open the Frontend

    Open the index.html File:

    Open the index.html file in a web browser. You can do this by double-clicking the file or using the browser's "Open File" option.

    Upload an Image:
        On the webpage, click the "Upload" button to select and upload an image (JPG/JPEG).
        The image will be sent to the backend for OCR processing.

    View the OCR Results:

    Once the image is processed, the extracted information (such as PLN name, date, time, duration, and affected area) will be displayed on the page and stored in your excel file.
