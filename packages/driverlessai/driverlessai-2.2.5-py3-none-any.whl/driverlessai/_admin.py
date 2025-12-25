"""Admin module."""

import abc
import functools
import re
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple, TYPE_CHECKING

from driverlessai import _commons
from driverlessai import _core
from driverlessai import _enums
from driverlessai import _utils

if TYPE_CHECKING:
    import fsspec  # noqa F401


def _requires_admin(func: Callable) -> Callable:
    """Decorates methods that require admin access."""

    @functools.wraps(func)
    def wrapped(self: "Admin", *args: Any, **kwargs: Any) -> Any:
        if not self.is_admin:
            raise Exception("Administrator access is required to access this feature.")
        return func(self, *args, **kwargs)

    return wrapped


class _EntityKind(str, Enum):
    DATASET = "dataset"
    EXPERIMENT = "model_summary"
    INTERPRETATION = "interpretation"
    MODEL_DIAGNOSTIC = "model_diagnostic"
    AUTOVIZ = "autoviz"
    PROJECT = "project"


class Admin:
    """
    Facilitate operations to perform administrative tasks on the Driverless AI server.
    """

    def __init__(self, client: "_core.Client") -> None:
        self._client = client
        self._is_admin: Optional[bool] = None

    @property
    def is_admin(self) -> bool:
        """
        Returns whether the current user is an admin or not.

        Returns:
            `True` if the user is an admin, otherwise `False`.
        """
        if self._is_admin is None:
            try:
                self._client._backend.get_users_insights()
                self._is_admin = True
            except self._client._server_module.protocol.RemoteError:
                self._is_admin = False
        return self._is_admin

    @_requires_admin
    def list_users(self) -> List[str]:
        """
        Lists users in the Driverless AI server.

        Returns:
            Usernames of the users.
        """
        return [
            user_insight.dump()["user"]
            for user_insight in self._client._backend.get_users_insights()
        ]

    @_requires_admin
    @_utils.beta
    @_utils.min_supported_dai_version("1.10.5")
    def list_current_users(self) -> List[str]:
        """
        Lists users who are currently logged-in to the Driverless AI server.

        Returns:
            Usernames of the currently logged-in users.
        """
        return list(set(self._client._backend.get_current_users()))

    @_requires_admin
    @_utils.beta
    def list_datasets(self, username: str) -> List["DatasetProxy"]:
        """
        Lists datasets created by the specified user.

        Args:
            username: Username of the user.

        Returns:
            Datasets of the user.

        ??? example "Example: Delete all datasets created by a user"
            ```py
            for d in client.admin.list_datasets("alice"):
                print(f"Deleting {d.name} ...")
                d.delete()
            ```
        """
        response = self._client._backend.admin_list_entities(
            username=username, kind=_EntityKind.DATASET
        )
        return [DatasetProxy(self._client, username, item) for item in response.items]

    @_requires_admin
    @_utils.beta
    def list_experiments(self, username: str) -> List["ExperimentProxy"]:
        """
        Lists experiments created by the specified user.

        Args:
            username: Username of the user.

        Returns:
            Experiments of the user.

        ??? example "Example: Find running experiments of a user"
            ```py
            running_experiments = [
                e for e in client.admin.list_experiments("alice") if e.is_running()
            ]
            ```
        """
        response = self._client._backend.admin_list_entities(
            username=username, kind=_EntityKind.EXPERIMENT
        )
        return [
            ExperimentProxy(self._client, username, item) for item in response.items
        ]

    @_requires_admin
    @_utils.beta
    @_utils.min_supported_dai_version("1.11.1")
    def list_interpretations(
        self, username: str, start_index: int = 0, count: int = None
    ) -> List["InterpretationProxy"]:
        """
        Lists interpretations created by the specified user.

        Args:
            username: Username of the user.
            start_index: The index of the first interpretation to retrieve.
            count: The maximum number of interpretations to retrieve.
                If `None`, retrieves all available interpretations.

        Returns:
            Interpretations of the user.

        ??? example "Example: Find running interpretations of a user"
            ```py
            running_interpretations = [
                i for i in client.admin.list_interpretations("alice") if i.is_running()
            ]
            ```
        """
        if count:
            data = self._client._backend.admin_list_interpretations_of(
                username=username, offset=start_index, limit=count
            ).items
        else:
            page_size = 100
            page_position = start_index
            data = []
            while True:
                page = self._client._backend.admin_list_interpretations_of(
                    username=username, offset=page_position, limit=page_size
                ).items
                data += page
                if len(page) < page_size:
                    break
                page_position += page_size
        return [InterpretationProxy(self._client, username, item) for item in data]

    @_requires_admin
    @_utils.beta
    @_utils.min_supported_dai_version("1.11.1")
    def list_model_diagnostics(
        self, username: str, start_index: int = 0, count: int = None
    ) -> List["ModelDiagnosticProxy"]:
        """
        Lists model diagnostics created by the specified user.

        Args:
            username: Username of the user.
            start_index: The index of the first model diagnostic to retrieve.
            count: The maximum number of model diagnostics to retrieve.
                If `None`, retrieves all available model diagnostics.

        Returns:
            Model diagnostics of the user.

        ??? example "Example: Delete all model diagnostics created by a user"
            ```py
            for m in client.admin.list_model_diagnostics("alice"):
                print(f"Deleting {m.name} ...")
                m.delete()
            ```
        """
        if count:
            data = self._client._backend.admin_list_model_diagnostics_of(
                username=username, offset=start_index, limit=count
            ).items
        else:
            page_size = 100
            page_position = start_index
            data = []
            while True:
                page = self._client._backend.admin_list_model_diagnostics_of(
                    username=username, offset=page_position, limit=page_size
                ).items
                data += page
                if len(page) < page_size:
                    break
                page_position += page_size
        return [ModelDiagnosticProxy(self._client, username, item) for item in data]

    @_requires_admin
    @_utils.beta
    @_utils.min_supported_dai_version("1.11.1")
    def list_projects(
        self, username: str, start_index: int = 0, count: int = None
    ) -> List["ProjectProxy"]:
        """
        Lists projects created by the specified user.

        Args:
            username: Username of the user.
            start_index: The index of the first project to retrieve.
            count: The maximum number of projects to retrieve.
                If `None`, retrieves all available projects.

        Returns:
            Projects of the user.

        ??? example "Example: Delete all projects created by a user"
            ```py
            for p in client.admin.list_projects("alice"):
                print(f"Deleting {p.name} ...")
                p.delete()
            ```
        """
        if count:
            data = self._client._backend.admin_list_projects_of(
                username=username, offset=start_index, limit=count
            ).items
        else:
            page_size = 100
            page_position = start_index
            data = []
            while True:
                page = self._client._backend.admin_list_projects_of(
                    username=username, offset=page_position, limit=page_size
                ).items
                data += page
                if len(page) < page_size:
                    break
                page_position += page_size
        return [ProjectProxy(self._client, username, item) for item in data]

    @_requires_admin
    @_utils.beta
    @_utils.min_supported_dai_version("1.11.1")
    def list_visualizations(
        self, username: str, start_index: int = 0, count: int = None
    ) -> List["VisualizationProxy"]:
        """
        Lists visualizations created by the specified user.

        Args:
            username: Username of the user.
            start_index: The index of the first visualization to retrieve.
            count: The maximum number of visualizations to retrieve.
                If `None`, retrieves all available visualizations.

        Returns:
            Visualizations of the user.

        ??? example "Example: Delete all visualizations created by a user"
            ```py
            for v in client.admin.list_visualizations("alice"):
                print(f"Deleting {v.name} ...")
                v.delete()
            ```
        """
        if count:
            data = self._client._backend.admin_list_visualizations_of(
                username=username, offset=start_index, limit=count
            ).items
        else:
            page_size = 100
            page_position = start_index
            data = []
            while True:
                page = self._client._backend.admin_list_visualizations_of(
                    username=username, offset=page_position, limit=page_size
                ).items
                data += page
                if len(page) < page_size:
                    break
                page_position += page_size
        return [VisualizationProxy(self._client, username, item) for item in data]

    @_requires_admin
    def transfer_data(self, from_user: str, to_user: str) -> None:
        """
        Transfers all data belonging to one user to another user.

        Args:
            from_user: Username of the user that data will be transferred from.
            to_user: Username of the user that data will be transferred to.
        """
        if from_user == to_user:
            raise ValueError("Cannot transfer data between the same user.")
        self._client._backend.admin_transfer_entities(
            username_from=from_user, username_to=to_user
        )

    @_requires_admin
    @_utils.min_supported_dai_version("1.10.5")
    def list_server_logs(self) -> List["DAIServerLog"]:
        """
        Lists the server logs of the Driverless AI server.

        Returns:
            Server logs of the Driverless AI server.
        """
        log_files = self._client._backend.get_server_logs_details()

        return [
            DAIServerLog(
                client=self._client,
                raw_info=log_file,
            )
            for log_file in log_files
        ]

    @_requires_admin
    def list_running_tasks(self, user: str = None) -> List["RunningTask"]:
        """
        Lists the running tasks of the Driverless AI server.

        Returns:
            Running tasks of the Driverless AI server.
        """
        running_tasks = self._client._backend.get_runtime_task_information(
            cpu_queue=True, gpu_queue=True, local_queue=True
        )

        all_running_tasks = [
            task_info
            for tasks in [
                running_tasks.cpu_tasks,
                running_tasks.gpu_tasks,
                running_tasks.local_tasks,
            ]
            for task_info in tasks
        ]
        if user:
            return [
                RunningTask(
                    client=self._client,
                    key=task_info.key,
                    user=task_info.user,
                    procedure=task_info.procedure,
                    worker=task_info.worker,
                )
                for task_info in all_running_tasks
                if task_info.user == user
            ]

        return [
            RunningTask(
                client=self._client,
                key=task_info.key,
                user=task_info.user,
                procedure=task_info.procedure,
                worker=task_info.worker,
            )
            for task_info in all_running_tasks
            if not user or task_info.user == user
        ]

    @_requires_admin
    @_utils.min_supported_dai_version("2.0")
    def get_runtime_experiment_insights(
        self, user: str = None, start_index: int = 0, count: int = 100
    ) -> List["RuntimeTaskInsights"]:
        """
        Retrieves the system insights for running experiments
        in the Driverless AI server.

        Args:
            user: Username of the user
            start_index: The index of the first running experiment to retrieve.
            count: The maximum number of running experiments to retrieve.
                If `None`, retrieves all available running experiments.

        Returns:
            System insights of running experiments of the Driverless AI server.
        """
        system_insights = self._client._backend.admin_list_runtime_experiments_insights(
            page_size=count + start_index, page_token=""
        ).insights[start_index:]

        return [
            RuntimeTaskInsights(client=self._client, raw_info=task_info)
            for task_info in system_insights
            if not user or task_info.username == user
        ]


