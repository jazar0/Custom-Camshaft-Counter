import cv2
import cv2 as cv
import numpy as np
from Arduino import Arduino

import time
import math
from matplotlib import pyplot as plt
import qrcode
import pyzbar.pyzbar as pyzbar

bSimulateArduino = True

current_slot_location = 1


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
    return 0

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

    if oResult.max() > 0.45:
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

def template_matching(original_image, template_image):
    """
    Perform template matching and return the result.
    """
    # Convert images to grayscale
    #gray_original = cv2.cvtColor(original_image, cv2.COLOR_BGR2GRAY)
    #gray_template = cv2.cvtColor(template_image, cv2.COLOR_BGR2GRAY)
    #cv2.imshow("gray_original",gray_original)
    #cv2.imshow("gray_template",gray_template)

    # Perform template matching
    result = cv2.matchTemplate(original_image, template_image, cv2.TM_CCOEFF_NORMED)

    return result

def find_template_location(result):
    """
    Find the location of the maximum value in the result.
    """
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    return max_loc

def create_blank_image_opencv(width, height, background_color=(255, 255, 255)):
    """
    Create a blank image with a specified width, height, and background color using OpenCV.
    """
    blank_image = np.ones((height, width, 3), dtype=np.uint8)
    blank_image[:] = background_color
    return blank_image

def rotate_image2(image, angle):
    # Get the image dimensions
    height, width = image.shape[:2]

    # Calculate the rotation matrix
    rotation_matrix = cv2.getRotationMatrix2D((width / 2, height / 2), angle, 1)

    # Apply the rotation to the image
    rotated_image = cv2.warpAffine(image, rotation_matrix, (width, height))

    return rotated_image


def rotate_image(image, angle, background_color=(0, 0, 0)):
    """
    Rotate an image by a specified angle with a specified background color.
    """
    # Get image dimensions
    height, width = image.shape[:2]

    # Calculate rotated corners' positions
    rotated_corners = np.array([[0, 0], [width - 1, 0], [0, height - 1], [width - 1, height - 1]])
    rotation_matrix = cv2.getRotationMatrix2D((width / 2, height / 2), angle, 1.0)
    rotated_corners = cv2.transform(np.array([rotated_corners]), rotation_matrix)[0]

    # Find the new dimensions for the canvas
    min_x, max_x = np.min(rotated_corners[:, 0]), np.max(rotated_corners[:, 0])
    min_y, max_y = np.min(rotated_corners[:, 1]), np.max(rotated_corners[:, 1])

    # Create a canvas with the minimum required size and fill it with the specified background color
    rotated_image = np.full((int(max_y - min_y + 1), int(max_x - min_x + 1), 3), background_color, dtype=np.uint8)

    # Calculate the translation matrix to place the image on the canvas
    translation_matrix = np.array([[1, 0, -min_x], [0, 1, -min_y]])

    # Apply translation to the rotation matrix
    rotated_matrix = np.vstack([rotation_matrix, [0, 0, 1]])
    translated_matrix = np.vstack([translation_matrix, [0, 0, 1]])
    final_matrix = np.dot(translated_matrix, rotated_matrix)[:2, :]

    # Perform the rotation and translation
    rotated_image = cv2.warpAffine(image, final_matrix, (rotated_image.shape[1], rotated_image.shape[0]), borderMode=cv2.BORDER_CONSTANT, borderValue=background_color)

    return rotated_image

