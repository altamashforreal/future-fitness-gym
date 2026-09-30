from sqlalchemy.orm import Session
from datetime import date, datetime, timezone, timedelta
from typing import List

from app.models.checkin import CheckIn, CheckInStatus
from app.models.member import Member
from app.schemas.checkin import CheckInResult, CheckInOut
from app.services.member_service import search_members
from app.services.alert_service import send_expiry_alert_if_needed


def process_checkin(db: Session, query: str, method: str, staff_id: int) -> CheckInResult:
    """
    Core check-in logic:
    1. Find member by member_id or phone
    2. Determine status
    3. Log the attempt (even denied ones)
    4. Return structured result for reception display
    """
    member = search_members(db, query)

    if not member:
        return CheckInResult(
            status=CheckInStatus.denied,
            member_id="—",
            full_name="Member not found",
            plan_name=None,
            expires_on=None,
            days_remaining=None,
            message=f"No member found for '{query}'. Check the ID or phone number.",
        )

    m = member.active_membership

    # no membership or latest one is expired
    if not m or m.status.value == "expired":
        _log_checkin(db, member.id, CheckInStatus.denied, staff_id, method)
        send_expiry_alert_if_needed(member, expired=True)
        return CheckInResult(
            status=CheckInStatus.denied,
            member_id=member.member_id,
            full_name=member.full_name,
            plan_name=m.plan.name if m else None,
            expires_on=str(m.end_date) if m else None,
            days_remaining=m.days_remaining if m else None,
            message=f"Membership expired. Please renew to continue.",
        )

    # expiring soon
    if m.status.value == "expiring":
        ci = _log_checkin(db, member.id, CheckInStatus.expiring, staff_id, method)
        send_expiry_alert_if_needed(member, expired=False)
        return CheckInResult(
            status=CheckInStatus.expiring,
            member_id=member.member_id,
            full_name=member.full_name,
            plan_name=m.plan.name,
            expires_on=str(m.end_date),
            days_remaining=m.days_remaining,
            message=f"Entry allowed. Membership expires in {m.days_remaining} day(s). Remind to renew.",
            check_in_id=ci.id,
        )

    # fully active
    ci = _log_checkin(db, member.id, CheckInStatus.allowed, staff_id, method)
    return CheckInResult(
        status=CheckInStatus.allowed,
        member_id=member.member_id,
        full_name=member.full_name,
        plan_name=m.plan.name,
        expires_on=str(m.end_date),
        days_remaining=m.days_remaining,
        message="Access granted.",
        check_in_id=ci.id,
    )


def _log_checkin(
    db: Session,
    member_id: int,
    status: CheckInStatus,
    staff_id: int,
    method: str,
) -> CheckIn:
    ci = CheckIn(
        member_id=member_id,
        status=status,
        checked_in_by=staff_id,
        method=method,
    )
    db.add(ci)
    db.commit()
    db.refresh(ci)
    return ci


def get_todays_log(db: Session, limit: int = 100) -> List[CheckInOut]:
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    rows = (
        db.query(CheckIn)
        .filter(CheckIn.checked_in_at >= today_start)
        .order_by(CheckIn.checked_in_at.desc())
        .limit(limit)
        .all()
    )
    result = []
    for ci in rows:
        result.append(CheckInOut(
            id=ci.id,
            member_id=ci.member_id,
            member_name=ci.member.full_name if ci.member else "—",
            checked_in_at=ci.checked_in_at,
            status=ci.status,
            method=ci.method,
        ))
    return result


def get_checkin_history(db: Session, member_id: int, days: int = 30) -> List[CheckInOut]:
    since = datetime.now(timezone.utc) - timedelta(days=days)
    rows = (
        db.query(CheckIn)
        .filter(CheckIn.member_id == member_id, CheckIn.checked_in_at >= since)
        .order_by(CheckIn.checked_in_at.desc())
        .all()
    )
    return [
        CheckInOut(
            id=ci.id,
            member_id=ci.member_id,
            member_name=ci.member.full_name if ci.member else "—",
            checked_in_at=ci.checked_in_at,
            status=ci.status,
            method=ci.method,
        )
        for ci in rows
    ]