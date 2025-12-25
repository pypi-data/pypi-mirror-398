from sqlalchemy import Column, Integer, String, DateTime, func
from datetime import datetime, timedelta, timezone
from dataflow.db import Base

def otp_expiry():
    # Make sure this uses UTC
    return datetime.now(timezone.utc) + timedelta(minutes=10)

class UserOtp(Base):
    """
    Table USER_OTP
    """

    __tablename__ = 'USER_OTP'

    id = Column(Integer, primary_key=True, index=True, unique=True, nullable=False, autoincrement=True)
    email = Column(String, unique=True, nullable=False)
    otp = Column(Integer, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False, default=otp_expiry)
