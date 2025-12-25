import base64
import json
from urllib.parse import urljoin


def join_url(base: str, path: str) -> str:
    # If `path` starts with "/", treat it as absolute — don't modify.
    if path.startswith("/"):
        return urljoin(base, path)
    # Ensure the base ends with "/"
    if not base.endswith("/"):
        base += "/"
    return urljoin(base, path)


def generate_context(**kwargs):
    encoded_context = base64.b64encode(json.dumps(kwargs).encode("utf-8"))
    return encoded_context.decode("utf-8")
