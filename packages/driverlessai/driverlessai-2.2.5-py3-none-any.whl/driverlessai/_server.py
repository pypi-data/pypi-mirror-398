"""Server module of official Python client for Driverless AI."""

import re
import urllib.parse
from typing import Any, Dict, List, Optional, Union

from packaging.version import parse

from driverlessai import _core
from driverlessai import _logging
from driverlessai import _utils


class Version:
    """
    A version of H2O Driverless AI.
    Compatible with `==`, `!=`, `<`, `<=`, `>`, `>=` operators.

    ??? Example "Example: Comparing the Driverless AI server version"
        ```py
        client.server.version == "1.10.5"
        ```
        ```py
        client.server.version < "1.10.5"
        ```
        ```py
        client.server.version > "1.10.5"
        ```
    """

    def __init__(self, version_str: str) -> None:
        self._version = parse(version_str)

    def __eq__(self, other: Any) -> bool:
        """Return self==other."""
        if isinstance(other, (str, Version)):
            return self._version == self._parse(other)._version
        # as per docs https://docs.python.org/3/reference/datamodel.html#object.__eq__
        return NotImplemented

    def __ge__(self, other: Union[str, "Version"]) -> bool:
        """Return self>=other."""
        return self._version >= self._parse(other)._version

    def __gt__(self, other: Union[str, "Version"]) -> bool:
        """Return self>other."""
        return self._version > self._parse(other)._version

    def __le__(self, other: Union[str, "Version"]) -> bool:
        """Return self<=other."""
        return self._version <= self._parse(other)._version

    def __lt__(self, other: Union[str, "Version"]) -> bool:
        """Return self<other."""
        return self._version < self._parse(other)._version

    def __repr__(self) -> str:
        """Return repr(self)."""
        return repr(self._version)

    def __str__(self) -> str:
        """Return str(self)."""
        return str(self._version)

    @property
    def major(self) -> int:
        """The first part of the version or `0` if unavailable.

        Examples:
            >>> Version("1.10.5.1").major
            1
        """
        return self._version.major

    @property
    def minor(self) -> int:
        """The second part of the version or `0` if unavailable.

        Examples:
            >>> Version("1.10.5.1").minor
            10
        """
        return self._version.minor

    @property
    def micro(self) -> int:
        """The third part of the version or `0` if unavailable.

        Examples:
            >>> Version("1.10.5.1").micro
            5
        """
        return self._version.micro

    @property
    def patch(self) -> int:
        """The forth part of the version or `0` if unavailable.

        Examples:
            >>> Version("1.10.5.1").patch
            1
        """
        return self._version.release[3] if len(self._version.release) >= 4 else 0

    @staticmethod
    def _parse(version: Any) -> "Version":
        if isinstance(version, str):
            return Version(version)
        elif isinstance(version, Version):
            return version
        else:
            raise ValueError(f"Cannot parse {type(version)} into a Version.")


class License:
    """License of the Driverless AI server."""

    def __init__(self, client: "_core.Client") -> None:
        self._client = client

    def _get_info(self) -> Any:
        info = self._client._backend.have_valid_license()
        if info.message:
            _logging.logger.info(info.message)
        return info

    def days_left(self) -> int:
        """Returns the remaining number of days until license expiration."""
        return self._get_info().days_left

    def is_valid(self) -> bool:
        """Whether the license is valid and not-expired."""
        return self._get_info().is_valid