class DAIServerLog(_commons.ServerLog):
    """A server log file in the Driverless AI server."""

    def __init__(self, client: "_core.Client", raw_info: Any):
        path = re.sub(
            "^.*?/files/",
            "",
            re.sub("^.*?/log_files/", "", raw_info.resource_url),
        )
        super().__init__(client=client, file_path=path)
        self._raw_info = raw_info

    def download(
        self,
        dst_dir: str = ".",
        dst_file: Optional[str] = None,
        file_system: Optional["fsspec.spec.AbstractFileSystem"] = None,
        overwrite: bool = False,
        timeout: float = 30,
    ) -> str:
        """
        Downloads the log file.

        Args:
            dst_dir: The path where the log file will be saved.
            dst_file: The name of the log file (overrides the default file name).
            file_system: FSSPEC-based file system to download to
                instead of the local file system.
            overwrite: Whether to overwrite or not if a file already exists.
            timeout: Connection timeout in seconds.

        Returns:
            Path to the downloaded log file.
        """
        return super()._download(
            dst_dir=dst_dir,
            dst_file=dst_file,
            file_system=file_system,
            overwrite=overwrite,
            timeout=timeout,
            download_type=_enums.DownloadType.LOGS,
        )

    @property
    def size(self) -> int:
        """Size of the log file in bytes."""
        return self._raw_info.size

    @property
    def created(self) -> str:
        """Time of creation."""
        return self._raw_info.ctime_str

    @property
    def last_modified(self) -> str:
        """Time of last modification."""
        return self._raw_info.mtime_str


