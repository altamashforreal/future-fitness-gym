from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.db.session import Base

class CheckInStatus(str, enum.Enum):
    allowed = "allowed"
    denied = "denied"
    expiring = "expiring"

class CheckIn(Base):
    __tablename__ = "checkins"

    id = Column(Integer, primary_key=True, index=True)
    member_id = Column(Integer, ForeignKey("members.id", ondelete="CASCADE"), nullable=False)
    checked_in_by = Column(Integer, ForeignKey("users.id"), nullable=True)  # Staff who checked them in
    status = Column(Enum(CheckInStatus, name="checkin_status"), nullable=False)
    method = Column(String(50), nullable=False) # e.g., "member_id", "phone", "qr_code"
    checked_in_at = Column(DateTime(timezone=True), server_default=func.now())

    member = relationship("Member", back_populates="check_ins")
