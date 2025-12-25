from typing import Any, Dict
from urllib.parse import urljoin
import logging
import httpx

logger = logging.getLogger(__name__)


def safe_json(response: httpx.Response) -> Any:
    """Return response.json() when possible, else text, else None."""
    try:
        return response.json()
    except Exception:
        try:
            return response.text
        except Exception:
            logger.debug("Unable to parse response body as json or text")
            return None


def build_url(base_url: str, path_template: str, path_params: Dict[str, str] | None = None) -> str:
    """
    Build a full URL by combining base_url and path_template, substituting path_params.
    """

    if path_template.startswith("http://") or path_template.startswith("https://"):
        if path_params:
            path_template = path_template.format(**path_params)
        return path_template

    # Substitute path params if any
    if path_params:
        try:
            path = path_template.format(**path_params)
        except KeyError as e:
            missing = e.args[0]
            raise ValueError(f"Missing path param: '{missing}' for template '{path_template}'")

    else:
        path = path_template

    # Sanitize base and path to avoid accidental double slashes
    if base_url.endswith("/"):
        base_url = base_url[:-1]
    if not path.startswith("/"):
        path = "/" + path

    # urljoin ensures correct semantics
    return urljoin(base_url + "/", path.lstrip("/"))
