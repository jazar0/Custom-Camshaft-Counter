from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import qrcode
import numpy as np
import cv2

# File name that is set via variable (will be identical to the users name that is inputted, just using a placeholder for now)
fileName = "uploaded_image.jpg"
drive = None  # variable to store authenticated googledrive object

def authenticate():
    global drive
    if not drive:
        gauth = GoogleAuth()
        # load saved credentials
        gauth.LoadCredentialsFile("credentials.txt")
        if gauth.credentials is None:
            # no credentials saved, generate file to load them after user authenticates
            gauth.LocalWebserverAuth()
            gauth.SaveCredentialsFile("credentials.txt")
        elif gauth.access_token_expired:
            # refresh in case the token is expired
            gauth.Refresh()
        else:
            # authenticate with saved credentials
            gauth.Authorize()
        drive = GoogleDrive(gauth)
    return drive


def upload_image(drive, image_path, folder_id, iUploadName, ibLeaderBoard):
    if ibLeaderBoard:
        file_id = 'REPLACE_WITH_YOUR_DRIVE_ID' # ID for the leaderboard
        #file_id = 'REPLACE_WITH_YOUR_DRIVE_ID' # LSM-Report Box 123
        file = drive.CreateFile({'title': iUploadName, 'parents': [{'id': folder_id}],'id': file_id})
    else:
        file = drive.CreateFile({'title': iUploadName, 'parents': [{'id': folder_id}]})

    file.SetContentFile(image_path)
    file.Upload()
    print("Uploaded " + iUploadName)
    
    # Get the link to the uploaded file
    link = file['alternateLink']
    print("Link to the uploaded file: " + link)
    print('Uploaded file with ID {}'.format(file['id']))
    # generate qr code
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
    qr.add_data(link)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    
    qr_img.save("generatedqr.png")

    #Add QR code to image
    reportImg = cv2.imread(image_path, 1)
    cv2.imshow("The uploaded report ", reportImg)


    generatedQr = cv2.imread("generatedqr.png")
    cv2.imshow('QR Code', generatedQr)
    cv2.waitKey(0)
    cv2.destroyWindow('QR Code')

def upload_to_drive(iUploadName, iImage_path, ibLeaderBoard):
    # Authenticate
    drive = authenticate()

    # Folder ID (need to select this from the folder in Google Drive)
    folder_id = 'REPLACE_WITH_YOUR_DRIVE_ID'

    print("Image Path Recognized: " + iImage_path)

    # Upload the image
    upload_image(drive, iImage_path, folder_id, iUploadName, ibLeaderBoard)

# Set the parameter to any file path you want, currently using a placeholder already in the folder

def main():
    fileName = "C3-Mastermine-LeaderBoard.jpg"
    # upload_to_drive('F:\\Box124\\FullBox-124.jpg')

    # while True:
    #    upload_to_drive('F:\\LeaderBoard.jpg')

    fileName = "LSM-Report-Box123.jpg"
    #upload_to_drive('F:\\LSM-Report-Box123.jpg')
    upload_to_drive('My Test File','F:\\test.jpg', False)

if __name__ == "__main__":
    main()


#upload_to_drive('F:\\Box124\\Raw-124R0C2.jpg')

#upload_to_drive('Jurius_ID.png')
