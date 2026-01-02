from typing import Dict, Optional

try:
    import requests
except ImportError:
    raise ImportError("This module depends on requests.")


def create_session(
    session: Optional[requests.Session] = None,
    session_attrs: Optional[Dict] = None,
) -> requests.Session:
    session = session or requests.Session()
    if not session_attrs:
        return session
    if "proxies" in session_attrs:
        session.proxies = session_attrs.pop("proxies")
    elif "proxy" in session_attrs:
        session.proxies = session_attrs.pop("proxy")
    if "stream" in session_attrs:
        session.stream = session_attrs.pop("stream")
    if "verify" in session_attrs or "verify_ssl" in session_attrs:
        session.verify = session_attrs.pop(
            "verify", session_attrs.pop("verify_ssl", True)
        )
    if "cert" in session_attrs:
        session.cert = session_attrs.pop("cert")
    if "max_redirects" in session_attrs:
        session.max_redirects = session_attrs.pop("max_redirects")
    if "trust_env" in session_attrs:
        session.trust_env = session_attrs.pop("trust_env")

    return session


def safe_request(
    url: str,
    method: str = None,
    params: Optional[Dict] = None,
    data: Optional[Dict] = None,
    json: Optional[Dict] = None,
    headers: Optional[Dict] = None,
    allow_redirects: bool = False,
    timeout: int = 30,
    verify_ssl: bool = True,
    session: Optional[requests.Session] = None,
    session_attrs: Optional[Dict] = None,
) -> requests.Response:
    """A slightly safer version of `request`."""

    session = create_session(session, session_attrs)

    kwargs = {}

    if json:
        kwargs["json"] = json
        if not headers:
            headers = {}
        headers.setdefault("Content-Type", "application/json")

    if data:
        kwargs["data"] = data

    if params:
        kwargs["params"] = params

    if headers:
        kwargs["headers"] = headers

    method = method or ("POST" if (data or json) else "GET")

    response = session.request(
        method=method,
        url=url,
        allow_redirects=allow_redirects,
        timeout=timeout,
        verify=verify_ssl,
        **kwargs,
    )

    return response