class ServerObjectProxy(abc.ABC):
    def __init__(self, client: "_core.Client", owner: str, key: str, name: str = None):
        self._client = client
        self._owner = owner
        self._key = key
        self._name = name

    @property
    def key(self) -> str:
        """Universally unique identifier of the entity."""
        return self._key

    @property
    def name(self) -> str:
        """Name of the entity."""
        return self._name

    @property
    def owner(self) -> str:
        """Owner of the entity."""
        return self._owner

    @property
    @abc.abstractmethod
    def _kind(self) -> _EntityKind:
        raise NotImplementedError

    @abc.abstractmethod
    def _get_raw_info(self) -> dict:
        raise NotImplementedError

    def delete(self) -> None:
        """Permanently deletes the entity from the Driverless AI server."""
        self._client._backend.admin_delete_entity(
            username=self.owner, kind=self._kind, key=self.key
        )


class DatasetProxy(ServerObjectProxy):
    """A Proxy for admin access for a dataset in the Driverless AI server."""

    def __init__(self, client: "_core.Client", owner: str, raw_info: dict) -> None:
        super().__init__(
            client=client,
            owner=owner,
            key=raw_info["entity"]["key"],
            name=raw_info["entity"]["name"],
        )
        self._raw_info = raw_info

    @property
    def _kind(self) -> _EntityKind:
        return _EntityKind.DATASET

    @property
    def columns(self) -> List[str]:
        """Column names of the dataset."""
        return [c["name"] for c in self._get_raw_info()["entity"]["columns"]]

    @property
    def creation_timestamp(self) -> float:
        """
        Creation timestamp of the dataset in seconds since the epoch (POSIX timestamp).
        """
        return self._get_raw_info()["created"]

    @property
    def data_source(self) -> str:
        """Original data source of the dataset."""
        return self._get_raw_info()["entity"]["data_source"]

    @property
    def description(self) -> Optional[str]:
        """Description of the dataset."""
        return self._get_raw_info()["entity"].get("notes")

    @property
    def file_path(self) -> str:
        """Path to the dataset bin file in the Driverless AI server."""
        return self._get_raw_info()["entity"]["bin_file_path"]

    @property
    def file_size(self) -> int:
        """Size in bytes of the dataset bin file in the Driverless AI server."""
        return self._get_raw_info()["entity"]["file_size"]

    @property
    def shape(self) -> Tuple[int, int]:
        """Dimensions of the dataset in (rows, cols) format."""
        return (
            self._get_raw_info()["entity"]["row_count"],
            self._get_raw_info()["entity"]["column_count"],
        )

    def _get_raw_info(self) -> dict:
        return self._raw_info


