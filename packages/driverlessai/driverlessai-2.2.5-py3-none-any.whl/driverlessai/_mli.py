"""MLI module of official Python client for Driverless AI."""

import abc
import collections
import datetime
import inspect
import json
import tempfile
import textwrap
from typing import Any
from typing import Callable
from typing import Dict
from typing import List
from typing import Mapping
from typing import Optional
from typing import Sequence
from typing import Tuple
from typing import TYPE_CHECKING
from typing import Union

import toml

from driverlessai import _commons
from driverlessai import _commons_mli
from driverlessai import _core
from driverlessai import _datasets
from driverlessai import _experiments
from driverlessai import _logging
from driverlessai import _mli_plot
from driverlessai import _recipes
from driverlessai import _utils

if TYPE_CHECKING:
    import fsspec  # noqa F401
    import pandas  # noqa F401


class Artifacts(abc.ABC):
    """An abstract class that interacts with files created by an MLI interpretation in
    the Driverless AI server."""

    def __init__(self, client: "_core.Client", paths: Dict[str, str]) -> None:
        self._client = client
        self._paths = paths

    def __repr__(self) -> str:
        return f"<class '{self.__class__.__name__}'> {list(self._paths.keys())}"

    def __str__(self) -> str:
        return f"{list(self._paths.keys())}"

    def _download(
        self,
        only: Union[str, List[str]] = None,
        dst_dir: str = ".",
        file_system: Optional["fsspec.spec.AbstractFileSystem"] = None,
        overwrite: bool = False,
        timeout: float = 30,
    ) -> Dict[str, str]:
        """Downloads the interpretation artifacts from the Driverless AI server.
        Returns a dictionary of relative paths for the downloaded artifacts.

        Args:
            only: Specify the specific artifacts to download, use
                `interpretation.artifacts.list()` to see the available
                artifacts in the Driverless AI server.
            dst_dir: The path to the
                directory where the interpretation artifacts will be saved.
            file_system: FSSPEC based file system to download to,
                instead of local file system.
            overwrite: Overwrite existing files.
            timeout: Connection timeout in seconds.
        """
        dst_paths = {}
        if isinstance(only, str):
            only = [only]
        if only is None:
            only = self._list()
        for k in only:
            path = self._paths.get(k)
            if path:
                dst_paths[k] = self._client._download(
                    server_path=path,
                    dst_dir=dst_dir,
                    file_system=file_system,
                    overwrite=overwrite,
                    timeout=timeout,
                )
            else:
                _logging.logger.info(
                    f"'{k}' does not exist in the Driverless AI server."
                )
        return dst_paths

    def _list(self) -> List[str]:
        """List of interpretation artifacts that exist in the Driverless AI server."""
        return [k for k, v in self._paths.items() if v]


