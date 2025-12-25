"""Autodoc module."""

import os
from typing import Any, Optional, TYPE_CHECKING

import toml

from driverlessai import (
    _commons,
    _core,
    _experiments,
)

if TYPE_CHECKING:
    import fsspec  # noqa F401


class AutoDoc(_commons.ServerObject):
    """An AutoDoc in the Driverless AI server."""

    def __init__(self, client: "_core.Client", key: str) -> None:
        super().__init__(client=client, key=key)
        self._experiment: Optional[_experiments.Experiment] = None

    @property
    def experiment(self) -> "_experiments.Experiment":
        """The experiment documented by the AutoDoc."""
        if self._experiment is None:
            self._experiment = _experiments.Experiments(self._client).get(
                self._get_raw_info().entity.model_key
            )
        return self._experiment

    @property
    def creation_time(self) -> float:
        """
        Creation timestamp of the AutoDoc in seconds since the epoch (POSIX timestamp).
        """
        return self._get_raw_info().created

    def _update(self) -> None:
        self._set_raw_info(self._client._backend.get_autoreport_job(key=self.key))
        self._set_name(os.path.basename(self._get_raw_info().entity.report_path))

    def download(
        self,
        dst_dir: str = ".",
        dst_file: Optional[str] = None,
        file_system: Optional["fsspec.spec.AbstractFileSystem"] = None,
        overwrite: bool = False,
        timeout: float = 30,
    ) -> str:
        """
        Downloads the AutoDoc as in MS Word format (.docx).

        Args:
            dst_dir: The path where the doc file will be saved.
            dst_file: The name of the doc file (overrides the default file name).
            file_system: FSSPEC-based file system to download to
                instead of the local file system.
            overwrite: Whether to overwrite or not if a file already exists.
            timeout: Connection timeout in seconds.

        Returns:
            Path to the downloaded doc file.
        """
        path = self._client._backend.get_autoreport_job(key=self.key).entity.report_path

        return self._client._download(
            server_path=path,
            dst_dir=dst_dir,
            dst_file=dst_file,
            file_system=file_system,
            overwrite=overwrite,
            timeout=timeout,
        )


class AutoDocJob(_commons.ServerJob):
    """Monitor the creation of an AutoDoc in the Driverless AI server."""

    def __init__(self, client: "_core.Client", key: str) -> None:
        super().__init__(client=client, key=key)

    def _update(self) -> None:
        self._set_raw_info(self._client._backend.get_autoreport_job(key=self.key))

    def result(self, silent: bool = False) -> AutoDoc:
        """Awaits the job's completion before returning the created AutoDoc.

        Args:
            silent: Whether to display status updates or not.

        Returns:
            Created AutoDoc by the job.
        """

        self._wait(silent)
        return AutoDoc(self._client, self.key)


class AutoDocs:
    """
    Interact with
    [AutoDocs](https://docs.h2o.ai/driverless-ai/1-10-lts/docs/userguide/autodoc-using.html)
    in the Driverless AI server.
    """

    def __init__(self, client: "_core.Client") -> None:
        self._client = client

    def create(
        self,
        experiment: "_experiments.Experiment",
        **config_overrides: Any,
    ) -> AutoDoc:
        """
        Creates a new AutoDoc.

        Args:
            experiment: The experiment to generate the document for.
            config_overrides: Configuration overrides to override configurations set for
                AutoDoc generation in Driverless AI server. Please refer
                [AutoDoc&nbsp;Settings](https://docs.h2o.ai/driverless-ai/1-10-lts/docs/userguide/expert_settings/autodoc_settings.html)
                docs for available configuration options.

        Returns:
            Created AutoDoc.
        """
        return self.create_async(
            experiment,
            **config_overrides,
        ).result()

    def create_async(
        self,
        experiment: "_experiments.Experiment",
        **config_overrides: Any,
    ) -> AutoDocJob:
        """
        Launches creation of a new AutoDoc.

        Args:
            experiment: The experiment to generate the document for.
            config_overrides: Configuration overrides to override configurations set for
                AutoDoc generation in Driverless AI server. Please refer
                [AutoDoc&nbsp;Settings](https://docs.h2o.ai/driverless-ai/1-10-lts/docs/userguide/expert_settings/autodoc_settings.html)
                docs for available configuration options.

        Returns:
            Started AutoDoc job.
        """
        config_overrides_toml = ""
        if config_overrides:
            config_overrides_toml = toml.dumps(config_overrides)

        key = self._client._backend.make_autoreport(
            model_key=experiment.key,
            mli_key=None,
            individual_rows=None,
            autoviz_key=None,
            template_path="",
            placeholders={},
            external_dataset_keys=[],
            reuse_model_key=False if config_overrides_toml else True,
            config_overrides=config_overrides_toml,
        )
        return AutoDocJob(self._client, key)
