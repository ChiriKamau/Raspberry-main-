import cv2
import firebase_admin
from firebase_admin import credentials, storage, auth
import datetime
import time
import os

# Determine absolute path to firebase-adminsdk.json
ABSOLUTE_PATH = '/home/lima/Raspberry/firebase-adminsdk.json'  # Replace with your actual absolute path

# Initialize Firebase Admin SDK
cred = credentials.Certificate(ABSOLUTE_PATH)
firebase_admin.initialize_app(cred, {
    'storageBucket': 'espcam-69f58.appspot.com'
})

def get_uid_from_email(email):
    try:
        user = auth.get_user_by_email(email)
        return user.uid
    except firebase_admin.auth.AuthError as e:
        print(f"Error getting user: {e}")
        return None

def is_daytime():
    now = datetime.datetime.now()
    # Assuming daytime is between 6 AM and 6 PM
    return 6 <= now.hour < 18

def create_farm_images_folder():
    """Create the farm_images folder if it doesn't exist"""
    folder_path = "farm_images"
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        print(f"Created folder: {folder_path}")
    return folder_path

def take_and_upload_image(uid):
    if not is_daytime():
        print("It's not daytime. Skipping image capture.")
        return

    # Initialize the camera
    camera = cv2.VideoCapture(0)
    
    if not camera.isOpened():
        print("Error: Unable to open camera.")
        return
    
    ret, frame = camera.read()
    
    if not ret:
        print("Error: Unable to capture frame.")
        camera.release()
        return
    
    # Generate a filename based on the current timestamp
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"{timestamp}.jpg"
    
    # Create farm_images folder
    folder_path = create_farm_images_folder()
    local_file_path = os.path.join(folder_path, filename)
    
    # Save the captured image locally with increased quality
    quality = 99  # You can adjust this value as needed
    cv2.imwrite(local_file_path, frame, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
    print(f"Image saved locally: {local_file_path}")
    
    # Encode image for Firebase upload
    _, img_encoded = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
    
    # Release the camera
    camera.release()
    
    # Upload the image to Firebase Storage
    try:
        bucket = storage.bucket()
        blob = bucket.blob(f"images/{uid}/{filename}")
        blob.upload_from_string(img_encoded.tobytes(), content_type='image/jpeg')
        print(f"Image '{filename}' uploaded to Firebase Storage.")
    except Exception as e:
        print("Error uploading image to Firebase Storage:", str(e))

# Main execution
if __name__ == "__main__":
    print("Starting the image capture script...")
    
    # Check if Firebase credentials file exists
    if not os.path.exists(ABSOLUTE_PATH):
        print(f"Error: Firebase credentials file not found at {ABSOLUTE_PATH}")
        exit(1)
    
    email = "chiri.levisk@gmail.com"
    print(f"Looking up user with email: {email}")
    
    try:
        uid = get_uid_from_email(email)
        if uid:
            print(f"User found. UID: {uid}")
            
            # Test camera first
            print("Testing camera connection...")
            camera = cv2.VideoCapture(0)
            if not camera.isOpened():
                print("Error: Camera not accessible. Please check camera connection.")
                exit(1)
            camera.release()
            print("Camera test successful.")
            
            # Loop to capture an image and upload it to Firebase every 4 minutes (240 seconds)
            print("Starting image capture loop...")
            while True:
                take_and_upload_image(uid)
                print("Waiting 4 minutes before next capture...")
                time.sleep(240)
        else:
            print("User not found. Exiting.")
    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()