class Explainer(_commons.ServerJob):
    """Interact with MLI explainers in the Driverless AI server."""

    _HELP_TEXT_WIDTH = 88
    _HELP_TEXT_INDENT = " " * 4

    def __init__(
        self,
        client: "_core.Client",
        key: str,
        mli_key: str,
        explainer_info: _commons_mli._ExplainerInfo,
        experiment_key: Optional[str],
    ) -> None:
        super().__init__(client=client, key=key)
        self._id: Optional[str] = None
        self._mli_key = mli_key
        self._explainer_info = explainer_info
        self._experiment_key = experiment_key
        self._frames: Optional[ExplainerFrames] = None
        self._help: Optional[
            Dict[str, Dict[str, Dict[str, List[Dict[str, Union[str, bool]]]]]]
        ] = None
        self._artifacts: Optional[ExplainerArtifacts] = None
        self._plots: List[_mli_plot.ExplanationPlot] = []
        self._plot_available: Optional[bool] = None

        _commons_mli.update_method_doc(
            obj=self,
            method_to_update="get_data",
            updated_doc=self._format_help("data"),
            new_signature=self._method_signature("data"),
            custom_doc_update_func=self._custom_doc_update_func,
        )

    @property
    def artifacts(self) -> "ExplainerArtifacts":
        """
        Artifacts of the explainer.

        ??? example "Example: Accessing artifacts of an explainer"
            ```py
            explainer = Explainer(client, key, mli_key, explainer_info, experiment_key)
            artifacts = explainer.artifacts
            print(artifacts)
            ```
        """
        if not self._artifacts:
            self._artifacts = ExplainerArtifacts(
                client=self._client, mli_key=self._mli_key, e_job_key=self.key
            )
        return self._artifacts

    @property
    def frames(self) -> Optional["ExplainerFrames"]:
        """
        An `ExplainerFrames` object that contains the paths to the explainer
        frames retrieved from the Driverless AI Server. If the explainer frame is not
        available, the value of this property is `None`.

        ??? example "Example: Retrieving explainer frames"
            ```py
            explainer = Explainer(client, key, mli_key, explainer_info, experiment_key)
            frames = explainer.frames
            if frames:
                print(frames)
            else:
                print("No frames available")
            ```
        """
        if not self._frames:
            frame_paths = self._client._backend.get_explainer_frame_paths(
                mli_key=self._mli_key, explainer_job_key=self.key
            )
            if frame_paths:
                self._frames = ExplainerFrames(
                    client=self._client, frame_paths=frame_paths
                )
        return self._frames

    @property
    def explanation_plots(self) -> List[_mli_plot.ExplanationPlot]:
        """
        The available plots for the explainer.

        ??? example "Example: Retrieving explanation plots"
            ```py
            explainer = Explainer(client, key, mli_key, explainer_info, experiment_key)
            plots = explainer.explanation_plots
            for plot in plots:
                print(plot)
            ```
        """
        if self._plot_available is not False and not self._plots:
            plots = _mli_plot.ExplanationPlot._create_explanation_plots(
                client=self._client,
                explainer_infos=[self._explainer_info],
                mli_key=self._mli_key,
                experiment_key=self._experiment_key,
            )
            if plots:
                self._plots, self._plot_available = plots, True
            else:
                self._plots, self._plot_available = [], False
        return self._plots

    @property
    def id(self) -> str:
        """The explainer Id."""
        return self._get_raw_info().entity.id

    def __repr__(self) -> str:
        return (
            f"<class '{self.__class__.__name__}'> {self._mli_key}/{self.key} "
            f"{self.name}"
        )

    def __str__(self) -> str:
        return f"{self.name} ({self._mli_key}/{self.key})"

    def _check_has_data(self) -> None:
        if not self.is_complete():
            raise RuntimeError(
                f"'{ExplainerData.__name__}' is only available for successfully "
                "completed explainers."
            )

    @staticmethod
    def _custom_doc_update_func(orig: str, updated: str) -> str:
        # Only include the first three line so that we don't include line refering
        # to `help(explainer.get_data)`
        orig = "\n".join(orig.split("\n")[:3])
        return f"{orig}\n\n{updated}"

    def _format_help(self, method_name: str) -> str:
        return self._do_format_help(method_name=method_name, help_dict=self._get_help())

    @classmethod
    def _do_format_help(
        cls,
        method_name: str,
        help_dict: Optional[
            Dict[str, Dict[str, Dict[str, List[Dict[str, Union[str, bool]]]]]]
        ],
    ) -> str:
        formatted_help = ""
        if help_dict:
            method = help_dict.get("methods", {method_name: {}}).get(method_name, {})
            parameters = method.get("parameters")
            if parameters:
                title = "Keyword arguments"
                underline = "-" * len(title)
                formatted_help += f"{title}\n{underline}\n"
                for param in parameters:
                    required = "required" if param["required"] else "optional"
                    formatted_help += (
                        f"{param['name']} : {param['type']}    [{required}]\n"
                    )
                    if param["default"]:
                        formatted_help += (
                            cls._indent_and_wrap(f"Default: {param['default']}") + "\n"
                        )
                    if param["doc"]:
                        doc: str = str(param["doc"])
                        formatted_help += f"{cls._indent_and_wrap(doc)}\n"
            elif help_dict:
                formatted_help = "This method does not require any arguments."
        return formatted_help

    def _get_help(
        self,
    ) -> Optional[Dict[str, Dict[str, Dict[str, List[Dict[str, Union[str, bool]]]]]]]:
        if self._help is None:
            explainer_result_help = self._client._backend.get_explainer_result_help(
                mli_key=self._mli_key, explainer_job_key=self.key
            )
            self._help = json.loads(explainer_result_help.help)
        return self._help

    @classmethod
    def _indent_and_wrap(cls, text: str) -> str:
        wrapped = textwrap.wrap(
            text=text,
            width=cls._HELP_TEXT_WIDTH,
            initial_indent=cls._HELP_TEXT_INDENT,
            subsequent_indent=cls._HELP_TEXT_INDENT,
        )
        return "\n".join(wrapped)

    def _method_signature(self, method_name: str) -> Optional[inspect.Signature]:
        help_dict = self._get_help()
        if help_dict:
            parameters = (
                help_dict.get("methods", {method_name: {}})
                .get("data", {})
                .get("parameters")
            )
            param_objs: List[inspect.Parameter] = [
                inspect.Parameter(
                    name="self", kind=inspect.Parameter.POSITIONAL_OR_KEYWORD
                )
            ]
            if parameters:
                for param in parameters:
                    param_objs.append(
                        inspect.Parameter(
                            name=str(param["name"]),
                            kind=inspect.Parameter.KEYWORD_ONLY,
                            default=inspect.Parameter.empty
                            if param["required"]
                            else None,
                            annotation=param["type"]
                            if param["type"]
                            else inspect.Parameter.empty,
                        )
                    )
            return inspect.Signature(parameters=param_objs)
        return None

    def _set_id(self, e_id: str) -> None:
        self._id = e_id

    def _update(self) -> None:
        self._set_raw_info(
            self._client._backend.get_explainer_run_job(explainer_job_key=self.key)
        )
        self._set_name(self._get_raw_info().entity.name)
        self._set_id(self._get_raw_info().entity.id)

    def get_data(self, **kwargs: Any) -> "ExplainerData":
        """
        Retrieves the `ExplainerData` from the Driverless AI server.
        Raises a `RuntimeError` exception if the explainer has not been completed
        successfully.

        Use `help(explainer.get_data)` to view help on available keyword arguments.
        """

        self._check_has_data()
        ExplainerResultDataArgs = (
            self._client._server_module.messages.ExplainerResultDataArgs
        )
        explainer_result_data_args = [
            ExplainerResultDataArgs(param_name, value)
            for param_name, value in kwargs.items()
        ]
        explainer_result_data = self._client._backend.get_explainer_result_data(
            mli_key=self._mli_key,
            explainer_job_key=self.key,
            args=explainer_result_data_args,
        )
        return ExplainerData(
            data=explainer_result_data.data,
            data_type=explainer_result_data.data_type,
            data_format=explainer_result_data.data_format,
        )

    def result(self, silent: bool = False) -> "Explainer":
        """Waits for the explainer to complete, then returns self.

        Args:
            silent: If True, do not display status updates.
        """
        self._wait(silent)
        return self


class ExplainerArtifacts(Artifacts):
    """Interact with artifacts created by an explainer during interpretation on the
    Driverless AI server."""

    def __init__(self, client: "_core.Client", mli_key: str, e_job_key: str) -> None:
        super().__init__(client=client, paths={})
        self._mli_key = mli_key
        self._e_job_key = e_job_key
        self._paths["log"] = self._get_artifact(
            self._client._backend.get_explainer_run_log_url_path
        )
        self._paths["snapshot"] = self._get_artifact(
            self._client._backend.get_explainer_snapshot_url_path
        )

    @property
    def file_paths(self) -> Dict[str, str]:
        """
        Paths to explainer artifact files on the server.

        ??? example "Example: Accessing file paths for explainer artifacts"
            ```py
            artifacts = ExplainerArtifacts(client, mli_key, e_job_key)
            paths = artifacts.file_paths
            print(paths)
            ```
        """
        return self._paths

    def _get_artifact(self, artifact_method: Callable) -> Optional[str]:
        try:
            return artifact_method(self._mli_key, self._e_job_key)
        except self._client._server_module.protocol.RemoteError:
            return ""

    def download(
        self,
        only: Union[str, List[str]] = None,
        dst_dir: str = ".",
        file_system: Optional["fsspec.spec.AbstractFileSystem"] = None,
        overwrite: bool = False,
        timeout: float = 30,
    ) -> Dict[str, str]:
        """Downloads explainer artifacts from the Driverless AI server. Returns
        a dictionary of relative paths for the downloaded artifacts.

        Args:
            only: Specify the specific artifacts to download, use
                `interpretation.artifacts.list()` to see the available
                artifacts in the Driverless AI server.
            dst_dir: The path to the
                directory where the interpretation artifacts will be saved.
            file_system: FSSPEC based file system to download to,
                instead of local file system.
            overwrite: Overwrite existing files.
            timeout: Connection timeout in seconds.

        ??? example "Example: Downloading explainer artifacts"
            ```py
            artifacts = ExplainerArtifacts(client, mli_key, e_job_key)
            downloaded_files = artifacts.download(only="log", dst_dir="artifacts_dir")
            print(downloaded_files)
            ```
        """
        return self._download(
            only=only,
            dst_dir=dst_dir,
            file_system=file_system,
            overwrite=overwrite,
            timeout=timeout,
        )

    def list(self) -> List[str]:
        """
        Lists the explainer artifacts that exist in the Driverless AI server.
        """
        return self._list()


