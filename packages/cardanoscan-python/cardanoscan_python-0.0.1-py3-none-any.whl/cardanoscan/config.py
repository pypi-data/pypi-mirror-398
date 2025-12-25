from typing import Optional, Dict

DEFAULT_TIMEOUT = 10.0

class BaseConfig:
    def __init__(
        self,
        base_url: str = "https://api.cardanoscan.io/api/v1",
        api_key: Optional[str] = None,
        timeout: float = DEFAULT_TIMEOUT,
        headers: Optional[Dict[str, str]] = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.headers = headers or {}

    def auth_headers(self) -> Dict[str, str]:
        headers = dict(self.headers)
        if self.api_key:
            headers["apiKey"] = f"{self.api_key}"
        return headers
