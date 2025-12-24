import time
from typing import Optional
from ..errors import QueryTimeoutExceededException

def calc_remaining_timeout_minutes(start_time: float, total_query_timeout: Optional[int], config_file_path: Optional[str]) -> Optional[int]:
    """Return the remaining whole minutes in the global budget.
       Raise if none are left.
    """
    if total_query_timeout is None:
        return None

    elapsed = time.monotonic() - start_time
    remaining_seconds = total_query_timeout * 60 - elapsed

    # Convert to full minutes (floor division)
    remaining_minutes = int(remaining_seconds // 60)

    if remaining_minutes <= 0:
        raise QueryTimeoutExceededException(
            total_query_timeout, config_file_path=config_file_path,
        )

    return remaining_minutes

