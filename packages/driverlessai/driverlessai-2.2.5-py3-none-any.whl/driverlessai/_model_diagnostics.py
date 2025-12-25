"""Model diagnostics module of official Python client for Driverless AI."""

import math
import re
from typing import Any, Dict, List, Optional, Sequence, TYPE_CHECKING

from driverlessai import (
    _common_metric_plots,
    _commons,
    _core,
    _datasets,
    _experiments,
    _logging,
    _utils,
)

if TYPE_CHECKING:
    import fsspec  # noqa F401


class ModelDiagnosticMetricPlots(_common_metric_plots.CommonMetricPlots):
    """
    Interact with the metric plots of a model diagnostic in the Driverless AI server.
    """

    def __init__(
        self,
        client: "_core.Client",
        raw_info: Any,
        key: str,
        is_classification: bool,
    ) -> None:
        super().__init__(client, key, is_classification)
        self._raw_info = raw_info

    def _get_act_vs_pred_data(self) -> Any:
        return self._raw_info.act_vs_pred

    def _get_gains(self) -> Any:
        return self._raw_info.gains

    def _get_roc_data(self) -> Any:
        return self._raw_info.roc

    def _get_residual_plot_data(self) -> Any:
        return self._raw_info.residual_plot

    def _get_residual_loess_data(self) -> Any:
        return self._raw_info.residual_loess

    @property
    def residual_histogram(self) -> Optional[Dict[str, Any]]:
        """
        Residual Histogram of the model diagnostic.

        Returns:
            A residual histogram in Vega Lite (v3) format.
        """
        if self._is_classification:
            return None

        raw_info = self._raw_info.residual_hist

        ticks = raw_info.ticks
        counts = raw_info.counts
        x_values = [float(t) for t in ticks if not math.isnan(float(t))]
        y_values = [
            float(c) for c in counts if not math.isnan(float(ticks[counts.index(c)]))
        ]

        values = [
            {
                "Residual": round(float(x_values[point]), 1),
                "Count": float(y_values[point]),
                "label": f"<{round(float(x_values[point]), 4)};"
                f"{round(float(x_values[point + 1]), 4)}>",
            }
            for point in range(min(len(x_values), len(y_values)))
        ]

        return self._get_single_layer_vega_plot(
            name="Residual Histogram",
            data=values,
            marks=["bar"],
            x_axis="Residual",
            y_axis="Count",
        )


class ModelDiagnostic(_commons.ServerObject):
    """A model diagnostic in the Driverless AI server."""

    def __init__(self, client: "_core.Client", key: str) -> None:
        super().__init__(client=client, key=key)
        self._experiment: Optional[_experiments.Experiment] = None
        self._scores: Optional[Dict[str, Dict[str, float]]] = None
        self._test_dataset: Optional[_datasets.Dataset] = None

    @property
    def experiment(self) -> "_experiments.Experiment":
        """Diagnosed experiment by the model diagnostic."""
        if self._experiment is None:
            self._experiment = _experiments.Experiment(
                self._client, self._get_raw_info().entity.model.key
            )
        return self._experiment

    @property
    @_utils.beta
    def metric_plots(self) -> "ModelDiagnosticMetricPlots":
        """Metric plots of the model diagnostic."""
        model_summary = self._client._backend.get_model_summary(key=self.experiment.key)
        return ModelDiagnosticMetricPlots(
            client=self._client,
            raw_info=self._get_raw_info().entity,
            key=self.key,
            is_classification=model_summary.parameters.is_classification,
        )

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

    @property
    def test_dataset(self) -> "_datasets.Dataset":
        """Test dataset that was used for the model diagnostic."""
        if self._test_dataset is None:
            try:
                self._test_dataset = self._client.datasets.get(
                    self._get_raw_info().entity.dataset.key
                )
            except self._client._server_module.protocol.RemoteError:
                # assuming a key error means deleted dataset, if not the error
                # will still propagate to the user else where
                self._test_dataset = self._get_raw_info().entity.dataset.dump()
        return self._test_dataset

    def __repr__(self) -> str:
        return f"<class '{self.__class__.__name__}'> {self.key} {self.name}"

    def __str__(self) -> str:
        return f"{self.name} ({self.key})"

    def _update(self) -> None:
        self._set_raw_info(self._client._backend.get_model_diagnostic_job(key=self.key))
        self._set_name(self._get_raw_info().entity.name)

    def delete(self) -> None:
        """Permanently deletes the model diagnostic from the Driverless AI server."""
        key = self.key
        self._client._backend.delete_model_diagnostic_job(key=key)
        _logging.logger.info(
            f"Driverless AI Server reported model diagnostic {key} deleted."
        )

    def gui(self) -> _utils.Hyperlink:
        """
        Returns the full URL to the model diagnostic page in the Driverless AI server.

        Returns:
            URL to the model diagnostic details page.
        """
        return _utils.Hyperlink(
            f"{self._client.server.address}{self._client._gui_sep}diagnostics?"
            f"diagnostic_key={self.key}&model_key={self.experiment.key}"
        )

    def download_predictions(
        self,
        dst_dir: str = ".",
        dst_file: Optional[str] = None,
        file_system: Optional["fsspec.spec.AbstractFileSystem"] = None,
        overwrite: bool = False,
        timeout: float = 30,
    ) -> str:
        """
        Downloads the predictions of the model diagnostic as a CSV file.

        Args:
            dst_dir: The path where the CSV file will be saved.
            dst_file: The name of the CSV file (overrides the default file name).
            file_system: FSSPEC-based file system to download to
                instead of the local file system.
            overwrite: Whether to overwrite or not if a file already exists.
            timeout: Connection timeout in seconds.

        Returns:
            Path to the downloaded CSV file.
        """
        path = re.sub(
            "^.*?/files/",
            "",
            re.sub(
                "^.*?/datasets_files/", "", self._get_raw_info().entity.preds_csv_path
            ),
        )
        return self._client._download(
            server_path=path,
            dst_dir=dst_dir,
            dst_file=dst_file,
            file_system=file_system,
            overwrite=overwrite,
            timeout=timeout,
        )


