import asyncio
import logging
import os
import time
from functools import lru_cache
from typing import Literal
from typing import Optional

import httpx
import hvac
from sapure.auth.exceptions import SAAuthError
from sapure.utils import async_timed_lru_cache


logger = logging.getLogger(__file__)

SAuthType = Literal["sdk", "internal"]


@lru_cache(maxsize=None)
def retrieve_k8s_credentials(kubernetes_token_path):
    with open(kubernetes_token_path, "r") as f:
        return f.read().strip()


@async_timed_lru_cache(ttl_seconds=3600)
async def retrieve_vault_token(vault_addr, vault_role, kubernetes_token_path):
    async with httpx.AsyncClient() as client:
        # Authenticate with Vault
        auth_response = await client.post(
            f"{vault_addr}/v1/auth/kubernetes/login",
            json={
                "role": vault_role,
                "jwt": retrieve_k8s_credentials(kubernetes_token_path),
            },
        )
        auth_response.raise_for_status()
        vault_token = auth_response.json()["auth"]["client_token"]
        return vault_token


class SAInternalAuth(httpx.Auth):
    """
    Authentication handler for internal services using HashiCorp Vault.

    This class provides a robust authentication mechanism for internal service-to-service communication.
    It leverages HashiCorp Vault for secure token management and implements automatic token refresh
    mechanisms. The authentication process works as follows:

    1. Retrieves authentication tokens from Vault using Kubernetes service account credentials
    2. Attaches tokens to requests via both headers and query parameters for maximum compatibility
    3. Automatically refreshes tokens on authentication failures (401/403 responses)
    4. Supports both synchronous and asynchronous HTTP requests

    The class can be configured through environment variables or direct initialization parameters:
    - VAULT_ADDR: Address of the Vault server
    - VAULT_ROLE: Kubernetes role for Vault authentication
    - KUBERNETES_TOKEN_PATH: Path to Kubernetes service account token
    - INTERNAL_TOKEN_PATH: Path to the internal token secret in Vault
    """

    AUTH_TYPE: SAuthType = "internal"

    def __init__(
        self,
        vault_addr: Optional[str] = None,
        vault_role: Optional[str] = None,
        kubernetes_token_path: Optional[str] = None,
        internal_token_path: Optional[str] = None,
    ):
        self.vault_addr = vault_addr if vault_addr else os.environ.get("VAULT_ADDR")
        self.vault_role = vault_role if vault_role else os.environ.get("VAULT_ROLE")
        self.kubernetes_token_path = (
            kubernetes_token_path
            if kubernetes_token_path
            else os.getenv(
                "KUBERNETES_TOKEN_PATH",
                "/var/run/secrets/kubernetes.io/serviceaccount/token",
            )
        )
        self.internal_token_path = (
            internal_token_path
            if internal_token_path
            else os.environ.get("INTERNAL_TOKEN_PATH")
        )

        self._secret = None

    def get_vault_client(self) -> hvac.Client:
        # Read the Kubernetes service account token
        with open(self.kubernetes_token_path, "r") as file:
            token = file.read().strip()

        client = hvac.Client(url=self.vault_addr)
        client.auth.kubernetes.login(role=self.vault_role, jwt=token)

        if not client.is_authenticated():
            raise SAAuthError("Failed to authenticate to Vault.")
        return client

    @staticmethod
    def _normalize_path(path: str) -> str:
        if path.startswith("kv/data/"):
            return path[len("kv/data/") :]
        return path

    def _fetch_secret(self) -> str:
        try:
            client = self.get_vault_client()
            internal_token = client.secrets.kv.v2.read_secret_version(
                mount_point="kv", path=self._normalize_path(self.internal_token_path)
            )["data"]["data"]["key"]
        except SAAuthError:
            raise
        except Exception as e:
            raise SAAuthError(str(e))
        return internal_token

    async def _afetch_secret(self) -> str:
        vault_url = f"{self.vault_addr}/v1/kv/data/{self.internal_token_path}"
        token = await retrieve_vault_token(
            vault_addr=self.vault_addr,
            vault_role=self.vault_role,
            kubernetes_token_path=self.kubernetes_token_path,
        )
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(vault_url, headers=headers)

        if response.status_code == 200:
            vault_data = response.json()
            # Extract the token from Vault response structure
            return vault_data["data"]["data"]["key"]
        else:
            logger.error(f"Vault API returned {response.status_code}")
            raise Exception(
                f"Failed to get internal token from Vault: {response.status_code}"
            )

    def _get_secret(self) -> str:
        if not self._secret:
            self._secret = self._fetch_secret()
        return self._secret

    async def _aget_secret(self) -> str:
        if not self._secret:
            self._secret = await self._afetch_secret()
        return self._secret

    def _refresh_auth_token(self):
        self._secret = self._fetch_secret()

    async def _arefresh_auth_token(self):
        self._secret = await self._afetch_secret()

    def _add_auth_headers(self, request: httpx.Request):
        request.headers.update(
            {
                "Authorization": self._get_secret(),
                "authtype": self.AUTH_TYPE,
            }
        )

    async def _aadd_auth_headers(self, request: httpx.Request):
        request.headers.update(
            {
                "Authorization": await self._aget_secret(),
                "authtype": self.AUTH_TYPE,
            }
        )

    def _add_auth_params(self, request: httpx.Request):
        request.url = request.url.copy_merge_params(
            {"internal_token": self._get_secret()}
        )

    async def _aadd_auth_params(self, request: httpx.Request):
        request.url = request.url.copy_merge_params(
            {"internal_token": await self._aget_secret()}
        )

    def _sign_request(self, request: httpx.Request):
        self._add_auth_headers(request)
        self._add_auth_params(request)

    async def _asign_request(self, request: httpx.Request):
        await self._aadd_auth_headers(request)
        self._add_auth_params(request)

    def sync_auth_flow(self, request: httpx.Request):
        self._sign_request(request)
        response = yield request  # Send request

        if response.status_code in [401, 403]:  # If unauthorized, refresh and retry
            self._refresh_auth_token()
            self._sign_request(request)
            yield request

    async def async_auth_flow(self, request: httpx.Request):
        await self._asign_request(request)
        response = yield request

        if response.status_code in [401, 403]:
            await self._arefresh_auth_token()
            await self._asign_request(request)
            yield request


