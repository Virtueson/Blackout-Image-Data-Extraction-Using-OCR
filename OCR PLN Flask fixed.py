from flask import Flask, request, jsonify, render_template
from Utils import find_lines, body_extraction, delete_all_files_in_folder, split_time, format_time
import cv2
import pytesseract
import pandas as pd
import re
import os
from datetime import datetime
from flask_cors import CORS

# Initialize the Flask app and enable Cross-Origin Resource Sharing (CORS)
app = Flask(__name__)
CORS(app)


@app.route('/upload', methods=['POST'])
def upload_file():
    """
    Endpoint to handle file uploads, process the image, and perform OCR.
    Returns processed data in JSON format.
    """
    # Check if a file is provided in the request
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    # Save the uploaded file to the 'uploads' directory
    file_path = os.path.join('uploads', file.filename)
    file.save(file_path)

    # Read and prepare the uploaded image for processing
    image = cv2.imread(file_path)
    image_copy = image.copy()

    # Initialize a DataFrame to store the extracted data
    columns = ["Filename", "PLN", "Date", "Time", "Affected_Area"]
    df = pd.DataFrame(columns=columns)

    try:
        # Step 1: Process the image for OCR by identifying vertical and horizontal lines
        find_lines(image, "vertical", image_copy)
        body = cv2.imread('temp/image_cut.png')
        body_copy = body.copy()
        find_lines(body, "horizontal", body_copy)
        title = cv2.imread('temp/title.png')

        # Step 2: Extract text from the title image using Tesseract OCR
        title_ocr = pytesseract.image_to_string(title)
        title_lines = title_ocr.split('\n')

        # Step 3: Identify the PLN (company) name based on keywords in the OCR output
        for line in title_lines:
            if "PERSERO" in line:
                nama_pln = line
                break
            elif "ULP" in line:
                nama_pln = line

        # Clean up the PLN name using a regular expression
        nama_pln = re.sub(r'^.*\bPT', 'PT', nama_pln)

        new_row = [file_path, nama_pln]

        # Step 4: Extract relevant information from different parts of the image
        for i in range(1, 4):
            try:
                body = cv2.imread(f'temp/body part {i}.png')
                body_copy = body.copy()
                # Use different OCR strategies for specific image parts
                if (i == 1) or (i == 3):
                    text = body_extraction(body, body_copy)
                else:
                    text = pytesseract.image_to_string(body, lang='eng')
                cleaned_text = text.replace("\x0c", "").replace("\n", "")
                new_row.append(cleaned_text)
            except:
                new_row.append(None)

            # Add a new row to the DataFrame after processing all parts
            if i == 3:
                df.loc[len(df)] = new_row
                new_row = []

        # Step 5: Clean up temporary files used during the process
        delete_all_files_in_folder(r'D:\Russell\Project\OCR project\temp')

        # Extract digits from the 'Time' column for further processing
        df['Digits'] = df['Time'].apply(lambda x: [int(digit) for digit in re.findall(r'\d', x)])

        # Extract and clean time and date information
        df['Time'] = df['Time'].apply(lambda x: x.lower().split('waktu')[1] if 'waktu' in x.lower() else None)
        df['Date'] = df['Date'].apply(lambda x: x.lower().split('tanggal')[1].replace(":", "") if 'tanggal' in x.lower() else None)

        # Split time into start and end times and format them
        df[['start_time', 'end_time']] = df['Digits'].apply(lambda x: pd.Series(split_time(x)))
        df['start_time'] = df['start_time'].apply(format_time)
        df['end_time'] = df['end_time'].apply(format_time)

        # Calculate the duration in hours between start and end times
        df['duration(hours)'] = (pd.to_datetime(df['end_time']) - pd.to_datetime(df['start_time'])).dt.total_seconds() / 3600

        # Clean up the 'Affected_Area' column
        df['Affected_Area'] = df['Affected_Area'].apply(
            lambda x: x.replace("Wilayah Pemadaman", "")
                      .replace(":", "")
                      .replace("&", "")
                      .replace("Wilayah Pemeliharaan", "")
                      .replace("9", "")
                      .replace("@", "")
        )

        # Reorder and select relevant columns for the final DataFrame
        df = df[['Filename', 'PLN', 'Date', 'start_time', 'end_time', 'duration(hours)', 'Affected_Area']]

        # Save the DataFrame to a CSV file
        file_path = "PLN.csv"
        if not os.path.exists(file_path):
            # If the file does not exist, create it with headers
            df.to_csv(file_path, index=False)
        else:
            # If the file exists, append the data without headers
            df.to_csv(file_path, mode='a', index=False, header=False)

        # Prepare the response data
        result = {
            'pln_name': nama_pln,
            'time': df.loc[0, 'Date'],
            'start_time': str(df.loc[0, 'start_time']),
            'end_time': str(df.loc[0, 'end_time']),
            'duration': str(df.loc[0, 'duration(hours)']),
            'affected_area': df.loc[0, 'Affected_Area']
        }

    except Exception as e:
        # Handle any errors and return an appropriate message
        return jsonify({'error': str(e)}), 500

    # Return the extracted data as a JSON response
    return jsonify(result)

if __name__ == '__main__':
    # Ensure the required directories exist
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    if not os.path.exists('temp'):
        os.makedirs('temp')

    # Run the Flask app in debug mode
    app.run(debug=True)