class ModelDiagnosticJob(_commons.ServerJob):
    """Monitor the creation of a model diagnostic in the Driverless AI server."""

    def __init__(self, client: "_core.Client", key: str) -> None:
        super().__init__(client=client, key=key)

    def _update(self) -> None:
        self._set_raw_info(self._client._backend.get_model_diagnostic_job(key=self.key))

    def result(self, silent: bool = False) -> ModelDiagnostic:
        """
        Awaits the job's completion before returning the created model diagnostic.

        Args:
            silent: Whether to display status updates or not.

        Returns:
            Created model diagnostic by the job.
        """
        self._wait(silent)
        return ModelDiagnostic(self._client, self.key)


class ModelDiagnostics:
    """
    Interact with model
    [diagnostics](https://docs.h2o.ai/driverless-ai/1-10-lts/docs/userguide/diagnosing.html)
    in the Driverless AI server.
    """

    def __init__(self, client: "_core.Client") -> None:
        self._client = client

    def _list_model_diagnostics(self, offset: int, limit: int) -> List[Any]:
        response = self._client._backend.list_model_diagnostic(
            offset=offset, limit=limit
        )
        return [mdj.entity for mdj in response.items]

    def create(
        self,
        diagnose_experiment: _experiments.Experiment,
        test_dataset: _datasets.Dataset,
    ) -> "ModelDiagnostic":
        """
        Creates a model diagnostic in the Driverless AI server.

        Args:
            diagnose_experiment: Experiment to be diagnosed.
            test_dataset: Test dataset for the diagnosis.

        Returns:
            Created model diagnostic.
        """
        return self.create_async(diagnose_experiment, test_dataset).result()

    def create_async(
        self,
        diagnose_experiment: _experiments.Experiment,
        test_dataset: _datasets.Dataset,
    ) -> "ModelDiagnosticJob":
        """
        Launches the creation of a model diagnostic in the Driverless AI server.

        Args:
            diagnose_experiment: Experiment to be diagnosed.
            test_dataset: Test dataset for the diagnosis.

        Returns:
            Started the model diagnostic job.
        """
        key = self._client._backend.get_model_diagnostic(
            model_key=diagnose_experiment.key, dataset_key=test_dataset.key
        )
        return ModelDiagnosticJob(self._client, key)

    def get(self, key: str) -> "ModelDiagnostic":
        """
        Retrieves a model diagnostic in the Driverless AI server.

        Args:
            key: The unique ID of the model diagnostic.

        Returns:
            The model diagnostic corresponding to the key.
        """
        return ModelDiagnostic(self._client, key)

    def gui(self) -> _utils.Hyperlink:
        """
        Returns the full URL to the Model Diagnostics page in the Driverless AI server.

        Returns:
            The full URL to the Model Diagnostics page.
        """
        return _utils.Hyperlink(
            f"{self._client.server.address}{self._client._gui_sep}diagnostics"
        )

    def list(
        self, start_index: int = 0, count: int = None
    ) -> Sequence["ModelDiagnostic"]:
        """
        Retrieves model diagnostics in the Driverless AI server.

        Args:
            start_index: The index of the first model diagnostic to retrieve.
            count: The maximum number of model diagnostics to retrieve.
                If `None`, retrieves all available model diagnostics.

        Returns:
            Model diagnostics.
        """
        if count:
            data = self._list_model_diagnostics(start_index, count)
        else:
            page_size = 100
            page_position = start_index
            data = []
            while True:
                page = self._list_model_diagnostics(page_position, page_size)
                data += page
                if len(page) < page_size:
                    break
                page_position += page_size
        return _commons.ServerObjectList(
            data=data, get_method=self.get, item_class_name=ModelDiagnostic.__name__
        )
