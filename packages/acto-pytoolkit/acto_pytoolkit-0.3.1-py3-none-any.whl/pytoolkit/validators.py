import ipaddress
import re
import uuid
from urllib.parse import urlparse


# More robust email regex following RFC 5322 (simplified)
EMAIL_REGEX = re.compile(
    r"^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$"
)


def is_email(value: str, strict: bool = False) -> bool:
    """Return true if the value looks like an email address.

    Parameters
    ----------
    value : str
        Email address to validate
    strict : bool
        If True, perform additional checks (length limits, no consecutive dots)

    Examples
    --------
    >>> is_email("user@example.com")
    True
    >>> is_email("invalid@")
    False
    """
    if not EMAIL_REGEX.match(value):
        return False
    
    if strict:
        # Additional checks for strict mode
        if len(value) > 254:  # RFC 5321
            return False
        local, domain = value.rsplit("@", 1)
        if len(local) > 64 or len(domain) > 253:
            return False
        if ".." in value:  # No consecutive dots
            return False
    
    return True


def is_url(value: str, require_tld: bool = True) -> bool:
    """Return true if the value looks like a HTTP or HTTPS URL.

    Parameters
    ----------
    value : str
        URL to validate
    require_tld : bool
        If True, require a top-level domain (e.g., .com, .org)

    Examples
    --------
    >>> is_url("https://example.com")
    True
    >>> is_url("ftp://example.com")
    False
    """
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return False
    
    if require_tld and "." not in parsed.netloc:
        return False
    
    return True


def is_uuid(value: str) -> bool:
    """Return true if the value is a valid UUID string."""
    try:
        uuid.UUID(value)
        return True
    except (ValueError, AttributeError, TypeError):
        return False


def has_extension(filename: str, extension: str) -> bool:
    """Return true if the filename has the given extension.

    The comparison is case insensitive and `extension` may optionally start with a dot.
    """
    ext = extension.lower().lstrip(".")
    return filename.lower().endswith("." + ext)


def is_ipv4(value: str) -> bool:
    """Return true if the value is a valid IPv4 address."""
    try:
        ipaddress.IPv4Address(value)
        return True
    except ipaddress.AddressValueError:
        return False


def is_ipv6(value: str) -> bool:
    """Return true if the value is a valid IPv6 address."""
    try:
        ipaddress.IPv6Address(value)
        return True
    except ipaddress.AddressValueError:
        return False


def min_length(value: str, length: int) -> bool:
    """Return true if the string has at least the given length."""
    return len(value) >= length


def max_length(value: str, length: int) -> bool:
    """Return true if the string has at most the given length."""
    return len(value) <= length
