"""SQLAlchemy database models."""
from sqlalchemy import Boolean, Column, Integer, String, DateTime, ForeignKey, JSON, text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from db.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    clerk_user_id = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), nullable=False)
    full_name = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"), onupdate=datetime.utcnow)

    # Relationship
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")


class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    key_value = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    platform = Column(String(50))  # MT4, MT5, OANDA, etc.
    account_number = Column(String(100))
    plan_type = Column(String(20), nullable=False, server_default="starter")  # starter, pro, enterprise
    monthly_ohlc_limit = Column(Integer, nullable=False, server_default="500")  # Starter default: 500/month
    monthly_trade_limit = Column(Integer)  # NULL for unlimited (Pro/Enterprise), or specific limit for Starter
    status = Column(String(20), nullable=False, server_default="active", index=True)  # active, suspended, cancelled
    is_starter = Column(Boolean, default=False)
    stripe_customer_id = Column(String(255), index=True)
    stripe_subscription_id = Column(String(255), index=True)
    last_used_at = Column(DateTime(timezone=True))
    next_billing_date = Column(DateTime(timezone=True))  # Next billing cycle date
    deleted_at = Column(DateTime(timezone=True))  # Soft delete
    created_at = Column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"), onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="api_keys")
    usage_logs = relationship("UsageLog", back_populates="api_key", cascade="all, delete-orphan")
    usage_summary = relationship("UsageSummary", back_populates="api_key", cascade="all, delete-orphan")


class UsageLog(Base):
    __tablename__ = "usage_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    api_key_id = Column(UUID(as_uuid=True), ForeignKey("api_keys.id", ondelete="CASCADE"), nullable=False, index=True)
    metric_type = Column(String(20), nullable=False, index=True)  # 'ohlc', 'trade'
    endpoint = Column(String(100))
    request_details = Column(JSON)
    timestamp = Column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    month = Column(String(7), nullable=False, index=True)  # Format: '2025-01'

    # Relationship
    api_key = relationship("APIKey", back_populates="usage_logs")


class UsageSummary(Base):
    __tablename__ = "usage_summary"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    api_key_id = Column(UUID(as_uuid=True), ForeignKey("api_keys.id", ondelete="CASCADE"), nullable=False)
    month = Column(String(7), nullable=False)  # Format: '2025-01'
    ohlc_count = Column(Integer, default=0)
    trade_count = Column(Integer, default=0)
    last_updated = Column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"), onupdate=datetime.utcnow)

    # Relationship
    api_key = relationship("APIKey", back_populates="usage_summary")

    __table_args__ = (
        # Unique constraint on api_key_id and month
        UniqueConstraint('api_key_id', 'month', name='uq_usage_summary_api_key_month'),
    )
