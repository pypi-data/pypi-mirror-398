import json
from typing import Any, Dict, Optional


def prepare_metadata_for_headers(meta: Optional[Dict[str, Any]]) -> str:
    """Prepare metadata for HTTP header transmission.
    
    Handles user input gracefully without throwing errors.
    Note: json.dumps automatically escapes newlines (\n), carriage returns (\r), 
    and null characters (\0) as \\n, \\r, and \\u0000 respectively, making the 
    JSON string safe for HTTP headers.
    
    Args:
        meta: Raw metadata dictionary from user
        
    Returns:
        JSON string safe for HTTP headers
    """
    if not meta:
        return ""
    
    # Handle JSON serialization
    try:
        return json.dumps(meta)
    except (TypeError, ValueError):
        str_meta = {k: str(v) for k, v in meta.items()}
        return json.dumps(str_meta)
