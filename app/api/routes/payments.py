from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
import razorpay
import hmac
import hashlib
import os

from app.db.session import get_db
from app.models.member import Member
from app.models.plan import Plan
from app.models.membership import Membership
from datetime import date, timedelta

router = APIRouter(prefix="/payments", tags=["Payments"])

RAZORPAY_KEY_ID = os.environ.get("RAZORPAY_KEY_ID", "")
RAZORPAY_KEY_SECRET = os.environ.get("RAZORPAY_KEY_SECRET", "")


def get_razorpay_client():
    if not RAZORPAY_KEY_ID or not RAZORPAY_KEY_SECRET:
        raise HTTPException(status_code=503, detail="Razorpay is not configured on this server.")
    return razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))


@router.post("/create-order")
def create_razorpay_order(body: dict, db: Session = Depends(get_db)):
    """
    Create a Razorpay order for a given member and plan.
    Body: { "member_id": int, "plan_id": int }
    Returns: { "order_id": str, "amount": int, "currency": str, "key_id": str }
    """
    member_id = body.get("member_id")
    plan_id = body.get("plan_id")

    if not member_id or not plan_id:
        raise HTTPException(status_code=400, detail="member_id and plan_id are required.")

    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found.")

    plan = db.query(Plan).filter(Plan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found.")

    client = get_razorpay_client()

    # Razorpay amount is in paise (1 INR = 100 paise)
    amount_paise = int(plan.price * 100)

    try:
        order = client.order.create({
            "amount": amount_paise,
            "currency": "INR",
            "receipt": f"gym_member_{member_id}_plan_{plan_id}",
            "notes": {
                "member_name": f"{member.first_name} {member.last_name}",
                "plan_name": plan.name,
                "gym": "Future Fitness Gym"
            }
        })
        return {
            "order_id": order["id"],
            "amount": amount_paise,
            "currency": "INR",
            "key_id": RAZORPAY_KEY_ID,
            "member_name": f"{member.first_name} {member.last_name}",
            "member_email": member.email or "",
            "member_phone": member.phone or "",
            "plan_name": plan.name
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Razorpay error: {str(e)}")


@router.post("/verify")
def verify_razorpay_payment(body: dict, db: Session = Depends(get_db)):
    """
    Verify Razorpay payment signature and record the membership.
    Body: { "razorpay_order_id", "razorpay_payment_id", "razorpay_signature", "member_id", "plan_id" }
    """
    order_id = body.get("razorpay_order_id")
    payment_id = body.get("razorpay_payment_id")
    signature = body.get("razorpay_signature")
    member_id = body.get("member_id")
    plan_id = body.get("plan_id")

    if not all([order_id, payment_id, signature, member_id, plan_id]):
        raise HTTPException(status_code=400, detail="Missing required payment fields.")

    # Verify signature using HMAC-SHA256
    msg = f"{order_id}|{payment_id}"
    expected_sig = hmac.new(
        RAZORPAY_KEY_SECRET.encode("utf-8"),
        msg.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

    if expected_sig != signature:
        raise HTTPException(status_code=400, detail="Invalid payment signature. Payment could not be verified.")

    # Signature is valid — create membership record
    plan = db.query(Plan).filter(Plan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found.")

    from app.models.payment import Payment
    start = date.today()
    end = start + timedelta(days=plan.duration_days)

    membership = Membership(
        member_id=member_id,
        plan_id=plan_id,
        start_date=start,
        end_date=end,
        is_renewal=True,
    )
    db.add(membership)
    db.flush()  # get membership.id before commit

    payment = Payment(
        membership_id=membership.id,
        member_id=member_id,
        amount=plan.price,
        payment_method="razorpay",
        transaction_id=payment_id,
    )
    db.add(payment)
    db.commit()
    db.refresh(membership)

    member = db.query(Member).filter(Member.id == member_id).first()
    if member:
        # Send WhatsApp & Email Receipt in background
        from app.services.alert_service import send_payment_receipt
        try:
            send_payment_receipt(
                member=member,
                amount=plan.price,
                plan_name=plan.name,
                method="razorpay",
                start_date=start,
                end_date=end,
                tx_id=payment_id
            )
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Failed to send Razorpay receipt: {e}")


    return {
        "status": "success",
        "membership_id": membership.id,
        "payment_id": payment_id,
        "start_date": str(start),
        "end_date": str(end)
    }
