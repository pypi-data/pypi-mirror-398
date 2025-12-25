import logging

from sapure.services import aservices


logging.getLogger("httpx").setLevel(logging.ERROR)


__all__ = ["aservices"]
