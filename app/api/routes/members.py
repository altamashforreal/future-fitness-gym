from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import date
from app.db.session import get_db
from app.models.member import Member
from app.models.membership import Membership
from app.schemas.member import MemberCreate, MemberUpdate, MemberResponse

router = APIRouter(prefix="/members", tags=["Members"])


def _enrich(member: Member) -> dict:
    """Attach membership status info to a member dict for the response."""
    data = {
        "id": member.id,
        "member_id": member.member_id,
        "first_name": member.first_name,
        "last_name": member.last_name,
        "phone": member.phone,
        "email": member.email,
        "date_of_birth": member.date_of_birth,
        "gender": member.gender,
        "address": member.address,
        "emergency_contact": member.emergency_contact,
        "is_active": member.is_active,
        "membership_status": None,
        "membership_end_date": None,
        "membership_plan": None,
        "days_remaining": None,
    }

    today = date.today()

    # Pick the most recent membership
    memberships = sorted(member.memberships, key=lambda m: m.start_date, reverse=True)
    if memberships:
        latest = memberships[0]
        days_left = (latest.end_date - today).days
        data["membership_end_date"] = latest.end_date
        data["membership_plan"] = latest.plan.name if latest.plan else None
        data["days_remaining"] = days_left

        if days_left < 0:
            data["membership_status"] = "expired"
        elif days_left <= 7:
            data["membership_status"] = "expiring"
        else:
            data["membership_status"] = "active"
    else:
        data["membership_status"] = "none"

    return data


@router.post("/", response_model=MemberResponse, status_code=status.HTTP_201_CREATED)
def create_member(member_in: MemberCreate, db: Session = Depends(get_db)):
    """Create a new gym member."""
    existing = db.query(Member).filter(Member.phone == member_in.phone).first()
    if existing:
        raise HTTPException(status_code=400, detail="Member with this phone number already exists.")

    last_member = db.query(Member).order_by(Member.id.desc()).first()
    new_num = (last_member.id + 1) if last_member else 1
    new_member_id = f"GF{new_num:04d}"
    
    # Ensure it's strictly unique to avoid constraint errors
    while db.query(Member).filter(Member.member_id == new_member_id).first():
        new_num += 1
        new_member_id = f"GF{new_num:04d}"

    new_member = Member(**member_in.dict(), member_id=new_member_id)
    db.add(new_member)
    db.commit()
    db.refresh(new_member)
    return _enrich(new_member)


@router.get("/", response_model=list[MemberResponse])
def get_all_members(db: Session = Depends(get_db)):
    """Retrieve all members with their current membership status."""
    members = db.query(Member).order_by(Member.created_at.desc()).all()
    return [_enrich(m) for m in members]


@router.get("/{member_id}", response_model=MemberResponse)
def get_member(member_id: int, db: Session = Depends(get_db)):
    """Get a single member by database ID."""
    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found.")
    return _enrich(member)


@router.put("/{member_id}", response_model=MemberResponse)
def update_member(member_id: int, member_in: MemberUpdate, db: Session = Depends(get_db)):
    """Update an existing member."""
    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found.")

    # Check phone number uniqueness if it's being updated
    if member_in.phone and member_in.phone != member.phone:
        existing = db.query(Member).filter(Member.phone == member_in.phone).first()
        if existing:
            raise HTTPException(status_code=400, detail="Member with this phone number already exists.")

    update_data = member_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(member, field, value)

    db.commit()
    db.refresh(member)
    return _enrich(member)


@router.delete("/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_member(member_id: int, db: Session = Depends(get_db)):
    """Delete a member."""
    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found.")
    db.delete(member)
    db.commit()


@router.post("/{member_id}/send-payment-link")
def send_payment_link(member_id: int, body: dict, db: Session = Depends(get_db)):
    """
    Send a WhatsApp payment link directly to the member via Twilio.
    Body: { "plan_id": int, "pay_url": str }
    """
    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found.")

    plan_id = body.get("plan_id")
    pay_url = body.get("pay_url")

    if not plan_id or not pay_url:
        raise HTTPException(status_code=400, detail="plan_id and pay_url are required.")

    if not member.phone:
        raise HTTPException(status_code=400, detail="Member has no phone number registered.")

    from app.services.alert_service import twilio_client, TWILIO_WHATSAPP_NUMBER

    # Twilio Sandbox strictly requires matching a pre-approved template for outbound messages.
    # The default sandbox template is: "Your {{1}} code is {{2}}"
    msg = f"Your Future Fitness Payment code is {pay_url}"

    if twilio_client and TWILIO_WHATSAPP_NUMBER:
        try:
            phone = member.phone if member.phone.startswith('+') else f"+91{member.phone}"
            message = twilio_client.messages.create(
                from_=TWILIO_WHATSAPP_NUMBER,
                body=msg,
                to=f"whatsapp:{phone}"
            )
            return {"status": "sent", "to": phone, "sid": message.sid}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Twilio error: {str(e)}")
    else:
        raise HTTPException(status_code=503, detail="WhatsApp service not configured on server.")
