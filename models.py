from sqlalchemy import Column, Integer, String, DateTime, Time, ForeignKey, UniqueConstraint
from db import Base
from sqlalchemy.sql import func
from datetime import datetime
from sqlalchemy.orm import relationship

class RecognisedFaces(Base):
    __tablename__ = "recognised_faces"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, ForeignKey("users.username"))
    datetime = Column(DateTime, default=func.now())
    date = Column(DateTime, default=func.current_date())

    user = relationship("User", back_populates="recognised_faces")

    __table_args__ = (
        UniqueConstraint('username', 'date', name='uix_username_date'),
    )

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    photo = Column(String, nullable=True)

    recognised_faces = relationship("RecognisedFaces", back_populates="user")

class UnknownRecognisedFaces(Base):
    __tablename__ = "unknown_recognised_faces"
    id = Column(Integer, primary_key=True, index=True)
    path = Column(String, nullable=False)
    datetime = Column(DateTime, default=datetime.utcnow)
