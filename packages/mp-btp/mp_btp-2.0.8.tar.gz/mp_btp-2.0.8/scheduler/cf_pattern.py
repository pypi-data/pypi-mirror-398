"""CF Active Pattern logic."""
from datetime import date, timedelta
from typing import Tuple

def parse_pattern(pattern: str) -> Tuple[int, int]:
    """Parse 'n-m' pattern to (window_days, active_days)."""
    try:
        parts = pattern.split('-')
        return int(parts[0]), int(parts[1])
    except:
        return 7, 5  # default

def should_be_active_today(active_pattern: str, history: dict, today: date = None) -> bool:
    """
    Determine if CF should be active today based on pattern.
    
    Pattern "7-5" means: in a 7-day window, be active 5 days.
    Pattern "7-7" means: always active (restart if stopped).
    """
    if today is None:
        today = date.today()
    
    window_days, target_active_days = parse_pattern(active_pattern)
    
    # Special case: always active
    if window_days == target_active_days:
        return True
    
    # Count active days in the past (window - 1) days
    active_count = 0
    for i in range(1, window_days):
        day = today - timedelta(days=i)
        day_str = day.isoformat()
        if history.get(day_str, False):
            active_count += 1
    
    # If we haven't reached target, should be active today
    return active_count < target_active_days

def update_history(history: dict, today: date, was_active: bool, window_days: int = 7) -> dict:
    """Update history and prune old entries."""
    history = dict(history) if history else {}
    history[today.isoformat()] = was_active
    
    # Prune entries older than window
    cutoff = today - timedelta(days=window_days)
    return {k: v for k, v in history.items() if date.fromisoformat(k) >= cutoff}