def rotate_image1(image, angle, background_color=(0, 0, 0)):
    """
    Rotate an image by a specified angle with a specified background color.
    """
    # Get image dimensions
    height, width = image.shape[:2]

    # Calculate rotated corners' positions
    rotated_corners = np.array([[0, 0], [width - 1, 0], [0, height - 1], [width - 1, height - 1]])
    rotation_matrix = cv2.getRotationMatrix2D((width / 2, height / 2), angle, 1.0)
    rotated_corners = cv2.transform(np.array([rotated_corners]), rotation_matrix)[0]

    # Find the new dimensions for the canvas
    min_x, max_x = np.min(rotated_corners[:, 0]), np.max(rotated_corners[:, 0])
    min_y, max_y = np.min(rotated_corners[:, 1]), np.max(rotated_corners[:, 1])

    # Create a canvas with the minimum required size and the desired background color
    rotated_image = np.full((int(max_y - min_y + 1), int(max_x - min_x + 1), 3), background_color, dtype=np.uint8)

    # Calculate the translation matrix to place the image on the canvas
    translation_matrix = np.array([[1, 0, -min_x], [0, 1, -min_y]])

    # Apply translation to the rotation matrix
    rotated_matrix = np.vstack([rotation_matrix, [0, 0, 1]])
    translated_matrix = np.vstack([translation_matrix, [0, 0, 1]])
    final_matrix = np.dot(translated_matrix, rotated_matrix)[:2, :]

    # Perform the rotation and translation
    rotated_image = cv2.warpAffine(image, final_matrix, (rotated_image.shape[1], rotated_image.shape[0]))

    return rotated_image

def create_blank_image_like(original_image, color=(255, 255, 255)):
    """
    Create a new blank image with the same size as the original image and fill it with a specified color.
    """
    height, width, channels = original_image.shape
    colorBlank = np.full((height, width, channels), color, dtype=np.uint8)
    #cv2.imshow("Color", colorBlank)
    return colorBlank

def copy_contour_contents(original_image, contour, color=(255, 255, 255)):
    """
    Create a new image with the same size as the original, with the specified contour drawn on it.
    Copy the contents of the original image within the contour to the new image.
    """
    # Create a new blank image with the same size as the original
    result_image = create_blank_image_like(original_image, color)

    # Draw the specified contour on the new image and fill it with the specified color
    cv2.drawContours(result_image, [contour], -1, color, thickness=cv2.FILLED)

    # Create a mask for the contour
    mask = np.zeros_like(result_image, dtype=np.uint8)

    cv2.drawContours(mask, [contour], -1, (255, 255, 255), thickness=cv2.FILLED)


    # Copy contents of the original image to the new image within the contour
    result_imageInside = cv2.bitwise_and(original_image, mask)
    result_imageOutside = cv2.bitwise_and(result_image, cv2.bitwise_not(mask))
    result_image = cv2.max(result_imageInside, result_imageOutside)

    return result_image


def processCommands(iCommands):
    for cmd in iCommands:
        # time.sleep(0.025)
        if cmd == "Up":
            cnc.write("Z0")
            cnc.write("G4 P0.25")
        elif cmd == "Down":
            cnc.write(downline)
            cnc.write("G4 P0.25")
        elif cmd == "Red":
            downline = "Z10.0"
        elif cmd == "Green":
            downline = "Z-10.0"
        else:
            cnc.write(cmd)

def nothing(x):
    pass
    #print(x)

def findContours(iContours, iAreaMin, iAreaMax):
    #starting position of machine is at slot 1
    #is CNC moving variable (dont want it to try to write to variable whilst machine is moving as will produce innacurate results.)
    isMoving = False
    #create an array that with 111 values. first value is dummy value, 1-110 represents each and every cam slot in the box.
    camMap = [2] * 111
    #set dummy value to -1, so it does not conflict
    camMap[0] = -1

    oContours = iContours
    if len(iContours) > 0:
        oContours = sorted(iContours, key=cv2.contourArea, reverse=True)

    oList = []
    for wContour in oContours:
        wHull = cv2.convexHull(wContour)
        wArea = cv2.contourArea(wContour)

        x, y, w, h = cv2.boundingRect(wContour)
        aspect_ratio = min (float(w) / h, float(h) / w)

        wHullArea = cv2.contourArea(wHull)
        '''#if (wArea / wHullArea > 0.75 and wHullArea > 3000 and wHullArea < 8000 and aspect_ratio > 0.8):
        '''
        areaMultiplier = 20000
        aspect = 0.80
        if wHullArea > 0:
            if (wArea / wHullArea > aspect and wHullArea > iAreaMin*areaMultiplier and wHullArea < iAreaMax*areaMultiplier and aspect_ratio > aspect):
                #print(wHullArea, wArea, wArea/wHullArea, aspect_ratio)
                oList.append(wHull)
            ''' 
                if isMoving == False:
                    camMap[current_slot_location] = 1 #1 = CAMSHAFT DETECTED

        
        elif wHullArea <= 0 & isMoving == False:
            camMap[current_slot_location] = 0
        

        elif isMoving == True:
            camMap[current_slot_location] = 2

        '''
    return (oList[0:min(25,len(iContours))])


