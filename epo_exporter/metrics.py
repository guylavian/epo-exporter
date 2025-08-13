from typing import Optional


def get_int(value) -> Optional[int]:
    try:
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return int(value)
        return int(str(value).strip())
    except Exception:
        return None


def get_str(value) -> Optional[str]:
    if value is None:
        return None
    return str(value)


def parse_epoch_or_iso(value) -> Optional[int]:
    """Parse int-like epoch seconds or ISO datetime into epoch seconds."""
    integer_value = get_int(value)
    if integer_value is not None and integer_value > 0:
        return integer_value
    try:
        from datetime import datetime

        # Handle trailing Z
        return int(datetime.fromisoformat(str(value).replace("Z", "+00:00")).timestamp())
    except Exception:
        return None


