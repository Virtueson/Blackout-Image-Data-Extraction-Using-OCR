import easyocr
import cv2
import matplotlib.pyplot as plt
import numpy as np
from skimage.morphology import skeletonize
import pytesseract
import pandas as pd
import re
import os
from datetime import datetime


# Function to find and extract lines (horizontal/vertical) from an image
def find_lines(image, line_type_func, image_copy):
    height, width = image.shape[:2]
    
    # Convert the image to grayscale for edge detection
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Apply Canny edge detection to find edges
    edges = cv2.Canny(gray_image, 50, 150)
    
    # Convert edge-detected image to binary format
    binary = edges > 0

    # Apply skeletonization to thin the edges for better line identification
    skeleton = skeletonize(binary)
    skeleton_uint8 = (skeleton * 255).astype(np.uint8)
    
    # Determine line orientation (horizontal or vertical)
    line_type = line_type_func
    if line_type == 'horizontal':
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (20,1))
        kernel2 = cv2.getStructuringElement(cv2.MORPH_RECT, (45,5))
    elif line_type =='vertical':
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1,20))
        kernel2 = cv2.getStructuringElement(cv2.MORPH_RECT, (5,20))
    
    # Perform morphological transformation to detect lines
    lines = cv2.morphologyEx(skeleton_uint8, cv2.MORPH_OPEN, kernel)
    
    # Dilate the lines to make them more visible
    dilate = cv2.dilate(lines, kernel2, iterations = 1)
    
    # Find contours (connected components) of the lines
    contours, _ = cv2.findContours(dilate, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    y_temp = 0  # Temporary variable to track last y-coordinate
    i = 1  # Counter for saving different file parts
    
    # Sort contours from top to bottom (based on the y-coordinate)
    contours = sorted(contours, key=lambda x: cv2.boundingRect(x)[1])

    # Process each contour
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        if line_type == 'horizontal' and h < 20 and w > 250:  # Horizontal line condition
            roi = image_copy[y_temp:y, 0:width]
            cv2.rectangle(image_copy, (x, y), (x + w, y + h), (0, 255, 0), 2)
            y_temp = y + h + 1
            cv2.imwrite("temp/body part "+str(i)+".png", roi)
            i += 1    
        if line_type == 'vertical' and h > 250 and w < 20:  # Vertical line condition
            margin = 20  # Margin to exclude lines near the edges
            if x > margin and (x + w) < (width - margin):
                roi = image_copy[y:y+h, 0:x]
                title = image_copy[0:y, 0:width]
                cv2.rectangle(image_copy, (x, y), (x + w, y + h), (0, 255, 0), 2)
    
    # Save remaining parts after contour processing
    if line_type == 'horizontal':           
        roi = image_copy[y_temp:height, 0:width]
        cv2.imwrite("temp/body part "+str(i)+".png", roi)
    
    # Save contour and image cut for vertical line processing
    if line_type == 'horizontal':
        cv2.imwrite("temp/body_contour.png", image_copy)
    elif line_type == 'vertical':
        cv2.imwrite("temp/image_contour.png", image_copy)
        cv2.imwrite("temp/image_cut.png", roi)
        cv2.imwrite("temp/title.png", title)


# Function to extract text from a body part of an image using OCR
def body_extraction(image, image_copy):
    # Convert the image to grayscale and apply Gaussian blur to reduce noise
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred_image = cv2.GaussianBlur(gray_image, (7, 7), 0)
    
    # Apply Otsu's thresholding to get a binary image for contour detection
    thresh = cv2.threshold(blurred_image, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
    
    # Create a rectangular kernel for dilation operation
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (10, 15))
    dilate = cv2.dilate(thresh, kernel, iterations=1)
    
    list_text = []  # List to store extracted text
    
    # Find contours in the dilated image
    contours, _ = cv2.findContours(dilate, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=lambda x: cv2.boundingRect(x)[0])  # Sort by x-coordinate
    
    i = 0  # Counter for ROI image parts
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        if h > 20 and w > 50:  # Filter small contours
            roi = image_copy[y:y+h, x:w+x]  # Extract region of interest (ROI)
            cv2.imwrite("temp/test" + str(i) + ".png", roi)
            roi_text = pytesseract.image_to_string(roi, lang='ind')  # Perform OCR on the ROI
            print(roi_text)
            list_text.append(roi_text)
            cv2.rectangle(image_copy, (x, y), (x + w, y + h), (0, 255, 0), 2)  # Draw rectangle around ROI
            i += 1
    # Save the image with all ROIs marked
    cv2.imwrite("temp/body_with_roi.png", image_copy)
    
    # Return the extracted text as a single string
    text = '\n'.join(list_text)
    return text


# Function to delete all files in a folder
def delete_all_files_in_folder(folder_path):
    if not os.path.exists(folder_path):  # Check if the folder exists
        print(f"The folder {folder_path} does not exist.")
        return
    
    # Iterate through the files in the folder and delete them
    for file_name in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file_name)
        if os.path.isfile(file_path):
            os.remove(file_path)  # Delete the file
        else:
            print(f"Skipped (not a file): {file_path}")

# Function to split a list of digits into start and end time
def split_time(digits):
    if not digits or len(digits) < 8:  # Check for empty or invalid lists
        return None, None
    if len(digits) > 9:  # If there are more than 9 digits, return None
        return None, None
    if len(digits) == 9:
        digits = digits[1:]  # Ignore the first digit if length is 9
    digits_str = ''.join(map(str, digits))  # Convert digits list to string
    start = digits_str[:4]  # First 4 digits as start time
    end = digits_str[4:8]  # Next 4 digits as end time
    return start, end

# Function to format time in HH:MM format
def format_time(time_str):
    if not time_str:  # Handle empty strings
        return None
    formatted_time = time_str[:2] + ':' + time_str[2:]  # Format as HH:MM
    return formatted_time
