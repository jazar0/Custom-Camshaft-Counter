#--------------------------------------------------
# Team 2705-01: C3 - Custom Camshaft Counter
# Robofest Exhibition 2024
# Nik Lowe - 8 Years Robotics experience
# Jurius Azar - 7 Years Robotics experience
#
# Overview: The C3 system is a computer vision based
# system that scan and identifies camshafts.  The
# system incorporates a G-code based multi-axis
# motion controller through # a USB interface as well
# as a camera to be able to move to location and take
# photographs of each camshaft.  It then uses Trig,
# Geometry and various Computer Vision techniques
# utilizing the OpenCV library to identify each
# camshaft.
#
# First we identify if each cell in the shipping
# container contains a camshaft or not. This is
# done by our "Image Processing Pipeline" which
# consists of:
#  - Capturing a high resolution image
#  - Converting the image to gray scale
#  - Thresholding the image to try to
#    highlight the cam
#  - Using a Morphological operation to
#    remove any gaps in the image
#  - Detecting contours
#  - Analyzing the contours to find out which
#    ones are camshafts
#  - Identifying the center and the drain hole
#    and rotating the image
#
# Finally we identify what type of camshaft each one is.
#  - First try to read the QR code
#  - Next try template matching to identify the cams
#  - Finally, we allow the user to type in the idegntity
#    of any unknown cams.
#------------------------------------------------------------------
import cv2
import numpy as np
from Arduino import Arduino
import math
import pyzbar.pyzbar as pyzbar
from Upload_code import upload_to_drive
from MasterMind import MasterMind
from ReportUpload import generateReport
game = MasterMind("Jurius")

#Game Reports Folder ID
folder_id = 'REPLACE_WITH_YOUR_DRIVE_ID'
wFolder = "BoxTemplates"
wTemplateFolder = "Templates\\"
wReportFileName = "TestReport.jpg"
wBoxNum = "Game" # Pick M1 or NIK
scanRow = 0
scanCol = 0
bSimulateAll = True
bMasterMind = False

if bSimulateAll:
    cPauseRowChange = 1000  # ms Run fast since just using images to simulate
    cPauseColumnChange = 1000  # ms

    if bMasterMind: # Sizes of the cells are slightly different
        wFullBoxScale = 0.1  # 0.1 for 4x4, 0.05 for 11x10
        boxRows = 9  # 11
        boxColumns = 4  # 10
    else:
        wFullBoxScale = 0.1  # 0.1 for 4x4, 0.05 for 11x10
        boxRows = 4 #11
        boxColumns = 4 # 10
    bVideo = False
    bSimulateArduino = True
    wCellWidthX = 69
    wCellLengthY = 44
else: # Connect to Real Hardware
    cPauseRowChange = 5000  # ms
    cPauseColumnChange = 3000  # ms

    wFullBoxScale = 0.05 #for 11x10
    bVideo = True
    bSimulateArduino = False
    if bMasterMind: # Sizes of the cells are slightly different
        wCellWidthX = 67.25
        wCellLengthY = 39.75+0.28+0.15
        boxRows = 9  # 11
        boxColumns = 4  # 10
    else:
        wCellWidthX = 67
        wCellLengthY = 40
        boxRows = 11
        boxColumns = 10
wGrid = [["NONE" for j in range(boxColumns)] for i in range(boxRows)]
wCamCountTotals = {}
wBoxCount = 0

def AddTemplate(iFolder, iFile, iName):
    wFileName = iFolder + iFile+".jpg"
    print(wFileName)
    wImage = cv2.imread(wFileName)

    #cv2.imshow(iName, wImage)
    gTemplates.append([wImage, iName])


gTemplates=[]

AddTemplate(wTemplateFolder, "Red1", "Red")
AddTemplate(wTemplateFolder, "Blue1", "Blue")
AddTemplate(wTemplateFolder, "Green1", "Green")
AddTemplate(wTemplateFolder, "Yellow1", "Yellow")
AddTemplate(wTemplateFolder, "Orange1", "Orange")
AddTemplate(wTemplateFolder, "Purple1", "Purple")

# Colors BGR sequence
Black = (0, 0, 0)
White = (255, 255, 255)
Red =  (0, 0, 255)
Green = (0, 255, 0)
Blue = (255, 0, 0)
Yellow = (0, 255, 255)
Cyan = (255, 255, 0)
Magenta = (255, 0, 255)
Orange = (0, 165, 255)
Pink = (203, 192, 255)
Purple = (128, 0, 128)
wGlobalColors = {}
wGlobalColors["BLACK"] = Black
wGlobalColors["WHITE"] = White
wGlobalColors["UNKNOWN"] = White # Also highlight the unknowns with a color
wGlobalColors["RED"] = Red
wGlobalColors["GREEN"] = Green
wGlobalColors["BLUE"] = Blue
wGlobalColors["YELLOW"] = Yellow
wGlobalColors["CYAN"] = Cyan
wGlobalColors["MAGENTA"] = Magenta
wGlobalColors["ORANGE"] = Orange
wGlobalColors["PINK"] = Pink
wGlobalColors["PURPLE"] = Purple



# Parameters for the Box clicking subroutine
clickedX = 0
clickedY = 0
globalCickCell = False

#
def click_eventBoxCellClicked(event, x, y, flags, param):
    global clickedX
    global clickedY
    global globalCickCell
    if event == cv2.EVENT_LBUTTONDOWN:
        clickedX = x
        clickedY = y
        print("Click Set: ",x,y)
        globalCickCell = True

