"""Token providers module."""

import datetime
from typing import Mapping
from typing import Optional

import requests

from driverlessai import _logging


class OAuth2TokenProvider:
    def __init__(
        self,
        refresh_token: str,
        client_id: str,
        token_endpoint_url: str,
        token_introspection_url: str,
        access_token: Optional[str] = None,
        client_secret: Optional[str] = None,
        *,
        refresh_expiry_threshold_band: datetime.timedelta = datetime.timedelta(
            seconds=5
        ),
    ) -> None:
        """
        Provide an [OAuth 2.0](https://oauth.net/2/) token.

        Args:
            refresh_token: The refresh token (from the Driverless AI server web UI)
                used to obtain new access tokens.
            client_id: The client identifier as assigned by the authorization server.
            token_endpoint_url: The URL of the authorization server's token endpoint.
            token_introspection_url: The URL of the authorization server's
                token introspection endpoint.
            access_token: The initial access token, if available.
            client_secret: The client secret, if required for the client credentials.
            refresh_expiry_threshold_band: The time duration before actual expiry when
                the access token should be refreshed.

        ??? Example
            ```py
            # Create a token provider with a refresh token from the Driverless AI web UI
            token_provider = driverlessai.token_providers.OAuth2TokenProvider(
                refresh_token="eyJhbGciOiJIUzI1N...",
                client_id="python_client",
                token_endpoint_url="https://keycloak-server/auth/realms/driverlessai/protocol/openid-connect/token",
                token_introspection_url="https://keycloak-server/auth/realms/driverlessai/protocol/openid-connect/token/introspect"
            )

            # Use the token provider to get authorization to connect to the server
            client = driverlessai.Client(
                address="https://localhost:12345",
                token_provider=token_provider.ensure_fresh_token
            )
            ```
        """
        self._access_token = access_token
        self._refresh_token = refresh_token
        self._token_expiry: datetime.datetime = None

        self._client_id = client_id
        self._client_secret = client_secret

        self._token_endpoint_url = token_endpoint_url
        self._token_introspection_url = token_introspection_url

        self._refresh_expiry_threshold_band = refresh_expiry_threshold_band

    def ensure_fresh_token(self) -> str:
        """
        Returns an access token ensuring that it is fresh and valid.

        Returns:
            The current access token.
        """
        if self.refresh_possible() and self.refresh_required():
            self.do_refresh()
        return self._access_token

    def refresh_required(self) -> bool:
        """
        Returns whether the current access token needs to be refreshed.

        Returns:
            `True` if the current access token needs to be refreshed, otherwise `False`.
        """
        if self._access_token is None:
            return True

        now = datetime.datetime.now(datetime.timezone.utc)
        return self._token_expiry is None or (
            self._token_expiry <= (now + self._refresh_expiry_threshold_band)
        )

    def refresh_possible(self) -> bool:
        """
        Returns whether it is possible to refresh the access token.

        Returns:
            `True` if possible to refresh the access token, otherwise `False`.
        """
        return self._refresh_token is not None

    def do_refresh(self) -> None:
        """Refreshes the current access token."""
        token_data = self._retrieve_token_data()
        self._access_token = token_data["access_token"]
        self._refresh_token = token_data["refresh_token"]

        token_expires_in = token_data.get("expires_in")
        if token_expires_in:
            self._token_expiry = datetime.datetime.now(
                datetime.timezone.utc
            ) + datetime.timedelta(seconds=int(token_expires_in))
            return

        token_info = self._retrieve_access_token_info()
        expiry_timestamp = int(token_info["exp"])
        self._token_expiry = datetime.datetime.fromtimestamp(
            expiry_timestamp, tz=datetime.timezone.utc
        )

    def _retrieve_token_data(self) -> Mapping[str, str]:
        data = dict(
            client_id=self._client_id,
            grant_type="refresh_token",
            refresh_token=self._refresh_token,
        )
        if self._client_secret:
            data["client_secret"] = self._client_secret

        resp = requests.post(self._token_endpoint_url, data=data)
        try:
            resp.raise_for_status()
        except requests.exceptions.HTTPError:
            _logging.logger.error(resp.text)
            raise

        return resp.json()

    def _retrieve_access_token_info(self) -> Mapping:
        data = dict(client_id=self._client_id, token=self._access_token)

        if self._client_secret:
            data["client_secret"] = self._client_secret

        resp = requests.post(self._token_introspection_url, data=data)
        try:
            resp.raise_for_status()
        except requests.exceptions.HTTPError:
            _logging.logger.error(resp.text)
            raise

        return resp.json()
