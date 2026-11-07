"""Timer gates: everyone waits for the next drop; the wait shrinks as the streak grows.

Pure code, no LLM. Kuku tunes TIERS and LEVELS; nothing else changes.
"""
import re
from datetime import datetime, timedelta

TIERS = {
    # drops_per_unlock: how many ~5 min drops open at once; waits_h: wait at streak level 0, 1, 2
    "free": {"drops_per_unlock": 1, "waits_h": [24, 10, 5]},
    "subscriber": {"drops_per_unlock": 2, "waits_h": [10, 5, 2]},  # assumption: shorter, never zero
}
LEVELS = [0, 3, 7]  # streak days needed to reach level 0, 1, 2
GRACE_H = 24  # come back within this long after an unlock to keep the streak


def level(streak):
    return max(i for i, need in enumerate(LEVELS) if max(0, streak) >= need)


def next_unlock(watched_at: datetime, tier: str, streak: int) -> datetime:
    return watched_at + timedelta(hours=TIERS[tier]["waits_h"][level(streak)])


def reminder(unlock_at: datetime, slots: list) -> datetime:
    """First of the viewer's own time slots ("HH:MM") at or after the unlock: the appointment."""
    times = []
    for day in (0, 1):
        for s in [s for s in (slots or []) if re.fullmatch(r"([01]\d|2[0-3]):[0-5]\d", s)] or ["20:00"]:
            h, m = map(int, s.split(":"))
            t = (unlock_at + timedelta(days=day)).replace(hour=h, minute=m, second=0, microsecond=0)
            if t >= unlock_at:
                times.append(t)
    return min(times)


def update_streak(streak: int, unlock_at: datetime, came_back_at: datetime) -> int:
    """On time: streak + 1. Late: fall back one level, not to zero."""
    if came_back_at <= unlock_at + timedelta(hours=GRACE_H):
        return streak + 1
    return LEVELS[max(level(streak) - 1, 0)]


def simulate(tier, slots, total_drops, days=10, start=None, skip_days=()):
    """Viewer who watches at each reminder (except on skip_days). Returns one row per session."""
    t = start or datetime(2026, 11, 9, 20, 0)
    streak, opened, rows = 0, 0, []
    for day in range(days):
        if opened >= total_drops:
            break
        opened = min(total_drops, opened + TIERS[tier]["drops_per_unlock"])
        unlock = next_unlock(t, tier, streak)
        remind = reminder(unlock, slots)
        rows.append({"session": day + 1, "watched_at": t.isoformat(timespec="minutes"), "streak": streak,
                     "drops_open": opened, "wait_h": TIERS[tier]["waits_h"][level(streak)],
                     "next_unlock": unlock.isoformat(timespec="minutes"),
                     "reminder": remind.isoformat(timespec="minutes")})
        back = remind + (timedelta(days=2) if day + 1 in skip_days else timedelta())
        streak, t = update_streak(streak, unlock, back), back
    return rows
