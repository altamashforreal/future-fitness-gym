"""
Alert service for WhatsApp and Email notifications.
"""
import logging
import smtplib
import os
from email.message import EmailMessage
from twilio.rest import Client

logger = logging.getLogger(__name__)

# SMTP settings from environment (for real emails)
SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", 587))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")

# Twilio settings from environment (for real WhatsApp messages)
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN", "")
TWILIO_WHATSAPP_NUMBER = os.environ.get("TWILIO_WHATSAPP_NUMBER", "")

# Initialize Twilio Client if credentials exist
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN) if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN else None

def send_automated_alerts(member, pay_link: str, days_left: int):
    """
    Automatically called by the daily background job to send payment reminders.
    """
    subject = f"Future Fitness Gym: Membership Expiring in {days_left} Days!"
    
    msg_body = (
        f"Hi {member.first_name},\n\n"
        f"Your membership at Future Fitness Gym is expiring in {days_left} days. "
        f"To avoid any interruption to your fitness journey, you can renew instantly online.\n\n"
        f"Click the secure link below to pay online:\n{pay_link}\n\n"
        f"Thank you,\nFuture Fitness Gym"
    )

    # 1. SEND EMAIL
    if member.email:
        if SMTP_USER and SMTP_PASSWORD:
            try:
                msg = EmailMessage()
                msg.set_content(msg_body)
                msg['Subject'] = subject
                msg['From'] = f"Future Fitness <{SMTP_USER}>"
                msg['To'] = member.email

                server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
                server.starttls()
                server.login(SMTP_USER, SMTP_PASSWORD)
                server.send_message(msg)
                server.quit()
                logger.info(f"✅ Automated Email sent to {member.email}")
            except Exception as e:
                logger.error(f"❌ Failed to send email to {member.email}: {e}")
        else:
            logger.info(f"[MOCK EMAIL to {member.email}] Subject: {subject} | Body: {msg_body}")

    # 2. SEND WHATSAPP
    if member.phone:
        if twilio_client:
            try:
                # Ensure phone number has country code for WhatsApp (e.g., +91)
                phone_formatted = member.phone if member.phone.startswith('+') else f"+91{member.phone}"
                message = twilio_client.messages.create(
                    from_=TWILIO_WHATSAPP_NUMBER,
                    body=msg_body,
                    to=f"whatsapp:{phone_formatted}"
                )
                logger.info(f"✅ Automated WhatsApp sent to {phone_formatted} (SID: {message.sid})")
            except Exception as e:
                logger.error(f"❌ Failed to send WhatsApp to {member.phone}: {e}")
        else:
            logger.info(f"[MOCK WHATSAPP to {member.phone}] {msg_body}")


def send_expiry_alert_if_needed(member, expired: bool):
    """
    Send a WhatsApp alert to the member if their membership is expired or expiring.
    Called during biometric check-in.
    """
    if not member.whatsapp_alerts:
        return

    if expired:
        msg = (
            f"Hi {member.first_name}, your Future Fitness Gym membership has *EXPIRED*. "
            f"Please visit the gym to renew and continue your fitness journey! 💪"
        )
    else:
        msg = (
            f"Hi {member.first_name}, your Future Fitness Gym membership is expiring soon. "
            f"Renew now to avoid interruption! 🏋️"
        )

    if member.phone:
        if twilio_client:
            try:
                phone_formatted = member.phone if member.phone.startswith('+') else f"+91{member.phone}"
                message = twilio_client.messages.create(
                    from_=TWILIO_WHATSAPP_NUMBER,
                    body=msg,
                    to=f"whatsapp:{phone_formatted}"
                )
                logger.info(f"✅ Alert WhatsApp sent to {phone_formatted} (SID: {message.sid})")
            except Exception as e:
                logger.error(f"❌ Failed to send Alert WhatsApp to {member.phone}: {e}")
        else:
            logger.info(f"[MOCK ALERT WHATSAPP to {member.phone}]: {msg}")


def send_payment_receipt(member, amount: float, plan_name: str, method: str, start_date, end_date, tx_id: str = None):
    """
    Send payment receipt via WhatsApp and Email.
    """
    subject = "Future Fitness Gym - Payment Receipt"
    
    msg_body = (
        f"Hi {member.first_name},\n\n"
        f"Thank you for your payment! Here is your receipt:\n\n"
        f"Amount: Rs {amount}\n"
        f"Plan: {plan_name}\n"
        f"Valid from: {start_date} to {end_date}\n"
        f"Method: {method.upper()}\n"
    )
    if tx_id:
        msg_body += f"Txn ID: {tx_id}\n"
        
    msg_body += "\nThank you for choosing Future Fitness Gym! 💪"

    # 1. Email
    if member.email and SMTP_USER and SMTP_PASSWORD:
        try:
            msg = EmailMessage()
            msg.set_content(msg_body)
            msg['Subject'] = subject
            msg['From'] = f"Future Fitness <{SMTP_USER}>"
            msg['To'] = member.email

            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
            server.quit()
            logger.info(f"✅ Receipt Email sent to {member.email}")
        except Exception as e:
            logger.error(f"❌ Failed to send receipt email to {member.email}: {e}")

    # 2. WhatsApp
    if member.phone and twilio_client and TWILIO_WHATSAPP_NUMBER:
        try:
            phone_formatted = member.phone if member.phone.startswith('+') else f"+91{member.phone}"
            import json
            # We'll use the hello_world template for Sandbox to avoid ContentSid errors
            # Template: "Your {{1}} code is {{2}}"
            message = twilio_client.messages.create(
                from_=TWILIO_WHATSAPP_NUMBER,
                content_sid="HXb5b62575e6e4ff6129ad7c8efe1f983e",  
                content_variables=json.dumps({
                    "1": f"{member.first_name}'s Future Fitness Gym receipt",
                    "2": f"\nAmt: Rs{amount}\nPlan: {plan_name}\nTo: {end_date}"
                }),
                to=f"whatsapp:{phone_formatted}"
            )
            logger.info(f"✅ Receipt WhatsApp sent to {phone_formatted} (SID: {message.sid})")
        except Exception as e:
            logger.error(f"❌ Failed to send receipt WhatsApp to {member.phone}: {e}")
