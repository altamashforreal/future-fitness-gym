from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base

class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    member_id = Column(Integer, ForeignKey("members.id", ondelete="CASCADE"), nullable=False)
    membership_id = Column(Integer, ForeignKey("memberships.id"), nullable=True)
    amount = Column(Float, nullable=False)
    payment_method = Column(String(50), nullable=False) # cash, card, upi
    transaction_id = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    member = relationship("Member", back_populates="payments")
    membership = relationship("Membership", back_populates="payment")
