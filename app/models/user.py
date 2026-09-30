from sqlalchemy import Column, Integer, String, Enum
from app.db.session import Base
import enum

class UserRole(str, enum.Enum):
    owner = "owner"
    reception = "reception"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole, name="user_role"), nullable=False, default=UserRole.reception)
