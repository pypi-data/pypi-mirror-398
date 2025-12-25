import logging
import os
import typing

import wialon.api

logger = logging.getLogger(__name__)


class WialonAPIError(Exception):
    """Raised when a Wialon API call fails."""

    def __init__(self, message, *args, **kwargs) -> None:
        self.message = message
        try:
            self._code = int(message._code)
        except ValueError:
            self._code = 6  # 'Unknown Error' according to Wialon
        return super().__init__(message, *args, **kwargs)

    @property
    def code(self) -> int:
        """Wialon API error code."""
        return self._code


class Wialon(wialon.api.Wialon):
    def call(self, action_name, *argc, **kwargs) -> dict[str, typing.Any]:
        try:
            return super().call(action_name, *argc, **kwargs)
        except wialon.api.WialonError as e:
            logger.warning(f"Failed to execute '{action_name}': '{e}'")
            raise WialonAPIError(e)


class WialonSession:
    def __init__(
        self,
        scheme: str = "https",
        host: str = "hst-api.wialon.com",
        port: int = 443,
        sid: str | None = None,
        token: str | None = None,
        auth_hash: str | None = None,
        username: str | None = None,
        check_service: str | None = None,
    ) -> None:
        """
        Starts or continues a Wialon API session.

        :param scheme: HTTP request scheme to use. Default is ``"https"``.
        :type scheme: str
        :param host: Wialon API host url. Default is ``"hst-api.wialon.com"``.
        :type host: str
        :param port: Wialon API port. Default is ``443``.
        :type port: int
        :param sid: A Wialon API session id. Default is :py:obj:`None`.
        :type sid: str | None
        :param token: A Wialon API token. Default is environment variable ``"WIALON_TOKEN"``.
        :type token: str | None
        :param auth_hash: A Wialon API authentication hash. Default is :py:obj:`None`.
        :type auth_hash: str | None
        :param username: A Wialon user to operate as during the session.
        :type username: str | None
        :param check_service: A Wialon service name to check before calling the Wialon API. Default is :py:obj:`None`.
        :type check_service: str | None
        :returns: Nothing.
        :rtype: None

        """
        self._uid = None
        self._wialon_api = Wialon(scheme=scheme, host=host, port=port, sid=sid)
        self._token = token if token else os.getenv("WIALON_TOKEN")
        self._username = username
        self._auth_hash = auth_hash
        self._check_service = check_service

    def __str__(self) -> str:
        return f"Session #{self.id}"

    def __repr__(self) -> str:
        return f"{self.__class__}(sid={self.id})"

    def __enter__(self) -> "WialonSession":
        """Logs into the Wialon API session if it wasn't already active before returning it."""
        if self.id is None:
            if self._token:
                self.token_login(token=self._token, username=self._username)
            elif self._auth_hash and self._username:
                self.auth_hash_login(
                    auth_hash=self._auth_hash,
                    username=self._username,
                    check_service=self._check_service,
                )
            else:
                raise WialonAPIError(
                    message="Failed to login to the Wialon API", code=9001
                )
        return self

    def __exit__(self, *args, **kwargs) -> None:
        """Logs out of the Wialon API session if :py:attr:`id` was set."""
        if self.id is not None:
            self.logout()

    def token_login(self, token: str, username: str | None = None) -> None:
        """
        Logs in to a Wialon API session using a token.

        :param token: A Wialon API token.
        :type token: str
        :param username: Wialon user to operate as during the Wialon API session. Default is :py:obj:`None`.
        :type username: str
        :returns: Nothing.
        :rtype: None

        """
        params = {"token": token, "flags": 0x3 if username else 0x1}
        if username is not None:
            params.update({"operateAs": username})
        response = self.wialon_api.token_login(**params)
        self.wialon_api.sid = response.get("eid")
        self._username = response.get("au")
        self._uid = response.get("user", {}).get("id")
        self._gis_sid = response.get("gis_sid")

    def auth_hash_login(
        self, auth_hash: str, username: str, check_service: str | None = None
    ) -> None:
        """
        Logs in to a Wialon API session using an auth hash.

        :param auth_hash: An authorization hash.
        :type auth_hash: str
        :param username: Wialon user to operate as during the Wialon API session.
        :type username: str
        :param check_service: Name of a Wialon service to check if the user has access to. Default is :py:obj:`None` (no service check).
        :type check_service: str | None
        :returns: Nothing.
        :rtype: None

        """
        params = {"authHash": auth_hash, "operateAs": username}
        if check_service is not None:
            params.update({"checkService": check_service})
        response = self.wialon_api.core_use_auth_hash(**params)
        self.wialon_api.sid = response.get("eid")
        self._username = response.get("au")
        self._uid = response.get("user", {}).get("id")

    def logout(self) -> None:
        """
        Logs out of the Wialon API session.

        :raises WialonAPIError: If the Wialon API session logout failed.
        :returns: Nothing.
        :rtype: None

        """
        session_id = self.wialon_api.sid
        if session_id is not None:
            response = self.wialon_api.core_logout({})
            if not int(response.get("error")) == 0:
                raise WialonAPIError(
                    message=f"Failed to logout of the Wialon API session #{session_id}",
                    code=int(response.get("error")),
                )
            self.wialon_api.sid = None

    @property
    def wialon_api(self) -> Wialon:
        return self._wialon_api

    @property
    def uid(self) -> str | None:
        """
        User id of the session's authenticated Wialon user.

        :type: str | None
        :value: None
        """
        return self._uid

    @property
    def username(self) -> str | None:
        """
        Username of the session's authenticated Wialon user.

        :type: str | None
        :value: None

        """
        return self._username

    @property
    def gis_sid(self) -> str | None:
        """
        GIS session id for the Wialon API session.

        :type: str | None
        :value: None

        """
        return self._gis_sid

    @property
    def id(self) -> str | None:
        """
        Wialon API session id.

        Shortcut property for :py:attr:`WialonSession.wialon_api.sid`.

        Returns :py:obj:`None` if the session wasn't logged in.

        :type: str | None
        :value: None

        """
        return self.wialon_api.sid
