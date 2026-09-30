from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.db.session import Base


class Gender(str, enum.Enum):
    male = "male"
    female = "female"
    other = "other"


class Member(Base):
    __tablename__ = "members"

    id = Column(Integer, primary_key=True, index=True)
    member_id = Column(String(20), unique=True, index=True)  # GF0001, GF0002 …
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone = Column(String(20), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=True)
    date_of_birth = Column(Date, nullable=True)
    gender = Column(Enum(Gender, name="member_gender"), nullable=True)
    address = Column(Text, nullable=True)
    emergency_contact = Column(String(20), nullable=True)
    photo_url = Column(String(500), nullable=True)
    qr_code_url = Column(String(500), nullable=True)
    notes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    whatsapp_alerts = Column(Boolean, default=True)  # can opt out
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # relationships
    memberships = relationship("Membership", back_populates="member", order_by="desc(Membership.start_date)")
    check_ins = relationship("CheckIn", back_populates="member")
    payments = relationship("Payment", back_populates="member")

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @property
    def active_membership(self):
        """Returns the current active membership or None."""
        from datetime import date
        for m in self.memberships:
            if m.start_date <= date.today() <= m.end_date:
                return m
        return None