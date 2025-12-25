from typing import Dict, Optional


def build_headers(
    api_key: Optional[str] = None,
    access_token: Optional[str] = None,
    extra_headers: Optional[Dict[str, str]] = None,
) -> Dict[str, str]:
    """
    Build HTTP headers for SDK requests.
    """

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "Reckomate-SDK/1.0.0",
    }

    token = api_key or access_token
    if token:
        headers["Authorization"] = f"Bearer {token}"

    if extra_headers:
        headers.update(extra_headers)

    return headers