wDigitalStep = 120


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
    thresholds = np.linspace(50, 200, 1) # Five sample
    angles = np.arange(-20, 20, 5) # Arrange takes Start, stop and step
    scales = np.linspace(0.6, 0.9, 5)
    wBest = 0.0
    oResult = []
    oScale = 1

    wGrayImage = cv2.cvtColor(iOriginalImage, cv2.COLOR_BGR2GRAY)
    wGrayTemplate =  cv2.cvtColor(iTemplate, cv2.COLOR_BGR2GRAY)

    for scale in scales:
        (r, c) = wGrayTemplate.shape
        wResizeTemplate = cv2.resize(wGrayTemplate, (int(c * scale), int(r * scale)))
        for thresh in thresholds:
            #cv2.imshow(str(scale),wResizeTemplate)
            for angle in angles:
                NewCamImageBW = rotate_image2(wGrayImage, angle)
                #ret, threshMAX = cv2.threshold(NewCamImageBW, thresh, 255, cv2.THRESH_BINARY)
                #result = template_matching(threshMAX, wResizeTemplate)
                result = template_matching(NewCamImageBW, wResizeTemplate)
                if result.max() > wBest:
                    wBest = result.max()
                    oResult = result
                    oAngle = angle
                    oThresh = thresh
                    oScale = scale
                    if wBest > 0.85: # We are most likely good!
                        break

    if wBest > 0.75 and wBest < 0.85:  # We are close but not certain
        thresholds = np.linspace(oThresh-20, oThresh+20, 1) # Three samples
        angles = np.arange(oAngle-3, oAngle+3, 1.0) # Step of 20
        scales = np.linspace(oScale-0.1, oScale+0.1, 3)

        for scale in scales:
            (r,c) = wGrayTemplate.shape
            wResizeTemplate = cv2.resize(wGrayTemplate, (int(c * scale), int(r * scale)))
            for thresh in thresholds:
                for angle in angles:
                    NewCamImageBW = rotate_image2(wGrayImage, angle)
                    #ret, threshMAX = cv2.threshold(NewCamImageBW, thresh, 255, cv2.THRESH_BINARY)
                    #result = template_matching(threshMAX, wGrayTemplate)
                    result = template_matching(NewCamImageBW, wResizeTemplate)
                    if result.max() > wBest:
                        wBest = result.max()
                        oResult = result
                        oAngle = angle
                        oThresh = thresh

    return oResult, oAngle, oThresh, oScale

def PromptUserKey(iPrompt):
    return PromptUserChoice(iPrompt, True)

def PromptUser(iPrompt):
    return PromptUserChoice(iPrompt, False)

