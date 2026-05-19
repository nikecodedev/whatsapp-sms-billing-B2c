"""
CDC compliance rules (Lei 8.078/90 + LGPD).
All contact attempts must pass these checks before being sent.
"""
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

BRAZIL_TZ = ZoneInfo("America/Sao_Paulo")
CDC_START_HOUR = 8    # 08:00
CDC_END_HOUR = 21     # 21:00 (last send allowed at 20:59)
MAX_CONTACTS_PER_DAY = 1


def is_allowed_time(dt: datetime | None = None) -> bool:
    """Return True if the current time is within CDC-allowed contact hours."""
    now = dt or datetime.now(BRAZIL_TZ)
    if now.tzinfo is None:
        now = now.replace(tzinfo=BRAZIL_TZ)
    return CDC_START_HOUR <= now.hour < CDC_END_HOUR


def next_allowed_slot(from_dt: datetime | None = None) -> datetime:
    """Return the next datetime that is within CDC contact hours."""
    now = from_dt or datetime.now(BRAZIL_TZ)
    if now.tzinfo is None:
        now = now.replace(tzinfo=BRAZIL_TZ)

    if CDC_START_HOUR <= now.hour < CDC_END_HOUR:
        return now

    # If past 21:00, schedule for next day at 08:00
    if now.hour >= CDC_END_HOUR:
        next_day = (now + timedelta(days=1)).replace(
            hour=CDC_START_HOUR, minute=0, second=0, microsecond=0
        )
        return next_day

    # If before 08:00, schedule same day at 08:00
    return now.replace(hour=CDC_START_HOUR, minute=0, second=0, microsecond=0)


def parse_send_time(send_time_str: str, from_dt: datetime | None = None) -> datetime:
    """
    Convert AI-suggested HH:MM to a concrete datetime, respecting CDC rules.
    Falls back to next_allowed_slot if the suggested time is outside allowed hours.
    """
    base = from_dt or datetime.now(BRAZIL_TZ)
    if base.tzinfo is None:
        base = base.replace(tzinfo=BRAZIL_TZ)

    try:
        hour, minute = map(int, send_time_str.split(":"))
    except Exception:
        return next_allowed_slot(base)

    candidate = base.replace(hour=hour, minute=minute, second=0, microsecond=0)

    # If suggested time already passed today, move to tomorrow
    if candidate <= base:
        candidate += timedelta(days=1)

    if not (CDC_START_HOUR <= candidate.hour < CDC_END_HOUR):
        candidate = candidate.replace(hour=CDC_START_HOUR, minute=0, second=0, microsecond=0)

    return candidate


def contacted_today(last_contact_at: datetime | None) -> bool:
    """Return True if a contact was already made today for this debtor."""
    if last_contact_at is None:
        return False
    now = datetime.now(BRAZIL_TZ)
    last = last_contact_at.astimezone(BRAZIL_TZ) if last_contact_at.tzinfo else last_contact_at.replace(tzinfo=BRAZIL_TZ)
    return last.date() == now.date()


def interval_elapsed(last_contact_at: datetime | None, interval_hours: int) -> bool:
    """Return True if enough time has passed since the last contact attempt."""
    if last_contact_at is None:
        return True
    now = datetime.now(BRAZIL_TZ)
    last = last_contact_at.astimezone(BRAZIL_TZ) if last_contact_at.tzinfo else last_contact_at.replace(tzinfo=BRAZIL_TZ)
    return (now - last) >= timedelta(hours=interval_hours)