class ServerJobProxy(ServerObjectProxy):
    @abc.abstractmethod
    def _get_raw_info(self) -> dict:
        raise NotImplementedError

    @abc.abstractmethod
    def _status(self) -> _enums.JobStatus:
        raise NotImplementedError

    def is_complete(self) -> bool:
        """
        Returns whether the job has been completed successfully or not.

        Returns:
            `True` if the job finished successfully, otherwise `False`.
        """
        return _commons.is_server_job_complete(self._status())

    def is_running(self) -> bool:
        """
        Returns whether the job is currently running or not.

        Returns:
            `True` if the job has been scheduled or is running, finishing, or syncing.
                Otherwise, `False`.
        """
        return _commons.is_server_job_running(self._status())

    def status(self, verbose: int = 0) -> str:
        """
        Returns the status of the job.

        Args:
            verbose:
                - 0: A short description.
                - 1: A short description with a progress percentage.
                - 2: A detailed description with a progress percentage.

        Returns:
            Current status of the job.
        """

        status = self._status()
        # server doesn't always show 100% complete
        progress = 1 if self.is_complete() else self._get_raw_info()["progress"]
        if verbose == 1:
            return f"{status.message} {progress:.2%}"
        elif verbose == 2:
            if status == _enums.JobStatus.FAILED:
                message = self._get_raw_info()["error"]
            elif "message" in self._get_raw_info():
                message = self._get_raw_info()["message"].split("\n")[0]
            else:
                message = ""
            return f"{status.message} {progress:.2%} - {message}"

        return status.message


