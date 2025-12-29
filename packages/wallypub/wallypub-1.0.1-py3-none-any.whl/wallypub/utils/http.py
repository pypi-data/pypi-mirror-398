import ssl
import json
import http.client
from typing import Any, Dict, Optional

BAD_REQUEST = 400
GET_METHOD = "GET"
POST_METHOD = "POST"
PUT_METHOD = "PUT"
DELETE_METHOD = "DELETE"


class HttpsClient:
    """
    Wrapper class for http.client.HTTPSConnection
    """

    def __init__(
        self,
        host: str,
        port: int = 443,
        timeout: float = 10.0,
        context: ssl.SSLContext | None = None,
    ) -> None:
        self.host = host
        self.port = port
        self.timeout = timeout
        self.context = context or ssl.create_default_context()

    def _request(
        self,
        method: str,
        path: str,
        body: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        conn = http.client.HTTPSConnection(
            host=self.host,
            port=self.port,
            timeout=self.timeout,
            context=self.context,
        )
        try:
            hdr = headers or {}
            if body is not None:
                data = json.dumps(body).encode("utf-8")
                hdr.setdefault("Content-Type", "application/json")
            else:
                data = None

            conn.request(method, path, body=data, headers=hdr)
            resp = conn.getresponse()
            payload = resp.read()

            if resp.status >= BAD_REQUEST:
                raise RuntimeError(
                    f"{method} {path} failed: {resp.status} {resp.reason}"
                )
            if not payload:
                return {}
            return json.loads(payload)
        finally:
            conn.close()

    def get(self, path: str, **kw: Any) -> None:
        self._request(GET_METHOD, path, **kw)

    def delete(self, path: str, **kw: Any) -> None:
        self._request(DELETE_METHOD, path, **kw)

    def post(self, path: str, body: Dict[str, Any], **kw: Any) -> None:
        self._request(POST_METHOD, path, body=body, **kw)

    def put(self, path: str, body: Dict[str, Any], **kw: Any) -> None:
        self._request(PUT_METHOD, path, body=body, **kw)
