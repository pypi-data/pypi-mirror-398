from datetime import datetime, timezone

# Pick the right UTC tzinfo once at import time (this changed in 3.11+)
UTC = getattr(datetime, "UTC", timezone.utc)

def get_timestamp():
    return datetime.now(UTC)