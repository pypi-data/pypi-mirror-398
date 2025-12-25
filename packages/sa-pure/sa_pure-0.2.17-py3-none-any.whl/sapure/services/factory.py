from typing import Dict
from typing import Optional
from typing import TypeVar

import httpx
from sapure.auth.httpx_backends import SAInternalAuth
from sapure.auth.httpx_backends import SASDKAuth
from sapure.auth.httpx_backends import SAuthType


TService = TypeVar("TService")


def build_auth(
    auth_type: SAuthType,
    *,
    # SDK auth
    sdk_token: Optional[str] = None,
    # Internal/Vault auth
    vault_addr: Optional[str] = None,
    vault_role: Optional[str] = None,
    kubernetes_token_path: Optional[str] = None,
    internal_token_path: Optional[str] = None,
) -> httpx.Auth:
    """
    Construct an httpx.Auth instance based on the desired authentication mode.

    Args:
        auth_type: "sdk" or "internal".
        sdk_token: Token string for SASDKAuth (when auth_type="sdk").
        vault_addr, vault_role, kubernetes_token_path, internal_token_path:
            Parameters for SAInternalAuth (when auth_type="internal"). If omitted,
            corresponding environment variables will be used by SAInternalAuth.

    Returns:
        An httpx.Auth implementation.
    """
    if auth_type == "sdk":
        if not sdk_token:
            raise ValueError("sdk_token is required when auth_type='sdk'")
        return SASDKAuth(sdk_token=sdk_token)
    if auth_type == "internal":
        return SAInternalAuth(
            vault_addr=vault_addr,
            vault_role=vault_role,
            kubernetes_token_path=kubernetes_token_path,
            internal_token_path=internal_token_path,
        )
    raise ValueError(f"Unsupported auth_type: {auth_type}")


def make_client(
    *,
    auth: Optional[httpx.Auth] = None,
    timeout: Optional[float] = 30.0,
    headers: Optional[Dict[str, str]] = None,
    base_url: Optional[str] = None,
    http2: bool = False,
    verify: bool | str | None = None,
) -> httpx.Client:
    """
    Build a configured httpx.Client suitable for Service classes in sapure.services.*

    Notes:
    - Services typically construct full URLs using their own service_url, so base_url
      is optional here. It is provided for callers who prefer to set it.
    """
    client = httpx.Client(
        auth=auth,
        timeout=timeout,
        headers=headers,
        base_url=base_url or "",
        http2=http2,
        verify=verify,
    )
    return client


def make_aclient(
    *,
    auth: Optional[httpx.Auth] = None,
    timeout: Optional[float] = 30.0,
    headers: Optional[Dict[str, str]] = None,
    base_url: Optional[str] = None,
    http2: bool = False,
    verify: bool | str | None = None,
) -> httpx.AsyncClient:
    """
    Build a configured httpx.Client suitable for Service classes in sapure.services.*

    Notes:
    - Services typically construct full URLs using their own service_url, so base_url
      is optional here. It is provided for callers who prefer to set it.
    """
    client = httpx.AsyncClient(
        auth=auth,
        timeout=timeout,
        headers=headers,
        base_url=base_url or "",
        http2=http2,
        verify=verify,
    )
    return client
