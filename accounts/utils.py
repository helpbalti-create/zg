"""
accounts/utils.py — shared security utilities.
"""


def get_client_ip(request) -> str:
    """
    Return the real client IP address.

    Security note: X-Forwarded-For can be spoofed by any client unless
    your infrastructure strips/overwrites it.  We only trust it when it
    is set AND we take the *last* IP in the chain (the one appended by
    the first trusted reverse-proxy), which cannot be forged.

    If you run behind a single reverse-proxy (nginx/Caddy) you can safely
    use x_forwarded[-1].  If you run directly (no proxy), REMOTE_ADDR is
    authoritative and cannot be spoofed.
    """
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if x_forwarded_for:
        # Last entry is set by the nearest trusted proxy — not the client
        ip = x_forwarded_for.split(",")[-1].strip()
    else:
        ip = request.META.get("REMOTE_ADDR", "")
    return ip


def axes_oauth_whitelist(request) -> bool:
    """
    Tell axes to never lock out OAuth callback URLs.

    These endpoints have no password field — they receive a one-time code
    from Google/GitHub. Counting them as login failures would be wrong, and
    axes blocking them returns 401 to the OAuth provider's redirect.
    """
    return request.path.startswith('/oauth/')
