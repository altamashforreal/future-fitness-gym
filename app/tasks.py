import logging
from datetime import date
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.member import Member
from app.models.membership import Membership
from app.services.alert_service import send_automated_alerts

logger = logging.getLogger(__name__)

# Replace with the actual URL of your deployed frontend or ngrok for production
BASE_APP_URL = "http://127.0.0.1:5500"

def check_and_send_expiring_alerts():
    """
    Job that runs daily to find members whose plans are expiring in exactly 7 days.
    """
    logger.info("Starting automated membership expiry check...")
    db: Session = SessionLocal()
    try:
        members = db.query(Member).all()
        today = date.today()

        for member in members:
            # Find their latest active membership
            latest_membership = db.query(Membership).filter(
                Membership.member_id == member.id
            ).order_by(Membership.end_date.desc()).first()

            if not latest_membership or not latest_membership.end_date:
                continue

            days_left = (latest_membership.end_date - today).days

            # E.g., send reminder exactly 7 days before it expires
            if days_left == 7:
                logger.info(f"Member {member.first_name} expires in 7 days. Sending alerts...")
                # Assuming base plan is being renewed, we can pick the previous plan_id or a default
                # For this automated link, we just pre-fill their current plan_id
                plan_id = latest_membership.plan_id
                pay_link = f"{BASE_APP_URL}/frontend/pay.html?member_id={member.id}&plan_id={plan_id}"
                
                send_automated_alerts(member, pay_link, days_left)

    except Exception as e:
        logger.error(f"Error in expiry check job: {e}")
    finally:
        db.close()
    
    logger.info("Automated membership expiry check completed.")