class ExplainerData:
    """Interact with the result data of an explainer in the Driverless AI server."""

    def __init__(self, data: str, data_type: str, data_format: str) -> None:
        self._data: str = data
        self._data_as_dict: Optional[Union[List, Dict]] = None
        self._data_as_pandas: Optional["pandas.DataFrame"] = None
        self._data_type: str = data_type
        self._data_format: str = data_format

    @property
    def data(self) -> str:
        """The explainer result data as string."""
        return self._data

    @property
    def data_format(self) -> str:
        """The explainer data format."""
        return self._data_format

    @property
    def data_type(self) -> str:
        """The explainer data type."""
        return self._data_type

    def __repr__(self) -> str:
        return f"<class '{self.__class__.__name__}'> {self.data_type}"

    def __str__(self) -> str:
        return f"{self.data_type}"

    def data_as_dict(self) -> Optional[Union[List, Dict]]:
        """Return the explainer result data as a dictionary."""
        if self._data_as_dict is None and self._data:
            self._data_as_dict = json.loads(self._data)
        return self._data_as_dict

    @_utils.beta
    def data_as_pandas(self) -> Optional["pandas.DataFrame"]:
        """Return the explainer result data as a pandas frame."""
        if self._data_as_pandas is None and self._data:
            import pandas as pd

            self._data_as_pandas = pd.read_json(self._data)
        return self._data_as_pandas


class ExplainerFrames(Artifacts):
    """Interact with explanation frames created by an explainer during interpretation
    in the Driverless AI server."""

    def __init__(self, client: "_core.Client", frame_paths: Any) -> None:
        paths = {fp.name: fp.path for fp in frame_paths}
        super().__init__(client=client, paths=paths)

    @property
    def frame_paths(self) -> Dict[str, str]:
        """Frame names and paths to artifact files on the server."""
        return self._paths

    @_utils.beta
    def frame_as_pandas(
        self,
        frame_name: str,
        custom_tmp_dir: Optional[str] = None,
        keep_downloaded: bool = False,
    ) -> "pandas.DataFrame":
        """Download a frame with the given frame name to a temporary directory and
        return it as a `pandas.DataFrame`.

        Args:
            frame_name: The name of the frame to open.
            custom_tmp_dir: If specified, use this directory as the temporary
                directory instead of the default.
            keep_downloaded: If `True`, do not delete the downloaded frame. Otherwise,
                the downloaded frame is deleted before returning from this
                method.
        """
        import pandas

        args = dict(
            suffix=f"explainer-frame-{frame_name}",
            prefix="python-api",
            dir=custom_tmp_dir,
        )

        def _open_as_pandas(tmp_dir: str) -> pandas.DataFrame:
            downloaded = self.download(frame_name=frame_name, dst_dir=tmp_dir)
            frame_file_path: str = downloaded[frame_name]
            return pandas.read_csv(frame_file_path)

        if keep_downloaded:
            return _open_as_pandas(tempfile.mkdtemp(**args))
        else:
            with tempfile.TemporaryDirectory(**args) as tmp_dir:
                return _open_as_pandas(tmp_dir)

    def frame_names(self) -> List[str]:
        """
        Lists the explainer frames that exist in the Driverless AI server.
        """
        return self._list()

    def download(
        self,
        frame_name: Union[str, List[str]] = None,
        dst_dir: str = ".",
        file_system: Optional["fsspec.spec.AbstractFileSystem"] = None,
        overwrite: bool = False,
        timeout: float = 30,
    ) -> Dict[str, str]:
        """Downloads the explainer frames from the Driverless AI server. Returns
        a dictionary of relative paths for the downloaded artifacts.

        Args:
            frame_name: Specify the specific frame to download, use
                `explainer.frames.list()` to see the available
                artifacts in the Driverless AI server.
            dst_dir: The path to the
                directory where the interpretation artifacts will be saved.
            file_system: Optional["fsspec.spec.AbstractFileSystem"] = None.
            overwrite: Overwrite existing files.
            timeout: Connection timeout in seconds.
        """
        ret: Dict[str, str] = self._download(
            only=frame_name,
            dst_dir=dst_dir,
            file_system=file_system,
            overwrite=overwrite,
            timeout=timeout,
        )
        return ret


