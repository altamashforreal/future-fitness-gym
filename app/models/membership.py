from sqlalchemy import Column, Integer, ForeignKey, Date, DateTime, Boolean, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import date
import enum

from app.db.session import Base


class MembershipStatus(str, enum.Enum):
    active = "active"
    expiring = "expiring"   # within 7 days
    expired = "expired"
    cancelled = "cancelled"
    frozen = "frozen"       # member temporarily paused


class Membership(Base):
    __tablename__ = "memberships"

    id = Column(Integer, primary_key=True, index=True)
    member_id = Column(Integer, ForeignKey("members.id", ondelete="CASCADE"), nullable=False)
    plan_id = Column(Integer, ForeignKey("plans.id"), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    is_renewal = Column(Boolean, default=False)   # was this a renewal?
    freeze_start = Column(Date, nullable=True)
    freeze_end = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # relationships
    member = relationship("Member", back_populates="memberships")
    plan = relationship("Plan", back_populates="memberships")
    payment = relationship("Payment", back_populates="membership", uselist=False)
    addons = relationship("MembershipAddon", back_populates="membership")

    @property
    def status(self) -> MembershipStatus:
        today = date.today()
        days_left = (self.end_date - today).days
        if days_left < 0:
            return MembershipStatus.expired
        elif days_left <= 7:
            return MembershipStatus.expiring
        return MembershipStatus.active

    @property
    def days_remaining(self) -> int:
        return (self.end_date - date.today()).days


class MembershipAddon(Base):
    """Addons attached to a membership (locker, PT, etc.)"""
    __tablename__ = "membership_addons"

    id = Column(Integer, primary_key=True, index=True)
    membership_id = Column(Integer, ForeignKey("memberships.id", ondelete="CASCADE"))
    plan_id = Column(Integer, ForeignKey("plans.id"))   # addon plan
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    membership = relationship("Membership", back_populates="addons")
    plan = relationship("Plan")