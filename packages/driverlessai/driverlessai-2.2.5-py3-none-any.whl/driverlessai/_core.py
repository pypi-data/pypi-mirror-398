"""Core module."""

import json
import re
from pathlib import Path
from typing import Any, Callable, Dict, Optional, TYPE_CHECKING, Union

import requests

from driverlessai import __version__
from driverlessai import _admin
from driverlessai import _autodoc
from driverlessai import _autoviz
from driverlessai import _datasets
from driverlessai import _deployments
from driverlessai import _enums
from driverlessai import _exceptions
from driverlessai import _experiments
from driverlessai import _h2oai_client
from driverlessai import _logging
from driverlessai import _mli
from driverlessai import _model_diagnostics
from driverlessai import _projects
from driverlessai import _recipes
from driverlessai import _server
from driverlessai import _utils

if TYPE_CHECKING:
    import fsspec  # noqa F401


###############################
# Helper Functions
###############################


def is_server_up(
    address: str, timeout: int = 10, verify: Union[bool, str] = False
) -> bool:
    """
    Checks whether a Driverless AI server is up and running.

    Args:
        address: The full URL to the Driverless AI server.
        timeout: The maximum time in seconds
            to wait for a response from the server.
        verify: Enable or disable SSL certificate verification when
                using HTTP to connect to the server. Pass a string path to
                a CA bundle file to use it for SSL verification. See `requests`
                [docs](https://requests.readthedocs.io/en/latest/user/advanced.html#ssl-cert-verification)
                for more details.

    Returns:
        `True` if the server is up, otherwise `False`.

    ??? Example
        ```py
        is_up = driverlessai.is_server_up("http://localhost:12345")
        if is_up:
            print("Driverless AI server is up")
        ```
    """
    try:
        return requests.get(address, timeout=timeout, verify=verify).status_code == 200
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        return False