class ExperimentProxy(ServerJobProxy):
    """A Proxy for admin access for an experiment in the Driverless AI server."""

    def __init__(self, client: "_core.Client", owner: str, raw_info: dict) -> None:
        super().__init__(
            client=client,
            owner=owner,
            key=raw_info["key"],
            name=raw_info["description"],
        )
        self._all_datasets: Optional[List["DatasetProxy"]] = None
        self._datasets: Optional[Dict[str, Optional["DatasetProxy"]]] = None
        self._raw_info = raw_info
        self._settings: Optional[Dict[str, Any]] = None

    def _get_dataset(self, key: str) -> Optional["DatasetProxy"]:
        if self._all_datasets is None:
            self._all_datasets = self._client.admin.list_datasets(self.owner)
        for dataset in self._all_datasets:
            if dataset.key == key:
                return dataset
        return None

    def _get_raw_info(self) -> dict:
        return self._raw_info

    @property
    def _kind(self) -> _EntityKind:
        return _EntityKind.EXPERIMENT

    def _status(self) -> _enums.JobStatus:
        return _enums.JobStatus(self._get_raw_info()["status"])

    @property
    def creation_timestamp(self) -> float:
        """
        Creation timestamp of the experiment in seconds since the epoch
        (POSIX timestamp).
        """
        return self._get_raw_info()["created"]

    @property
    def datasets(self) -> Dict[str, Optional["DatasetProxy"]]:
        """
         Datasets used for the experiment.

        Returns:
            Dictionary of `train_dataset`,`validation_dataset`, and `test_dataset`.
        """
        if not self._datasets:
            train_dataset = self._get_dataset(
                self._get_raw_info()["parameters"]["dataset"]["key"]
            )
            validation_dataset = None
            test_dataset = None
            if self._get_raw_info()["parameters"]["validset"]["key"]:
                validation_dataset = self._get_dataset(
                    self._get_raw_info()["parameters"]["validset"]["key"]
                )
            if self._get_raw_info()["parameters"]["testset"]["key"]:
                test_dataset = self._get_dataset(
                    self._get_raw_info()["parameters"]["testset"]["key"]
                )
            self._datasets = {
                "train_dataset": train_dataset,
                "validation_dataset": validation_dataset,
                "test_dataset": test_dataset,
            }

        return self._datasets

    @property
    def run_duration(self) -> Optional[float]:
        """Run duration of the experiment in seconds."""
        return self._get_raw_info()["training_duration"]

    @property
    def settings(self) -> Dict[str, Any]:
        """Experiment settings."""
        if not self._settings:
            self._settings = self._client.experiments._parse_server_settings(
                self._get_raw_info()["parameters"]
            )
        return self._settings

    @property
    def size(self) -> int:
        """Size in bytes of all the experiment files on the Driverless AI server."""
        return self._get_raw_info()["model_file_size"]

    @property
    @_utils.min_supported_dai_version("2.0")
    def runtime_insights(self) -> "RuntimeTaskInsights":
        """System insights of the running experiment."""
        if not self.is_running():
            raise ValueError(f"Experiment '{self.key}' is not in the running state.")
        insights = self._client._backend.admin_get_runtime_experiment_insights_of(
            self.owner, self.key
        )
        return RuntimeTaskInsights(client=self._client, raw_info=insights)


