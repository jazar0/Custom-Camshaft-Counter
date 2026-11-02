from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.pdfbase.pdfmetrics import registerFont
from reportlab.pdfbase.ttfonts import TTFont
registerFont(TTFont('Arial','ARIAL.ttf'))
import cv2
import numpy as np
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import qrcode
from datetime import datetime

def authenticate():
    gauth = GoogleAuth()
    # Try to load saved credentials
    gauth.LoadCredentialsFile("credentials.txt")
    if gauth.credentials is None:
        # No credentials saved, authenticate via local webserver
        gauth.LocalWebserverAuth()
        gauth.SaveCredentialsFile("credentials.txt")
    elif gauth.access_token_expired:
        # Refresh token if expired
        gauth.Refresh() 
    else:
        # Authenticate with saved credentials
        gauth.Authorize()
    return GoogleDrive(gauth)

drive = authenticate()

def generateReport(image_path, array, boxnum, folder_id):
    
    drive = authenticate()  
    dummy_file = drive.CreateFile({'title': f"Box-Report-{boxnum}.pdf", 'parents': [{'id': folder_id}]})
    dummy_file.Upload()
    dummy_link = dummy_file['alternateLink']
    dummy_file_id = dummy_file['id']
      # generate qr code
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
    qr.add_data(dummy_link)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    
    qr_img.save("generatedqr.png")
    print("Status: Dummy File Created and QR saved")

    #BEGIN COLOR CODING CODE

    # load in the fullbox
    image = cv2.imread(image_path)

    # get fullbox dimensions
    image_h, image_w, _ = image.shape

    # resize (scale factor 11 best for pdf)
    resized_image = cv2.resize(image, (image_w // 11, image_h // 11))

    # declare counts for each value 0-7 (key for each value below)
    counts = {"BLUE": 0, "PURPLE": 0, "RED": 0, "YELLOW": 0, "GREEN": 0, "ORANGE": 0, "UNKNOWN": 0, "NONE": 0}

    # calculate dimensions for each slot by dividing the height by the amount of rows in arrays and the width by the amount of columns in array
    resized_h, resized_w, _ = resized_image.shape
    num_rows, num_cols = len(array), len(array[0])
    slot_height = resized_h // num_rows
    slot_width = resized_w // num_cols

    # color code with lower opacity rectangle
    for i in range(num_rows):
        for j in range(num_cols):
            # Find coords of current slot
            top_left_x = j * slot_width
            top_left_y = i * slot_height
            bottom_right_x = (j + 1) * slot_width
            bottom_right_y = (i + 1) * slot_height
            
            # get the value of the current slot
            value = array[i][j]

            # Update counts
            if value != "NONE":
                # Increase total of this specific type of camshaft
                counts[value] += 1
            else:
                # Increment the count for "NONE"
                counts["NONE"] += 1
            # corresponding colors
            color_map = {
                "BLUE": (255, 0, 0),    # Blue
                "PURPLE": (128, 0, 128),  # Purple
                "RED": (0, 0, 255),    # Red
                "YELLOW": (0, 255, 255),  # Yellow
                "GREEN": (0, 255, 0),    # Green
                "ORANGE": (0, 165, 255),  # Orange
                "UNKNOWN": (255, 255, 255) # White (Undefined)
                #NOTE: 7 is not listed here as instead of doing anything, it just doesnt apply any effect to the slot. the code handling 7 is above
            }
            color = color_map.get(value, (0, 0, 0))  # Default to black if color is not found

            # Create a rectangle of the corresponding color, which is combined with original image at a lower opacity
            overlay = resized_image.copy()
            cv2.rectangle(overlay, (top_left_x, top_left_y), (bottom_right_x, bottom_right_y), color, -1)  # -1 fills the rectangle
            alpha = 0.4  # Opacity level
            cv2.addWeighted(overlay, alpha, resized_image, 1 - alpha, 0, resized_image)

            #calculate total cams (adds all values except for 7), to list later on in code
    total_cams = sum(counts[color] for color in counts if color != "NONE")

    #save color image to disk for pdf generation later
    cv2.imwrite('color.jpg', resized_image)
    print("Status: Color Coded Box Image Created")

        #BEGIN PDF GENERATION CODE

    # Create a canvas 
    c = canvas.Canvas(f"Box-Report-{boxnum}.pdf", pagesize=letter)

    # draw the background image without scaling
    background_image = "LSM-TEMPLATE.jpg"
    c.drawImage(background_image, 0, 0, width=letter[0], height=letter[1])


    # Draw the input image with scaling
    report_image = "color.jpg"

    # Set width and height for the image (help resize color coded image to work on the pdf)
    c.drawImage(report_image, 124, 300, width=350, height=350) 

    qr_image = "generatedqr.png"

    # Set width and height for the image (help resize color coded image to work on the pdf)
    c.drawImage(qr_image, 465, 105, width=125, height=125) 
    c.setFont("Arial", 33)
    c.drawString(80, 678, f"{boxnum}")  # write box number based on boxnum variable

    today_date = datetime.now().strftime("%m/%d/%Y")    
    c.drawString(133, 713, today_date)

    c.setFont("Arial", 23)
    # Draw the text with variable counts from array and total_cams variable calculated earlier
    c.drawString(120, 270, f"Blue Cams: {counts['BLUE']}")   
    c.drawString(120, 245, f"Purple Cams: {counts['PURPLE']}")   
    c.drawString(120, 220, f"Red Cams: {counts['RED']}")   
    c.drawString(120, 195, f"Yellow Cams: {counts['YELLOW']}")   
    c.drawString(120, 170, f"Green Cams: {counts['GREEN']}")   
    c.drawString(120, 145, f"Orange Cams: {counts['ORANGE']}")   
    c.drawString(120, 120, f"Unknown Cams: {counts['UNKNOWN']}")  
    c.drawString(120, 95, f"Empty Cams: {counts.get('NONE', 0)}")
    c.drawString(120, 70, f"Total Cams: {total_cams}")  


    # save pdf
    c.save()
    print("Status: PDF Saved")
    file = drive.CreateFile({'id': dummy_file_id})
    file.SetContentFile(f"Box-Report-{boxnum}.pdf")
    file.Upload()
    print("Status: Dummy File Overwritten with PDF")
    print("Status: Complete!")

#array with correct value inputs. aligns with current 4x4 image but feel free to test out all the colors, "Unknown", and None    