class SASDKAuth(httpx.Auth):
    """
    Authentication using an SDK token for HTTPX requests.

    This class implements both synchronous and asynchronous authentication flows
    by adding authentication headers to HTTPX requests.
    """

    AUTH_TYPE: SAuthType = "sdk"

    def __init__(self, sdk_token: Optional[str]):
        self.sdk_token = sdk_token

    def _add_auth_headers(self, request: httpx.Request):
        request.headers.update(
            {
                "Authorization": self.sdk_token,
                "authtype": self.AUTH_TYPE,
            }
        )

    def _sign_request(self, request: httpx.Request):
        self._add_auth_headers(request)

    def sync_auth_flow(self, request: httpx.Request):
        self._sign_request(request)
        response = yield request  # Send request

        if response.status_code in [401, 403]:  # If unauthorized, refresh and retry
            time.sleep(1)
            yield request

    async def async_auth_flow(self, request: httpx.Request):
        self._sign_request(request)
        response = yield request

        if response.status_code in [401, 403]:
            await asyncio.sleep(1)
            self._sign_request(request)
            yield request


class SAJWTAuth(httpx.Auth):
    AUTH_TYPE: SAuthType = "sdk"

    def __init__(self, token: Optional[str]):
        self.token = token

    def _add_auth_headers(self, request: httpx.Request):
        request.headers.update({"Authorization": self.token})

    def _sign_request(self, request: httpx.Request):
        self._add_auth_headers(request)
