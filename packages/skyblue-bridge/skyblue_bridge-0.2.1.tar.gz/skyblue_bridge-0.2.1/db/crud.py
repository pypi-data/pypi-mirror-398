"""CRUD operations for database models."""
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime, timedelta, timezone
from typing import Optional, List
import secrets
import string

from db import models


def generate_api_key(prefix: str = "sk_live") -> str:
    """Generate a secure random API key."""
    random_part = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(48))
    return f"{prefix}_{random_part}"


# ==================== USER OPERATIONS ====================

def get_user_by_clerk_id(db: Session, clerk_user_id: str) -> Optional[models.User]:
    """Get user by Clerk user ID."""
    return db.query(models.User).filter(models.User.clerk_user_id == clerk_user_id).first()


def create_user(db: Session, clerk_user_id: str, email: str, full_name: Optional[str] = None) -> models.User:
    """Create a new user."""
    user = models.User(
        clerk_user_id=clerk_user_id,
        email=email,
        full_name=full_name
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_or_create_user(db: Session, clerk_user_id: str, email: str, full_name: Optional[str] = None) -> models.User:
    """Get existing user or create new one."""
    user = get_user_by_clerk_id(db, clerk_user_id)
    if not user:
        user = create_user(db, clerk_user_id, email, full_name)
    return user


# ==================== API KEY OPERATIONS ====================

def get_api_key_by_value(db: Session, key_value: str) -> Optional[models.APIKey]:
    """Get API key by its value, including soft-deleted keys that haven't expired."""
    current_time = datetime.now(timezone.utc)

    return db.query(models.APIKey).filter(
        and_(
            models.APIKey.key_value == key_value,
            # Include keys that are:
            # 1. Not deleted (deleted_at is NULL), OR
            # 2. Deleted but still within billing cycle (next_billing_date > now)
            or_(
                models.APIKey.deleted_at.is_(None),
                and_(
                    models.APIKey.deleted_at.isnot(None),
                    models.APIKey.next_billing_date > current_time
                )
            )
        )
    ).first()


def get_user_api_keys(db: Session, user_id: str) -> List[models.APIKey]:
    """Get all active API keys for a user, including soft-deleted keys that haven't expired."""
    current_time = datetime.now(timezone.utc)

    return db.query(models.APIKey).filter(
        and_(
            models.APIKey.user_id == user_id,
            # Include keys that are:
            # 1. Not deleted (deleted_at is NULL), OR
            # 2. Deleted but still within billing cycle (next_billing_date > now)
            or_(
                models.APIKey.deleted_at.is_(None),
                and_(
                    models.APIKey.deleted_at.isnot(None),
                    models.APIKey.next_billing_date > current_time
                )
            )
        )
    ).all()


def create_starter_key(db: Session, user_id: str) -> models.APIKey:
    """Create a starter API key for a new user."""
    key_value = generate_api_key(prefix="sk_starter")
    next_billing = datetime.now(timezone.utc) + timedelta(days=30)

    api_key = models.APIKey(
        user_id=user_id,
        key_value=key_value,
        name="Starter API Key",
        platform=None,
        account_number=None,
        plan_type="starter",
        monthly_ohlc_limit=500,  # Starter: 500 OHLC/month
        monthly_trade_limit=100,  # Starter: 100 trades/month
        status="active",
        is_starter=True,
        next_billing_date=next_billing
    )
    db.add(api_key)
    db.commit()
    db.refresh(api_key)
    return api_key


def create_api_key(
    db: Session,
    user_id: str,
    name: str,
    platform: str,
    account_number: str,
    plan_type: str = "pro",
    stripe_customer_id: Optional[str] = None,
    stripe_subscription_id: Optional[str] = None
) -> models.APIKey:
    """Create a new API key."""
    key_value = generate_api_key(prefix="sk_live")
    next_billing = datetime.now(timezone.utc) + timedelta(days=30)

    # Set limits based on plan
    ohlc_limit = 10000 if plan_type == "pro" else 999999  # Enterprise gets very high limit
    trade_limit = None  # Unlimited for pro and enterprise

    api_key = models.APIKey(
        user_id=user_id,
        key_value=key_value,
        name=name,
        platform=platform,
        account_number=account_number,
        plan_type=plan_type,
        monthly_ohlc_limit=ohlc_limit,
        monthly_trade_limit=trade_limit,
        status="active",
        is_starter=False,
        stripe_customer_id=stripe_customer_id,
        stripe_subscription_id=stripe_subscription_id,
        next_billing_date=next_billing
    )
    db.add(api_key)
    db.commit()
    db.refresh(api_key)
    return api_key


def update_api_key(
    db: Session,
    api_key_id: str,
    name: Optional[str] = None,
    platform: Optional[str] = None,
    account_number: Optional[str] = None
) -> Optional[models.APIKey]:
    """Update an existing API key."""
    api_key = db.query(models.APIKey).filter(models.APIKey.id == api_key_id).first()
    if not api_key:
        return None

    if name is not None:
        api_key.name = name
    if platform is not None:
        api_key.platform = platform
    if account_number is not None:
        api_key.account_number = account_number

    api_key.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(api_key)
    return api_key


def soft_delete_api_key(db: Session, api_key_id: str) -> bool:
    """Soft delete an API key."""
    api_key = db.query(models.APIKey).filter(models.APIKey.id == api_key_id).first()
    if not api_key or api_key.is_starter:  # Can't delete starter keys
        return False

    api_key.deleted_at = datetime.utcnow()
    api_key.status = "cancelled"
    db.commit()
    return True


def update_api_key_last_used(db: Session, key_value: str):
    """Update the last_used_at timestamp for an API key."""
    api_key = get_api_key_by_value(db, key_value)
    if api_key:
        api_key.last_used_at = datetime.utcnow()
        db.commit()


# ==================== USAGE TRACKING ====================

def log_usage(
    db: Session,
    api_key_id: str,
    metric_type: str,  # 'ohlc' or 'trade'
    endpoint: str,
    request_details: Optional[dict] = None
):
    """Log a usage event and update summary."""
    current_month = datetime.utcnow().strftime("%Y-%m")

    # Create detailed log
    usage_log = models.UsageLog(
        api_key_id=api_key_id,
        metric_type=metric_type,
        endpoint=endpoint,
        request_details=request_details or {},
        month=current_month
    )
    db.add(usage_log)

    # Update or create summary
    summary = db.query(models.UsageSummary).filter(
        and_(
            models.UsageSummary.api_key_id == api_key_id,
            models.UsageSummary.month == current_month
        )
    ).first()

    if not summary:
        summary = models.UsageSummary(
            api_key_id=api_key_id,
            month=current_month,
            ohlc_count=0,
            trade_count=0
        )
        db.add(summary)

    # Increment appropriate counter
    if metric_type == "ohlc":
        summary.ohlc_count += 1
    elif metric_type == "trade":
        summary.trade_count += 1

    summary.last_updated = datetime.utcnow()
    db.commit()


def get_usage_summary(db: Session, api_key_id: str, month: Optional[str] = None) -> Optional[models.UsageSummary]:
    """Get usage summary for an API key for a specific month."""
    if not month:
        month = datetime.utcnow().strftime("%Y-%m")

    return db.query(models.UsageSummary).filter(
        and_(
            models.UsageSummary.api_key_id == api_key_id,
            models.UsageSummary.month == month
        )
    ).first()


def check_usage_limit(db: Session, api_key: models.APIKey, metric_type: str) -> tuple[bool, dict]:
    """
    Check if API key has exceeded usage limits.
    Returns (can_proceed, usage_info)
    """
    current_month = datetime.utcnow().strftime("%Y-%m")
    summary = get_usage_summary(db, str(api_key.id), current_month)

    if not summary:
        # No usage yet this month
        return True, {"used": 0, "limit": api_key.monthly_ohlc_limit if metric_type == "ohlc" else api_key.monthly_trade_limit}

    if metric_type == "ohlc":
        used = summary.ohlc_count
        limit = api_key.monthly_ohlc_limit
    elif metric_type == "trade":
        used = summary.trade_count
        limit = api_key.monthly_trade_limit
        if limit is None:  # Unlimited
            return True, {"used": used, "limit": None}
    else:
        return True, {}

    can_proceed = used < limit
    return can_proceed, {"used": used, "limit": limit, "remaining": limit - used}
