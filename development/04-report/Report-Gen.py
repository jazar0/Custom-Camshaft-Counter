import cv2
import numpy as np

def generate_report(image_path, array, template_path):
    # Load the image
    image = cv2.imread(image_path)

    # Get dimensions
    image_h, image_w, _ = image.shape

    # dimensions to fit on paper
    new_height = int(image_h / 3.5)
    new_width = int(image_w / 3.5)

    # Resize image
    resized_image = cv2.resize(image, (new_width, new_height))

    # Load the template image
    template = cv2.imread(template_path)

    # Get dimensions of the template image
    template_h, template_w, _ = template.shape

    # Calculate the coordinates to place the resized image in the center of the template
    x_offset = (template_w - new_width) // 2
    y_offset = (template_h - new_height) // 2

    # Paste the resized image onto the template
    template[y_offset:y_offset+new_height, x_offset:x_offset+new_width] = resized_image

    # Get dimensions of array
    num_rows, num_cols = len(array), len(array[0])

    # Calculate slot dimensions
    slot_height = new_height // num_rows
    slot_width = new_width // num_cols

    # Color code with lower opacity rectangle
    for i in range(num_rows):
        for j in range(num_cols):
            # Find coordinates of current slot
            top_left_x = x_offset + j * slot_width
            top_left_y = y_offset + i * slot_height
            bottom_right_x = x_offset + (j + 1) * slot_width
            bottom_right_y = y_offset + (i + 1) * slot_height
            
            # Get the value of the current slot
            value = array[i][j]

            # If value is 6, continue to next slot
            if value == 6:
                continue

            # Corresponding colors
            color_map = {
                0: (255, 0, 0),    # Blue
                1: (128, 0, 128),  # Purple
                2: (0, 0, 255),    # Red
                3: (0, 255, 255),  # Yellow
                4: (0, 255, 0),    # Green
                5: (0, 165, 255)   # Orange
            }
            color = color_map.get(value, (0, 0, 0))  # Default to black if color is not found

            # Create a semi-transparent rectangle of the corresponding color
            overlay = template.copy()
            cv2.rectangle(overlay, (top_left_x, top_left_y), (bottom_right_x, bottom_right_y), color, -1)  # -1 fills the rectangle
            alpha = 0.4  # Opacity level
            cv2.addWeighted(overlay, alpha, template, 1 - alpha, 0, template)

    # Show the template image with the resized image and color coding in the middle
    cv2.imshow('Output Image', template)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    return template

array = [[1, 5, 4, 2],
         [4, 5, 2, 1],
         [2, 5, 1, 4],
         [4, 1, 5, 4]]

resized = generate_report('4x4.png', array, 'LSM-Report-Blank.jpg')
cv2.imwrite('output_image.jpg', resized)