class Client:
    def __init__(
        self,
        address: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
        token_provider: Optional[Callable[[], str]] = None,
        verify: Union[bool, str] = True,
        backend_version_override: Optional[str] = None,
        authentication_method: Optional[str] = None,
    ) -> None:
        """
        Connect with a Driverless AI server and interact with it.

        Args:
            address: Full URL to the Driverless AI server to connect with.
            username: username to authenticate with the server.
            password: password to authenticate with the server.
            token_provider: A function that returns a token to authenticate
                with the server. This precedes username & password authentication.
            verify: Enable or disable SSL certificate verification when
                using HTTP to connect to the server. Pass a string path to
                a CA bundle file to use it for SSL verification. See `requests`
                [docs](https://requests.readthedocs.io/en/latest/user/advanced.html#ssl-cert-verification)
                for more details.
            backend_version_override: Disables server version detection and
                use the specified server version. Set to `"latest"`
                to use the most recent server backend support.
            authentication_method: The authentication method used to connect to
                the Driverless AI server as described in
                [link](https://docs.h2o.ai/driverless-ai/1-10-lts/docs/userguide/authentication.html).

        ??? Example "Example: Connect with a username and password"
            ```py
            client = driverlessai.Client(
                address="http://localhost:12345",
                username="alice",
                password="alice-password",
            )
            ```

        ??? Example "Example: Connect with an OAuth token"
            - This assumes the Driverless AI server is configured to allow clients to
            authenticate through tokens.
            - Set up an OAuth token provider with a refresh token from
            the Driverless AI web UI.
                ```py
                token_provider = driverlessai.token_providers.OAuth2TokenProvider(
                    refresh_token="eyJhbGciOiJIUzI1N...",
                    client_id="python_client",
                    token_endpoint_url="https://keycloak-server/auth/realms/..."
                    token_introspection_url="https://keycloak-server/auth/realms/..."
                )
                ```
            - Then use the token provider to authorize and connect to the server.
                ```py
                client = driverlessai.Client(
                    address="https://localhost:12345",
                    token_provider=token_provider.ensure_fresh_token
                )
                ```

        ??? Example "Example: Connect with a newer server version"
            An older Client version will refuse to connect to a newer Driverless AI
            server version. Even though it is not recommended, you can still force
            the Client to connect to the server.
            ```py
            client = driverlessai.Client(
                address="http://localhost:12345",
                username="bob",
                password="bob-password",
                backend_version_override="latest",
            )
            ```

        ??? Example "Example: Connect using an alternative authentication method"
            ```py
            client = driverlessai.Client(
                address="http://localhost:12345",
                username="alice",
                password="alice-password",
                authentication_method="ldap",
            )
            ```
        """

        _logging.configure_console_logger()
        address = address.rstrip("/")

        # Check if the server is up, if we're unable to ping it we fail.
        if not is_server_up(address, verify=verify):
            message = (
                f"Cannot connect to the Driverless AI server at '{address}' "
                f"with verify={verify}. "
                "Please make sure that the server is running and address is correct."
            )
            if address.startswith("https"):
                message += " Also `verify` is specified."
            raise _exceptions.ServerDownException(message)

        # Try to get server version, if we can't, we fail.
        if backend_version_override is None:
            server_version = self._detect_server_version(address, verify)
        else:
            if backend_version_override == "latest":
                backend_version_override = re.search("[0-9.]+", __version__)[0].rstrip(
                    "."
                )
            server_version = backend_version_override

        if server_version[:3] in ["1.8", "1.9"]:
            raise _exceptions.ServerVersionNotSupported(
                "Driverless AI 1.8.x and 1.9.x server versions are no longer supported."
                " Please upgrade your Driverless AI server to a newer version to ensure"
                " compatibility and continued support."
            )

        # Import backend that matches server version, if we can't, we fail.
        try:
            self._server_module = _h2oai_client.get_h2oai_client_module_for(
                server_version
            )
        except ImportError as e:
            raise _exceptions.ServerVersionNotSupported(
                f"Server version {server_version} is not supported, "
                "try updating to the latest client."
            ) from e
        self._backend = self._server_module.PatchedClient(
            address=address,
            username=username,
            password=password,
            token_provider=token_provider,
            verify=verify,
            authentication_method=authentication_method,
        )

        self._gui_sep = "/#/"
        self._server = _server.Server(
            client=self,
            address=address,
        )
        self._autoviz = _autoviz.AutoViz(self)
        self._admin = _admin.Admin(self)
        self._connectors = _datasets.Connectors(self)
        self._datasets = _datasets.Datasets(self)
        self._deployments = _deployments.Deployments(self)
        self._experiments = _experiments.Experiments(self)
        self._mli = _mli.MLI(self)
        self._model_diagnostics = _model_diagnostics.ModelDiagnostics(self)
        self._projects = _projects.Projects(self)
        self._recipes = _recipes.Recipes(self)
        self._autodocs = _autodoc.AutoDocs(self)

        if not self.server.license.is_valid():
            raise _exceptions.ServerLicenseInvalid(
                self._backend.have_valid_license().message
            )

    @property
    @_utils.min_supported_dai_version("1.10.3")
    def admin(self) -> _admin.Admin:
        """Perform administrative tasks on the Driverless AI server."""
        return self._admin

    @property
    def autoviz(self) -> _autoviz.AutoViz:
        """
        Interact with dataset
        [visualizations](https://docs.h2o.ai/driverless-ai/1-10-lts/docs/userguide/autoviz.html)
        in the Driverless AI server.
        """
        return self._autoviz

    @property
    def connectors(self) -> _datasets.Connectors:
        """Interact with data sources that are enabled in the Driverless AI server."""
        return self._connectors

    @property
    def datasets(self) -> _datasets.Datasets:
        """
        Interact with
        [datasets](https://docs.h2o.ai/driverless-ai/1-10-lts/docs/userguide/datasets.html)
        in the Driverless AI server.
        """
        return self._datasets

    @property
    @_utils.beta
    @_utils.min_supported_dai_version("1.10.6")
    def deployments(self) -> _deployments.Deployments:
        """
        Interact with
        [deployments](https://docs.h2o.ai/driverless-ai/1-10-lts/docs/userguide/deployment.html)
        in the Driverless AI server.
        """
        return self._deployments

    @property
    def experiments(self) -> _experiments.Experiments:
        """
        Interact with
        [experiments](https://docs.h2o.ai/driverless-ai/1-10-lts/docs/userguide/running-experiment.html)
        in the Driverless AI server.
        """
        return self._experiments

    @property
    def mli(self) -> _mli.MLI:
        """
        Interact with experiment
        [interpretations](https://docs.h2o.ai/driverless-ai/1-10-lts/docs/userguide/interpret-a-model.html)
        in the Driverless AI server.
        """
        return self._mli

    @property
    def model_diagnostics(self) -> _model_diagnostics.ModelDiagnostics:
        """
        Interact with model
        [diagnostics](https://docs.h2o.ai/driverless-ai/1-10-lts/docs/userguide/diagnosing.html)
        in the Driverless AI server.
        """
        return self._model_diagnostics

    @property
    def projects(self) -> _projects.Projects:
        """
        Interact with
        [projects](https://docs.h2o.ai/driverless-ai/1-10-lts/docs/userguide/projects.html)
        in the Driverless AI server.
        """
        return self._projects

    @property
    def recipes(self) -> _recipes.Recipes:
        """
        Interact with
        [recipes](https://docs.h2o.ai/driverless-ai/1-10-lts/docs/userguide/custom_recipes.html)
        in the Driverless AI server.
        """
        return self._recipes

    @property
    def server(self) -> _server.Server:
        """Interact with the connected Driverless AI server"""
        return self._server

    @property
    @_utils.beta
    def autodocs(self) -> _autodoc.AutoDocs:
        """
        Interact with
        [AutoDocs](https://docs.h2o.ai/driverless-ai/1-10-lts/docs/userguide/autodoc-using.html)
        in the Driverless AI server.
        """
        return self._autodocs

    def __repr__(self) -> str:
        return f"{self.__class__} {self!s}"

    def __str__(self) -> str:
        return self.server.address

    @staticmethod
    def _detect_server_version(address: str, verify: Union[bool, str]) -> str:
        """Trys multiple methods to retrieve server version."""
        # query server version endpoint
        response = requests.get(f"{address}/serverversion", verify=verify)
        if response.status_code == 200:
            try:
                return response.json()["serverVersion"]
            except json.JSONDecodeError:
                pass
        # extract the version by scraping the login page
        response = requests.get(address, verify=verify)
        scrapings = re.search("DRIVERLESS AI ([0-9.]+)", response.text)
        if scrapings:
            return scrapings[1]
        # if login is disabled, get cookie and make rpc call
        with requests.Session() as s:
            s.get(f"{address}/login", verify=verify)
            response = s.post(
                f"{address}/rpc",
                data=json.dumps(
                    {"id": "", "method": "api_get_app_version", "params": {}}
                ),
            )
            try:
                return response.json()["result"]["version"]
            except json.JSONDecodeError:
                pass
        # fail
        raise _exceptions.ServerVersionExtractionFailed(
            "Unable to extract server version. "
            "Please make sure the address is correct."
        )

    def _download(
        self,
        server_path: str,
        dst_dir: str,
        dst_file: Optional[str] = None,
        file_system: Optional["fsspec.spec.AbstractFileSystem"] = None,
        overwrite: bool = False,
        timeout: float = 30,
        verbose: bool = True,
        download_type: _enums.DownloadType = _enums.DownloadType.FILES,
    ) -> str:
        """Download a file from the user's files on the Driverless AI server -
        assuming you know the path.

        Args:
            server_path: The path of the downloaded file inside the server.
            dst_dir: The path to the directory where the downloaded file will be saved.
            dst_file: The name of the downloaded file will be used as specified.
                If not specified, the server's file name will be used.
            file_system: FSSPEC based file system to download to,
                instead of local file system.
            overwrite: Overwrite existing files.
            timeout: The number of seconds to wait for the
                server to respond before throwing an error.
            verbose: Determines whether to print messages
                about the download status.
            download_type: Specifies the download type,
                allowing you to choose from a file, dataset, or log.
        """
        if not dst_file:
            dst_file = Path(server_path).name
        dst_path = str(Path(dst_dir, dst_file))
        res = self._get_file(server_path, timeout, download_type=download_type)
        try:
            if file_system is None:
                if overwrite:
                    mode = "wb"
                else:
                    mode = "xb"
                with open(dst_path, mode) as f:
                    f.write(res.content)
                if verbose:
                    _logging.logger.info(f"Downloaded '{dst_path}'")
            else:
                if not overwrite and file_system.exists(dst_path):
                    raise FileExistsError(f"File exists: {dst_path}")
                with file_system.open(dst_path, "wb") as f:
                    f.write(res.content)
                if verbose:
                    _logging.logger.info(f"Downloaded '{dst_path}' to {file_system}")
        except FileExistsError:
            _logging.logger.error(
                f"{dst_path} already exists. Use `overwrite` to force download."
            )
            raise

        return dst_path

    def _build_url(
        self,
        server_path: str,
        download_type: _enums.DownloadType = _enums.DownloadType.FILES,
    ) -> str:
        """
        Build server object `url`

        Args:
            server_path: The path of the downloaded file inside the server.
            download_type: Specifies the download type,
                allowing you to choose from a file, dataset, or log.
        """
        if self._server.version < "1.10.5":
            # the different types of downloads were only introduced in 1.10.5
            download_type = _enums.DownloadType.FILES

        return f"{self.server.address}/{download_type.value}/{server_path}"

    def _get_response(
        self,
        server_path: str,
        timeout: float = 5,
        download_type: _enums.DownloadType = _enums.DownloadType.FILES,
        stream: Optional[bool] = None,
    ) -> requests.models.Response:
        """Retrieve a requests response for any file from the user's files on
        the Driverless AI server - assuming you know the path.

        Args:
            server_path: The path of the downloaded file inside the server.
            timeout: The number of seconds to wait for
                the server to respond before raising an error.
            download_type: Specifies the download type, allowing
                you to choose from a file, dataset, or log.
            stream: To get the content as a stream.
        """
        url = self._build_url(server_path, download_type)
        if hasattr(self._backend, "_session") and hasattr(
            self._backend, "_get_authorization_headers"
        ):
            res = self._backend._session.get(
                url,
                headers=self._backend._get_authorization_headers(),
                timeout=timeout,
                stream=stream,
            )
        elif hasattr(self._backend, "_session"):
            res = self._backend._session.get(
                url,
                timeout=timeout,
                stream=stream,
            )
        else:
            res = requests.get(
                url,
                cookies=self._backend._cookies,
                verify=self._backend._verify,
                timeout=timeout,
                stream=stream,
            )
        return res

    def _get_file(
        self,
        server_path: str,
        timeout: float = 5,
        download_type: _enums.DownloadType = _enums.DownloadType.FILES,
    ) -> requests.models.Response:
        """Retrieve a requests response for any file from the user's files on
        the Driverless AI server - assuming you know the path.

        Args:
            server_path: The path of the downloaded file inside the server.
            timeout: The number of seconds to wait for the server
                to respond before throwing an error.
            download_type: The download type, specifying whether to
                choose from a file, dataset,
                or another option. The default value is None.

        """

        res = self._get_response(server_path, timeout, download_type)
        res.raise_for_status()
        return res

    def _get_json_file(self, server_path: str, timeout: float = 5) -> Dict[Any, Any]:
        """Retrieve a dictionary representation of a json file from the user's
        files on the Driverless AI server - assuming you know the path.

        Args:
            server_path: The path of the downloaded file inside the server.
            timeout: The number of seconds to wait for the
                server to respond before throwing an error.
        """
        return self._get_file(server_path, timeout).json()

    def _get_text_file(self, server_path: str, timeout: float = 5) -> str:
        """Retrieve a string representation of a text based file from the user's
        files on the Driverless AI server - assuming you know the path.

        Args:
            server_path: The path of the downloaded file inside the server.
            timeout: The number of seconds to wait for the
                server to respond before throwing an error.
        """
        return self._get_file(server_path, timeout).text
