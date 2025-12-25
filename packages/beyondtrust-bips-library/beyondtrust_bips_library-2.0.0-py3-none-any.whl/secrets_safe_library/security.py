"""Security module, includes sensitive data sanitization."""

import re


def sanitize_sensitive_data(message: str) -> str:
    """
    Sanitize sensitive information from log messages.

    Arguments:
        message (str): The original log message

    Returns:
        str: Sanitized log message with sensitive data redacted
    """

    if not isinstance(message, str):
        message = str(message)

    # Define sensitive data patterns

    # Compile regex patterns once at module initialization
    _COMPILED_PATTERNS = [
        (
            re.compile(
                r'("?api_?key"?\s*[:=]\s*["\']?)([a-zA-Z0-9+/=_-]{20,200})(["\']?)'
            ),
            r"\1***REDACTED***\3",
        ),
        (
            re.compile(r'("?key"?\s*[:=]\s*["\']?)([a-zA-Z0-9+/=_-]{20,200})(["\']?)'),
            r"\1***REDACTED***\3",
        ),
        (
            re.compile(r'("?password"?\s*[:=]\s*["\'])([^"\']+)(["\'])'),
            r"\1***REDACTED***\3",
        ),
        (
            re.compile(r'("?password"?\s*[:=]\s*)([^\s;&,"\']+)(?=[\s;&,]|$)'),
            r"\1***REDACTED***",
        ),
        (
            re.compile(r'("?pwd"?\s*[:=]\s*["\'])([^"\']+)(["\'])'),
            r"\1***REDACTED***\3",
        ),
        (
            re.compile(r'("?pwd"?\s*[:=]\s*)([^\s;&,"\']+)(?=[\s;&,]|$)'),
            r"\1***REDACTED***",
        ),
        (
            re.compile(r'("?passwd"?\s*[:=]\s*["\'])([^"\']+)(["\'])'),
            r"\1***REDACTED***\3",
        ),
        (
            re.compile(r'("?passwd"?\s*[:=]\s*)([^\s;&,"\']+)(?=[\s;&,]|$)'),
            r"\1***REDACTED***",
        ),
        (
            re.compile(
                r'("?client_?secret"?\s*[:=]\s*["\']?)'
                r'([a-zA-Z0-9+/=_-]{20,200})(["\']?)'
            ),
            r"\1***REDACTED***\3",
        ),
        (
            re.compile(
                r'("?secret"?\s*[:=]\s*["\']?)([a-zA-Z0-9+/=_-]{20,200})(["\']?)'
            ),
            r"\1***REDACTED***\3",
        ),
        (re.compile(r"(Bearer\s+)([a-zA-Z0-9+/=._-]{20,500})"), r"\1***REDACTED***"),
        (
            re.compile(
                r'("?token"?\s*[:=]\s*["\']?)([a-zA-Z0-9+/=._-]{20,500})(["\']?)'
            ),
            r"\1***REDACTED***\3",
        ),
        (
            re.compile(
                r'("?access_?token"?\s*[:=]\s*["\']?)'
                r'([a-zA-Z0-9+/=._-]{20,500})(["\']?)'
            ),
            r"\1***REDACTED***\3",
        ),
        (
            re.compile(
                r'(Authorization["\']?\s*[:=]\s*["\']?)([^"\'\\n\\r]{10,500})(["\']?)'
            ),
            r"\1***REDACTED***\3",
        ),
        (
            re.compile(r"(-----BEGIN[^-]*-----)(.*?)(-----END[^-]*-----)", re.DOTALL),
            r"\1***REDACTED***\3",
        ),
        (
            re.compile(r"(https?://)([^:/@]+):([^@]+)(@[^\s]+)"),
            r"\1\2:***REDACTED***\4",
        ),
        (re.compile(r"(eyJ[a-zA-Z0-9+/=._-]{20,})"), r"***REDACTED_JWT***"),
        (re.compile(r'(["\'][a-zA-Z0-9+/=]{40,}["\'])'), r"***REDACTED***"),
    ]

    # Apply sanitization patterns
    sanitized_message = message
    for cregex, replacement in _COMPILED_PATTERNS:
        sanitized_message = cregex.sub(replacement, sanitized_message)

    # Additional keyword-based sanitization for common sensitive field names
    # Note: Skip keywords already handled by main patterns to avoid double-processing
    sensitive_keywords = [
        "password",
        "passwd",
        "pwd",
        "secret",
        "token",
        "key",
        "api_key",
        "apikey",
        "client_secret",
        "client_key",
        "private_key",
        "certificate",
        "cert",
        "credential",
        "auth",
        "authorization",
        "access_token",
        "refresh_token",
    ]

    # Look for patterns like "field": "value" or field=value where field is sensitive
    for keyword in sensitive_keywords:
        # JSON-style assignments
        pattern = rf'("{keyword}"\s*:\s*")([^"]+)(")'
        sanitized_message = re.sub(
            pattern, r"\1***REDACTED***\3", sanitized_message, flags=re.IGNORECASE
        )

        # Form-style assignments for unquoted values
        # Use word boundaries and more specific delimiters
        pattern = rf'\b({keyword}\s*=\s*)([^\s;&,"\']+)(?=[\s;&,]|$)'
        sanitized_message = re.sub(
            pattern, r"\1***REDACTED***", sanitized_message, flags=re.IGNORECASE
        )

        # Form-style assignments for quoted values (single and double quotes)
        pattern = rf'\b({keyword}\s*=\s*")([^"]*?)(")'
        sanitized_message = re.sub(
            pattern, r"\1***REDACTED***\3", sanitized_message, flags=re.IGNORECASE
        )

        pattern = rf"\b({keyword}\s*=\s*')([^']*?)(')"
        sanitized_message = re.sub(
            pattern, r"\1***REDACTED***\3", sanitized_message, flags=re.IGNORECASE
        )

    return sanitized_message
