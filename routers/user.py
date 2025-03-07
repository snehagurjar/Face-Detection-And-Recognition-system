from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session
from db import SessionLocal
from models import User
from schemas import UserCreate, UserResponse
from utils import save_image, start_face_recognition
from typing import List

router = APIRouter()

# Database session dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create user endpoint
@router.post("/users/", response_model=UserResponse)
async def create_user(username: str, photo: UploadFile = File(...), db: Session = Depends(get_db)):
    file_location = save_image(photo)
    user = User(username=username, photo=file_location)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

# Get all users endpoint
@router.get("/users/", response_model=List[UserResponse])
def get_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return users

# Face recognition endpoint
@router.post("/start-recognition/")
def recognition(db: Session = Depends(get_db)):
    return start_face_recognition(db)