class ModelDiagnosticProxy(ServerJobProxy):
    """A Proxy for admin access for a model diagnostic in the Driverless AI server."""

    def __init__(self, client: "_core.Client", owner: str, raw_info: Any) -> None:
        super().__init__(
            client=client,
            owner=owner,
            key=raw_info.entity.key,
            name=raw_info.entity.name,
        )
        self._all_datasets: Optional[List["DatasetProxy"]] = None
        self._all_experiments: Optional[List["ExperimentProxy"]] = None
        self._test_dataset: Optional["DatasetProxy"] = None
        self._experiment: Optional["ExperimentProxy"] = None
        self._scores: Optional[Dict[str, Dict[str, float]]] = None
        self._raw_info = raw_info

    def _get_raw_info(self) -> Any:
        return self._raw_info

    @property
    def _kind(self) -> _EntityKind:
        return _EntityKind.MODEL_DIAGNOSTIC

    def _status(self) -> _enums.JobStatus:
        return _enums.JobStatus(self._get_raw_info().status)

    def _get_dataset(self, key: str) -> Optional["DatasetProxy"]:
        if self._all_datasets is None:
            self._all_datasets = self._client.admin.list_datasets(self.owner)
        for dataset in self._all_datasets:
            if dataset.key == key:
                return dataset
        return None

    def _get_experiment(self, key: str) -> Optional["ExperimentProxy"]:
        if self._all_experiments is None:
            self._all_experiments = self._client.admin.list_experiments(self.owner)
        for experiment in self._all_experiments:
            if experiment.key == key:
                return experiment
        return None

    @property
    def experiment(self) -> "ExperimentProxy":
        """Diagnosed experiment by the model diagnostic."""
        if self._experiment is None:
            self._experiment = self._get_experiment(
                self._get_raw_info().entity.model.key
            )
        return self._experiment

    @property
    def test_dataset(self) -> "DatasetProxy":
        """Test dataset that was used for the model diagnostic."""
        if self._test_dataset is None:
            try:
                self._test_dataset = self._get_dataset(
                    self._get_raw_info().entity.dataset.key
                )
            except self._client._server_module.protocol.RemoteError:
                # assuming a key error means deleted dataset, if not the error
                # will still propagate to the user else where
                self._test_dataset = self._get_raw_info().entity.dataset.dump()
        return self._test_dataset

    @property
    def scores(self) -> Dict[str, Dict[str, float]]:
        """Scores of the model diagnostic."""
        if self._scores is None:
            scores = {}
            for score in self._get_raw_info().entity.scores:
                scores[score.score_f_name] = {
                    "score": score.score,
                    "mean": score.score_mean,
                    "sd": score.score_sd,
                }
            self._scores = scores
        return self._scores


class ProjectProxy(ServerObjectProxy):
    """A Proxy for admin access for a project in the Driverless AI server."""

    def __init__(self, client: "_core.Client", owner: str, raw_info: Any) -> None:
        super().__init__(
            client=client,
            owner=owner,
            key=raw_info.key,
            name=raw_info.name,
        )
        self._all_datasets: Optional[List["DatasetProxy"]] = None
        self._datasets: Optional[Dict[str, List["DatasetProxy"]]] = None
        self._all_experiments: Optional[List["ExperimentProxy"]] = None
        self._experiments: Optional[List["ExperimentProxy"]] = None
        self._raw_info = raw_info

    def _get_dataset(self, key: str) -> Optional["DatasetProxy"]:
        if self._all_datasets is None:
            self._all_datasets = self._client.admin.list_datasets(self.owner)
        for dataset in self._all_datasets:
            if dataset.key == key:
                return dataset
        return None

    def _get_experiment(self, key: str) -> Optional["ExperimentProxy"]:
        if self._all_experiments is None:
            self._all_experiments = self._client.admin.list_experiments(self.owner)
        for experiment in self._all_experiments:
            if experiment.key == key:
                return experiment
        return None

    def _get_raw_info(self) -> Any:
        return self._raw_info

    @property
    def _kind(self) -> _EntityKind:
        return _EntityKind.PROJECT

    def _status(self) -> _enums.JobStatus:
        return _enums.JobStatus(self._get_raw_info().status)

    @property
    def datasets(self) -> Dict[str, List["DatasetProxy"]]:
        """Datasets linked to the project."""
        if not self._datasets:
            train_datasets = [
                self._get_dataset(dataset_key)
                for dataset_key in self._get_raw_info().train_datasets
            ]

            validation_datasets = [
                self._get_dataset(dataset_key)
                for dataset_key in self._get_raw_info().validation_datasets
            ]

            test_datasets = [
                self._get_dataset(dataset_key)
                for dataset_key in self._get_raw_info().test_datasets
            ]

            self._datasets = {
                "train_datasets": train_datasets,
                "validation_datasets": validation_datasets,
                "test_datasets": test_datasets,
            }

        return self._datasets

    @property
    def description(self) -> Optional[str]:
        """Description of the project."""
        return self._get_raw_info().description or None

    @property
    def experiments(self) -> Optional[List["ExperimentProxy"]]:
        """Experiments linked to the project."""
        if not self._experiments:
            self._experiments = [
                self._get_experiment(exp_key)
                for exp_key in self._get_raw_info().experiments
            ]

        return self._experiments