class Server:
    """The connected Driverless AI server.

    ??? Example
        ```py
        client = driverlessai.Client(
            address="http://localhost:12345",
            username="py",
            password="py",
        )

        client.server.address
        client.server.username
        client.server.version
        ```
    """

    def __init__(self, client: "_core.Client", address: str) -> None:
        server_info = client._backend.get_app_version()
        user_info = client._backend.get_current_user_info()

        self._address = address
        self._client = client
        self._license = License(client)
        self._storage_enabled = server_info.enable_storage
        self._username = user_info.name
        self._version = Version(re.search(r"^([\d.]+)", server_info.version).group(1))
        self._configurations: Optional[Dict[str, Any]] = None

    @property
    def address(self) -> str:
        """URL of the Driverless AI server."""
        return self._address

    @property
    def license(self) -> License:
        """License of the Driverless AI server."""
        return self._license

    @property
    def configurations(self) -> Dict[str, Any]:
        """Exposed configurations of the Driverless AI server.

        Returns:
            Exposed server configurations to the client.
        """
        if self._configurations is None:
            all_configs = self._client._backend.get_all_config_options()
            self._configurations = {config.name: config.val for config in all_configs}

        return self._configurations

    @property
    def storage_enabled(self) -> bool:
        """Whether the Driverless AI server is connected to H2O.ai Storage or not."""
        return self._storage_enabled

    @property
    def username(self) -> str:
        """Name the current user connected to the Driverless AI server."""
        return self._username

    @property
    def version(self) -> Version:
        """Version of the Driverless AI server."""
        return self._version

    @property
    def disk_usage(self) -> Dict[str, int]:
        """
        Disk usage statistics of the Driverless AI server.

        Returns:
            A dictionary with keys `total`, `available`, and `used`, representing
                the respective disk space in bytes.
        """
        disk_usage = self._client._backend.get_disk_stats()
        return {
            "total": disk_usage.total,
            "available": disk_usage.available,
            "used": disk_usage.total - disk_usage.available,
        }

    @property
    def gpu_usages(self) -> List[Dict[str, float]]:
        """
        GPU usage statistics of the Driverless AI server.

        Returns:
            A list of dictionaries, each containing `memory` and `usage` keys with
                corresponding GPU memory in bytes and usage.
        """
        gpu_stats = self._client._backend.get_gpu_stats()

        return [
            {
                "memory": gpu_stats.mems[index],
                "usage": gpu_stats.usages[index],
            }
            for index in range(gpu_stats.gpus)
        ]

    @property
    @_utils.beta
    @_utils.min_supported_dai_version("1.10.6")
    def cpu_usages(self) -> List[float]:
        """
        CPU usage statistics of the Driverless AI server.

        Returns:
            A list of CPU usage percentages for each CPU core.
        """
        return self._client._backend.get_system_stats(force_cpu=True).per

    @property
    @_utils.min_supported_dai_version("1.10.6")
    def memory_usage(self) -> Dict[str, int]:
        """
        Memory usage statistics of the Driverless AI server.

        Returns:
            A dictionary with keys `total`, `available`, and `used`, representing the
                respective memory space in bytes.
        """
        memory_stats = self._client._backend.get_system_stats(force_cpu=True).mem
        return {
            "total": memory_stats.total,
            "available": memory_stats.available,
            "used": memory_stats.total - memory_stats.available,
        }

    @property
    def experiment_stats(self) -> Dict[str, int]:
        """
        Experiments-related statistics of the Driverless AI server.

        Returns:
            A dictionary with keys `total`, `my_experiments_total`,
                `my_experiments_running`, containing the total number
                of experiments, total number of the user's experiments,
                and the number of the user's currently running experiments.
        """
        experiment_stats = self._client._backend.get_experiments_stats()
        return {
            "total": experiment_stats.total,
            "my_experiments_total": experiment_stats.my_total,
            "my_experiments_running": experiment_stats.my_running,
        }

    @property
    @_utils.beta
    def workers(self) -> List[Dict[str, Any]]:
        """
        Statistics for each worker node of the Driverless AI server.

        Returns:
            A list of dictionaries, each representing a worker node with details such as
                name, health status, IP address, number of GPUs,
                and other relevant metrics.
        """
        health_info = self._client._backend.get_health()

        return [
            {
                "name": worker.name,
                "healthy": worker.healthy,
                "ip": worker.ip,
                "gpus": worker.total_gpus,
                "status": worker.status,
                "max_processes": worker.remote_processors,
                "current_processes": worker.remote_tasks,
                "upload_speed": getattr(worker, "upload_speed", ""),
                "download_speed": getattr(worker, "download_speed", ""),
            }
            for worker in health_info.workers
        ]

    def docs(self, search: str = None) -> _utils.Hyperlink:
        """
        Returns the full URL to the Driverless AI documentation.

        Args:
            search: A query to search in docs. If provided,
                the hyperlink will point to the search results page.

        ??? Example
            ```py
            # Search the DAI docs for "experiments"
            client.server.docs(search="experiments")
            ```
        """
        if search is None:
            return _utils.Hyperlink(f"{self.address}/docs/userguide/index.html")
        else:
            search = urllib.parse.quote_plus(search)
            link = f"{self.address}/docs/userguide/search.html?q={search}"
            return _utils.Hyperlink(link)

    def gui(self) -> _utils.Hyperlink:
        """
        Returns the full URL to the Driverless AI server web UI.

        Returns:
            URL to the web UI.
        """
        return _utils.Hyperlink(self.address)