#cap = cv.VideoCapture(1)

cv.namedWindow('Tracking', cv2.WINDOW_NORMAL)
cv.resizeWindow('Tracking', 300, 400)
cv.createTrackbar("threshMIN", "Tracking", 55, 255, nothing)
cv.createTrackbar("threshMAX", "Tracking", 255, 255, nothing)
cv.createTrackbar("kernelSize", "Tracking", 6, 20, nothing)
cv.createTrackbar("lineThick", "Tracking", 2, 5, nothing)
cv.createTrackbar("Pick-BW-R-G-B-H-S-V", "Tracking", 1, 7, nothing)
cv.createTrackbar("AreaMin", "Tracking", 3, 20, nothing)
cv.createTrackbar("AreaMax", "Tracking", 15, 10, nothing)
cv.createTrackbar("Display", "Tracking", 7, 10, nothing)
cv.createTrackbar("rotateAngle", "Tracking", 0, 360, nothing)
cv.createTrackbar("scale", "Tracking", 1, 10, nothing)
cv.createTrackbar("Row", "Tracking", 0, 10, nothing)
cv.createTrackbar("Column", "Tracking", 0, 9, nothing)

scale = 1
index = 3
maxIndex = 10
filename =  "img-24-02-23-Demo-"+str(index)+".jpg"
img=cv.imread(filename, 1) # Read black and white
scale = 1.0

template = cv2.imread("Fullbox-Test2.jpg",1)
(r, c, colors) = template.shape
print(r,c, scale)
roiY = int(r/11)
roiX = int(c/10)
template = cv2.resize(template, (int(c*scale), int(r*scale)))
#cv2.imshow("template", template)
row = 5
column = 6
bVideo = False
if bVideo:
    cap = cv2.VideoCapture(0) # Pick the camera
    cap.set(3, 1920)
    #cap.set(4, 1200)
    cap.set(propId = cv.CAP_PROP_EXPOSURE, value=-7)
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter('output2.avi', fourcc, 20.0, (1280, 800))

    if (cap.isOpened()):
        ret, imgRaw = cap.read()
        img = imgRaw[450:650, 200:1000]

(r, c, colors) = img.shape

cnc = Arduino('com4', bSimulateArduino)
cnc.connect()
cnc.readLine()

initialize = ["$$",
              "$100=28.639", "$110=12000", "$120=300", "$130=800",  # X-Axis, 12V settings
              "$101=28.639", "$111=12000", "$121=200", "$131=800",  # Y-Axis, 12V settings
              "$102=30", "$112=20000", "$122=200", "$132=20",  # Z-Axis, 12V settings
              "G0G90", "$", "G1F18000",
              "$$"
              ]
processCommands(initialize)

test = ["$21=0","$22=0", "$5=0"] 
processCommands(test)

cnc.verbose = True

test = ["$12=0.002", "$11=0.050", "$10=1"]
processCommands(test)

test = ["G1X-50F3000", "G4 P1", "X0"]
processCommands(test)

xValue = 0
fValue = 3000
command = "X"+str(xValue)

num=0


def rotate_image(image, angle):
  #  Rotate image
    height, width = image.shape[:2]
    rotation_matrix = cv2.getRotationMatrix2D((width / 2, height / 2), angle, 1)
    rotated_image = cv2.warpAffine(image, rotation_matrix, (width, height))
    return rotated_image

def find_circles(image):
   # find circles, filter them

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    cv2.imshow("gray", gray)
    circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, dp=0.1, minDist=50, param1=200, param2=30, minRadius=50, maxRadius=70)
    if circles is not None:
        circles = np.round(circles[0, :]).astype("int")
        circles_to_keep = []
        for (x, y, r) in circles:
            circle_area = np.pi * r ** 2
            # Check if the area is within the specified range
            if 4000 <= circle_area <= 17000:
                circle_valid = True
                # Check for overlap with existing circles
                for (x_existing, y_existing, r_existing) in circles_to_keep:
                    distance = np.sqrt((x_existing - x) ** 2 + (y_existing - y) ** 2)
                    if distance < (r_existing + r):
                        circle_valid = False
                        break
                if circle_valid:
                    circles_to_keep.append((x, y, r))
        return np.array(circles_to_keep)
    else:
        return None