class VisualizationProxy(ServerJobProxy):
    """A Proxy for admin access for a visualization in the Driverless AI server."""

    def __init__(self, client: "_core.Client", owner: str, raw_info: Any) -> None:
        super().__init__(
            client=client,
            owner=owner,
            key=raw_info.key,
            name=raw_info.name,
        )
        self._all_datasets: Optional[List["DatasetProxy"]] = None
        self._dataset: Optional["DatasetProxy"] = None
        self._raw_info = raw_info

    def _get_dataset(self, key: str) -> Optional["DatasetProxy"]:
        if self._all_datasets is None:
            self._all_datasets = self._client.admin.list_datasets(self.owner)
        for dataset in self._all_datasets:
            if dataset.key == key:
                return dataset
        return None

    def _get_raw_info(self) -> Any:
        return self._raw_info

    @property
    def _kind(self) -> _EntityKind:
        return _EntityKind.AUTOVIZ

    def _status(self) -> _enums.JobStatus:
        return _enums.JobStatus(self._get_raw_info().status)

    @property
    def dataset(self) -> "DatasetProxy":
        """Visualized dataset."""
        if self._dataset is None:
            try:
                self._dataset = self._get_dataset(self._get_raw_info().dataset.key)
            except self._client._server_module.protocol.RemoteError:
                # assuming a key error means deleted dataset, if not the error
                # will still propagate to the user else where
                self._dataset = self._get_raw_info().dataset.dump()
        return self._dataset


class InterpretationProxy(ServerJobProxy):
    """A Proxy for admin access for an interpretation in the Driverless AI server."""

    def __init__(self, client: "_core.Client", owner: str, raw_info: Any) -> None:
        super().__init__(
            client=client,
            owner=owner,
            key=raw_info.key,
            name=raw_info.description,
        )
        self._interpretation_job: Any = None
        self._all_datasets: Optional[List["DatasetProxy"]] = None
        self._all_experiments: Optional[List["ExperimentProxy"]] = None
        self._dataset: Optional["DatasetProxy"] = None
        self._experiment: Optional["ExperimentProxy"] = None
        self._raw_info = raw_info
        self._settings: Optional[Dict[str, Any]] = None

    def _update(self) -> None:
        if self._interpretation_job is None:
            self._interpretation_job = (
                self._client._backend.admin_get_interpretation_job(self.owner, self.key)
            )

    def _get_dataset(self, key: str) -> Optional["DatasetProxy"]:
        if self._all_datasets is None:
            self._all_datasets = self._client.admin.list_datasets(self.owner)
        for dataset in self._all_datasets:
            if dataset.key == key:
                return dataset
        return None

    def _get_experiment(self, key: str) -> Optional["ExperimentProxy"]:
        if self._all_experiments is None:
            self._all_experiments = self._client.admin.list_experiments(self.owner)
        for experiment in self._all_experiments:
            if experiment.key == key:
                return experiment
        return None

    def _get_raw_info(self) -> Any:
        return self._raw_info

    @property
    def _kind(self) -> _EntityKind:
        return _EntityKind.INTERPRETATION

    def _status(self) -> _enums.JobStatus:
        return _enums.JobStatus(self._get_raw_info().status)

    @property
    def creation_timestamp(self) -> float:
        """
        Creation timestamp of the interpretation in seconds since the epoch
        (POSIX timestamp).
        """
        self._update()
        return self._interpretation_job.created

    @property
    def dataset(self) -> Optional["DatasetProxy"]:
        """Dataset for the interpretation."""
        if not self._dataset:
            if hasattr(self._get_raw_info().parameters, "dataset"):
                try:
                    self._dataset = self._get_dataset(
                        self._get_raw_info().parameters.dataset.key
                    )
                except self._client._server_module.protocol.RemoteError:
                    # assuming a key error means deleted dataset, if not the error
                    # will still propagate to the user else where
                    self._dataset = self._get_raw_info().parameters.dataset.dump()
            else:
                # timeseries sometimes doesn't have dataset attribute
                try:
                    self._dataset = self.experiment.datasets["train_dataset"]
                except self._client._server_module.protocol.RemoteError:
                    # assuming a key error means deleted dataset, if not the error
                    # will still propagate to the user else where
                    self._dataset = None
        return self._dataset

    @property
    def experiment(self) -> Optional["ExperimentProxy"]:
        """Experiment for the interpretation."""
        if not self._experiment:
            experiment_key: str = self._get_raw_info().parameters.dai_model.key
            if experiment_key:
                try:
                    self._experiment = self._get_experiment(experiment_key)
                except self._client._server_module.protocol.RemoteError:
                    # assuming a key error means deleted experiment, if not the error
                    # will still propagate to the user else where
                    self._experiment = None
            else:
                self._experiment = None
        return self._experiment

    @property
    def run_duration(self) -> Optional[float]:
        """Run duration of the interpretation in seconds."""
        self._update()
        return self._interpretation_job.entity.training_duration

    @property
    def settings(self) -> Dict[str, Any]:
        """Interpretation settings."""
        self._update()
        if not self._settings:
            self._settings = self._client.mli._parse_server_settings(
                self._interpretation_job.entity.parameters.dump()
            )
        return self._settings


