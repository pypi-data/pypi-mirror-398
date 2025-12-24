from __future__ import annotations

from typing import Any, Dict, Optional


class WhatsappApiException(Exception):
    """Exception raised for Instagram API errors.

    Captures HTTP details, endpoint, method, payload, and parsed error body when available.
    """

    def __init__(
        self,
        message: str,
        *,
        status_code: Optional[int] = None,
        endpoint: Optional[str] = None,
        method: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
        response_text: Optional[str] = None,
        response_json: Optional[Dict[str, Any]] = None,
        details: Optional[str] = None,
        error_code: Optional[str] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.endpoint = endpoint
        self.method = method
        self.payload = payload
        self.response_text = response_text
        self.response_json = response_json
        self.details = details
        self.error_code = error_code

    def __str__(self) -> str:
        base = self.message
        parts = []
        if self.status_code is not None:
            parts.append(f"status={self.status_code}")
        if self.endpoint:
            parts.append(f"endpoint={self.endpoint}")
        if self.method:
            parts.append(f"method={self.method}")
        if self.error_code:
            parts.append(f"error_code={self.error_code}")
        if self.details:
            parts.append(f"details={self.details}")
        if parts:
            base += " (" + ", ".join(parts) + ")"
        return base

    @classmethod
    def from_httpx_response(
        cls,
        response: Any,
        *,
        endpoint: Optional[str] = None,
        method: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
    ) -> "WhatsappApiException":
        """
        Build an exception from an httpx.Response, attempting to parse JSON error details.
        """
        status = getattr(response, "status_code", None)
        text = None
        data: Optional[Dict[str, Any]] = None
        code: Optional[str] = None
        message: str = "Instagram API request failed"

        try:
            data = response.json()
            # Graph API errors are often under { "error": { "message": "...", "code": 190, ... } }
            err = data.get("error") if isinstance(data, dict) else None
            if isinstance(err, dict):
                message = err.get("message") or message
                code_value = err.get("code")
                code = str(code_value) if code_value is not None else None
        except Exception:
            text = getattr(response, "text", None)

        return cls(
            message=message,
            status_code=status,
            endpoint=endpoint,
            method=method,
            payload=payload,
            response_text=text,
            response_json=data,
            error_code=code,
        )
