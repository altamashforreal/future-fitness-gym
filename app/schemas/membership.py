from pydantic import BaseModel
from typing import Optional, List
from datetime import date
from .member import MemberResponse
from app.models.membership import MembershipStatus

class MembershipCreate(BaseModel):
    member_id: int
    plan_id: int
    start_date: Optional[date] = None
    addon_ids: List[int] = []
    payment_method: str = "cash"
    transaction_id: Optional[str] = None
    is_renewal: bool = False

class MembershipResponse(BaseModel):
    id: int
    member_id: int
    plan_id: int
    start_date: date
    end_date: date
    is_renewal: bool
    status: MembershipStatus
    
    class Config:
        from_attributes = True
        orm_mode = True
