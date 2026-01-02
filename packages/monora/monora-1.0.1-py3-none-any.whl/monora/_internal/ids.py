"""ID generation utilities using ULID format."""
import time
import random
import os


def generate_ulid(prefix: str = "") -> str:
    """
    Generate a ULID-like identifier.
    Format: <prefix>_<timestamp><randomness>

    Args:
        prefix: Optional prefix (e.g., "evt", "trc", "spn")

    Returns:
        ULID string like "evt_01JCXYZ123ABC"
    """
    # Timestamp component (milliseconds since epoch, base32-ish)
    timestamp_ms = int(time.time() * 1000)

    # Random component (10 bytes = 16 base32 chars)
    random_bytes = os.urandom(10)
    random_part = random_bytes.hex()[:16].upper()

    # Base32-like encoding for timestamp (simplified)
    timestamp_part = f"{timestamp_ms:013X}"[:10]

    ulid = f"{timestamp_part}{random_part}"

    if prefix:
        return f"{prefix}_{ulid}"
    return ulid
