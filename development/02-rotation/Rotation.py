import cv2
import numpy as np
import pyzbar.pyzbar as pyzbar

def decodeCode(image):
    # Try OpenCV QR code detection and decoding
    qrCodeDetector = cv2.QRCodeDetector()
    decodedText, points, _ = qrCodeDetector.detectAndDecode(image)
    if decodedText:
        print("QR Code Data:", decodedText)
        return

    # If OpenCV failed, try PyZBar
    decodedObjects = pyzbar.decode(image)
    if decodedObjects:
        for obj in decodedObjects:
            print("QR Code Data:", obj.data)
        return

    print("No QR code found or unable to decode.")

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


def main():
    # Load the image
    image = cv2.imread("roi2.png")
    # Find circles in the image
    circles = find_circles(image)
    cv2.waitKey(0)
    if circles is not None:
        if len(circles) >= 2:
            # Display circles detected
            circle_image = image.copy()
            for (x, y, r) in circles:
                cv2.circle(circle_image, (x, y), r, (0, 255, 0), 4)
            cv2.imshow("Circles Detected", circle_image)
            cv2.waitKey(0)
            
            # Calculate rotation angle
            circle_centers = circles[:, :2]
            rotation_angle = calculate_rotation_angle(circle_centers) 
            print("Rotation angle:", rotation_angle)
            
            # Draw line between circles
            line_image = image.copy()
            cv2.line(line_image, tuple(circle_centers[0]), tuple(circle_centers[1]), (0, 0, 255), 2)

            # Define the starting point of the line
            start_point = (100, 100)

            # Define the vector [1, 0]
            vector = np.array([1, 0])

            # Scale the vector for visualization
            scaled_vector = vector * 100

            # Calculate the end point of the line
            end_point = (start_point[0] + scaled_vector[0], start_point[1] + scaled_vector[1])

            # Draw the line on the image
            cv2.line(line_image, start_point, end_point, (0, 255, 0), 2)
            cv2.imshow("Line Drawn", line_image)
            cv2.waitKey(0)
            
            # Rotate the image
            rotated_image = rotate_image(image, rotation_angle)
            
            # Display the original and rotated images
            cv2.imshow("Original Image", image)
            cv2.imshow("Rotated Image", rotated_image)

            cv2.waitKey(0)
            cv2.destroyAllWindows()
            decodeCode(rotated_image)
            
            #add qr detection code on rotated image
        else:
            print("less than 2 circles detected")
    else:
        print("Circles not detected/multiple circles present")

main()