def calculate_rotation_angle(circle_centers):
    ref_vector = np.array([1, 0])  # Reference vector pointing to the right
    
    # Assuming only two circles are detected
    vector_between_circles = circle_centers[1] - circle_centers[0]
    
    angle_radians = np.arctan2(vector_between_circles[1], vector_between_circles[0])
    angle_degrees = np.degrees(angle_radians)
    return angle_degrees

def rotate_the_image():
    # Load the image
    image = roi
    
    # Find circles in the image
    circles = find_circles(image)
    cv2.waitKey(0)
    if circles is not None:
        if len(circles) >= 2:
            # Display circles detected
            circle_image = image.copy()
            for (x, y, r) in circles:
                cv2.circle(circle_image, (x, y), r, (0, 255, 0), 4)
            cv2.imshow("circle_img", circle_image)
            # Calculate rotation angle
            circle_centers = circles[:, :2]
            rotation_angle = calculate_rotation_angle(circle_centers) - 180

            
            # Rotate the image
            rotated_image = rotate_image(image, rotation_angle)
           
            return rotated_image
            cv2.imshow("Rotated Image", rotated_image)

        else:
            rotated_image = image    
            decodeCode(rotated_image)
            print("less than 2 circles detected")
            cv2.imshow("Rotated Image", rotated_image)
            return rotated_image
    else:
        rotated_image = image    
        decodeCode(rotated_image)
        print("Circles not detected/multiple circles present")
        cv2.imshow("Rotated Image", rotated_image)
        return rotated_image
# Initialize the 2D array
array_2d = [[None for _ in range(11)] for _ in range(10)]

# Function to update the array with information
# Function to update the array with information
# Function to update the array with information
def update_array(row, column, image):
    decoded_info = decodeCode(image)  # Call decodeCode with rotated image to get decoded information
    array_2d[row][column] = decoded_info



