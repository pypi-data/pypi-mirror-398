from urllib.parse import urlparse

# keyring is not available in the snowflake notebook environment
try:
    import keyring
    KEYRING_AVAILABLE = True
except ImportError:
    KEYRING_AVAILABLE = False
    keyring = None

def is_localhost(url: str) -> bool:
    parsed = urlparse(url)
    hostname = parsed.hostname

    return hostname in {"localhost", "127.0.0.1", "::1"}

def extract_port(url: str) -> int:
    parsed = urlparse(url)
    port = parsed.port
    if port is None:
        if parsed.scheme == "https":
            port = 443
        else:
            port = 80
    return port

def remove_url_scheme(url: str) -> str:
    parsed = urlparse(url)
    # If there's a scheme, reconstruct without it
    if parsed.scheme:
        return parsed.netloc + parsed.path
    return url
    
def is_keyring_secure() -> bool:
    if not KEYRING_AVAILABLE or keyring is None:
        return False
    kr = keyring.get_keyring()
    if kr.__class__.__name__ in ("PlaintextKeyring", "fail"):
        print("Warning: Keyring is not secure. Please use a secure keyring backend.")
        return False
    return True