class ExplainerList(collections.abc.Sequence):
    """List that lazy loads Explainer objects."""

    def __init__(
        self,
        explainer_infos: List[_commons_mli._ExplainerInfo],
        client: "_core.Client",
        mli_key: str,
        experiment_key: Optional[str],
    ):
        self._client = client
        self._mli_key = mli_key
        self._explainer_infos: Any = explainer_infos
        self._experiment_key = experiment_key
        self._key_to_index = {}
        self._name_to_index = {}
        headers = ["", "Key", "Name"]
        data = [
            [
                i,
                d.key,
                d.name,
            ]
            for i, d in enumerate(explainer_infos)
        ]
        for idx, e_info in enumerate(explainer_infos):
            self._key_to_index[e_info.key] = idx
            self._name_to_index[e_info.name] = idx
        self._table = _utils.Table(headers=headers, data=data)

    def __getitem__(self, index: Union[int, slice, tuple]) -> Any:
        if isinstance(index, int):
            return self.__get_by_index(index)
        if isinstance(index, slice):
            return ExplainerList(
                self._explainer_infos[index],
                self._client,
                self._mli_key,
                self._experiment_key,
            )
        if isinstance(index, tuple):
            return ExplainerList(
                [self._explainer_infos[i] for i in index],
                self._client,
                self._mli_key,
                self._experiment_key,
            )

    def __len__(self) -> int:
        return len(self._explainer_infos)

    def __repr__(self) -> str:
        return self._table.__repr__()

    def _repr_html_(self) -> str:
        return self._table._repr_html_()

    @_utils.beta
    def get_by_key(self, key: str) -> Explainer:
        """Finds the explainer object that corresponds to the given key, and
        initializes it if it is not already initialized.

        Args:
            key: The job key of the desired explainer.
        """
        return self.__get_by_index(self._key_to_index[key])

    def __get_by_index(self, idx: int) -> Explainer:
        """Finds the explainer object that corresponds to the given index, and
        initializes it if it is not already initialized.

        Args:
            index: The index of the desired explainer.
        """
        data: Union[_commons_mli._ExplainerInfo, Explainer] = self._explainer_infos[idx]
        if not isinstance(data, Explainer):
            self._explainer_infos[idx] = Explainer(
                client=self._client,
                mli_key=self._mli_key,
                key=data.key,
                explainer_info=data,
                experiment_key=self._experiment_key,
            )
        return self._explainer_infos[idx]

    @_utils.beta
    def get_by_name(self, name: str) -> Explainer:
        """Finds the explainer object that corresponds to the given explainer name, and
        initializes it if it is not already initialized.

        Args:
            key: The name of the desired explainer.
        """
        return self.__get_by_index(self._name_to_index[name])


class Interpretation(_commons.ServerJob):
    """Interact with an MLI interpretation in the Driverless AI server."""

    def __init__(
        self,
        client: "_core.Client",
        key: str,
        update_method: Callable[[str], Any],
        url_method: Callable[["Interpretation"], str],
    ) -> None:
        # super() calls _update() which relies on _update_method()
        self._update_method = update_method
        super().__init__(client=client, key=key)
        self._artifacts: Optional[InterpretationArtifacts] = None
        self._dataset: Optional[_datasets.Dataset] = None
        self._experiment: Optional[_experiments.Experiment] = None
        self._explainer_list: Optional[ExplainerList] = None
        self._settings: Optional[Dict[str, Any]] = None
        self._url = url_method(self)

    @property
    def artifacts(self) -> "InterpretationArtifacts":
        """
        Interact with artifacts that are created when the
        interpretation completes.
        """
        if not self._artifacts:
            self._artifacts = InterpretationArtifacts(
                self._client, self._get_raw_info()
            )
        return self._artifacts

    @property
    def creation_timestamp(self) -> float:
        """
        Creation timestamp in seconds since the epoch (POSIX timestamp).
        """
        return self._get_raw_info().created

    @property
    def dataset(self) -> Optional[_datasets.Dataset]:
        """
        Dataset for the interpretation.
        """
        if not self._dataset:
            if hasattr(self._get_raw_info().entity.parameters, "dataset"):
                try:
                    self._dataset = self._client.datasets.get(
                        self._get_raw_info().entity.parameters.dataset.key
                    )
                except self._client._server_module.protocol.RemoteError:
                    # assuming a key error means deleted dataset, if not the error
                    # will still propagate to the user else where
                    self._dataset = (
                        self._get_raw_info().entity.parameters.dataset.dump()
                    )
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
    def experiment(self) -> Optional[_experiments.Experiment]:
        """
        Experiment for the interpretation.
        """
        if not self._experiment:
            experiment_key: str = self._get_raw_info().entity.parameters.dai_model.key
            if experiment_key:
                try:
                    self._experiment = self._client.experiments.get(experiment_key)
                except self._client._server_module.protocol.RemoteError:
                    # assuming a key error means deleted experiment, if not the error
                    # will still propagate to the user else where
                    self._experiment = None
            else:
                self._experiment = None
        return self._experiment

    @property
    @_utils.beta
    @_utils.min_supported_dai_version("1.10.5")
    def explainers(self) -> ExplainerList:
        """
        Explainers that were ran as an `ExplainerList` object.
        """
        if self._explainer_list is None:
            explainer_infos = _commons_mli._ExplainerInfo.get_all(
                client=self._client, mli_key=self.key
            )
            if explainer_infos:
                self._explainer_list = ExplainerList(
                    explainer_infos=explainer_infos,
                    client=self._client,
                    mli_key=self.key,
                    experiment_key=self.experiment.key if self.experiment else "",
                )

        return self._explainer_list

    @property
    @_utils.beta
    @_utils.min_supported_dai_version("1.10.5")
    def explanation_plots(
        self,
    ) -> Mapping[Union[int, str], List[_mli_plot.ExplanationPlot]]:
        """Plots for explanations that were created for the interpretation.

        ??? example "Example: Retrieve global and local explanation plot"
            ```py
            # get the list of available plots for the Decision Tree explainer
            MLIExplainerId = driverlessai.MLIExplainerId
            dt_plots = interpretation.explanation_plots[MLIExplainerId.DECISION_TREE]

            # retrieve the global explanation
            dt_plot = dt_plots[0].get_plot()

            # get the local explanation (for row 44)
            dt_local_plot = dt_plots[0].get_plot(row_number=44)
            ```

        """
        explainer_infos = _commons_mli._ExplainerInfo.get_all(
            client=self._client, mli_key=self.key
        )

        return _mli_plot.ExplanationPlots(
            client=self._client,
            mli_key=self.key,
            explainer_infos=explainer_infos,
            experiment_key=self.experiment.key if self.experiment else "",
        )

    @property
    def run_duration(self) -> Optional[float]:
        """Run duration in seconds."""
        try:
            return self._get_raw_info().entity.training_duration
        except AttributeError:
            _logging.logger.warning(
                "Run duration not available for some time series interpretations."
            )
            return None

    @property
    def settings(self) -> Dict[str, Any]:
        """Interpretation settings."""
        if not self._settings:
            self._settings = self._client.mli._parse_server_settings(
                self._get_raw_info().entity.parameters.dump()
            )
        return self._settings

    def __repr__(self) -> str:
        return f"<class '{self.__class__.__name__}'> {self.key} {self.name}"

    def __str__(self) -> str:
        return f"{self.name} ({self.key})"

    def _update(self) -> None:
        self._set_raw_info(self._update_method(self.key))
        self._set_name(self._get_raw_info().entity.description)

    def delete(self) -> None:
        """
        Deletes the MLI interpretation in the Driverless AI server.
        """
        key = self.key
        self._client._backend.delete_interpretation(key=key)
        _logging.logger.info(
            "Driverless AI Server reported interpretation {key} deleted."
        )

    def gui(self) -> _utils.Hyperlink:
        """
        Gets the full URL for the interpretation's
        page in the Driverless AI server.
        """
        return _utils.Hyperlink(self._url)

    @_utils.min_supported_dai_version("1.10.5")
    def parameter_summary(self) -> _utils.Table:
        """
        Gets the MLI summary.
        """
        mli_summary = json.loads(
            self._client._backend.get_mli_summary(mli_key=self.key)
        )

        parameter_summary = []
        target_column = None

        if mli_summary.get("jobSummary"):
            job_summary = mli_summary["jobSummary"]["entity"]
            job_summary_params = job_summary["parameters"]

            # MLI Experiment
            mli_experiment_description = job_summary.get("description", "N/A")
            mli_experiment_key = job_summary.get("key", "N/A")
            parameter_summary.append(
                [
                    "MLI Experiment",
                    f"{mli_experiment_description} ({mli_experiment_key})",
                ]
            )

            parameter_summary.extend(
                [
                    [
                        "Dataset",
                        job_summary_params["dataset"]["display_name"],
                    ],
                    [
                        "Feature Space For Surrogate Models",
                        "Original Features"
                        if job_summary_params["use_raw_features"]
                        else "Transformed Features",
                    ],
                    [
                        "Target Transformer",
                        job_summary["dai_target_transformation"],
                    ],
                ]
            )

            if job_summary_params["prediction_col"]:
                parameter_summary.append(
                    [
                        "Prediction Column",
                        job_summary_params["prediction_col"],
                    ]
                )

            if job_summary["prediction_label"]:
                parameter_summary.append(
                    [
                        "Prediction Label",
                        job_summary["prediction_label"],
                    ]
                )

            parameter_summary.append(
                [
                    "Surrogate CV Folds",
                    job_summary_params["nfolds"],
                ]
            )

            parameter_summary.append(
                ["MLI Duration", str(datetime.timedelta(seconds=self.run_duration))]
            )
            target_column = job_summary_params["target_col"]

        if mli_summary.get("modelSummary"):
            model_summary = mli_summary["modelSummary"]
            parameter_summary.extend(
                [
                    [
                        "DAI Experiment",
                        f"{model_summary['description']} " f"({model_summary['key']})",
                    ],
                    [
                        "Problem type",
                        "Classification"
                        if model_summary["parameters"]["is_classification"]
                        else "Regression",
                    ],
                ]
            )
            target_column = model_summary["parameters"]["target_col"]

        parameter_summary.append(["Target Column", target_column])

        if mli_summary.get("dtParameters"):
            parameter_summary.extend(
                [
                    [
                        "Tree Depth for Decision Tree Surrogate Model",
                        mli_summary["dtParameters"]["dt_tree_depth"],
                    ],
                    [
                        "Decision Tree Surrogate CV Folds",
                        mli_summary["dtParameters"]["nfolds"],
                    ],
                ]
            )

        return _utils.Table(parameter_summary, ["Parameter", "Value"])

    def rename(self, name: str) -> "Interpretation":
        """Changes the interpretation display name.

        Args:
            name: New display name.
        """
        self._client._backend.update_mli_description(key=self.key, new_description=name)
        self._update()
        return self

    def result(self, silent: bool = False) -> "Interpretation":
        """
        Waits for the job to complete, then returns an Interpretation object.
        """
        self._wait(silent)
        return self