class RunningTask:
    """Information related to a running task in the Driverless AI server."""

    def __init__(
        self, client: "_core.Client", key: str, user: str, procedure: str, worker: str
    ) -> None:
        self._client = client
        self._key = key
        self._user = user
        self._procedure = procedure
        self._worker = worker

    @property
    def key(self) -> str:
        """Unique key of the running task in Driverless AI server."""
        return self._key

    @property
    def user(self) -> str:
        """Name of the user who initiated the task."""
        return self._user

    @property
    def procedure(self) -> str:
        """Name of the Driverless AI procedure that is executed in the task."""
        return self._procedure

    @property
    def worker(self) -> str:
        """Name of the worker node that the task is executed in."""
        return self._worker

    @_utils.min_supported_dai_version("1.11.1")
    def abort(self) -> None:
        """Aborts running tasks that belongs to the current user."""
        try:
            self._client._backend.admin_abort_task(self._key)
        except ValueError as e:
            raise ValueError(
                f"Driverless AI server failed to abort the "
                f"task {self._key} of {self._worker}. {e}"
            )


class RuntimeTaskInsights:
    """System insights related to a running task in the Driverless AI server."""

    def __init__(self, client: "_core.Client", raw_info: Any) -> None:
        self._client = client
        self._raw_info = raw_info

    @staticmethod
    def _convert_to_bytes(size_str: str) -> float:
        units = {
            "B": 1,
            "KB": 1024,
            "MB": 1024**2,
            "GB": 1024**3,
            "TB": 1024**4,
            "M": 1024**2,
        }
        size, unit = 0.0, ""
        if size_str[-2:].upper() in units:
            size, unit = float(size_str[:-2]), size_str[-2:].upper()
        elif size_str[-1].upper() in units:
            size, unit = float(size_str[:-1]), size_str[-1].upper()
        return size * units[unit]

    @property
    def entity_id(self) -> str:
        """Unique key of the entity related to the
        running task in Driverless AI server."""
        return self._raw_info.entity_id

    @property
    def username(self) -> str:
        """Name of the user who initiated the task."""
        return self._raw_info.username

    @property
    def cpu_usage(self) -> float:
        """CPU usage of the task."""
        return int(self._raw_info.cpu_utilization[:-1]) / 100

    @property
    def memory_usage(self) -> float:
        """Memory usage of the task in bytes."""
        return RuntimeTaskInsights._convert_to_bytes(self._raw_info.cpu_mem_usage)

    @property
    def gpu_usage(self) -> Dict[str, float]:
        """GPU usage statistics of the task."""
        return {
            "memory": RuntimeTaskInsights._convert_to_bytes(
                self._raw_info.gpu_mem_usage
            ),
            "usage": int(self._raw_info.gpu_utilization[:-1]) / 100,
        }

    @property
    def disk_usage(self) -> float:
        """Disk usage of the task in bytes."""
        return RuntimeTaskInsights._convert_to_bytes(self._raw_info.disk_usage)

    @property
    def creation_timestamp(self) -> str:
        """Creation timestamp of the task."""
        return self._raw_info.timestamp

    @property
    def worker_info(self) -> Dict[str, str]:
        """Name and IP of the worker node that the task is running."""
        return self._raw_info.worker_info.dump()
