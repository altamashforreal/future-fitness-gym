from pydantic import BaseModel
from typing import Optional
from datetime import date
from app.models.member import Gender


class MemberBase(BaseModel):
    first_name: str
    last_name: str
    phone: str
    email: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[Gender] = None
    address: Optional[str] = None
    emergency_contact: Optional[str] = None


class MemberCreate(MemberBase):
    pass


class MemberUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[Gender] = None
    address: Optional[str] = None
    emergency_contact: Optional[str] = None


class MemberResponse(MemberBase):
    id: int
    member_id: str
    is_active: bool
    # Computed membership fields (populated by the route)
    membership_status: Optional[str] = None      # active | expiring | expired | none
    membership_end_date: Optional[date] = None
    membership_plan: Optional[str] = None
    days_remaining: Optional[int] = None

    class Config:
        orm_mode = True
        from_attributes = True