def PromptUserChoice(iPrompt, ibSingleKey):
    # Create a blank image to display text input prompt
    wWindowName = iPrompt
    prompt_image = np.ones((100, 400, 3), np.uint8) * 255
    cv2.putText(prompt_image, iPrompt, (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)

    # Display the prompt image in a window
    cv2.imshow(wWindowName, prompt_image)
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
        cv2.putText(prompt_image, iPrompt + user_text, (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        cv2.imshow(wWindowName, prompt_image)
        if ibSingleKey and len(user_text)>0:
            break

    cv2.destroyWindow(wWindowName)
    print(user_text)
    return user_text



def decodeCode(image):
    # Try OpenCV QR code detection and decoding
    (r, c, colors) = image.shape
    qrCodeDetector = cv2.QRCodeDetector()
    for testScale in [0.5, 1, 2]: # range(1,2):
        testImage = cv2.resize(image, (int(c * testScale), int(r * testScale)))
        decodedText, points, _ = qrCodeDetector.detectAndDecode(testImage)
        print("QR Detected: ", testScale, decodedText)
        if len(decodedText) > 2:
            return("QR",decodedText)

        # If OpenCV failed, try PyZBar
        decodedObjects = pyzbar.decode(testImage)
        if decodedObjects:
            for obj in decodedObjects:
                print("QR Code Data:", obj.data)
                oText = obj.data.decode('utf-8')
            return "PZ",oText
        print("Pyzbar failed at ", testScale)

    print("No QR code found or unable to decode.")

    wMax = 0.0
    wBestTemplate = gTemplates[0]
    wInfo = []
    for template in gTemplates:
        result, rotateAngle, bestThresh, bestScale = template_matching_best(image, template[0])
        wResult = result.max()
        if wResult > wMax:
            wMax = wResult
            wBestTemplate = template
            wInfo = [wResult, rotateAngle, bestThresh, bestScale]
            print("New Best [", template[1], "] = ", wResult, wInfo)
            if wMax > 0.85: # We are good enough to confirm Definitively
                break
        else:
            print("Template [", template[1], "] = ", wResult)

    cam_number = wBestTemplate[1]

    if wMax > 0.65:
        template_location = find_template_location(result)

        # Draw a rectangle around the found template
        h, w = wBestTemplate[0].shape[:2]
        print("size:",h,w)
        h=int(h*wInfo[3])
        w=int(w*wInfo[3])
        if wInfo[0] > 0.55:
            cv2.rectangle(image, template_location, (template_location[0] + w, template_location[1] + h),
                          (0, 255, 0), 2)
        else:
            cv2.rectangle(image, template_location, (template_location[0] + w, template_location[1] + h),
                          (0, 0, 255), 2)

        '''
        #cv2.imshow("template matching", image)
        NewCamImageBW = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        ret, threshMAX = cv2.threshold(NewCamImageBW, bestThresh, 255, cv2.THRESH_BINARY)
        threshMAX = cv2.merge([threshMAX, threshMAX, threshMAX])
        print("Match: {0}, Thresh {1}, Rotate {2}, Scale {3}".format(result.max(), bestThresh, rotateAngle, bestScale))
        '''
        return "TEMPLATE",cam_number

    return "UNKNOWN", "UNKNOWN"

# Routine to process commands for the G-Code motion system
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

# Callbacks needed for the trackbars, just print out the values
def nothing(x):
    print(x)

# 4/13/2024 Separate out the image analysis portion
def AnalyzeImage(iFullCameraImage):
    global imgROI
    # img = imgRaw
    global r1, r2, c1, c2
    global Black
    imgROI = iFullCameraImage[r1:r2, c1:c2].copy()
    originalROI = imgROI.copy()

    # Black out the Borders to prevent the edges connecting to the contour
    # Should probably detect the edge of the cardboard and just delete that portion
    wBarWidth = 100
    cv2.rectangle(imgROI,(0,0), (wBarWidth,r2-r1), Black, -1) # Left
    cv2.rectangle(imgROI,(0,0), (c2-c1, wBarWidth), Black, -1) # Top
    cv2.rectangle(imgROI,(c2-c1-wBarWidth,0), (c2-c1,r2-r1), Black, -1) #Right
    cv2.rectangle(imgROI,(0,r2-r1-wBarWidth), (c2-c1,r2-r1), Black, -1) # Bottom
    wCornerWidth = 250
    cv2.rectangle(imgROI,(0,0), (wCornerWidth,wCornerWidth), Black, -1) # Top Left
    cv2.rectangle(imgROI,(c2-c1-wCornerWidth,0), (c2-c1, wCornerWidth), Black, -1) # Top Right
    cv2.rectangle(imgROI,(c2-c1-wCornerWidth,r2-r1-wCornerWidth), (c2-c1, r2-r1), Black, -1) # Bottom Right
    cv2.rectangle(imgROI,(0,r2-r1-wCornerWidth), (wCornerWidth, r2-r1), Black, -1) # Bottom Left
    threshMIN = min(max(1, cv2.getTrackbarPos('threshMIN', "Tracking")), 255)
    lineThick = 16
    kernelSize = cv2.getTrackbarPos('kernelSize', "Tracking")
    wPick = cv2.getTrackbarPos("Pick-BW-R-G-B-H-S-V", "Tracking")

    imgRawFull = iFullCameraImage
    global fullHeight, fullWidth, colors
    (fullHeight, fullWidth, colors) = imgRawFull.shape
    cv2.line(imgRaw, (c1, r1), (c1, r2), Green, lineThick)
    cv2.line(imgRaw, (c1, r2), (c2, r2), Green, lineThick)
    cv2.line(imgRaw, (c2, r2), (c2, r1), Green, lineThick)
    cv2.line(imgRaw, (c2, r1), (c1, r1), Green, lineThick)
    titles.append("imgRaw")
    images.append(imgRaw)
    scales.append(0.25)
    (r, c, colors) = imgROI.shape
    scale = wVideoScale
    img = cv2.resize(imgROI, (int(c * scale), int(r * scale)))

    kernelSize = max(1, kernelSize)
    if kernelSize % 2 == 0:
        kernelSize = kernelSize + 1
    kernel = np.ones((kernelSize, kernelSize), np.float32) / (kernelSize * kernelSize)

    imgray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    (imgBlue, imgGreen, imgRed) = cv2.split(img)
    zeros = np.zeros(img.shape[:2], dtype="uint8")

    imhsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    (imgH, imgS, imgV) = cv2.split(imhsv)

    imAnalyze = imgray
    wTitleAnalysis = "Gray"
    if wPick == 0:
        imAnalyze = imgray.copy()
        wTitleAnalysis = "Gray"
    elif wPick == 1:
        imAnalyze = imgRed
        wTitleAnalysis = "Red"
    elif wPick == 2:
        imAnalyze = imgGreen
        wTitleAnalysis = "Green"
    elif wPick == 3:
        imAnalyze = imgBlue
        wTitleAnalysis = "Blue"
    elif wPick == 4:
        imAnalyze = imgH
        wTitleAnalysis = "HSV-Hue"
    elif wPick == 5:
        imAnalyze = imgS
        wTitleAnalysis = "HSV-Saturation"
    elif wPick == 6:
        imAnalyze = imgV
        wTitleAnalysis = "HSV-Value"

    titles.append("1-Analysis")
    images.append(imAnalyze)
    scales.append(0.25)

    ret, threshMIN = cv2.threshold(imAnalyze, threshMIN, 255, cv2.THRESH_BINARY)

    titles.append("2-Threshold")
    images.append(threshMIN)
    scales.append(0.25)

    font = cv2.FONT_HERSHEY_SIMPLEX
    fontScale = 5
    imAnalyze = cv2.putText(imAnalyze, wTitleAnalysis, (40, 200), font, fontScale, 0, 15, cv2.LINE_AA)
    imAnalyze = cv2.putText(imAnalyze, wTitleAnalysis, (40, 200), font, fontScale, 255, 5, cv2.LINE_AA)

    opening = cv2.morphologyEx(threshMIN, cv2.MORPH_OPEN, kernel, 3)
    closing = cv2.morphologyEx(threshMIN, cv2.MORPH_CLOSE, kernel, 3)

    titles.append("3-MORPH_CLOSE")
    images.append(closing)
    scales.append(0.25)

    contours, heirarchy = cv2.findContours(closing, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)

    img_contours = originalROI.copy() #img
    cv2.drawContours(img_contours, contours, -1, Magenta, lineThick)

    titles.append("4-detect_contours")
    images.append(img_contours)
    scales.append(0.25)

    wFound, foundContours, wCamRadius, wCamCenter, wCenterRadius, wCenterCenter, wDrainRadius, wDrainCenter, wRotate = findCamContours(
        contours)
    found_contours = originalROI.copy()
    if wFound:
        rotatedROInoLines = rotate_image(found_contours, wRotate)
        cv2.drawContours(found_contours, foundContours, -1, Red, lineThick)
        #print(wCamCenter, wCamRadius)
        cv2.circle(found_contours, wCamCenter, wCamRadius, Cyan, lineThick)
        cv2.circle(found_contours, wCenterCenter, wCenterRadius, Green, lineThick)
        cv2.circle(found_contours, wDrainCenter, wDrainRadius, Yellow, lineThick)
        cv2.line(found_contours, wDrainCenter, wCenterCenter, White, lineThick)
        rotatedROI = rotate_image(found_contours, wRotate)
        titles.append("6-Rotated ROI")
        images.append(rotatedROI)
        scales.append(0.25)

        #rotatedThresh = rotate_image(threshMIN, wRotate)
        #titles.append("THRESH KEY")
        #images.append(rotatedThresh)
        #scales.append(1.0)


    else:
        rotatedROInoLines = found_contours
        rotatedROI = found_contours
        titles.append("6-Rotated ROI")
        images.append(found_contours)
        scales.append(0.25)

    titles.append("5-Cams Detected")
    images.append(found_contours)
    scales.append(0.25)

    for i in range(len(titles)):
        scale = scales[i]
        if len(images[i].shape) == 2:
            (r, c) = images[i].shape
        else:
            (r, c, colors) = images[i].shape
        wImage = cv2.resize(images[i], (int(c * scale), int(r * scale)))
        cv2.imshow(titles[i], wImage)

    imgROI = originalROI # Resent to the original ROI
    return wFound, wCamCenter, rotatedROInoLines

def rotate_image(image, angle):
    # Get the dimensions of the image
    height, width = image.shape[:2]

    # Calculate the rotation matrix
    rotation_matrix = cv2.getRotationMatrix2D((width / 2, height / 2), angle, 1)

    # Apply the rotation to the image using warpAffine
    rotated_image = cv2.warpAffine(image, rotation_matrix, (width, height))

    return  rotated_image


# Calculate the angle between two points
def CalcAngle(iPt1, iPt2):
    if CalcDistance(iPt1, iPt2)> 0.0:
        dX = iPt2[0] - iPt1[0]
        dY = iPt2[1] - iPt1[1]
        return 180.0+math.degrees(math.atan2(dY, dX))
    else:
        return 180.0

# Calculate the distance between two points
def CalcDistance(iPt1, iPt2):
    dX = iPt2[0]-iPt1[0]
    dY = iPt2[1]-iPt1[1]

    oDist = math.sqrt(dX*dX + dY*dY)
    return oDist

# Convert a point from floating point to integer values
def intPoint(iPt):
    return (int(iPt[0]),int(iPt[1]))

# Find the specific camshaft contours for a cam
def findCamContours(iContours):
    oContours = iContours
    if len(iContours) > 0:
        oContours = sorted(iContours, key=cv2.contourArea, reverse=True)

    wCount = 0
    wMax = 3
    oList = []
    oFound = False
    oCamDiameter = 0.0
    oCamCenter = (0.0,0.0)
    oCenterCircleCenter = (0.0, 0.0)
    oCenterCircleDiameter = 0.0
    oDrainCenter = (0.0,0.0)
    oDrainDiameter = 0.0
    wMinCenterDistance = 1000.0

    for wContour in oContours:
        wHull = cv2.convexHull(wContour)
        wArea = cv2.contourArea(wContour)

        x, y, w, h = cv2.boundingRect(wContour)
        wCenter = (x+w*0.5,y+h*0.5)
        aspect_ratio = min (float(w) / h, float(h) / w)
        minAspectRatio = 0.75
        avgDiameter = 0.5*(float(w)+float(h))
        circleArea = 3.14159*avgDiameter*avgDiameter/4.0
        wHullArea = cv2.contourArea(wHull)
        minHullAreaRatio = 0.80
        minCircleAreaRatio = 0.80
        maxCircleAreaRatio = 1.15
        if wCount == 0:
            minHullArea = 400000.0
            maxHullArea = 900000.0
        else:
            minHullArea = 5000.0
            maxHullArea = 100000.0
        if wHullArea > 0 and wCount < wMax:
            if (wHullArea > minHullArea):
                if (wHullArea < maxHullArea):
                    #print("Hull Area OK: ", wHullArea)
                    if (wArea/circleArea > minCircleAreaRatio and wArea/circleArea < maxCircleAreaRatio):
                        #print("Circle Area Pass")
                        if (wArea / wHullArea > minHullAreaRatio):
                            #print("Hull Raito Pass")
                            if (aspect_ratio > minAspectRatio):
                                oList.append(wHull)
                                wCount +=1
                                #print("Pass All, Add value: ", wCount, wHullArea)
                                #print("             --------------------")
                                if wCount == 1: # Detect First, should be the CAM
                                    oFound = True
                                    oCamCenter = wCenter
                                    oCamDiameter = avgDiameter
                                    oDrainCenter = wCenter
                                    oDrainDiameter = avgDiameter
                                    oCenterCircleCenter = wCenter
                                    oCenterCircleDiameter = avgDiameter
                                    #print("Cam Area: ",wHullArea)
                                elif wCount == 2: # This is Drain by default
                                    oDrainCenter = wCenter
                                    oDrainDiameter = avgDiameter
                                    wMinCenterDistance = CalcDistance(oCamCenter,wCenter)
                                elif wCount == 3:
                                    if (wMinCenterDistance < CalcDistance(oCamCenter,wCenter)): # First was the center
                                        oCenterCircleCenter = oDrainCenter
                                        oCenterCircleDiameter = oDrainDiameter
                                        oDrainCenter = wCenter
                                        oDrainDiameter = avgDiameter
                                    else: # Need to swap
                                        oCenterCircleCenter = wCenter
                                        oCenterCircleDiameter = avgDiameter

            else:
                pass

    if CalcDistance(oCenterCircleCenter,oDrainCenter) < 200:
        oAngle = 0.0
    else:
        oAngle = CalcAngle(oCenterCircleCenter,oDrainCenter)

    return (oFound, oList[0:min(25,len(iContours))],
            int(oCamDiameter*0.5), intPoint(oCamCenter),
            int(oCenterCircleDiameter*0.5), intPoint(oCenterCircleCenter),
            int(oDrainDiameter*0.5), intPoint(oDrainCenter),
            oAngle)


# Create a trackbar so the user can easily change parameters
cv2.namedWindow('Tracking', cv2.WINDOW_NORMAL)
cv2.resizeWindow('Tracking', 300, 200)
cv2.createTrackbar("threshMIN", "Tracking", 64, 255, nothing) # Was 55
cv2.createTrackbar("kernelSize", "Tracking", 6, 20, nothing)
cv2.createTrackbar("Pick-BW-R-G-B-H-S-V", "Tracking", 2, 6, nothing) # 0 = BW, 2 = Green

# Set the Region of interest on the image
wMultiplier = 1.0 # Use to easily grow or shrink the ROI
midX = 1920
midY = 1080
gWidth = 600*wMultiplier
gHeight = 600*wMultiplier
r1 = int(midY-gHeight)
r2 = int(midY+gHeight)
c1 = int(midX-gWidth)
c2 = int(midX+gWidth)
print(r1,r2,c1,c2)

def ResizeImage(iImage, iX, iY):
    #(r,c,colors) = iImage.shape
    oImage = cv2.resize(iImage, (iX, iY))
    return oImage




wVideoScale = 1.0
if bVideo:
    cap = cv2.VideoCapture(0) # Pick the camera

    cap.set(3, 3840) # Set to 4K resolution
    wXresolution = cap.get(3)
    wYresolution = cap.get(4)
    if (wXresolution != 3840):
        print("Resolution: ", wXresolution, " x ", wYresolution)
        input("Failed to reach desired resoltion")

    cap.set(propId = cv2.CAP_PROP_EXPOSURE, value=-3) # Set initial Exposure

    if (cap.isOpened()):
        ret, imgRaw = cap.read()
        imgRaw = ResizeImage(imgRaw, 3840, 2160)
        img = imgRaw[r1:r2, c1:c2]

else:
    wRAWfileName = wFolder + '\\Raw-' + wBoxNum + "R" + str(scanRow) + "C" + str(scanCol) + ".jpg"
    imgRawFull = cv2.imread(wRAWfileName, 1)  # Color
    scale = 1
    imgROI = imgRawFull[r1:r2, c1:c2]
    imgROI = imgROI.copy()
    imgRaw = imgRawFull.copy()

img = imgRaw[r1:r2, c1:c2]
(roiHeight, roiWidth, colors) = img.shape

fullBoxHeight = roiHeight*boxRows
fullBoxWeight = roiWidth*boxColumns

# Create a black image for capturing the box
fullBoxImage = np.zeros((fullBoxHeight, fullBoxWeight, 3), dtype=np.uint8)

#print(img.shape)
(r, c, colors) = img.shape

cnc = Arduino('com3',bSimulateArduino)
cnc.connect()
cnc.readLine()

initialize = ["$$",
              "$100=28.639", "$110=12000", "$120=300", "$130=800",  # X-Axis, 12V settings
              "$101=28.639", "$111=12000", "$121=200", "$131=800",  # Y-Axis, 12V settings
              "$102=28.639", "$112=12000", "$122=200", "$132=800",  # Z-Axis, 12V settings
              "G0G90", "$", "G1F18000",
              "$$"
              ]
processCommands(initialize)


test = ["$21=0","$22=0", "$5=0"] #"$H"] # No Homing

#$24=50.00   Homing feed rate (mm/min)
#$25=635.00  Homing seek speed (mm/min)
#$26=250     Homing Debounce (msec)
#$27=1       Homing pull-off (mm)

cnc.verbose = True

#test = ["$5=1","$24=500.0","$25=500.0","$26=250","$27=10","$21=1","$22=1", "G28.2 Y"] # Homing
processCommands(test)
test = ["$12=0.002", "$11=0.050", "$10=1"]
processCommands(test)

test = ["X815", "G4 P5", "X0"]
test = ["Y815", "G4 P5", "Y0"]
test = ["G1X-50F3000", "G4 P1", "X0"]
processCommands(test)

xValue = 0
yValue = 0
fValue = 3000
command = "X"+str(xValue)

#num=0
wXoffset = 0
wYoffset = 0

def GetImageAtLocation(iRow, iCol):
    global bVideo, cap, imgRaw, imgROI, fullHeight, fullWidth, colors, fullScale, wVideoScale, img, boxRows
    wRAWfileName = wFolder + '\\Raw-' + wBoxNum + "R" + str(iRow) + "C" + str(iCol) + ".jpg"
    if bVideo:
        if (cap.isOpened()):
            ret, imgRaw = cap.read()
            imgRaw = ResizeImage(imgRaw, 3840, 2160)
            scale = 1
            imgROI = imgRaw[r1:r2, c1:c2].copy()
            (fullHeight, fullWidth, colors) = imgRaw.shape
            fullScale = 1.0
            imgRawFull = imgRaw.copy()
            cv2.line(imgRaw,(c1,r1),(c1,r2),Green,lineThick)
            cv2.line(imgRaw,(c1,r2),(c2,r2),Green,lineThick)
            cv2.line(imgRaw,(c2,r2),(c2,r1),Green,lineThick)
            cv2.line(imgRaw,(c2,r1),(c1,r1),Green,lineThick)
            imgRaw = cv2.resize(imgRaw, (int(fullWidth * fullScale), int(fullHeight * fullScale)))
            (r, c, colors) = imgROI.shape
            scale = wVideoScale
            img = cv2.resize(imgROI, (int(c * scale), int(r * scale)))
    else:
        imgRawFull = cv2.imread(wRAWfileName, 1)  # Color
        scale = 1
        imgROI = imgRawFull[r1:r2, c1:c2]
        imgROI = imgROI.copy()
        imgRaw = imgRawFull.copy()

    y_offset = (boxRows - iRow - 1) * roiHeight
    x_offset = iCol * roiWidth
    # Paste the ROI into the main image
    (r, c, colors) = fullBoxImage.shape
    scale = wFullBoxScale
    BoxImage = cv2.resize(fullBoxImage, (int(c * scale), int(r * scale)))
    cv2.rectangle(BoxImage, (int(x_offset * scale), int(y_offset * scale)),
                  (int((x_offset + roiWidth) * scale), int((y_offset + roiHeight) * scale)), Yellow, 4)
    #cv2.circle(BoxImage, (clickedX, clickedY), 4, Orange, 2)
    cv2.imshow("BOX",BoxImage)
    cv2.setMouseCallback('BOX', click_eventBoxCellClicked)



    return imgRawFull


def DetectCam(imgROIstraightened, bHasCam, ibPauseForInput):
    if bHasCam:
        wMethod, wID = decodeCode(imgROIstraightened)
        wID = wID.upper()
    else:
        wMethod = "CV"
        wID = "NONE"
    if ibPauseForInput and wID == "UNKNOWN":
        wID = PromptUser("Enter Type:")
        wID = wID.upper()
        wMethod = "USER"
    print(wMethod, wID)
    (r, c, colors) = imgROIstraightened.shape
    idScale = 0.25
    IDimage = cv2.resize(imgROIstraightened, (int(c * idScale), int(r * idScale)))
    wIDtext = wMethod + ":" + wID
    cv2.putText(IDimage, wIDtext, (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, Black, int(20*idScale+1))
    cv2.putText(IDimage, wIDtext, (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, White, int(6*idScale+1))
    cv2.imshow("7-Identify", IDimage)
    return wID


def sGotoScanLocation(iRow, iCol, iXoff, iYoff):
    global wCellWidthX, wCellLengthY

    print("goto: ",iRow,iCol,iXoff, iYoff)
    yValue = iRow * wCellLengthY + iYoff
    xValue = -iCol * wCellWidthX + iXoff
    command = "G1Y" + str(yValue) + "Z" + str(yValue)+"X" + str(xValue)+"F1750"
    print(command)
    processCommands([command])
    #while cnc.readLine():
    #    pass
    #cv2.waitKey(1000)

def  moveDigitalBox(iDx, iDy):
    iDx = int(iDx)
    iDy = int(iDy)
    global c1, c2, r1, r2, fullWidth
    if (iDx < 0):
        if (c1+iDx > 0):
            c1 += iDx
            c2 += iDx
    elif ((c2 + iDx + 1) < fullWidth):
        c1 += iDx
        c2 += iDx
    if iDy < 0:
        if (r1 > iDy):
            r1 += iDy
            r2 += iDy
    elif ((r2+iDy+1) < fullHeight):
            r1 += iDy
            r2 += iDy


def MoveDigitalCenter(iCamCenter, ibHasCam):
    if ibHasCam:
        cX = iCamCenter[0]
        cY = iCamCenter[1]
        moveX = cX - 0.5 * (c2 - c1)
        moveY = cY - 0.5 * (r2 - r1)
        print("Moving: ", moveX, moveY)
        moveDigitalBox(moveX, moveY)

def OverlayColor(iImage,iColorName):
    global wGlobalColors
    if iColorName in wGlobalColors:
        wOverlayColor = wGlobalColors[iColorName]
        height, width, _ = iImage.shape

        overlay_image = np.full((height, width, 3), wOverlayColor, dtype=np.uint8)

        # Blend the overlay image with the original image using transparency
        alpha = 0.5  # Transparency level (0.0 - fully transparent, 1.0 - fully opaque)
        oImage = cv2.addWeighted(iImage, 1 - alpha, overlay_image, alpha, 0)
    else:
        oImage = iImage.copy()
    return oImage



def AnalyzeCell(iRow, iCol):

    global bHasCam, wCamCenter, imgROIstraightened, imgRawFull, wCamCenter, imgROI, wCamID
    global roiHeight, scanRow, scanCol, fullBoxImage

    scanRow = iRow
    scanCol = iCol

    for i in range(0, 3):
        bHasCam, wCamCenter, imgROIstraightened = AnalyzeImage(imgRawFull)
        MoveDigitalCenter(wCamCenter, bHasCam)

    wCamID = DetectCam(imgROIstraightened, bHasCam, True)
    wGrid[iRow][iCol] = wCamID
    imgROI = OverlayColor(imgROI, wCamID)
    y_offset = (boxRows - scanRow - 1) * roiHeight
    x_offset = scanCol * roiWidth
    fullBoxImage[y_offset:y_offset + roiHeight, x_offset:x_offset + roiWidth] = imgROI


def AssignImageToBox():
    global scanRow, scanCol, wBoxNum, bVideo, bMasterMind

    name = wFolder + '\\FullBox-' + wBoxNum + ".jpg"
    RAWname = wFolder + '\\Raw-' + wBoxNum + "R" + str(scanRow) + "C" + str(scanCol) + ".jpg"
    if bVideo:  # Write the imae only if we are in video mode
        cv2.imwrite(RAWname, imgRawFull)

    y_offset = (boxRows - scanRow - 1) * roiHeight
    x_offset = scanCol * roiWidth
    # Paste the ROI into the main image
    print("Image:", imgROI.shape)
    print(roiHeight, roiWidth)
    fullBoxImage[y_offset:y_offset + roiHeight, x_offset:x_offset + roiWidth] = imgROI
    if bVideo or bMasterMind:  # Write full box if in game mode or video is live
        cv2.imwrite(name, fullBoxImage)
    else:
        cv2.imwrite(name, fullBoxImage) # normally wouldn't overwrite the full box if cams and simulate

    (r, c, colors) = fullBoxImage.shape
    print("Full Box: ", fullBoxImage.shape)
    scale = wFullBoxScale
    BoxImage = cv2.resize(fullBoxImage, (int(c * scale), int(r * scale)))
    cv2.rectangle(BoxImage, (int(x_offset * scale), int(y_offset * scale)),
                  (int((x_offset + roiWidth) * scale), int((y_offset + roiHeight) * scale)), (0, 255, 255), 1)
    cv2.setMouseCallback('BOX', click_eventBoxCellClicked)
    print(scanRow, scanCol)
# num=num+1


# Continuously loop until "ESC" key is entered
while True:
    titles = []
    images = []
    scales = []
    lineThick = 16
    imgRawFull = GetImageAtLocation(scanRow, scanCol)

    bHasCam, wCamCenter, imgROIstraightened = AnalyzeImage(imgRawFull)

    k = cv2.waitKey(1) & 0xFF
    # Set the digigal move based on upper case or lower case
    if k < ord('a'):
        wMoveStep = int(wDigitalStep * 0.15)
    else:
        wMoveStep = wDigitalStep

    if k == 27:
        break
    elif k==ord('E') or k==ord('e'): # E for Every Opening inn the Box
        print("Scanning Every Cell:")
        wCamCountTotals = {}
        bNewRow = True
        wBoxCount = 0
        wCellCount = 0
        cv2.waitKey(1)
        bFirstCell = True # Skip the pause on the first cell
        wGrid = [["NONE" for j in range(boxColumns)] for i in range(boxRows)]
        for wRow in range(0,boxRows):
            bNewRow = True # Takes a bit longer to move Y than X
            if wRow % 2 == 0:
                wRange = range(0,boxColumns)
            else:
                wRange = range(boxColumns-1, -1, -1)
            for wCol in wRange:
                wCellCount += 1
                print(f"Row {wRow}, Col {wCol}")
                sGotoScanLocation(wRow, wCol, wXoffset, wYoffset)
                imgRawFull = GetImageAtLocation(wRow, wCol)
                if bNewRow:
                    bNewRow = False
                    if not bFirstCell:
                        cv2.waitKey(cPauseRowChange)
                    bFirstCell = False
                else:
                    cv2.waitKey(cPauseColumnChange)
                imgRawFull = GetImageAtLocation(wRow, wCol)
                # For best results we need to center the ROI on the detected canter of the cam
                for wCenterCount in range(0,3): # Ceenter the cam threee times
                    bHasCam, wCamCenter, imgROIstraightened = AnalyzeImage(imgRawFull)
                    MoveDigitalCenter(wCamCenter, bHasCam)
                bHasCam, wCamCenter, imgROIstraightened = AnalyzeImage(imgRawFull)
                # Identify what type of cam it is:
                wCamID = DetectCam(imgROIstraightened, bHasCam, False)
                if wCamID in wCamCountTotals: # Is this cam key in the dictionary already?
                    wCamCountTotals[wCamID] = wCamCountTotals[wCamID] + 1
                else:
                    wCamCountTotals[wCamID] = 1
                wGrid[wRow][wCol]=wCamID
                if bHasCam:
                    imgROI = OverlayColor(imgROI,wCamID)
                    wBoxCount += 1

                cv2.waitKey(1)
                #DetectCam(imgROIstraightened)
                scanRow = wRow
                scanCol = wCol
                name = wFolder + '\\FullBox-' + wBoxNum + ".jpg"
                RAWname = wFolder + '\\Raw-' + wBoxNum + "R" + str(scanRow) + "C" + str(scanCol) + ".jpg"
                if bVideo:  # Only write images if in full box mode!
                    cv2.imwrite(RAWname, imgRawFull)

                y_offset = (boxRows - scanRow - 1) * roiHeight
                x_offset = scanCol * roiWidth
                # Paste the ROI into the main image
                print("Image:", imgROI.shape)
                print(roiHeight, roiWidth)

                fullBoxImage[y_offset:y_offset + roiHeight, x_offset:x_offset + roiWidth] = imgROI
                if bVideo:  # Only write the image if we are reading images
                    cv2.imwrite(name, fullBoxImage)
                (r, c, colors) = fullBoxImage.shape
                print("Full Box: ", fullBoxImage.shape)
                scale = wFullBoxScale
                BoxImage = cv2.resize(fullBoxImage, (int(c * scale), int(r * scale)))
                cv2.rectangle(BoxImage, (int(x_offset * scale), int(y_offset * scale)),
                              (int((x_offset + roiWidth) * scale), int((y_offset + roiHeight) * scale)), (0, 255, 255),
                              1)
                cv2.setMouseCallback('BOX', click_eventBoxCellClicked)
                font = cv2.FONT_HERSHEY_SIMPLEX
                fontScale = 4

                BoxImage = cv2.putText(BoxImage, str(wBoxCount), (80, 250), font, fontScale, Green, 10, cv2.LINE_AA)
                cv2.imshow("BOX Count",BoxImage)
                print(scanRow, scanCol)
                #num = num + 1


    elif k == ord('V') or k == ord('v'):  # Camshaft Center
        bFirstCamCentering = True
        if bHasCam:
            if bFirstCamCentering:
                bFirstCamCentering = False
                print("----------------------")
                MoveDigitalCenter(wCamCenter, bHasCam)
                bHasCam, wCamCenter, imgROIstraightened = AnalyzeImage(imgRawFull)
                MoveDigitalCenter(wCamCenter, bHasCam)
                bHasCam, wCamCenter, imgROIstraightened = AnalyzeImage(imgRawFull)
                MoveDigitalCenter(wCamCenter, bHasCam)
                bHasCam, wCamCenter, imgROIstraightened = AnalyzeImage(imgRawFull)
    elif k == ord('A') or k == ord('a'):
        if (c1>wMoveStep):
            c1 -= wMoveStep
            c2 -= wMoveStep
        else:
            wMove = c1
            c1 -= wMove
            c2 -= wMove
    elif k == ord('S') or k == ord('s'):
        #input("Enter")
        if ((c2+wMoveStep+1) < fullWidth):
            c1 += wMoveStep
            c2 += wMoveStep
        else:
            wMove = fullWidth - c2 - 1
            c1 += wMove
            c2 += wMove
    elif k == ord('W') or k == ord('w'):
        if (r1 > wMoveStep):
            r1 -= wMoveStep
            r2 -= wMoveStep
        else:
            wMove = r1
            r1 -= wMove
            r2 -= wMove
    elif k == ord('Z') or k == ord('z'):
        if ((r2+wMoveStep+1) < fullHeight):
            r1 += wMoveStep
            r2 += wMoveStep
        else:
            wMove = fullHeight - r2 - 1
            r1 += wMove
            r2 += wMove
    elif k == ord('1'):
        cap.set(propId=cv2.CAP_PROP_EXPOSURE, value=-1)
    elif k == ord('2'):
        cap.set(propId=cv2.CAP_PROP_EXPOSURE, value=-2)
    elif k == ord('3'):
        cap.set(propId=cv2.CAP_PROP_EXPOSURE, value=-3)
    elif k == ord('4'):
        cap.set(propId=cv2.CAP_PROP_EXPOSURE, value=-4)
    elif k == ord('5'):
        cap.set(propId=cv2.CAP_PROP_EXPOSURE, value=-5)
    elif k == ord('6'):
        cap.set(propId=cv2.CAP_PROP_EXPOSURE, value=-6)
    elif k == ord('7'):
        cap.set(propId=cv2.CAP_PROP_EXPOSURE, value=-7)
    elif k == ord('8'):
        cap.set(propId=cv2.CAP_PROP_EXPOSURE, value=-8)
    elif k == ord('9'):
        cap.set(propId=cv2.CAP_PROP_EXPOSURE, value=-9)
    elif k == ord('0'):
        cap.set(propId=cv2.CAP_PROP_EXPOSURE, value=0)

    elif k == ord('r') or k == ord('R'): # Generate Report
        #cv2.imwrite(wReportFileName, fullBoxImage)
        #upload_to_drive('Report', wReportFileName, False)
        print("Box Totals: ",wCamCountTotals)
        for key, value in wCamCountTotals.items():
            print(key, "->", value)
        for wRow in wGrid:
            print(wRow)
        print("Total Cams: ",wBoxCount)
        reversed_wGrid = list(reversed(wGrid))
        reportBoxNum = PromptUser("Enter Box Number:")
        generateReport(f'BoxTemplates\\FullBox-{wBoxNum}.jpg', reversed_wGrid, reportBoxNum, folder_id)

    elif k == ord('c') or k == ord('C'): # Pick a Color
        wPick = PromptUserKey("Color (RGBYOP):")
        wPick = wPick.upper()

        if wPick == "P":
            RAWname = wFolder + '\\Color-Purple.jpg'
            imgRawFull = cv2.imread(RAWname)
        elif wPick == "B":
            RAWname = wFolder + '\\Color-Blue.jpg'
            imgRawFull = cv2.imread(RAWname)
        elif wPick == "Y":
            RAWname = wFolder + '\\Color-Yellow.jpg'
            imgRawFull = cv2.imread(RAWname)
        elif wPick == "R":
            RAWname = wFolder + '\\Color-Red.jpg'
            imgRawFull = cv2.imread(RAWname)
        elif wPick == "O":
            RAWname = wFolder + '\\Color-Orange.jpg'
            imgRawFull = cv2.imread(RAWname)
        elif wPick == "G":
            RAWname = wFolder + '\\Color-Green.jpg'
            imgRawFull = cv2.imread(RAWname)
        else:
            RAWname = wFolder + '\\Color-Blank.jpg'
            imgRawFull = cv2.imread(RAWname)
        print("New Image:", RAWname)
        #cv2.imshow("New Image:", imgRawFull)

        bHasCam, wCamCenter, imgROIstraightened = AnalyzeImage(imgRawFull)
        RAWname = wFolder + '\\Raw-' + wBoxNum + "R" + str(scanRow) + "C" + str(scanCol) + ".jpg"
        cv2.imwrite(RAWname, imgRawFull)
        AssignImageToBox()

    elif k == ord('t') or k == ord('T'): # Load a blank box
        RAWname = wFolder + '\\Color-Blank.jpg'
        imgRawFull = cv2.imread(RAWname)

        wGrid = [["NONE" for j in range(boxColumns)] for i in range(boxRows)]
        for wR in range(0,boxRows):
            print("Row:", wR)
            for wC in range(0, boxColumns):
                RAWname = wFolder + '\\Raw-' + wBoxNum + "R" + str(wR) + "C" + str(wC) + ".jpg"
                cv2.imwrite(RAWname, imgRawFull)

        if bMasterMind:
            RAWname = wFolder + '\\FullBox-Game-Blank.jpg'
            fullBoxImage = cv2.imread(RAWname)
        else:
            RAWname = wFolder + '\\FullBox-Cams-Blank.jpg'
            fullBoxImage = cv2.imread(RAWname)

        name = wFolder+'\\FullBox-' + wBoxNum + ".jpg"
        cv2.imwrite(name, fullBoxImage)
    elif k == ord(' '):
        AssignImageToBox()
    elif k == ord('G'): # Start a Game
        wGameRow = 0
        scanRow = 0
        scanCol = 0
        game.newCode()
    elif k == ord('g'): # Guess The Row
        for wCol in range(0, boxColumns):
            sGotoScanLocation(scanRow, wCol, wXoffset, wYoffset)
            imgRawFull = GetImageAtLocation(scanRow, wCol)
            bHasCam, wCamCenter, imgROIstraightened = AnalyzeImage(imgRawFull)
            AnalyzeCell(scanRow, wCol)
        print("Guess Row {}:{}".format(scanRow,wGrid[scanRow]))
        wBlack, wWhite = game.guess(wGrid[scanRow],scanRow)
        (r, c, colors) = fullBoxImage.shape
        scale = wFullBoxScale*1.75
        wTempBoxImage = cv2.resize(fullBoxImage, (int(c * scale), int(r * scale)))
        (r, c, colors) = wTempBoxImage.shape

        wGameTemplateFile = wFolder + '\\Score-Blank.jpg'
        wGameTemplate = cv2.imread(wGameTemplateFile,1)
        wResultX = 575
        wResultY = 675
        wGameTemplate[wResultY:wResultY + r, wResultX:wResultX + c] = wTempBoxImage
        #cv2.imshow("Game Template", wGameTemplate)
        # Add the scores:

        wResults = game.getResults()
        print("Results:",wResults)
        for i in range(0,9):
            wColors = []
            wBlack = wResults[i][0]
            wWhite = wResults[i][1]
            for j in range(0, wBlack):
                wColors.append(Black)
            for j in range(0, wWhite):
                wColors.append(Orange)

            wRow = 900+500+100+45
            wCol = 1500+200+400+320-(i+9-boxRows)*210
            wRadius = 25
            wSpace = 90
            wCenters = []
            wCenters.append((wRow, wCol))
            wCenters.append((wRow+wSpace, wCol))
            wCenters.append((wRow, wCol+wSpace))
            wCenters.append((wRow+wSpace, wCol+wSpace))
            n = 0
            for color in wColors:
                wCenter = wCenters[n]
                cv2.circle(wGameTemplate, wCenter, wRadius + 5, Black, -1)
                cv2.circle(wGameTemplate, wCenter, wRadius, color, -1)
                n=n+1
        # This is where the full res image needs to be saved!
        (r, c, colors) = wGameTemplate.shape


        scale = 0.40
        wGameTemplate = cv2.resize(wGameTemplate, (int(c * scale), int(r * scale)))

        cv2.imshow("Game", wGameTemplate)
        cv2.imwrite(wReportFileName, wGameTemplate)
        upload_to_drive('Report', wReportFileName, False)

        wGameRow = min(boxRows -1, scanRow+1)
        scanRow = wGameRow
        scanCol = 0
    elif k == ord('k'):  # left
        scanCol = min(boxColumns - 1, scanCol + 1)
        sGotoScanLocation(scanRow, scanCol, wXoffset, wYoffset)
    elif k == ord('j'): # Right Arrow ord("4"):
        scanCol = max(0, scanCol - 1)
        sGotoScanLocation(scanRow, scanCol, wXoffset, wYoffset)
    elif k == ord('i'): #82: # Up Arrow ord("Q") or k == ord("q"):
        scanRow = min(boxRows - 1, scanRow + 1)
        sGotoScanLocation(scanRow, scanCol, wXoffset, wYoffset)
    elif k == ord('m'): # Down Arroword("A") or k == ord("a"):
        scanRow = max(0, scanRow - 1)
        sGotoScanLocation(scanRow, scanCol, wXoffset, wYoffset)
    elif k == ord("J"):
        wXoffset += 2
        sGotoScanLocation(scanRow, scanCol, wXoffset, wYoffset)
    elif k == ord("K"):
        wXoffset -= 2
        sGotoScanLocation(scanRow, scanCol, wXoffset, wYoffset)
    elif k == ord("I"):
        wYoffset += 2
        sGotoScanLocation(scanRow, scanCol, wXoffset, wYoffset)
    elif k == ord("M"):
        wYoffset -= 2
        sGotoScanLocation(scanRow, scanCol, wXoffset, wYoffset)
    elif k == ord("Z") or k==ord("z"):
        scanRow = 0
        scanCol = 0

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
    elif k == ord('b') or k == ord('B'):
        AnalyzeCell(scanRow,scanCol)

    elif k == ord('n') or k == ord('N'):
        wGrid = [[0 for j in range(boxColumns)] for i in range(boxRows)]
        name = wFolder+'\\FullBox-' + wBoxNum + ".jpg"
        fullBoxImage = cv2.imread(name, 1)

    else:
        if (k!= 255) and (k!=13) and (k!=0):
            print(k)

    if globalCickCell:
        globalCickCell = False
        scanRow = boxRows-int((float(clickedY)/wFullBoxScale)/roiHeight)-1
        scanCol = int((float(clickedX)/wFullBoxScale)/roiWidth)
        sGotoScanLocation(scanRow, scanCol, wXoffset, wYoffset)
        print("Clicked: ", clickedX, clickedY, scanRow, scanCol, roiHeight, roiWidth)


if bVideo:
    cap.release()
cv2.destroyAllWindows()
