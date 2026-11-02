import cv2
import cv2 as cv
import numpy as np
from Arduino import Arduino
from matplotlib import pyplot as plt
import pyzbar.pyzbar as pyzbar


template = cv2.imread("template.png")
template_2 = cv2.imread("template2.png")
template_3 = cv2.imread("template3.png")
template_4 = cv2.imread("template4.png")

def rotate_image2(image, angle):
    # Get the image dimensions
    height, width = image.shape[:2]

    # Calculate the rotation matrix
    rotation_matrix = cv2.getRotationMatrix2D((width / 2, height / 2), angle, 1)

    # Apply the rotation to the image
    rotated_image = cv2.warpAffine(image, rotation_matrix, (width, height))

    return rotated_image

def find_template_location(result):
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    return max_loc

def template_matching(original_image, template_image):
    # Perform template matching
    result = cv2.matchTemplate(original_image, template_image, cv2.TM_CCOEFF_NORMED)
    return result

def template_matching_best(iOriginalImage, iTemplate):
    thresholds = np.linspace(50, 200, 5) # Five sample
    angles = np.arange(0, 360, 5) # Step of 20
    scales = np.linspace(0.8, 1.2, 5)
    wBest = 0.0
    oResult = []
    oScale = 1

    wGrayImage = cv2.cvtColor(iOriginalImage, cv2.COLOR_BGR2GRAY)
    wGrayTemplate =  cv2.cvtColor(iTemplate, cv2.COLOR_BGR2GRAY)

    for thresh in thresholds:
        for angle in angles:
            NewCamImageBW = rotate_image2(wGrayImage, angle)
            ret, threshMAX = cv2.threshold(NewCamImageBW, thresh, 255, cv2.THRESH_BINARY)
            result = template_matching(threshMAX, wGrayTemplate)
            if result.max() > wBest:
                wBest = result.max()
                oResult = result
                oAngle = angle
                oThresh = thresh

    if oResult.max() > 0.75:
        thresholds = np.linspace(oThresh-20, oThresh+20, 3) # Three samples
        angles = np.arange(oAngle-5, oAngle+5, 0.5) # Step of 20

        for thresh in thresholds:
            for angle in angles:
                NewCamImageBW = rotate_image2(wGrayImage, angle)
                ret, threshMAX = cv2.threshold(NewCamImageBW, thresh, 255, cv2.THRESH_BINARY)
                result = template_matching(threshMAX, wGrayTemplate)
                if result.max() > wBest:
                    wBest = result.max()
                    oResult = result
                    oAngle = angle
                    oThresh = thresh

    return oResult, oAngle, oThresh, oScale


def decodeCode(image):
    # Try OpenCV QR code detection and decoding
    qrCodeDetector = cv2.QRCodeDetector()
    decodedText, points, _ = qrCodeDetector.detectAndDecode(image)
    if decodedText:
        print("QR Code Data:", decodedText)
        return decodedText

    # If OpenCV failed, try PyZBar
    decodedObjects = pyzbar.decode(image)
    if decodedObjects:
        for obj in decodedObjects:
            print("QR Code Data:", obj.data)
        return obj.data

    print("No QR code found or unable to decode.")

    result, rotateAngle, bestThresh, bestScale = template_matching_best(image, template)

    if result.max() > 0.70:
        template_location = find_template_location(result)

            # Draw a rectangle around the found template
        h, w = template.shape[:2]
        if result.max() > 0.55:
            cv2.rectangle(image, template_location, (template_location[0] + w, template_location[1] + h),
                    (0, 255, 0), 2)
        else:
            cv2.rectangle(image, template_location, (template_location[0] + w, template_location[1] + h),
                    (0, 0, 255), 2)
        

        cv2.imshow("template matching", image)
        cv2.waitKey(0)
        NewCamImageBW = cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
        ret, threshMAX = cv2.threshold(NewCamImageBW, bestThresh, 255, cv2.THRESH_BINARY)
        threshMAX = cv2.merge([threshMAX, threshMAX, threshMAX])
        print(result.max())
        return "C08R20E"

    # Create a blank image to display text input prompt
    prompt_image = np.ones((100, 400, 3), np.uint8) * 255
    cv2.putText(prompt_image, "Enter text:", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)

    # Display the prompt image in a window
    cv2.imshow("Text Input", prompt_image)

    # Variable to hold user input
    user_text = ""

    # Capture keyboard input until Enter key is pressed
    while True:
        key = cv2.waitKey(1) & 0xFF
        if key == 13:  # Enter key
            break
        elif key == 8:  # Backspace key
            user_text = user_text[:-1]  # Remove the last character
        elif key != 255:  # Valid key pressed
            user_text += chr(key)

        # Update prompt image with user input
        prompt_image = np.ones((100, 400, 3), np.uint8) * 255
        cv2.putText(prompt_image, "Enter text: " + user_text, (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        cv2.imshow("Text Input", prompt_image)

    cv2.destroyWindow("Text Input")
    print(user_text)
    return user_text


image = cv2.imread("Rotated Image-40.png")
decodeCode(image)