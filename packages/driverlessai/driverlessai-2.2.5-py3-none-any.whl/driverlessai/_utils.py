"""Utilities module."""

import ast
import functools
import sys
import warnings
from typing import Any, Callable, Dict, IO, List, Optional, Union

import tabulate
import toml

from driverlessai import _core
from driverlessai import _exceptions


class Hyperlink(str):
    """
    Renders a clickable link for URLs in Jupyter Notebooks,
    otherwise behaves the same as `str`.
    """

    def _repr_html_(self) -> str:
        link = self.__str__()
        html = (
            "<pre>"
            f"<a href='{link}' rel='noopener noreferrer' target='_blank'>{link}</a>"
            "</pre>"
        )
        return html


class StatusUpdate:
    """Status of a job in the Driverless AI server."""

    def __init__(self, stdout: IO = sys.stdout) -> None:
        self._needs_end = False
        self._prev_message_len = 0
        self.stdout = stdout

    def _overwrite_line(self, old_line_len: int, new_line: str) -> None:
        self.stdout.write("\r")
        self.stdout.write(" " * old_line_len)
        self.stdout.write("\r")
        self.stdout.write(new_line)
        self.stdout.flush()

    def display(self, message: str) -> None:
        """Displays the status message on the current line in STDOUT."""
        self._overwrite_line(self._prev_message_len, message)
        self._prev_message_len = len(message)
        self._needs_end = True

    def end(self) -> None:
        """Marks the end of the status."""
        if self._needs_end:
            self.stdout.write("\n")


class Table:
    """A table that pretty prints."""

    def __init__(self, data: List[List[Any]], headers: List[str]) -> None:
        self._data = data
        self._headers = headers

    @property
    def data(self) -> List[List[Any]]:
        """Data of the table."""
        return self._data

    @property
    def headers(self) -> List[str]:
        """Headers of the table."""
        return self._headers

    def __str__(self) -> str:
        return tabulate.tabulate(self.data, headers=self.headers, tablefmt="presto")

    def _repr_html_(self) -> str:
        return tabulate.tabulate(self.data, headers=self.headers, tablefmt="html")

    def __repr__(self) -> str:
        return self.__str__()


def check_server_support(
    client: "_core.Client", minimum_server_version: str, parameter: str
) -> None:
    if client.server.version < minimum_server_version:
        raise _exceptions.NotSupportedByServer(
            f"'{parameter}' requires Driverless AI server version "
            f"{minimum_server_version} or higher."
        )


def error_if_dataset_exists(client: "_core.Client", name: str) -> None:
    if name in client._backend.list_datasets_with_similar_name(name=name):
        raise _exceptions.DatasetExists(
            f"Dataset with name '{name}' already exists on server. "
            "Use `force=True` to create another dataset with same name."
        )


def error_if_experiment_exists(client: "_core.Client", name: str) -> None:
    if name in client._backend.list_models_with_similar_name(name=name):
        raise _exceptions.ExperimentExists(
            f"Experiment with name '{name}' already exists on server. "
            "Use `force=True` to create another experiment with same name."
        )


def error_if_project_exists(client: "_core.Client", name: str) -> None:
    if name in [p.name for p in client.projects.list()]:
        raise _exceptions.ProjectExists(
            f"Project with name '{name}' already exists on server. "
            "Use `force=True` to create another project with same name."
        )


def get_or_default(obj: Any, attribute_name: str, default_value: Any = None) -> Any:
    return getattr(obj, attribute_name, None) or default_value


def get_storage_user_id(client: "_core.Client", name: str) -> str:
    page_position = 0
    page_size = 100
    while True:
        page = client._backend.list_storage_users(offset=page_position, limit=page_size)
        for user in page:
            if name == user.username:
                return user.id
        if len(page) < page_size:
            raise RuntimeError(f"User name '{name}' not found.")
        page_position += page_size


def get_storage_user_name(client: "_core.Client", uuid: str) -> str:
    page_position = 0
    page_size = 100
    while True:
        page = client._backend.list_storage_users(offset=page_position, limit=page_size)
        for user in page:
            if uuid == user.id:
                return user.username
        if len(page) < page_size:
            raise RuntimeError(f"User ID '{uuid}' not found.")
        page_position += page_size


def get_storage_role_id(client: "_core.Client", name: str) -> str:
    for role in client._backend.list_storage_roles():
        if name.lower() == role.display_name.lower():
            return role.id
    raise RuntimeError(f"Role name '{name}' not found.")