while True:
    row = cv.getTrackbarPos("Row", "Tracking")
    column = cv.getTrackbarPos("Column", "Tracking")
    #_, frame = cap.read()
    if bVideo:
        if (cap.isOpened()):
            ret, imgRaw = cap.read()
            scale = 1
            #img = cv2.resize(img, (int(c / scale), int(r / scale)))
            cv.imshow("image", img)



    roi = template[row*roiY:(row+1)*roiY, column*roiX:(column+1)*roiX]
    
    img = roi

    rotated_image = rotate_the_image()

    update_array(row, column, rotated_image)
    for row in array_2d:
        print(row)
    cv.imshow("roi", roi)
    
    titles = []
    images = []


    threshMIN = min(max(1, cv.getTrackbarPos('threshMIN', "Tracking")),255)
    threshMAX = min(max(1, cv.getTrackbarPos('threshMAX', "Tracking")),255)
    lineThick= min(max(1, cv.getTrackbarPos('lineThick', "Tracking")),8)
    kernelSize = cv.getTrackbarPos('kernelSize', "Tracking")
    scale = max(cv.getTrackbarPos('scale', "Tracking"), 0.5)

    wDisplay = cv.getTrackbarPos('Display', "Tracking")
    wPick = cv.getTrackbarPos("Pick-BW-R-G-B-H-S-V", "Tracking")
    wAreaMin = cv.getTrackbarPos("AreaMin", "Tracking")
    wAreaMax = cv.getTrackbarPos("AreaMax", "Tracking")
    rotateAngle = cv.getTrackbarPos("rotateAngle", "Tracking")

    kernelSize = max(1, kernelSize)
    if kernelSize % 2 == 0:
        kernelSize = kernelSize + 1
    kernel = np.ones((kernelSize, kernelSize), np.float32) / (kernelSize * kernelSize)

    imgray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    #if wDisplay >= 1:
    #    titles.append("imgray")
    #    images.append(imgray)

    (imgBlue, imgGreen, imgRed) = cv2.split(img)
    zeros = np.zeros(img.shape[:2], dtype="uint8")
    #if wDisplay == 2:
    #    cv2.imshow("Red", cv2.merge([zeros, zeros, imgRed]))
    #    cv2.imshow("Green", cv2.merge([zeros, imgGreen, zeros]))
    #    cv2.imshow("Blue", cv2.merge([imgBlue, zeros, zeros]))

    imhsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    (imgH, imgS, imgV) = cv2.split(imhsv)
    #if wDisplay == 3:
    #    cv2.imshow("Hue", imgH)
    #    cv2.imshow("Saturation", imgS)
    #    cv2.imshow("Value", imgV)

    imAnalyze = imgray
    wTitleAnalysis = "Gray"
    if wPick == 1:
        imAnalyze = imgray.copy()
        wTitleAnalysis = "Gray"
    elif wPick == 2:
        imAnalyze = imgRed
        wTitleAnalysis = "Red"
    elif wPick == 3:
        imAnalyze = imgGreen
        wTitleAnalysis = "Green"
    elif wPick == 4:
        imAnalyze = imgBlue
        wTitleAnalysis = "Blue"
    elif wPick == 5:
        imAnalyze = imgH
        wTitleAnalysis = "HSV-Hue"
    elif wPick == 6:
        imAnalyze = imgS
        wTitleAnalysis = "HSV-Saturation"
    elif wPick == 7:
        imAnalyze = imgV
        wTitleAnalysis = "HSV-Value"

    #titles.append("Analysis")
    #images.append(imAnalyze)


    ret, imgThreshMIN = cv2.threshold(imAnalyze, threshMIN, 255, cv2.THRESH_BINARY)
    threshMinRotate = rotate_image2(imgThreshMIN, rotateAngle)
    ret, imgThreshMAX = cv2.threshold(imAnalyze, threshMAX, 255, cv2.THRESH_BINARY)
    threshRange = cv2.bitwise_and(imgThreshMIN, cv2.bitwise_not(imgThreshMAX))
 


    font = cv2.FONT_HERSHEY_SIMPLEX
    imAnalyze = cv2.putText(imAnalyze, wTitleAnalysis, (10, 50), font, 1, 0, 3, cv2.LINE_AA)
    imAnalyze = cv2.putText(imAnalyze, wTitleAnalysis, (10, 50), font, 1, 255, 1, cv2.LINE_AA)

    opening = cv2.morphologyEx(imgThreshMIN, cv2.MORPH_OPEN, kernel,3)
    closing = cv2.morphologyEx(imgThreshMIN, cv2.MORPH_CLOSE, kernel,3)

    contours, heirarchy = cv2.findContours(closing, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
    #print("contours = %d" % len(contours))

    img_contours = img.copy()
    cv2.drawContours(img_contours, contours, -1, (0,255,0), lineThick)

    detect_contours = cv2.cvtColor(closing.copy(), cv2.COLOR_GRAY2RGB)
    cv2.drawContours(detect_contours, contours, -1, (0,255,0), lineThick)
    if wDisplay >= 6:
        titles.append("detect_contours")
        images.append(detect_contours)

    foundContours = findContours(contours, wAreaMin, wAreaMax)
    found_contours = img.copy()
    cv2.drawContours(found_contours, foundContours, -1, (0,0,255), lineThick)
    if wDisplay >= 6:
        titles.append("Cams Detected")
        images.append(found_contours)

    if wDisplay >= 1:
        n = 1
        camImage = create_blank_image_opencv(200, 200, background_color=(255, 255, 255))
        for contour in foundContours:
            x, y, w, h = cv2.boundingRect(contour)
            #print("Shape: ", img.shape)
            x1 = max(x-40,x,0)
            x2 = min(x+w,img.shape[1]-1)
            y1 = max(y-40,y,0)
            y2 = min(y+h,img.shape[0]-1)
            #print (x1,x2,y1,y2)
            camImage = img[y1:y2, x1:x2]
            (r, c, colors) = camImage.shape
            WhiteCamImage = create_blank_image_opencv(r, c, background_color=(255, 255, 255))
            backgroundColor = color=(255, 255, 255)
            NewCamImage = copy_contour_contents(img, contour, backgroundColor)
            NewCamImage = NewCamImage[y1:y2, x1:x2]
            #cv2.imshow("NewPreRotate", NewCamImage)

            result, rotateAngle, bestThresh, bestScale = template_matching_best(NewCamImage, template)

            NewCamImage = rotate_image2(NewCamImage, rotateAngle)
            #scale = 2
            NewCamImage = cv2.resize(NewCamImage, (int(c * scale), int(r * scale)))
            #cv2.imshow("New", NewCamImage)
            decodeCode(NewCamImage)
            NewCamImageBW = cv2.cvtColor(NewCamImage,cv2.COLOR_BGR2GRAY)


            #ret, threshMAX = cv2.threshold(NewCamImageBW, threshMAX, 255, cv2.THRESH_BINARY)
            ret, threshMAX = cv2.threshold(NewCamImageBW, bestThresh, 255, cv2.THRESH_BINARY)
            threshMAX = cv2.merge([threshMAX, threshMAX, threshMAX])
            #cv2.imshow("threshMAX", threshMAX)

            print("Match: {0}, Thresh {1}, Rotate {2}, Scale {3}".format(result.max(),bestThresh,rotateAngle, bestScale ))


            # Find the location of the maximum value in the result
            if result.max() > 0.35:
                template_location = find_template_location(result)

                # Draw a rectangle around the found template
                h, w = template.shape[:2]
                if result.max() > 0.55:
                    cv2.rectangle(NewCamImage, template_location, (template_location[0] + w, template_location[1] + h),
                          (0, 255, 0), 2)
                else:
                    cv2.rectangle(NewCamImage, template_location, (template_location[0] + w, template_location[1] + h),
                          (0, 0, 255), 2)

            cv2.imshow("Template Match", NewCamImage)

            camTitle = "%d" % n
            n += 1
        #cv2.imshow("camTitle", camImage)


    for i in range(len(titles)):
        cv.imshow(titles[i],images[i])


    k = cv.waitKey(1) & 0xFF
    if k == 27:
        break
    elif k == ord('s'):
        name = 'img-24-02-23-Demo-'+str(num)+".jpg"
        cv2.imwrite(name, roi)
        num=num+1
        print ('running')
    elif k == ord('.'):
        index = (index + 1) % maxIndex
        filename = "img-24-02-23-Demo-" + str(index) + ".jpg"
        img = cv.imread(filename, 1)  # Read black and white
    elif k == ord(','):
        index = (index + maxIndex - 1) % maxIndex
        filename = "img-24-02-23-Demo-" + str(index) + ".jpg"
        img = cv.imread(filename, 1)  # Read black and white
    elif k == ord("1"):
        xValue = 0
        command = "X" + str(xValue)
        processCommands([command])
    elif k == ord("2"):
        xValue = xValue + 10
        command = "X" + str(xValue)
        processCommands([command])
    elif k == ord("3"):
        xValue = xValue - 10
        command = "X" + str(xValue)
        processCommands([command])
    elif k == ord("4"):
        xValue = xValue + 65
        command = "X" + str(xValue)
        processCommands([command])

    elif k == ord("5"):
        xValue = xValue - 65
        command = "X" + str(xValue)
        processCommands([command])
    elif k == ord("0"):
        fValue = fValue + 1000
        command = "F" + str(fValue)
        processCommands([command])
    elif k == ord("9"):
        fValue = fValue - 1000
        if fValue < 1000:
            fValue = 500
        command = "F" + str(fValue)
        processCommands([command])
'''
for row in range(0, 11):
    for column in range(0, 10):
        goto_cell(row, column)
        #wait for motion to stop
        #detect cam or not write corresponding value to array, determine type of cam (unkown [run through various things to try to figure out type of cam] OR known)
for row in range(0, 11):
    for column in range(0, 10):
        if unknown_cam:
            #prompt user to select cam OR manually select cam from map and rerun detection

'''
#manual motion
#
#generate report 

if bVideo:
    cap.release()
cv.destroyAllWindows()