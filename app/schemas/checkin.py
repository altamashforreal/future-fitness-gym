from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.checkin import CheckInStatus


class CheckInRequest(BaseModel):
    """Payload for manual check-in (staff desk or frontend search)."""
    query: str                  # member_id (e.g. GF0001) or phone number
    method: str = "member_id"  # member_id | phone | qr_code | biometric


class BiometricVerifyRequest(BaseModel):
    """
    Payload sent by a biometric device/middleware on fingerprint scan.
    The device enrolls members with their member_id as the user identifier.
    """
    biometric_user_id: str       # The ID the biometric device has enrolled (= member_id)
    device_id: Optional[str] = None   # Which scanner triggered this (e.g. "DOOR_A")
    device_secret: Optional[str] = None  # Shared secret to authenticate the device


class CheckInResult(BaseModel):
    """Unified response returned for any check-in attempt."""
    status: CheckInStatus          # allowed | denied | expiring
    member_id: str
    full_name: str
    plan_name: Optional[str] = None
    expires_on: Optional[str] = None
    days_remaining: Optional[int] = None
    message: str
    check_in_id: Optional[int] = None


class CheckInOut(BaseModel):
    """Check-in log entry returned in lists."""
    id: int
    member_id: int
    member_name: str
    checked_in_at: datetime
    status: CheckInStatus
    method: str

    class Config:
        from_attributes = True
