from datetime import time, datetime, timedelta


def add_to_time(t: time, hours: int = 0, minutes: int = 0) -> time:
    base = datetime.combine(datetime.today(), t)
    updated = base + timedelta(hours=hours, minutes=minutes)
    return updated.time()


def remove_to_time(t: time, hours: int = 0, minutes: int = 0) -> time:
    base = datetime.combine(datetime.today(), t)
    updated = base - timedelta(hours=hours, minutes=minutes)
    return updated.time()
