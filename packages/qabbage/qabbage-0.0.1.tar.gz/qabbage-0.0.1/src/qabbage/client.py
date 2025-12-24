from __future__ import annotations

from typing import Any, Dict, Optional
import httpx


import os

DEFAULT_BASE_URL = os.getenv("QABBAGE_BASE_URL", "http://3.78.181.66:8000")


def solve(problem: Dict[str, Any], base_url: str = DEFAULT_BASE_URL, timeout: float = 60.0) -> Dict[str, Any]:
    """
    Send a problem to the Qabbage server and return the result.
    """
    url = f"{base_url.rstrip('/')}/solve"
    with httpx.Client(timeout=timeout) as client:
        r = client.post(url, json={"problem": problem})
        r.raise_for_status()
        return r.json()
