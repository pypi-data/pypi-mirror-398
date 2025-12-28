import re
from typing import Any

RSYNC_RATE_LIMIT_RE = re.compile(r"^(?:\d+|\d+m|\d+\.\d+m)$")

def is_rsync_rate_limit(value: Any) -> bool:
    return (
        (isinstance(value, int) and value >= 0)
        or
        (isinstance(value, str) and bool(re.match(RSYNC_RATE_LIMIT_RE, value)))
    )
