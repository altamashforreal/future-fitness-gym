from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import date, timedelta
from typing import List

from app.db.session import get_db
from app.models.member import Member
from app.models.plan import Plan
from app.models.membership import Membership, MembershipAddon
from app.models.payment import Payment
from app.schemas.membership import MembershipCreate, MembershipResponse

router = APIRouter(prefix="/memberships", tags=["Memberships"])

@router.post("/", response_model=MembershipResponse, status_code=status.HTTP_201_CREATED)
def create_or_renew_membership(data: MembershipCreate, db: Session = Depends(get_db)):
    """Assign a membership to a member and record the payment."""
    member = db.query(Member).filter(Member.id == data.member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
        
    plan = db.query(Plan).filter(Plan.id == data.plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
        
    start = data.start_date or date.today()
    end = start + timedelta(days=plan.duration_days)
    
    # Create Membership
    membership = Membership(
        member_id=data.member_id,
        plan_id=data.plan_id,
        start_date=start,
        end_date=end,
        is_renewal=data.is_renewal
    )
    db.add(membership)
    db.flush() # flush to get membership.id
    
    total_amount = plan.price
    
    # Add Addons
    for addon_id in data.addon_ids:
        addon_plan = db.query(Plan).filter(Plan.id == addon_id).first()
        if addon_plan:
            total_amount += addon_plan.price
            addon = MembershipAddon(
                membership_id=membership.id,
                plan_id=addon_id
            )
            db.add(addon)
            
    # Record Payment
    payment = Payment(
        member_id=data.member_id,
        membership_id=membership.id,
        amount=total_amount,
        payment_method=data.payment_method,
        transaction_id=data.transaction_id
    )
    db.add(payment)
    
    db.commit()
    db.refresh(membership)

    # Send WhatsApp & Email Receipt in background
    from app.services.alert_service import send_payment_receipt
    try:
        send_payment_receipt(
            member=member,
            amount=total_amount,
            plan_name=plan.name,
            method=data.payment_method,
            start_date=start,
            end_date=end,
            tx_id=data.transaction_id
        )
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Failed to send receipt: {e}")

    return membership
