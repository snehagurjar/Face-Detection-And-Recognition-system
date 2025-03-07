import shutil
from fastapi import UploadFile
import os
import uuid
import cv2
import face_recognition
import numpy as np
from datetime import datetime, timedelta,date
from models import RecognisedFaces, UnknownRecognisedFaces, User
from sqlalchemy.orm import Session
# Update the import at the top
from db import SessionLocal
# Rest of the utils.py content remains the same

# Function to save user images
def save_image(file: UploadFile):
    folder_path = 'images'
    os.makedirs(folder_path, exist_ok=True)
    file_location = os.path.join(folder_path, file.filename)

    print("file Location\n",file_location)
    print("-------")
    
    with open(file_location, "wb") as f:
        f.write(file.file.read())  # Save the image
    return file_location

# Function to save unknown images
def save_unknown_image(image):
    uuid_filename = f"{uuid.uuid4()}.jpg"  # Generate unique filename
    path = os.path.join("unknown_recognised_faces", uuid_filename)
    os.makedirs("unknown_recognised_faces", exist_ok=True)
    
    cv2.imwrite(path, image)  # Save the image using OpenCV
    return path

# Function to check if the face is already stored
def is_face_known(encodings, known_encodings, threshold=0.5):
    for known_encoding in known_encodings:
        matches = face_recognition.compare_faces([known_encoding], encodings)
        distances = face_recognition.face_distance([known_encoding], encodings)

        print("matches_unknown\n",matches)
        print("distances_unknow\n",distances)        
        if True in matches and min(distances) < threshold:
            return True
    return False

# Load and encode known faces
def findEncodings(images):
    encodeList = []
    for img in images:
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        encodings = face_recognition.face_encodings(img_rgb)
        if encodings:
            encodeList.append(encodings[0])
    print("encodingList for known\n",encodeList)
    return encodeList

def load_known_faces(db: Session):
    users = db.query(User).all()
    images = []
    classNames = []
    for user in users:
        file_path = user.photo
        if os.path.exists(file_path):
            image = cv2.imread(file_path)
            if image is not None:
                images.append(image)
                classNames.append(user.username)
    print("images\n",images)
    print('\n')
    print("classnames\n",classNames)
    return images, classNames

# Main face recognition function
def start_face_recognition(db: Session):
    images, classNames = load_known_faces(db)
    encodeListKnown = findEncodings(images)
    
    known_unknown_encodings = []  # List to store encodings of unknown faces

    print("knonwn_unknown_encodings\n",known_unknown_encodings)
    print("---------")
    cap = cv2.VideoCapture(0)

    while True:
        success, img = cap.read()
        if not success:
            break
        
        img_small = cv2.resize(img, (0, 0), None, 0.5, 0.5)
        img_rgb = cv2.cvtColor(img_small, cv2.COLOR_BGR2RGB)
        facesInFrame = face_recognition.face_locations(img_rgb)
        encodesInFrame = face_recognition.face_encodings(img_rgb, facesInFrame)

        for encodeFace, faceLoc in zip(encodesInFrame, facesInFrame):
            faceDistances = face_recognition.face_distance(encodeListKnown, encodeFace)
            bestMatchIndex = np.argmin(faceDistances)
            if faceDistances[bestMatchIndex] < 0.5:
                username = classNames[bestMatchIndex]
                print("Username:",username)
                print("----")



                # Check if there's an entry within the last 24 hours
                # last_24_hours = datetime.now() - timedelta(hours=24)
                # existing_entry = db.query(RecognisedFaces).filter(
                #     RecognisedFaces.username == username,
                #     RecognisedFaces.datetime >= last_24_hours
                # ).first()
                
                # Check if an entry exists for today
                existing_entry = db.query(RecognisedFaces).filter(
                    RecognisedFaces.username == username,
                    RecognisedFaces.date == date.today()
                ).first()
                
                print("existing_entry\n",existing_entry)
                print("----------")

                # Only add new entry if none exists for today
                if not existing_entry:
                    new_entry = RecognisedFaces(username=username, datetime=datetime.now(), date=date.today())
                    db.add(new_entry)
                    db.commit()

                y1, x2, y2, x1 = faceLoc
                y1, x2, y2, x1 = y1 * 2, x2 * 2, y2 * 2, x1 * 2
                cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(img, username, (x1 + 6, y2 - 6), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 2)
            else:
                # Check if the unknown face has already been stored
                if not is_face_known(encodeFace, known_unknown_encodings):
                    # Save the unknown face
                    unknown_image_path = save_unknown_image(img_rgb)
                    unknown_entry = UnknownRecognisedFaces(path=unknown_image_path, datetime=datetime.utcnow())
                    db.add(unknown_entry)
                    db.commit()

                    print("unknown_entry\n",unknown_entry)
                    print("------")
                    
                    # Add the encoding of the new unknown face to the known unknown encodings
                    known_unknown_encodings.append(encodeFace)
                    print("known_unknown_encodings\n",known_unknown_encodings)
                y1, x2, y2, x1 = faceLoc
                y1, x2, y2, x1 = y1 * 2, x2 * 2, y2 * 2, x1 * 2
                cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(img, "unknown person", (x1 + 6, y2 - 6), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 2)

        cv2.imshow("Webcam", img)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()