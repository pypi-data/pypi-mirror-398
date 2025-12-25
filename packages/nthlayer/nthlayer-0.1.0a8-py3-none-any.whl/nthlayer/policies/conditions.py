"""
Built-in condition functions for policy evaluation.

Provides time-based, date-based, and service-based conditions.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any


def get_current_context(
    budget_remaining: float = 100.0,
    budget_consumed: float = 0.0,
    burn_rate: float = 1.0,
    tier: str = "standard",
    environment: str = "prod",
    downstream_count: int = 0,
    high_criticality_downstream: int = 0,
    now: datetime | None = None,
) -> dict[str, Any]:
    """
    Build context dictionary for condition evaluation.

    Args:
        budget_remaining: Percentage of error budget remaining (0-100)
        budget_consumed: Percentage of error budget consumed (0-100)
        burn_rate: Current burn rate multiplier (1.0 = normal)
        tier: Service tier (critical, standard, low)
        environment: Deployment environment (dev, staging, prod)
        downstream_count: Number of downstream services
        high_criticality_downstream: Number of high-criticality downstream services
        now: Current datetime (defaults to now)

    Returns:
        Context dictionary for condition evaluation
    """
    if now is None:
        now = datetime.now()

    return {
        # Time-based
        "hour": now.hour,
        "minute": now.minute,
        "weekday": now.weekday() < 5,  # Mon-Fri
        "day_of_week": now.weekday(),  # 0=Mon, 6=Sun
        "date": now.date().isoformat(),
        "month": now.month,
        "day": now.day,
        "year": now.year,
        # SLO-based
        "budget_remaining": budget_remaining,
        "budget_consumed": budget_consumed,
        "burn_rate": burn_rate,
        # Service-based
        "tier": tier,
        "environment": environment,
        "env": environment,  # Alias
        "downstream_count": downstream_count,
        "high_criticality_downstream": high_criticality_downstream,
    }


def is_business_hours(
    now: datetime | None = None,
    start_hour: int = 9,
    end_hour: int = 17,
) -> bool:
    """
    Check if current time is within business hours.

    Args:
        now: Current datetime (defaults to now)
        start_hour: Business hours start (default 9 AM)
        end_hour: Business hours end (default 5 PM)

    Returns:
        True if within business hours on a weekday
    """
    if now is None:
        now = datetime.now()

    # Must be a weekday
    if now.weekday() >= 5:
        return False

    # Check hour range
    return start_hour <= now.hour < end_hour


def is_weekday(now: datetime | None = None) -> bool:
    """
    Check if current day is a weekday (Mon-Fri).

    Args:
        now: Current datetime (defaults to now)

    Returns:
        True if Monday through Friday
    """
    if now is None:
        now = datetime.now()

    return now.weekday() < 5


def is_freeze_period(
    start_date: str,
    end_date: str,
    now: datetime | None = None,
) -> bool:
    """
    Check if current date is within a freeze period.

    Args:
        start_date: Freeze start date (YYYY-MM-DD)
        end_date: Freeze end date (YYYY-MM-DD)
        now: Current datetime (defaults to now)

    Returns:
        True if within freeze period

    Example:
        >>> is_freeze_period("2024-12-20", "2025-01-02")
        True  # If current date is Dec 25, 2024
    """
    if now is None:
        now = datetime.now()

    try:
        start = date.fromisoformat(start_date)
        end = date.fromisoformat(end_date)
        current = now.date()

        return start <= current <= end
    except ValueError:
        return False


def is_peak_traffic(
    now: datetime | None = None,
    peak_hours: list[tuple[int, int]] | None = None,
) -> bool:
    """
    Check if current time is during peak traffic hours.

    Args:
        now: Current datetime (defaults to now)
        peak_hours: List of (start, end) hour tuples (default: 10-12, 14-16)

    Returns:
        True if within peak traffic hours

    Example:
        >>> is_peak_traffic(peak_hours=[(10, 12), (14, 16)])
        True  # If current hour is 11 or 15
    """
    if now is None:
        now = datetime.now()

    if peak_hours is None:
        peak_hours = [(10, 12), (14, 16)]  # Default peaks

    hour = now.hour
    for start, end in peak_hours:
        if start <= hour < end:
            return True

    return False