class InterpretationArtifacts(Artifacts):
    """Interact with files created by an MLI interpretation on the
    Driverless AI server."""

    def __init__(self, client: "_core.Client", info: Any) -> None:
        paths = {
            "lime": getattr(info.entity, "lime_rc_csv_path", ""),
            "python_pipeline": getattr(info.entity, "scoring_package_path", ""),
        }
        super().__init__(client=client, paths=paths)
        self._key = info.entity.key
        if self._client.server.version >= "1.10.4":
            self._paths["log"] = self._get_artifact(
                self._client._backend.get_interpretation_zipped_logs_url_path
            )

        self._paths["shapley_transformed_features"] = self._get_artifact(
            self._client._backend.get_transformed_shapley_zip_archive_url
        )

        self._paths[
            "shapley_original_features"
        ] = self._client._backend.get_orig_shapley_zip_archive_url(
            key=self._key, use_kernel=False
        )

    @property
    def file_paths(self) -> Dict[str, str]:
        """Paths to interpretation artifact files on the server."""
        return self._paths

    def _get_artifact(self, artifact_method: Callable) -> Optional[str]:
        try:
            return artifact_method(self._key)
        except self._client._server_module.protocol.RemoteError:
            return ""

    def download(
        self,
        only: Union[str, List[str]] = None,
        dst_dir: str = ".",
        file_system: Optional["fsspec.spec.AbstractFileSystem"] = None,
        overwrite: bool = False,
    ) -> Dict[str, str]:
        """Downloads interpretation artifacts from the Driverless AI server. Returns
        a dictionary of relative paths for the downloaded artifacts.

        Args:
            only: Specify the specific artifacts to download, use
                `interpretation.artifacts.list()` to see the available
                artifacts in the Driverless AI server.
            dst_dir: The path to the
                directory where the interpretation artifacts will be saved.
            file_system: FSSPEC based file system to download to,
                instead of local file system.
            overwrite: Overwrite existing files.
        """
        return self._download(
            only=only, dst_dir=dst_dir, file_system=file_system, overwrite=overwrite
        )

    def list(self) -> List[str]:
        """List of interpretation artifacts that exist in the Driverless AI server."""
        return self._list()


