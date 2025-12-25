"""Breach checking using HaveIBeenPwned k-anonymity API.

Implements privacy-preserving breach checking by sending only the first
5 characters of the SHA-1 hash to the API (k-anonymity model).
"""

import hashlib
from typing import Any

import httpx


HIBP_API_URL = "https://api.pwnedpasswords.com/range/"
TIMEOUT = 5.0  # seconds


def hash_password_sha1(password: str) -> str:
    """Hash password using SHA-1.

    Parameters
    ----------
    password : str
        Password to hash.

    Returns
    -------
    str
        Uppercase SHA-1 hash (40 hex characters).

    Raises
    ------
    ValueError
        If password is not a string.

    Examples
    --------
    >>> hash_password_sha1("password")
    '5BAA61E4C9B93F3F0682250B6CF8331B7EE68FD8'
    """
    if not isinstance(password, str):
        raise ValueError("Password must be a string")

    # SHA-1 is required by the HaveIBeenPwned API; this is not used to protect
    # stored secrets. Setting usedforsecurity=False also avoids FIPS-related
    # restrictions and silences Bandit (B324).
    return hashlib.sha1(
        password.encode("utf-8"),
        usedforsecurity=False,
    ).hexdigest().upper()


def get_hash_prefix_suffix(hash_value: str) -> tuple[str, str]:
    """Split hash into prefix (first 5 chars) and suffix.

    Parameters
    ----------
    hash_value : str
        SHA-1 hash (40 characters).

    Returns
    -------
    tuple[str, str]
        Prefix (5 chars) and suffix (35 chars).

    Raises
    ------
    ValueError
        If hash_value is not a 40-character string.

    Examples
    --------
    >>> get_hash_prefix_suffix("5BAA61E4C9B93F3F0682250B6CF8331B7EE68FD8")
    ('5BAA6', '1E4C9B93F3F0682250B6CF8331B7EE68FD8')
    """
    if not isinstance(hash_value, str) or len(hash_value) != 40:
        raise ValueError("hash_value must be a 40-character string")

    return hash_value[:5], hash_value[5:]


async def check_breach_api(password: str) -> dict[str, Any]:
    """Check password against HaveIBeenPwned API using k-anonymity.

    Parameters
    ----------
    password : str
        Password to check.

    Returns
    -------
    dict[str, Any]
        Breach check results with is_breached flag and count.

    Raises
    ------
    ValueError
        If password is not a string.

    Examples
    --------
    >>> import asyncio
    >>> result = asyncio.run(check_breach_api("password"))
    >>> result["is_breached"]
    True
    """
    if not isinstance(password, str):
        raise ValueError("Password must be a string")

    # Hash password
    hash_value = hash_password_sha1(password)
    prefix, suffix = get_hash_prefix_suffix(hash_value)

    try:
        # Query API with hash prefix
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.get(f"{HIBP_API_URL}{prefix}")
            response.raise_for_status()

        # Parse response - format is "SUFFIX:COUNT\n..."
        for line in response.text.splitlines():
            if ":" in line:
                hash_suffix, count = line.split(":", 1)
                if hash_suffix == suffix:
                    return {
                        "is_breached": True,
                        "breach_count": int(count),
                    }

        return {
            "is_breached": False,
            "breach_count": 0,
        }

    except (httpx.HTTPError, ValueError, TimeoutError) as e:
        # Return error state - don't fail password analysis
        return {
            "is_breached": False,
            "breach_count": 0,
            "error": str(e),
        }


async def analyze_breach(password: str) -> dict[str, Any]:
    """Comprehensive breach analysis.

    Parameters
    ----------
    password : str
        Password to analyze.

    Returns
    -------
    dict[str, Any]
        Breach analysis results with penalty score.

    Raises
    ------
    ValueError
        If password is not a string.

    Examples
    --------
    >>> import asyncio
    >>> result = asyncio.run(analyze_breach("password"))
    >>> result["is_breached"]
    True
    """
    if not isinstance(password, str):
        raise ValueError("Password must be a string")

    result = await check_breach_api(password)

    # Calculate penalty
    if result["is_breached"]:
        # Any breach is severe
        score_penalty = 100
    else:
        score_penalty = 0

    return {
        "is_breached": result["is_breached"],
        "breach_count": result.get("breach_count", 0),
        "score_penalty": score_penalty,
        "checked": True,
        "error": result.get("error"),
    }