def get_storage_role_name(client: "_core.Client", uuid: str) -> str:
    for role in client._backend.list_storage_roles():
        if uuid == role.id:
            return role.display_name
    raise RuntimeError(f"Role ID '{uuid}' not found.")


def is_key_error(error: Exception) -> bool:
    message = getattr(error, "message", {}).get("message", "")
    return "KeyError" in message


def is_number(string: Union[bool, float, int, str]) -> bool:
    try:
        float(string)
        return True
    except Exception:  # noqa: B902
        return False


def toml_to_api_settings(
    toml_string: str, default_api_settings: Dict[str, Any], blacklist: List[str]
) -> Dict[str, Any]:
    """Convert toml string to dictionary of API settings.

    If setting not in defaults or is in blacklist, it will be skipped.
    If setting is in defaults but has default value, it will be skipped.
    """
    api_settings = {}
    toml_dict = toml.loads(toml_string)
    for setting, value in toml_dict.items():
        if setting in default_api_settings and setting not in blacklist:
            default_value = default_api_settings[setting]
            if value != default_value:
                api_settings[setting] = value
    return api_settings


def try_eval(value: Any) -> Any:
    try:
        return ast.literal_eval(value)
    except Exception:  # noqa: B902
        return value


_ADMONITION_TEMPLATE = """

        ??? {type} "{title}"
            {body}
"""


def beta(func):  # type: ignore
    """
    Mark a function as a beta API.

    Args:
        func: Function to be marked as a beta API
    """

    @functools.wraps(func)
    def _wrapper(*args, **kwargs):  # type: ignore
        warnings.warn(
            f"'{func.__qualname__}' is a beta API that is subject to future changes.",
            stacklevel=2,
        )
        return func(*args, **kwargs)

    _wrapper.__doc__ += _ADMONITION_TEMPLATE.format(
        type="warning",
        title="Beta API",
        body="A [beta API][beta] that is subject to future changes.",
    )
    return _wrapper


def deprecated(
    version: str, new_api: Optional[str] = None, custom_message: Optional[str] = None
) -> Callable:
    """
    Mark a function as a deprecated API.

    Args:
        version: deprecating version
        new_api: fully qualified name of the new method users should use
        custom_message: custom message to override the default message
    """

    def _decorator(deprecated_func: Callable):  # type: ignore
        @functools.wraps(deprecated_func)
        def _wrapper(*args, **kwargs):  # type: ignore
            if custom_message:
                message = custom_message
            else:
                message = (
                    f"'{deprecated_func.__qualname__}' is deprecated. "
                    f"It will be removed from version {version} onwards."
                )
                if new_api:
                    message += f" Please use '{new_api}' instead."
            warnings.warn(message, category=FutureWarning, stacklevel=2)
            return deprecated_func(*args, **kwargs)

        doc = (
            "A [deprecated API][deprecated] that will be removed from "
            f"v{version} onwards."
        )
        if new_api:
            doc += f" Please use '{new_api}' instead."
        _wrapper.__doc__ += _ADMONITION_TEMPLATE.format(
            type="danger",
            title="Deprecated API",
            body=doc,
        )
        return _wrapper

    return _decorator


def min_supported_dai_version(version: str, custom_message: str = None):  # type: ignore
    """Check if the Driverless AI server supports a certain feature based on the
        minimum version required.

    Args:
        version (str): The minimum version required for the feature.
        custom_message (str): The custom message for the exception.

    Raises:
        _exceptions.NotSupportedByServer: If the server version is less than the
        minimum required version.

    Returns:
        The decorator function.
    """

    def _decorator(func):  # type: ignore
        @functools.wraps(func)
        def _wrapper(self, *args, **kwargs):  # type: ignore
            client = self if isinstance(self, _core.Client) else self._client
            if client.server.version < version:
                if custom_message:
                    message = custom_message
                else:
                    message = (
                        f"'{func.__qualname__}' requires Driverless AI server version "
                        f"{version} or higher."
                    )
                raise _exceptions.NotSupportedByServer(message)
            return func(self, *args, **kwargs)

        _wrapper.__doc__ += _ADMONITION_TEMPLATE.format(
            type="info",
            title="Driverless AI version requirement",
            body=f"Requires Driverless AI server {version} or higher.",
        )
        return _wrapper

    return _decorator