class IIDMethods:
    def __init__(self, mli: "MLI"):
        self._mli = mli

    def get(self, key: str) -> "Interpretation":
        return self._mli.get(key)

    def list(
        self, start_index: int = 0, count: int = None
    ) -> Sequence["Interpretation"]:
        return self._mli.list(start_index, count)


class MLI:
    """Interact with MLI results in the Driverless AI server."""

    def __init__(self, client: "_core.Client") -> None:
        self._client = client
        self._config_items = self._create_config_item()
        self._default_interpretation_settings = {
            name: c.default for name, c in self._config_items.items()
        }
        # legacy settings that should still be accepted
        self._default_legacy_interpretation_settings = {
            "sample_num_rows": -1,
            "dt_tree_depth": 3,
            "klime_cluster_col": "",
            "qbin_cols": [],
            "dia_cols": [],
            "pd_features": None,
            "debug_model_errors": False,
            "debug_model_errors_class": "False",
        }
        interpretation_url_path = getattr(
            self._client._backend, "interpretation_url_path", "/#/interpret_next"
        )
        self._update = client._backend.get_interpretation_job
        self._url_method = lambda x: (
            f"{self._client.server.address}"
            f"{interpretation_url_path}"
            f"?interpret_key={x.key}"
        )

        # convert setting name from key to value
        self._setting_for_server_dict = {
            "target_column": "target_col",
            "prediction_column": "prediction_col",
            "weight_column": "weight_col",
            "drop_columns": "drop_cols",
            "klime_cluster_column": "klime_cluster_col",
            "dia_columns": "dia_cols",
            "qbin_columns": "qbin_cols",
        }
        self._setting_for_api_dict = {
            v: k for k, v in self._setting_for_server_dict.items()
        }
        create_sig, create_async_sig = self._get_create_method_signature()
        _commons_mli.update_method_doc(
            obj=self, method_to_update="create", new_signature=create_sig
        )
        _commons_mli.update_method_doc(
            obj=self, method_to_update="create_async", new_signature=create_async_sig
        )

    @property
    @_utils.deprecated(
        version="1.10.7",
        new_api="driverlessai._mli.MLI",
        custom_message="IIDMethods functionality will be migrated to "
        "driverlessai._mli.MLI",
    )
    def iid(self) -> IIDMethods:
        """Retrieve IID interpretations."""
        return IIDMethods(self)

    def _common_dai_explainer_params(
        self,
        experiment_key: str,
        target_column: str,
        dataset_key: str,
        validation_dataset_key: str = "",
        test_dataset_key: str = "",
        **kwargs: Any,
    ) -> Any:
        return self._client._server_module.messages.CommonDaiExplainerParameters(
            common_params=self._client._server_module.CommonExplainerParameters(
                target_col=target_column,
                weight_col=kwargs.get("weight_col", ""),
                prediction_col=kwargs.get("prediction_col", ""),
                drop_cols=kwargs.get("drop_cols", []),
                sample_num_rows=kwargs.get("sample_num_rows", -1),
            ),
            model=self._client._server_module.ModelReference(experiment_key),
            dataset=self._client._server_module.DatasetReference(dataset_key),
            validset=self._client._server_module.DatasetReference(
                validation_dataset_key
            ),
            testset=self._client._server_module.DatasetReference(test_dataset_key),
            use_raw_features=kwargs["use_raw_features"],
            config_overrides=kwargs["config_overrides"],
            sequential_execution=True,
            debug_model_errors=kwargs.get("debug_model_errors", False),
            debug_model_errors_class=kwargs.get("debug_model_errors_class", "False"),
        )

    def _create_config_item(self) -> Dict[str, _commons_mli.ConfigItem]:
        config_items: Dict[str, _commons_mli.ConfigItem] = {}

        def _construct_config_item_tuple(
            dai_config_item: Any,
        ) -> Tuple[str, _commons_mli.ConfigItem]:
            alias = (
                dai_config_item.name[4:]
                if dai_config_item.name.startswith("mli_")
                else dai_config_item.name
            )
            ci = _commons_mli.ConfigItem.create_from_dai_config_item(
                dai_config_item=dai_config_item, alias=alias
            )
            return ci.name, ci

        config_items.update(
            dict(
                _construct_config_item_tuple(c)
                for c in self._client._backend.get_all_config_options()
                if "mli" in c.tags
            )
        )
        return config_items

    def _create_iid_interpretation_async(
        self,
        experiment: Optional[_experiments.Experiment] = None,
        explainers: Optional[List[_recipes.ExplainerRecipe]] = None,
        dataset: Optional[_datasets.Dataset] = None,
        test_dataset: Optional[_datasets.Dataset] = None,
        **kwargs: Any,
    ) -> str:
        if experiment and not dataset:
            dataset_key = experiment.datasets["train_dataset"].key
            experiment_key = experiment.key
            target_column = experiment.settings["target_column"]
        elif experiment and dataset:
            dataset_key = dataset.key
            experiment_key = experiment.key
            target_column = experiment.settings["target_column"]
        elif not experiment and dataset:
            dataset_key = dataset.key
            experiment_key = ""
            target_column = kwargs.get("target_col", None)
        else:
            raise ValueError("Must provide an experiment or dataset to run MLI.")

        if test_dataset:
            test_dataset_key = test_dataset.key
        else:
            test_dataset_key = (
                experiment.datasets["test_dataset"].key
                if experiment and experiment.datasets["test_dataset"]
                else ""
            )
        interpret_params = self._client._server_module.InterpretParameters(
            dai_model=self._client._server_module.ModelReference(experiment_key),
            dataset=self._client._server_module.DatasetReference(dataset_key),
            testset=self._client._server_module.DatasetReference(test_dataset_key),
            target_col=target_column,
            prediction_col=kwargs.get("prediction_col", ""),
            weight_col=kwargs.get("weight_col", ""),
            drop_cols=kwargs.get("drop_cols", []),
            # expert settings
            lime_method=kwargs["lime_method"],
            use_raw_features=kwargs["use_raw_features"],
            sample=kwargs["sample"],
            dt_tree_depth=kwargs.get("dt_tree_depth", 3),
            vars_to_pdp=kwargs["vars_to_pdp"],
            nfolds=kwargs["nfolds"],
            qbin_count=kwargs["qbin_count"],
            sample_num_rows=kwargs.get("sample_num_rows", -1),
            klime_cluster_col=kwargs.get("klime_cluster_col", ""),
            dia_cols=kwargs.get("dia_cols", []),
            qbin_cols=kwargs.get("qbin_cols", []),
            debug_model_errors=kwargs.get("debug_model_errors", False),
            debug_model_errors_class=kwargs.get("debug_model_errors_class", "False"),
            config_overrides=kwargs["config_overrides"],
        )
        if not explainers:
            return self._client._backend.run_interpretation(interpret_params)
        else:
            params = self._common_dai_explainer_params(
                experiment_key=experiment_key,
                target_column=target_column,
                dataset_key=dataset_key,
                **kwargs,
            )
            return self._client._backend.run_interpretation_with_explainers(
                explainers=[
                    self._client._server_module.messages.Explainer(
                        e.id, json.dumps(e.settings)
                    )
                    for e in explainers
                ],
                params=params,
                interpret_params=interpret_params,
                display_name="",
            ).mli_key

    def _create_timeseries_interpretation_async(
        self,
        experiment: _experiments.Experiment,
        explainers: Optional[List[_recipes.ExplainerRecipe]] = None,
        dataset: Optional[_datasets.Dataset] = None,
        test_dataset: Optional[_datasets.Dataset] = None,
        **kwargs: Any,
    ) -> str:
        dataset_key = experiment.datasets["train_dataset"].key
        experiment_key = experiment.key
        target_column = experiment.settings["target_column"]
        if dataset:
            dataset_key = dataset.key
        if test_dataset:
            test_dataset_key = test_dataset.key
        else:
            test_dataset_key = (
                experiment.datasets["test_dataset"].key
                if experiment.datasets["test_dataset"]
                else ""
            )
        interpret_params = self._client._server_module.InterpretParameters(
            dataset=self._client._server_module.ModelReference(dataset_key),
            dai_model=self._client._server_module.ModelReference(experiment_key),
            testset=self._client._server_module.DatasetReference(test_dataset_key),
            target_col=target_column,
            use_raw_features=None,
            prediction_col=None,
            weight_col=None,
            drop_cols=None,
            klime_cluster_col=None,
            nfolds=None,
            sample=None,
            qbin_cols=None,
            qbin_count=None,
            lime_method=None,
            dt_tree_depth=None,
            vars_to_pdp=None,
            dia_cols=None,
            debug_model_errors=False,
            debug_model_errors_class="",
            sample_num_rows=kwargs.get("sample_num_rows", -1),
            config_overrides="",
        )
        if not explainers:
            return self._client._backend.run_interpret_timeseries(interpret_params)
        else:
            params = self._common_dai_explainer_params(
                experiment_key=experiment_key,
                target_column=target_column,
                dataset_key=dataset_key,
                test_dataset_key=test_dataset_key,
                **kwargs,
            )
            return self._client._backend.run_interpretation_with_explainers(
                explainers=[
                    self._client._server_module.messages.Explainer(
                        e.id, json.dumps(e.settings)
                    )
                    for e in explainers
                ],
                params=params,
                interpret_params=interpret_params,
                display_name="",
            ).mli_key

    def _get_create_method_signature(
        self,
    ) -> Tuple[inspect.Signature, inspect.Signature]:
        params: List[inspect.Parameter] = []
        for ci in self._config_items.values():
            params.append(ci.to_method_parameter())
        return (
            _commons_mli.get_updated_signature(func=MLI.create, new_params=params),
            _commons_mli.get_updated_signature(
                func=MLI.create_async, new_params=params
            ),
        )

    def _parse_server_settings(self, server_settings: Dict[str, Any]) -> Dict[str, Any]:
        """Convert Driverless AI server interpretation settings to Python API format."""
        blacklist = ["config_overrides", "dai_model", "dataset", "testset"]
        settings: Dict[str, Any] = {}
        if server_settings.get("testset", None) and server_settings["testset"].get(
            "key", ""
        ):
            try:
                settings["test_dataset"] = self._client.datasets.get(
                    server_settings["testset"]["key"]
                )
            except self._client._server_module.protocol.RemoteError:
                # assuming a key error means deleted dataset, if not the error
                # will still propagate to the user else where
                settings["test_dataset"] = server_settings["testset"]
        for key, value in server_settings.items():
            if (
                key not in blacklist
                and value not in [None, "", [], -1]
                and value != self._default_interpretation_settings.get(key)
            ):
                settings[self._setting_for_api_dict.get(key, key)] = value
        if "target_column" not in settings and server_settings["dai_model"]["key"]:
            settings["target_column"] = self._client.experiments.get(
                server_settings["dai_model"]["key"]
            ).settings["target_column"]
        return settings

    def create(
        self,
        experiment: Optional[_experiments.Experiment] = None,
        dataset: Optional[_datasets.Dataset] = None,
        name: Optional[str] = None,
        force: bool = False,
        **kwargs: Any,
    ) -> "Interpretation":
        """Creates an MLI interpretation in the Driverless AI server.

        Args:
            experiment: The experiment to interpret. Will use training dataset if the
                `dataset` has not been specified.
            dataset: The dataset to use for the interpretation
                (if dataset includes target and prediction columns, then an
                experiment will not be needed).
            name: The display name for the interpretation.
            force: Create the new interpretation even
                if the interpretation with the same
                name already exists.

        Keyword Args:
            explainers (List[ExplainerRecipe]): The list of explainer recipe objects.
            test_dataset (Dataset): Dataset object (timeseries only).
            target_column (str): The name of the column in `dataset`.
            prediction_column (str): The name of the column in `dataset`.
            weight_column (str): The name of the column in `dataset`.
            drop_columns (List[str]): The names of the columns in `dataset`.

        !!! note
            Any expert setting can also be passed as a `kwarg`.
            To search possible expert settings for your server version,
            use `mli.search_expert_settings(search_term)`.
        """
        return self.create_async(experiment, dataset, name, force, **kwargs).result()

    def create_async(
        self,
        experiment: Optional[_experiments.Experiment] = None,
        dataset: Optional[_datasets.Dataset] = None,
        name: Optional[str] = None,
        force: bool = False,
        validate_settings: bool = True,
        **kwargs: Any,
    ) -> "Interpretation":
        """Launches the creation of an MLI interpretation in the Driverless AI server.

        Args:
            experiment: The experiment to interpret. Will use training dataset if the
                `dataset` has not been specified.
            dataset: The dataset to use for the interpretation
                (if dataset includes target and prediction columns, then an
                experiment will not be needed).
            name: The display name for the interpretation.
            force: Create the new interpretation
                even if the interpretation with the same
                name already exists.

        Keyword Args:
            explainers (List[ExplainerRecipe]): The list of explainer recipe objects.
            test_dataset (Dataset): Dataset object (timeseries only).
            target_column (str): The name of the column in `dataset`.
            prediction_column (str): The name of the column in `dataset`.
            weight_column (str): The name of the column in `dataset`.
            drop_columns (List[str]): The names of the columns in `dataset`.

        ??? example "Example: Create an MLI interpretation for a given experiment"
            ```py
            interpretation = client.mli.create_async(
                experiment=my_experiment,
                name="My MLI Interpretation",
                target_column="target",
                prediction_column="prediction"
            )
            print(f"Interpretation created with key: {interpretation.key}")
            ```

        !!! note
            Any expert setting can also be passed as a `kwarg`.
            To search possible expert settings for your server version,
            use `mli.search_expert_settings(search_term)`.
        """
        if not force:
            _commons_mli.error_if_interpretation_exists(self._client, name)
        explainers = kwargs.pop("explainers", None)

        test_dataset = kwargs.pop("test_dataset", None)
        config_overrides = toml.loads(kwargs.pop("config_overrides", ""))
        settings: Dict[str, Any] = {
            "prediction_col": "",
            "weight_col": "",
            "drop_cols": [],
        }
        settings.update(self._default_legacy_interpretation_settings)
        settings.update(self._default_interpretation_settings)
        for setting, value in kwargs.items():
            server_setting = self._setting_for_server_dict.get(setting, setting)
            if server_setting not in settings:
                raise RuntimeError(f"'{setting}' MLI setting not recognized.")
            ci = self._config_items.get(setting)
            if ci:
                if validate_settings:
                    ci.validate_value(value)
                config_overrides[ci.raw_name] = value
            settings[server_setting] = value
        # add any expert settings to config_override that have to be config override
        config_overrides["mli_pd_features"] = kwargs.get(
            "pd_features", settings.get("pd_features", None)
        )
        if experiment:
            # validate experiment before proceed
            if (
                experiment.is_deprecated
                or not experiment.is_complete()
                or not experiment.datasets["train_dataset"].name
                or not experiment.settings["target_column"]
            ):
                raise ValueError("Can't use a running or unsupervised experiment.")

            experiment_config_overrides = (
                experiment._get_raw_info().entity.parameters.config_overrides
            )
            experiment_config_overrides = toml.loads(experiment_config_overrides)
            experiment_config_overrides.update(config_overrides)
            config_overrides = experiment_config_overrides
        settings["config_overrides"] = toml.dumps(config_overrides)
        key = self._create_iid_interpretation_async(
            experiment, explainers, dataset, test_dataset, **settings
        )
        update_method = self._update
        url_method = self._url_method
        interpretation = Interpretation(self._client, key, update_method, url_method)
        if name:
            interpretation.rename(name)
        return interpretation

    def gui(self) -> _utils.Hyperlink:
        """
        Prints the full URL for the user's MLI page in the Driverless AI server.
        """
        return _utils.Hyperlink(
            f"{self._client.server.address}{self._client._gui_sep}interpretations"
        )

    def search_expert_settings(
        self,
        search_term: str = "",
        show_description: bool = False,
        show_valid_values: bool = False,
    ) -> _utils.Table:
        """Searches expert settings and prints result. Useful when looking for
        `kwargs` to use when creating interpretations.

        Args:
            search_term: Term to search for (case-insensitive).
            show_description: Include description in results.
            show_valid_values: Include the valid values that can be set for each setting
                in the results.
        """
        headers: List[str] = ["Name", "Default Value"]
        if show_valid_values:
            headers.append("Valid Values")
        if show_description:
            headers.append("Description")

        data: List[List[str]] = []
        for name, c in self._config_items.items():
            if c.matches_search_term(search_term):
                row = [
                    self._setting_for_api_dict.get(name, name),
                    str(self._default_interpretation_settings[name.strip()]),
                ]
                if show_valid_values:
                    row.append(c.formatted_valid_values)
                if show_description:
                    row.append(c.formatted_description)
                data.append(row)
        return _utils.Table(headers=headers, data=data)

    def get(self, key: str) -> "Interpretation":
        """Initializes an Interpretation object but does not request information
        from the server (it is possible for the
        interpretation key to not exist on the server).
        This is useful for populating lists without making multiple network calls.

        Args:
            key: Driverless AI server's unique ID for the MLI interpretation.
        """
        interpretation = self._lazy_get(key)
        interpretation._update()
        return interpretation

    def list(
        self, start_index: int = 0, count: int = None
    ) -> Sequence["Interpretation"]:
        """List of Interpretation objects available to the user.

        Args:
            start_index: The index of the first interpretation
                to retrieve.
            count: The max number of interpretations to request from the
                Driverless AI server.
        """
        if count:
            data = self._list(start_index, count)
        else:
            page_size = 100
            page_position = start_index
            data = []
            while True:
                page = self._list(page_position, page_size)
                data += page
                if len(page) < page_size:
                    break
                page_position += page_size
        return _commons.ServerObjectList(
            data=data,
            get_method=self._lazy_get,
            item_class_name=Interpretation.__name__,
        )

    def _lazy_get(self, key: str) -> "Interpretation":
        """Initialize an Interpretation object but do not request information
        from the server (possible for interpretation key to not exist on server).
        Useful for populating lists without making a bunch of network calls.

        Args:
            key: Driverless AI server's unique ID for the MLI interpretation
        """
        return Interpretation(self._client, key, self._update, self._url_method)

    def _list(self, start_index: int, count: int) -> Any:
        return self._client._backend.list_interpretations(
            offset=start_index, limit=count
        ).items
