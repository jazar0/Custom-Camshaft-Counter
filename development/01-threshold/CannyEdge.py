import cv2
import numpy as np

#load image
image = cv2.imread('IMG_3937.jpg')
image = cv2.resize(image, (480, 640))

#make image grayscale
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

#threshold the image
_, thresholded = cv2.threshold(gray, 100, 255, cv2.THRESH_BINARY)

#morph binary image
kernal = np.ones((2,2), np.uint8)
dilation = cv2.dilate(thresholded, kernal, iterations=5)

#turn all black pixels green and white pixels black
inverted_binary = cv2.bitwise_not(dilation)
green_image = np.zeros_like(image)
green_image[inverted_binary > 0] = [0, 255, 0]   



#show different images
cv2.imshow('Green Image', green_image)
cv2.imshow("dilation", dilation)
cv2.imshow("threshold", thresholded)
cv2.waitKey(0)
cv2.destroyAllWindows()
