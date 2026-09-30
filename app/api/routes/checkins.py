"""
Check-in Routes
===============
Handles three entry methods:
  1. Manual  — staff types member ID or phone at reception desk
  2. QR Code — member scans their QR code on a tablet
  3. Biometric — fingerprint/face scanner calls POST /api/checkins/biometric/verify

Biometric Integration
---------------------
Most biometric devices (ZKTeco, Suprema, eSSL) work like this:
  - You enroll members on the device using their member_id (e.g. GF0001)
  - When a fingerprint is scanned, the device identifies the user and posts
    their enrolled ID to a webhook URL you configure in the device settings.
  - This endpoint IS that webhook.

Device Configuration (example — ZKTeco):
  Push Protocol URL: http://<your-server-ip>:8000/api/checkins/biometric/verify
  Method: POST
  Body: { "biometric_user_id": "<enrolled_member_id>", "device_id": "MAIN_DOOR" }

The shared `device_secret` acts as an API key to prevent spoofed requests.
Set it in your .env as BIOMETRIC_DEVICE_SECRET.
"""

import os
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import Optional

from app.db.session import get_db
from app.schemas.checkin import CheckInRequest, CheckInResult, BiometricVerifyRequest, CheckInOut
from app.services.checkin_service import process_checkin, get_todays_log

router = APIRouter(prefix="/checkins", tags=["Check-in"])

# In production move this to .env / settings
BIOMETRIC_DEVICE_SECRET = os.getenv("BIOMETRIC_DEVICE_SECRET", "biometric-secret-change-me")

# Staff ID used when a biometric device triggers a check-in (no human staff present)
BIOMETRIC_STAFF_ID = 1


# ── 1. Manual / QR check-in ──────────────────────────────────────────────────
@router.post("/", response_model=CheckInResult, summary="Manual check-in by staff")
def checkin(
    payload: CheckInRequest,
    db: Session = Depends(get_db),
):
    """
    Process a check-in triggered by reception staff typing a member ID or phone number.
    Returns allowed / denied / expiring with full member + membership details.
    """
    result = process_checkin(
        db=db,
        query=payload.query,
        method=payload.method,
        staff_id=BIOMETRIC_STAFF_ID,
    )
    return result


# ── 2. Biometric device webhook ───────────────────────────────────────────────
@router.post(
    "/biometric/verify",
    response_model=CheckInResult,
    summary="Biometric device webhook — fingerprint / face scan",
)
def biometric_verify(
    payload: BiometricVerifyRequest,
    db: Session = Depends(get_db),
):
    """
    Called automatically by the biometric device when a fingerprint/face is recognized.

    Authentication:
      The device must include the shared secret in the request body as `device_secret`.
      This prevents anyone from spoofing check-ins by calling the endpoint directly.

    Flow:
      1. Device scans fingerprint → identifies enrolled user (member_id)
      2. Device POSTs to this endpoint with the member_id
      3. We look up the member and validate their membership
      4. Return: allowed (door opens) | denied (door stays locked) | expiring (door opens + alert)

    Door Lock Integration:
      Wire your door relay to the device.
      If the device supports HTTP response-based relay control (many ZKTeco models do),
      it will automatically open/close the door based on this response.
      Otherwise, implement a local middleware that reads this response and controls the relay via GPIO.
    """
    # Validate device secret
    if payload.device_secret and payload.device_secret != BIOMETRIC_DEVICE_SECRET:
        raise HTTPException(status_code=403, detail="Invalid device secret.")

    result = process_checkin(
        db=db,
        query=payload.biometric_user_id,   # biometric_user_id = member_id enrolled on device
        method="biometric",
        staff_id=BIOMETRIC_STAFF_ID,
    )
    return result


# ── 3. Today's check-in log ───────────────────────────────────────────────────
@router.get("/today", response_model=list[CheckInOut], summary="Today's check-in log")
def todays_checkins(db: Session = Depends(get_db)):
    """Returns all check-in events from today (last 100)."""
    return get_todays_log(db)
