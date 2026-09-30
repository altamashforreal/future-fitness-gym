from sqlalchemy.orm import Session
from app.models.member import Member


def search_members(db: Session, query: str) -> Member | None:
    """
    Find a member by member_id (e.g. GF0001) or phone number.
    Used by the check-in and biometric flows.
    """
    query = query.strip()
    # Try member_id first
    member = db.query(Member).filter(Member.member_id == query).first()
    if member:
        return member
    # Fall back to phone number
    member = db.query(Member).filter(Member.phone == query).first()
    return member
