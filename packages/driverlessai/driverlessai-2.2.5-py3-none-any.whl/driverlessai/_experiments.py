"""Experiments module of official Python client for Driverless AI."""

import csv
import functools
import io
import time
from pathlib import Path
from typing import Any
from typing import Callable
from typing import Dict
from typing import IO
from typing import List
from typing import Optional
from typing import Sequence
from typing import Tuple
from typing import TYPE_CHECKING
from typing import Union

import toml

from driverlessai import _autodoc
from driverlessai import _common_metric_plots
from driverlessai import _commons
from driverlessai import _core
from driverlessai import _datasets
from driverlessai import _enums
from driverlessai import _exceptions
from driverlessai import _logging
from driverlessai import _projects
from driverlessai import _recipes
from driverlessai import _utils

if TYPE_CHECKING:
    import fsspec  # noqa F401
    import pandas  # noqa F401


class ExperimentMetricPlots(_common_metric_plots.CommonMetricPlots):
    """Interact with the metric plots of an experiment in the Driverless AI server."""

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
        return self._raw_info.valid_act_vs_pred

    def _get_gains(self) -> Any:
        return self._raw_info.valid_gains

    def _get_roc_data(self) -> Any:
        return self._raw_info.valid_roc

    def _get_residual_plot_data(self) -> Any:
        return self._raw_info.valid_residual_plot

    def _get_residual_loess_data(self) -> None:
        return None


class Experiment(_commons.ServerJob):
    """Interact with an experiment in the Driverless AI server."""

    def __init__(
        self, client: "_core.Client", key: str, description: Optional[str] = None
    ) -> None:
        super().__init__(client=client, key=key)
        self._description: Optional[str] = description
        self._artifacts: Optional[ExperimentArtifacts] = None
        self._datasets: Optional[Dict[str, Optional[_datasets.Dataset]]] = None
        self._log: Optional[ExperimentLog] = None
        self._settings: Optional[Dict[str, Any]] = None

    @property
    def artifacts(self) -> "ExperimentArtifacts":
        """Artifacts that are created from a completed experiment."""
        if not self._artifacts:
            self._artifacts = ExperimentArtifacts(self)
        return self._artifacts

    @property
    def creation_timestamp(self) -> float:
        """Creation timestamp in seconds since the epoch (POSIX timestamp)."""
        return self._get_raw_info().created

    def compare_settings_with(
        self, experiment_to_compare_with: "Experiment"
    ) -> _utils.Table:
        """Compares settings of the experiment with another experiment.

        Args:
            experiment_to_compare_with: The experiment to compare the settings with.

        Returns:
            A comparison table highlighting any differences in settings between the
            experiment and another specified experiment.
        """
        comparison_dict = []
        self_settings = self.settings
        compare_settings = experiment_to_compare_with.settings

        for setting, value in self_settings.items():
            compare_value = compare_settings.get(setting)
            if compare_value is None:
                comparison_dict.append([setting, value, None])
            elif value != compare_value:
                comparison_dict.append([setting, value, compare_value])

        for setting, value in compare_settings.items():
            if setting not in self_settings:
                comparison_dict.append([setting, None, value])

        return _utils.Table(
            comparison_dict,
            ["Setting", self.name, experiment_to_compare_with.name],
        )

    @property
    def datasets(self) -> Dict[str, Optional[_datasets.Dataset]]:
        """
        Dictionary of `train_dataset`, `validation_dataset`, and
        `test_dataset` used for the experiment.

        ??? example "Example: Get train/valid/test datasets in the experiment."
            ```py
            datasets = experiment.datasets()
            train_dataset = datasets["train_dataset"]
            validation_dataset = datasets["validation_dataset"]
            test_dataset = datasets["test_dataset"]
            ```
        """
        if not self._datasets:
            train_dataset = self._client.datasets.get(
                self._get_raw_info().entity.parameters.dataset.key
            )
            validation_dataset = None
            test_dataset = None
            if self._get_raw_info().entity.parameters.validset.key:
                validation_dataset = self._client.datasets.get(
                    self._get_raw_info().entity.parameters.validset.key
                )
            if self._get_raw_info().entity.parameters.testset.key:
                test_dataset = self._client.datasets.get(
                    self._get_raw_info().entity.parameters.testset.key
                )
            self._datasets = {
                "train_dataset": train_dataset,
                "validation_dataset": validation_dataset,
                "test_dataset": test_dataset,
            }
        return self._datasets

    @property
    @_utils.min_supported_dai_version("2.0")
    def description(self) -> Optional[str]:
        """Description of the experiment."""
        raw_info = self._get_raw_info()
        return getattr(raw_info.entity, "notes")

    @property
    def is_deprecated(self) -> bool:
        """`True` if experiment was created by an old version of
        Driverless AI and is no longer fully compatible with the current
        server version."""
        return self._get_raw_info().entity.deprecated

    @property
    def log(self) -> "ExperimentLog":
        """Interact with experiment logs."""
        if not self._log:
            self._log = ExperimentLog(self)
        return self._log

    @property
    @_utils.beta
    def metric_plots(self) -> Optional["ExperimentMetricPlots"]:
        """Metric plots of this model diagnostic."""

        if getattr(self.settings, "recipe", None) == "unsupervised":
            return None

        return ExperimentMetricPlots(
            client=self._client,
            raw_info=self._get_raw_info().entity,
            key=self.key,
            is_classification=self._get_raw_info().entity.parameters.is_classification,
        )

    @property
    def run_duration(self) -> Optional[float]:
        """Run duration in seconds."""
        self._update()
        return self._get_raw_info().entity.training_duration

    @property
    def settings(self) -> Dict[str, Any]:
        """Experiment settings."""
        if not self._settings:
            self._settings = self._client.experiments._parse_server_settings(
                self._get_raw_info().entity.parameters.dump()
            )
        return self._settings

    @property
    def size(self) -> int:
        """Size in bytes of all experiment's files in the Driverless AI server."""
        self._update()
        return self._get_raw_info().entity.model_file_size

    @property
    def summary(self) -> Optional[str]:
        """
        An experiment summary that provides a brief overview
        of the experiment setup and results.
        """
        if not _commons.is_server_job_complete(self._status()):
            return None
        raw_info = self._get_raw_info()
        message = getattr(raw_info, "message", "")
        entity_summary = getattr(raw_info.entity, "summary", "")
        return f"{message}\n{entity_summary}"

    def __repr__(self) -> str:
        return f"<class '{self.__class__.__name__}'> {self.key} {self.name}"

    def __str__(self) -> str:
        return f"{self.name} ({self.key})"

    def _get_retrain_settings(
        self,
        use_smart_checkpoint: bool = False,
        final_pipeline_only: bool = False,
        final_models_only: bool = False,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        # Get parent experiment settings
        settings: Dict[str, Any] = {**self.datasets, **self.settings}
        # Remove settings that shouldn't be reused
        settings.pop("name", None)
        # Update settings with any new settings
        settings.update(kwargs)
        # Set parent experiment
        settings["parent_experiment"] = self
        if use_smart_checkpoint:
            settings["feature_brain_level"] = 1003
        if final_pipeline_only:
            settings["feature_brain_level"] = 1003
            settings["time"] = 0
        if final_models_only:
            settings["feature_brain_level"] = 1003
            settings["time"] = 0
            settings["brain_add_features_for_new_columns"] = False
            settings["refit_same_best_individual"] = True
            settings["feature_brain_reset_score"] = "off"
            settings["force_model_restart_to_defaults"] = False
        return settings

    def _get_parameter_differences(
        self, parameters: Dict, experiment_to_compare_with: "Experiment"
    ) -> Dict[str, Any]:
        """Compares the parameter lists of two experiments.

        Args:
            parameters: The list of parameters
            experiment_to_compare_with: The experiment to be compared with

        Returns:
            A dictionary with the property label (str) as the key and a list of the
            current and compared experiment values for the differing parameters.
        """
        experiment_parameters_differences = {}

        for setting, value in parameters[self.key].items():
            if parameters[experiment_to_compare_with.key][setting] != value:
                experiment_parameters_differences[
                    self._get_property_labels(setting)
                ] = [value, parameters[experiment_to_compare_with.key][setting]]

        return experiment_parameters_differences

    @staticmethod
    def _get_property_labels(key: str) -> str:
        """Returns proper label names for displaying."""
        labels = {
            "dataset": "Training Dataset",
            "resumed_model": "Parent Experiment",
            "target_col": "Target Column",
            "weight_col": "Weight Column",
            "fold_col": "Fold Column",
            "orig_time_col": "Original Time Column",
            "time_col": "Time Column",
            "is_classification": "Classification",
            "cols_to_drop": "Dropped Columns",
            "validset": "Validation Dataset",
            "testset": "Test Dataset",
            "enable_gpus": "GPUs",
            "seed": "Seed",
            "accuracy": "Accuracy",
            "time": "Time",
            "interpretability": "Interpretability",
            "score_f_name": "Scorer",
            "time_groups_columns": "Time Group Columns",
            "unavailable_columns_at_"
            "prediction_time": "Columns Unavailable at Prediction Time",
            "time_period_in_seconds": "Time Period",
            "num_prediction_periods": "Prediction Periods",
            "num_gap_periods": "Gap",
            "is_timeseries": "Time Series",
            "cols_imputation": "Imputation Columns",
            "is_image": "Image Experiment",
        }
        return labels.get(key, key)

    @staticmethod
    def _update_comparison_dict(model_parameters: Dict) -> Dict[str, Any]:
        """Converts model_parameters into a dict of list values for easy comparison."""
        converted_list = {}
        for key, parameter_list in model_parameters.items():
            comparison_dict = {}
            for k, v in parameter_list.items():
                if k in ["dataset", "validset", "testset", "resumed_model"]:
                    comparison_dict[k] = v["display_name"]
                elif k in ["weight_col", "fold_col", "orig_time_col"]:
                    comparison_dict[k] = v if v is not None else ""
                else:
                    comparison_dict[k] = v
            converted_list[key] = comparison_dict
        return converted_list

    def _model_ready(func: Callable) -> Callable:  # type: ignore
        @functools.wraps(func)
        def check(self: "Experiment", *args: Any, **kwargs: Any) -> Callable:
            if self.is_complete():
                return func(self, *args, **kwargs)
            raise RuntimeError("Experiment is not complete: " + self.status(verbose=2))

        return check

    def _update(self) -> None:
        self._set_raw_info(self._client._backend.get_model_job(key=self.key))
        self._set_name(self._get_raw_info().entity.description)

    def abort(self) -> None:
        """Terminate experiment immediately and only generate logs."""
        if self.is_running():
            return self._client._backend.abort_experiment(key=self.key)

    def compare_setup_with(
        self, experiment_to_compare_with: "Experiment"
    ) -> Dict[str, _utils.Table]:
        """Compares the setup of the experiment with another given experiment.

        Args:
            experiment_to_compare_with: The experiment to compare the setups with.
        """

        model_parameters = {
            self.key: self._get_raw_info().entity.parameters.dump(),
            experiment_to_compare_with.key: self._client._backend.get_model_job(
                key=experiment_to_compare_with.key
            ).entity.parameters.dump(),
        }
        config_overrides = {
            self.key: toml.loads(model_parameters[self.key].pop("config_overrides")),
            experiment_to_compare_with.key: toml.loads(
                model_parameters[experiment_to_compare_with.key].pop("config_overrides")
            ),
        }

        exp_parameters_differences = self._get_parameter_differences(
            self._update_comparison_dict(model_parameters), experiment_to_compare_with
        )
        expert_settings_differences = self._get_parameter_differences(
            config_overrides, experiment_to_compare_with
        )

        return {
            "experiment_parameters": _utils.Table(
                [
                    [parameter_name, values[0], values[1]]
                    for parameter_name, values in exp_parameters_differences.items()
                ],
                ["Property", self.name, experiment_to_compare_with.name],
            ),
            "expert_settings": _utils.Table(
                [
                    [parameter_name, values[0], values[1]]
                    for parameter_name, values in expert_settings_differences.items()
                ],
                ["Config", self.name, experiment_to_compare_with.name],
            ),
        }

    def delete(self) -> None:
        """
        Permanently deletes the experiment from the Driverless AI server.
        """
        key = self.key
        self._client._backend.delete_model(key=key)
        time.sleep(1)  # hack for https://github.com/h2oai/h2oai/issues/14519
        _logging.logger.info(f"Driverless AI Server reported experiment {key} deleted.")

    @_model_ready
    def export_dai_file(
        self,
        dst_dir: str = ".",
        dst_file: Optional[str] = None,
        file_system: Optional["fsspec.spec.AbstractFileSystem"] = None,
        overwrite: bool = False,
        timeout: float = 30,
    ) -> str:
        """Export the experiment from Driverless AI server in DAI format.

        Args:
            dst_dir: The path to the directory where the DAI file will be saved.
            dst_file: The name of the DAI file (overrides default file name).
            file_system: The FSSPEC based file system to download to,
                instead of the local file system.
            overwrite: Overwrite the existing file.
            timeout: Connection timeout in seconds.
        """
        job_key = self._client._backend.export_experiment(key=self.key)
        completed_job = ExperimentExportJob(self._client, job_key).result(silent=True)
        dst_path = self._client._download(
            server_path=completed_job._get_raw_info().experiment_zip_path,
            dst_dir=dst_dir,
            dst_file=dst_file,
            file_system=file_system,
            overwrite=overwrite,
            timeout=timeout,
        )
        return dst_path

    @_model_ready
    @_utils.beta
    def export_triton_model(
        self,
        deploy_predictions: bool = True,
        deploy_shapley: bool = False,
        deploy_original_shapley: bool = False,
        enable_high_concurrency: bool = False,
    ) -> "TritonModelArtifact":
        """
        Exports the model of this experiment as a Triton model.

        Args:
           deploy_predictions: whether to deploy model predictions
           deploy_shapley: whether to deploy model Shapley
           deploy_original_shapley: whether to deploy model original Shapley
           enable_high_concurrency: whether to enable handling multiple requests at once
        Returns: a triton model
        """
        exported_path = self._client._backend.export_triton_model(
            experiment_key=self.key,
            deploy_preds=deploy_predictions,
            deploy_pred_contribs=deploy_shapley,
            deploy_pred_contribs_orig=deploy_original_shapley,
            high_concurrency=enable_high_concurrency,
        )
        return TritonModelArtifact(self._client, exported_path)

    def finish(self) -> None:
        """Finish experiment by jumping to final pipeline training and generating
        experiment artifacts.
        """
        if self.is_running():
            return self._client._backend.stop_experiment(key=self.key)

    @_model_ready
    def fit_and_transform(
        self,
        training_dataset: _datasets.Dataset,
        validation_split_fraction: float = 0,
        seed: int = 1234,
        fold_column: str = None,
        test_dataset: _datasets.Dataset = None,
        validation_dataset: _datasets.Dataset = None,
    ) -> "FitAndTransformation":
        """Transform a dataset, then return a FitAndTransformation object.

        Args:
            training_dataset: The dataset to be used for refitting the
                data transformation pipeline.
            validation_split_fraction: The fraction of data used for validation.
            seed: A random seed to use to start a random generator.
            fold_column: The column to create a stratified validation split.
            test_dataset: The dataset to be used for final testing.
            validation_dataset: The dataset to be used for tune parameters of models.
        """
        return self.fit_and_transform_async(
            training_dataset=training_dataset,
            validation_split_fraction=validation_split_fraction,
            seed=seed,
            fold_column=fold_column,
            test_dataset=test_dataset,
            validation_dataset=validation_dataset,
        ).result()

    @_model_ready
    def fit_and_transform_async(
        self,
        training_dataset: _datasets.Dataset,
        validation_split_fraction: float = 0,
        seed: int = 1234,
        fold_column: str = None,
        test_dataset: _datasets.Dataset = None,
        validation_dataset: _datasets.Dataset = None,
    ) -> "FitAndTransformationJob":
        """Launch transform job on a dataset and return a FitAndTransformationJob object
        to track the status.

        Args:
            training_dataset: The dataset to be used for refitting the
                data transformation pipeline.
            validation_split_fraction: The fraction of data used for validation.
            seed: A random seed to use to start a random generator.
            fold_column: The column to create a stratified validation split.
            test_dataset: The dataset to be used for final testing.
            validation_dataset: The dataset to be used for tune parameters of models.
        """
        available_columns = self.datasets["train_dataset"].columns
        if fold_column and fold_column not in available_columns:
            raise ValueError(
                f"Invalid column '{fold_column}'. "
                f"Possible values are {available_columns}"
            )

        job_key = self._client._backend.fit_transform_batch(
            model_key=self.key,
            training_dataset_key=training_dataset.key,
            validation_dataset_key=validation_dataset.key if validation_dataset else "",
            test_dataset_key=test_dataset.key if test_dataset else "",
            validation_split_fraction=validation_split_fraction,
            seed=seed,
            fold_column=fold_column,
        )

        return FitAndTransformationJob(self._client, job_key)

    @_utils.min_supported_dai_version("1.11.0")
    @_utils.beta
    def get_previous_predictions(self) -> List["Prediction"]:
        """Get all previous predictions of the current experiment."""
        sort_query = self._client._server_module.messages.EntitySortQuery("", "", "")
        query_responses = self._client._backend.search_and_sort_predictions(
            model_key=self.key,
            dataset_key="",
            sort_query=sort_query,
            offset=0,
            limit=100,
            ascending=True,
        )
        prediction_jobs = []
        for response in query_responses.items:
            prediction_job = response.entity
            prediction_jobs.append(
                PredictionJob(
                    self._client,
                    prediction_job.key,
                    prediction_job.scoring_dataset_key,
                    prediction_job.model_key,
                )
            )
        return [Prediction([prediction_job]) for prediction_job in prediction_jobs]

    @_utils.min_supported_dai_version("1.10.5")
    def get_linked_projects(self) -> List["_projects.Project"]:
        """Get all the projects that the current experiment belongs to."""
        linked_projects = self._client._backend.list_projects_containing_experiment(
            experiment_key=self.key
        )
        return [self._client.projects.get(project.key) for project in linked_projects]

    def gui(self) -> _utils.Hyperlink:
        """Obtains the complete URL for the experiment's
        page in the Driverless AI server."""
        return _utils.Hyperlink(
            f"{self._client.server.address}{self._client._gui_sep}"
            f"experiment?key={self.key}"
        )

    def metrics(self) -> Dict[str, Union[str, float]]:
        """Return dictionary of experiment scorer metrics and AUC metrics,
        if available.
        """
        self._update()
        metrics = {}
        metrics["scorer"] = self._get_raw_info().entity.score_f_name

        metrics["val_score"] = self._get_raw_info().entity.valid_score
        metrics["val_score_sd"] = self._get_raw_info().entity.valid_score_sd
        metrics["val_roc_auc"] = self._get_raw_info().entity.valid_roc.auc
        metrics["val_pr_auc"] = self._get_raw_info().entity.valid_roc.aucpr

        metrics["test_score"] = self._get_raw_info().entity.test_score
        metrics["test_score_sd"] = self._get_raw_info().entity.test_score_sd
        metrics["test_roc_auc"] = self._get_raw_info().entity.test_roc.auc
        metrics["test_pr_auc"] = self._get_raw_info().entity.test_roc.aucpr

        return metrics

    def notifications(self) -> List[Dict[str, str]]:
        """Return list of experiment notification dictionaries."""
        notifications = []
        for n in self._client._backend.list_model_notifications(
            model_key=self.key, keys=self._get_raw_info().entity.notifications
        ):
            n = n.dump()
            del n["key"]
            notifications.append(n)
        return notifications

    @_model_ready
    def predict(
        self,
        dataset: Union["_datasets.Dataset", "pandas.DataFrame"],
        enable_mojo: bool = True,
        include_columns: Optional[List[str]] = None,
        include_labels: Optional[bool] = None,
        include_raw_outputs: Optional[bool] = None,
        include_shap_values_for_original_features: Optional[bool] = None,
        include_shap_values_for_transformed_features: Optional[bool] = None,
        use_fast_approx_for_shap_values: Optional[bool] = None,
    ) -> "Prediction":
        """Predict on a dataset, then return a Prediction object.

        Args:
            dataset: A Dataset or a Pandas DataFrame that can be predicted.
            enable_mojo: Use MOJO (if available) to make predictions.
            include_columns: The list of columns from the dataset to append to the
                prediction CSV.
            include_labels: Append labels in addition to probabilities for
                classification, ignored for regression.
            include_raw_outputs: Append predictions as margins (in link space)
                to the prediction CSV.
            include_shap_values_for_original_features: Append original feature
                contributions to the prediction CSV.
            include_shap_values_for_transformed_features: Append transformed
                feature contributions to the prediction CSV.
            use_fast_approx_for_shap_values: Speed up prediction contributions
                with approximation.
        """
        return self.predict_async(
            dataset,
            enable_mojo,
            include_columns,
            include_labels,
            include_raw_outputs,
            include_shap_values_for_original_features,
            include_shap_values_for_transformed_features,
            use_fast_approx_for_shap_values,
        ).result()

    @_model_ready
    def predict_async(
        self,
        dataset: Union["_datasets.Dataset", "pandas.DataFrame"],
        enable_mojo: bool = True,
        include_columns: Optional[List[str]] = None,
        include_labels: Optional[bool] = None,
        include_raw_outputs: Optional[bool] = None,
        include_shap_values_for_original_features: Optional[bool] = None,
        include_shap_values_for_transformed_features: Optional[bool] = None,
        use_fast_approx_for_shap_values: Optional[bool] = None,
    ) -> "PredictionJobs":
        """Launch prediction job on a dataset and return a PredictionJobs object
        to track the status.

        Args:
            dataset: A Dataset or a Pandas DataFrame that can be predicted.
            enable_mojo: Use MOJO (if available) to make predictions.
            include_columns: The list of columns from the dataset to append to the
                prediction CSV.
            include_labels: Append labels in addition to probabilities for
                classification, ignored for regression.
            include_raw_outputs: Append predictions as margins (in link space)
                to the prediction CSV.
            include_shap_values_for_original_features: Append original feature
                contributions to the prediction CSV.
            include_shap_values_for_transformed_features: Append transformed
                feature contributions to the prediction CSV.
            use_fast_approx_for_shap_values: Speed up prediction contributions
                with approximation.
        """
        if include_columns is None:
            include_columns = []

        if dataset.__class__.__name__ == "DataFrame":
            dataset = self._client.datasets.create(dataset)

        # note that `make_prediction` has 4 mutually exclusive options that
        # create different csvs, which is why it has to be called up to 4 times
        keys = []
        # creates csv of probabilities
        keys.append(
            self._client._backend.make_prediction(
                model_key=self.key,
                dataset_key=dataset.key,
                output_margin=False,
                pred_contribs=False,
                pred_contribs_original=False,
                enable_mojo=enable_mojo,
                fast_approx=False,
                fast_approx_contribs=False,
                keep_non_missing_actuals=False,
                include_columns=include_columns,
                pred_labels=include_labels or False,
                transform_only=False,
            )
        )
        if include_raw_outputs:
            # creates csv of raw outputs only
            keys.append(
                self._client._backend.make_prediction(
                    model_key=self.key,
                    dataset_key=dataset.key,
                    output_margin=True,
                    pred_contribs=False,
                    pred_contribs_original=False,
                    enable_mojo=enable_mojo,
                    fast_approx=False,
                    fast_approx_contribs=False,
                    keep_non_missing_actuals=False,
                    include_columns=[],
                    pred_labels=False,
                    transform_only=False,
                )
            )
        if include_shap_values_for_original_features:
            # creates csv of SHAP values only
            keys.append(
                self._client._backend.make_prediction(
                    model_key=self.key,
                    dataset_key=dataset.key,
                    output_margin=False,
                    pred_contribs=True,
                    pred_contribs_original=True,
                    enable_mojo=enable_mojo,
                    fast_approx=False,
                    fast_approx_contribs=use_fast_approx_for_shap_values or False,
                    keep_non_missing_actuals=False,
                    include_columns=[],
                    pred_labels=False,
                    transform_only=False,
                )
            )
        if include_shap_values_for_transformed_features:
            # creates csv of SHAP values only
            keys.append(
                self._client._backend.make_prediction(
                    model_key=self.key,
                    dataset_key=dataset.key,
                    output_margin=False,
                    pred_contribs=True,
                    pred_contribs_original=False,
                    enable_mojo=enable_mojo,
                    fast_approx=False,
                    fast_approx_contribs=use_fast_approx_for_shap_values or False,
                    keep_non_missing_actuals=False,
                    include_columns=[],
                    pred_labels=False,
                    transform_only=False,
                )
            )
        jobs = [PredictionJob(self._client, key, dataset.key, self.key) for key in keys]

        # The user will get a single csv created by concatenating all the above csvs.
        # From the user perspective they are creating a single csv even though
        # multiple csv jobs are spawned. The PredictionJobs object allows the
        # multiple jobs to be interacted with as if they were a single job.
        return PredictionJobs(
            client=self._client,
            jobs=jobs,
            dataset_key=dataset.key,
            experiment_key=self.key,
            include_columns=include_columns,
            include_labels=include_labels,
            include_raw_outputs=include_raw_outputs,
            include_shap_values_for_original_features=(
                include_shap_values_for_original_features
            ),
            include_shap_values_for_transformed_features=(
                include_shap_values_for_transformed_features
            ),
            use_fast_approx_for_shap_values=use_fast_approx_for_shap_values,
        )

    @_model_ready
    def transform(
        self,
        dataset: _datasets.Dataset,
        enable_mojo: bool = True,
        include_columns: Optional[List[str]] = None,
        include_labels: Optional[bool] = True,
    ) -> "Transformation":
        """Transform a dataset, then return a Transformation object.

        Args:
            dataset: A Dataset that can be predicted.
            enable_mojo: Use MOJO (if available) to make transformation.
            include_columns: List of columns from the dataset to append to the
                prediction CSV.
            include_labels: Append labels in addition to probabilities for
                classification, ignored for regression.
        """
        return self.transform_async(
            dataset=dataset,
            enable_mojo=enable_mojo,
            include_labels=include_labels,
            include_columns=include_columns,
        ).result()

    @_model_ready
    @_utils.min_supported_dai_version("1.10.4.1")
    def transform_async(
        self,
        dataset: _datasets.Dataset,
        enable_mojo: bool = True,
        include_columns: Optional[List[str]] = None,
        include_labels: Optional[bool] = None,
    ) -> "TransformationJob":
        """Launch transform job on a dataset and return a TransformationJob object
        to track the status.

        Args:
            dataset: A Dataset that can be predicted.
            enable_mojo: Use MOJO (if available) to make transformation.
            include_columns: List of columns from the dataset to append to the
                prediction CSV.
            include_labels: Append labels in addition to probabilities for
                classification, ignored for regression.
        """

        if include_columns is None:
            include_columns = []

        key = self._client._backend.make_prediction(
            model_key=self.key,
            dataset_key=dataset.key,
            output_margin=False,
            pred_contribs=False,
            pred_contribs_original=False,
            enable_mojo=enable_mojo,
            fast_approx=False,
            fast_approx_contribs=False,
            keep_non_missing_actuals=False,
            include_columns=include_columns,
            pred_labels=include_labels or False,
            transform_only=True,
        )

        return TransformationJob(
            client=self._client,
            key=key,
            dataset_key=dataset.key,
            experiment_key=self.key,
            include_columns=include_columns,
            include_labels=include_labels,
        )

    @_utils.min_supported_dai_version("2.0")
    def redescribe(self, description: str) -> "Experiment":
        """Change experiment description.
        Args:
            description: New description.
        """
        self._client._backend.annotate_experiment(self.key, description)
        self._update()
        return self

    def rename(self, name: str) -> "Experiment":
        """Change experiment display name.

        Args:
            name: New display name.
        """
        self._client._backend.update_model_description(
            key=self.key, new_description=name
        )
        self._update()
        return self

    def result(self, silent: bool = False) -> "Experiment":
        """Wait for training to complete, then return self.

        Args:
            silent: If True, do not display status updates.
        """
        self._wait(silent)
        if self._description:
            self._client._backend.annotate_experiment(self.key, self._description)
        return self

    def retrain(
        self,
        use_smart_checkpoint: bool = False,
        final_pipeline_only: bool = False,
        final_models_only: bool = False,
        **kwargs: Any,
    ) -> "Experiment":
        """Create a new experiment using the same datasets and settings. Through
        `kwargs` it's possible to pass new datasets or overwrite settings.

        Args:
            use_smart_checkpoint: Start the experiment from the last smart checkpoint.
            final_pipeline_only: Trains the final pipeline using smart checkpoint
                if available, otherwise uses default hyperparameters.
            final_models_only: Trains the final pipeline models (but not transformers)
                using smart checkpoint if available, otherwise uses default
                hyperparameters and transformers (overrides `final_pipeline_only`).
            kwargs: Datasets and experiment settings as defined in
                `experiments.create()`.
        """
        return self.retrain_async(
            use_smart_checkpoint=use_smart_checkpoint,
            final_pipeline_only=final_pipeline_only,
            final_models_only=final_models_only,
            **kwargs,
        ).result()

    def retrain_async(
        self,
        use_smart_checkpoint: bool = False,
        final_pipeline_only: bool = False,
        final_models_only: bool = False,
        **kwargs: Any,
    ) -> "Experiment":
        """Launch creation of a new experiment using the same datasets and
        settings. Through `kwargs` it's possible to pass new datasets or
        overwrite settings.

        Args:
            use_smart_checkpoint: Start the experiment from the last smart checkpoint.
            final_pipeline_only: Trains the final pipeline using smart checkpoint
                if available, otherwise uses default hyperparameters.
            final_models_only: Trains the final pipeline models (but not transformers)
                using smart checkpoint if available, otherwise uses default
                hyperparameters and transformers (overrides `final_pipeline_only`).
            kwargs: Datasets and experiment settings as defined in
                `experiments.create()`.
        """
        settings = self._get_retrain_settings(
            use_smart_checkpoint=use_smart_checkpoint,
            final_pipeline_only=final_pipeline_only,
            final_models_only=final_models_only,
            **kwargs,
        )
        return self._client.experiments.create_async(**settings)

    def variable_importance(
        self, iteration: int = None, model_index: int = None
    ) -> Optional[_utils.Table]:
        """Get variable importance of an iteration in a Table.

        Args:
            iteration: Zero-based index of the iteration of the experiment.
            model_index: The zero-based index of model
                        that was generated in a particular iteration.
        """
        if iteration is None:
            variable_importance = self._client._backend.get_variable_importance(
                key=self.key
            ).dump()
        else:
            model_index = -1 if model_index is None else model_index

            iterations = self._client._backend.list_model_iteration_data(
                key=self.key, limit=1, num_var_imp=None, offset=iteration
            )

            if not iterations:
                return None

            if model_index >= len(iterations[0].importances):
                return None

            variable_importance = iterations[0].importances[model_index].dump()
        return _utils.Table(
            [list(x) for x in zip(*variable_importance.values())],
            variable_importance.keys(),
        )

    def _to_dict(
        self, _object: object, excluded_list: list = []
    ) -> Union[Dict, object]:
        """Internal function to dump experiment meta data to a dictionary"""
        # TODO: It's a common function serialize any python object to a dictionary.
        # TODO: May be we can move this into a utils (need to discuss)
        experiment_meta_data = {}

        if hasattr(_object, "name"):
            experiment_meta_data["name"] = _object.name  # type: ignore

        if hasattr(_object, "key"):
            experiment_meta_data["key"] = _object.key  # type: ignore

        if isinstance(_object, dict):
            for k, v in _object.items():
                if k not in excluded_list:
                    experiment_meta_data[k] = self._to_dict(v)
            return experiment_meta_data

        properties = [
            name
            for name, value in vars(_object.__class__).items()
            if isinstance(value, property) and name not in excluded_list
        ]

        if not properties and not isinstance(
            _object, (int, bool, str, float, list, tuple)
        ):
            return experiment_meta_data

        if (
            isinstance(_object, Experiment)
            and self._client.server.version < "2.0"
            and "description" in properties
        ):
            properties.remove("description")

        for prop_name in properties:
            prop_value = getattr(_object, prop_name)
            if prop_value.__class__ and not isinstance(
                prop_value, (int, bool, str, float, list, tuple)
            ):
                experiment_meta_data[prop_name] = self._to_dict(prop_value)
            else:
                experiment_meta_data[prop_name] = prop_value

        return experiment_meta_data if experiment_meta_data else _object

    @_model_ready
    @_utils.beta
    def to_dict(self) -> Union[Dict, object]:
        """Dump experiment meta data to a python dictionary"""
        # TODO: Need to mark this function as PREVIEW / EXPERIMENTAL
        excluded_list = ["metric_plots"]
        experiment_meta_data = self._to_dict(self, excluded_list)

        if isinstance(experiment_meta_data, dict):
            parent_experiment = self.settings.get("parent_experiment", "")
            experiment_meta_data["parent_experiment"] = (
                parent_experiment if parent_experiment == "" else parent_experiment.key
            )
            experiment_meta_data["metrics"] = self.metrics()
            experiment_meta_data["status"] = self.status()
            experiment_meta_data[
                "variable_importance"
            ] = self._client._backend.get_variable_importance(key=self.key).dump()
        return experiment_meta_data

    @_model_ready
    def autodoc(self) -> "_autodoc.AutoDoc":
        """
        Returns the autodoc generated for this experiment.
        If it has not generated, creates a new autodoc and returns.
        """
        # wait for autodoc job to complete
        # then check whether report is available and return
        autodoc = _autodoc.AutoDocJob(self._client, self.key).result()
        if self._client._backend.get_autoreport_job(key=self.key).entity.report_path:
            return autodoc

        # else create autodoc and return it
        return _autodoc.AutoDocs(client=self._client).create(experiment=self)


class ExperimentArtifacts:
    """Interact with files created by an experiment in the Driverless AI server."""

    def __init__(self, experiment: "Experiment") -> None:
        self._experiment = experiment
        self._paths: Dict[str, str] = {}
        self._prediction_dataset_type = {
            "test_predictions": "test",
            "train_predictions": "train",
            "val_predictions": "valid",
        }

    @property
    def file_paths(self) -> Dict[str, str]:
        """Paths to artifact files on the server."""
        self.list()  # checks if experiment is complete and updates paths
        return self._paths

    def _get_path(self, attr: str, do_timeout: bool = True, timeout: int = 60) -> str:
        path = getattr(self._experiment._get_raw_info().entity, attr)
        if not do_timeout:
            return path
        seconds = 0
        while path == "" and seconds < timeout:
            time.sleep(1)
            seconds += 1
            self._experiment._update()
            path = getattr(self._experiment._get_raw_info().entity, attr)
        return path

    def _model_ready(func: Callable) -> Callable:  # type: ignore
        @functools.wraps(func)
        def check(self: "ExperimentArtifacts", *args: Any, **kwargs: Any) -> Callable:
            if self._experiment.is_complete():
                return func(self, *args, **kwargs)
            raise RuntimeError(
                "Experiment is not complete: " + self._experiment.status(verbose=2)
            )

        return check

    def _update(self) -> None:
        self._experiment._update()
        self._paths["autoreport"] = self._get_path(
            "autoreport_path", self._experiment.settings.get("make_autoreport", False)
        )
        self._paths["autodoc"] = self._paths["autoreport"]
        self._paths["logs"] = self._get_path("log_file_path")
        self._paths["mojo_pipeline"] = self._get_path(
            "mojo_pipeline_path",
            self._experiment.settings.get("make_mojo_pipeline", "off") == "on",
        )
        self._paths["python_pipeline"] = self._get_path(
            "scoring_pipeline_path",
            self._experiment.settings.get("make_python_scoring_pipeline", "off")
            == "on",
        )
        self._paths["summary"] = self._get_path("summary_path")
        self._paths["test_predictions"] = self._get_path("test_predictions_path", False)
        self._paths["train_predictions"] = self._get_path(
            "train_predictions_path", False
        )
        self._paths["val_predictions"] = self._get_path("valid_predictions_path", False)

    @_model_ready
    def create(self, artifact: str) -> None:
        """(Re)build certain artifacts, if possible.

        (re)buildable artifacts:

        - `'autodoc'`
        - `'mojo_pipeline'`
        - `'python_pipeline'`

        Args:
            artifact: The name of the artifact to (re)build.
        """
        if artifact == "python_pipeline":
            _logging.logger.info("Building Python scoring pipeline...")
            if not self._experiment._client._backend.build_scoring_pipeline_sync(
                model_key=self._experiment.key, force=True
            ).file_path:
                _logging.logger.info("Unable to build Python scoring pipeline.")
        if artifact == "mojo_pipeline":
            _logging.logger.info("Building MOJO pipeline...")
            if not self._experiment._client._backend.build_mojo_pipeline_sync(
                model_key=self._experiment.key, force=True
            ).file_path:
                _logging.logger.info("Unable to build MOJO pipeline.")
        if artifact == "autodoc" or artifact == "autoreport":
            _logging.logger.info("Generating autodoc...")
            if not self._experiment._client._backend.make_autoreport_sync(
                model_key=self._experiment.key, template="", config=""
            ).report_path:
                _logging.logger.info("Unable to generate autodoc.")

    @_model_ready
    def download(
        self,
        only: Union[str, List[str]] = None,
        dst_dir: str = ".",
        file_system: Optional["fsspec.spec.AbstractFileSystem"] = None,
        include_columns: Optional[List[str]] = None,
        overwrite: bool = False,
        timeout: float = 30,
    ) -> Dict[str, str]:
        """Download experiment artifacts from the Driverless AI server. Returns
        a dictionary of relative paths for the downloaded artifacts.

        Args:
            only: Specify the specific artifacts to download, use
                `experiment.artifacts.list()` to see the available
                artifacts in the Driverless AI server.
            dst_dir: The path to the
                directory where the experiment artifacts will be saved.
            file_system: FSSPEC based file system to download to,
                instead of local file system.
            include_columns: The list of dataset columns
                to append to prediction CSVs.
            overwrite: Overwrite the existing file.
            timeout: Connection timeout in seconds.
        """
        self._update()
        if include_columns is None:
            include_columns = []
        all_dataset_columns: List[str] = sum(
            [getattr(d, "columns", []) for d in self._experiment.datasets.values()],
            [],
        )
        for c in include_columns:
            if c not in all_dataset_columns:
                raise RuntimeError(f"Column '{c}' not found in datasets.")
        dst_paths = {}
        if isinstance(only, str):
            only = [only]
        if only is None:
            only = self.list()
        for artifact in only:
            if include_columns and artifact in self._prediction_dataset_type:
                key = self._experiment._client._backend.download_prediction(
                    model_key=self._experiment.key,
                    dataset_type=self._prediction_dataset_type[artifact],
                    include_columns=include_columns,
                )
                while _commons.is_server_job_running(
                    self._experiment._client._backend.get_prediction_job(key=key).status
                ):
                    time.sleep(1)
                prediction_job = self._experiment._client._backend.get_prediction_job(
                    key
                )
                if _commons.is_server_job_failed(prediction_job.status):
                    error = self._experiment._client._backend._format_server_error(
                        message=prediction_job.error
                    )
                    raise RuntimeError(
                        f"Cannot download '{artifact}' artifact. {error}"
                    )
                path = prediction_job.entity.predictions_csv_path
            else:
                path = self._paths.get(artifact)

            if not path:
                raise RuntimeError(
                    f"'{artifact}' does not exist in the Driverless AI server."
                )
            dst_paths[artifact] = self._experiment._client._download(
                server_path=path,
                dst_dir=dst_dir,
                file_system=file_system,
                overwrite=overwrite,
                timeout=timeout,
            )
        return dst_paths

    @_model_ready
    def export(
        self,
        only: Optional[Union[str, List[str]]] = None,
        include_columns: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> Dict[str, str]:
        """Export experiment artifacts from the Driverless AI server. Returns
        a dictionary of relative paths for the exported artifacts.

        Args:
            only: Specify the specific artifacts to download, use
                `experiment.artifacts.list()` to see the available
                artifacts in the Driverless AI server.
            include_columns: The list of dataset
                columns to append to prediction CSVs.

        !!! note
            Export location is configured in the Driverless AI server.
        """
        self._update()
        if include_columns is None:
            include_columns = []
        all_dataset_columns: List[str] = sum(
            [getattr(d, "columns", []) for d in self._experiment.datasets.values()],
            [],
        )
        for c in include_columns:
            if c not in all_dataset_columns:
                raise RuntimeError(f"Column '{c}' not found in datasets.")
        export_location = self._experiment._client._backend.list_experiment_artifacts(
            model_key=self._experiment.key,
            storage_destination=kwargs.get("storage_destination", ""),
        ).location
        exported_artifacts = {}
        if isinstance(only, str):
            only = [only]
        if only is None:
            only = self.list()
        for artifact in only:
            if include_columns and artifact in self._prediction_dataset_type:
                key = self._experiment._client._backend.download_prediction(
                    model_key=self._experiment.key,
                    dataset_type=self._prediction_dataset_type[artifact],
                    include_columns=include_columns,
                )
                while _commons.is_server_job_running(
                    self._experiment._client._backend.get_prediction_job(key=key).status
                ):
                    time.sleep(1)
                prediction_job = self._experiment._client._backend.get_prediction_job(
                    key=key
                )
                if _commons.is_server_job_failed(prediction_job.status):
                    error = self._experiment._client._backend._format_server_error(
                        message=prediction_job.error
                    )
                    raise RuntimeError(
                        f"Cannot download '{artifact}' artifact. {error}"
                    )
                artifact_path = prediction_job.entity.predictions_csv_path
            else:
                artifact_path = self._paths.get(artifact)

            if not artifact_path:
                raise RuntimeError(
                    f"'{artifact_path}' does not exist in the Driverless AI server."
                )
            artifact_file_name = Path(artifact_path).name
            job_key = self._experiment._client._backend.upload_experiment_artifacts(
                model_key=self._experiment.key,
                user_note=kwargs.get("user_note", ""),
                artifact_path=artifact_path,
                name_override=artifact_file_name,
                repo=kwargs.get("repo", ""),  # deprecated in 1.10.2
                storage_destination=kwargs.get("storage_destination", ""),
                branch=kwargs.get("branch", ""),
                username=kwargs.get("username", ""),
                password=kwargs.get("password", ""),
            )
            _commons.ArtifactExportJob(
                self._experiment._client,
                job_key,
                artifact_path,
                artifact_file_name,
                export_location,
            ).result()
            exported_artifacts[artifact] = str(
                Path(export_location, artifact_file_name)
            )
        return exported_artifacts

    @_model_ready
    def list(self) -> List[str]:
        """List of experiment artifacts that exist in the Driverless AI server."""
        self._update()
        return [k for k, v in self._paths.items() if v and k != "autoreport"]


class ExperimentExportJob(_commons.ServerJob):
    """Monitor the creation of experiment export binary in the Driverless AI server."""

    def __init__(self, client: "_core.Client", key: str) -> None:
        super().__init__(client=client, key=key)

    def _update(self) -> None:
        self._set_raw_info(
            self._client._backend.get_export_experiment_job(key=self.key)
        )

    def result(self, silent: bool = False) -> "ExperimentExportJob":
        """Wait for the job to complete, then return self.

        Args:
            silent: If True, do not display status updates.
        """
        self._wait(silent)
        return self

    def status(self, verbose: int = 0) -> str:
        """Return the job status string.

        Args:
            verbose:
                - 0: A short description.
                - 1: A short description with a progress percentage.
                - 2: A detailed description with a progress percentage.
        """
        status = self._status()
        if verbose == 1:
            return f"{status.message} {self._get_raw_info().progress:.2%}"
        if verbose == 2:
            if status == _enums.JobStatus.FAILED:
                message = " - " + self._get_raw_info().error
            else:
                message = ""  # no message for export jobs
            return f"{status.message} {self._get_raw_info().progress:.2%}{message}"
        return status.message


class ExperimentLog(_commons.ServerLog):
    """Interact with experiment logs."""

    def __init__(self, experiment: "Experiment") -> None:
        file_path = "h2oai_experiment_" + experiment.key + ".log"
        super().__init__(client=experiment._client, file_path=file_path)
        self._experiment = experiment

    def _error_message(self) -> str:
        self._experiment._update()
        error_message = (
            "No logs available for experiment " + self._experiment.name + "."
        )
        return error_message

    def download(
        self,
        archive: bool = True,
        dst_dir: str = ".",
        dst_file: Optional[str] = None,
        file_system: Optional["fsspec.spec.AbstractFileSystem"] = None,
        overwrite: bool = False,
        timeout: float = 30,
    ) -> str:
        """Download experiment logs from the Driverless AI server.

        Args:
            archive: If available, it is recommended
                to download an archive that contains
                multiple log files and stack traces if any were created.
            dst_dir: The path to the directory where the logs will be saved.
            dst_file: The name of the log file (overrides default file name).
            file_system: FSSPEC based file system to download to,
                instead of the local file system.
            overwrite: Overwrite the existing file.
            timeout: Connection timeout in seconds.
        """
        self._experiment._update()
        log_name = self._experiment._get_raw_info().entity.log_file_path
        if log_name == "" or not archive:
            log_name = self._file_path

        return super()._download(
            server_path=log_name,
            dst_dir=dst_dir,
            dst_file=dst_file,
            file_system=file_system,
            overwrite=overwrite,
            timeout=timeout,
        )


class Experiments:
    """Interact with experiments in the Driverless AI server."""

    def __init__(self, client: "_core.Client") -> None:
        self._client = client
        self._default_experiment_settings = {
            setting.name.strip(): setting.val
            for setting in client._backend.get_all_config_options()
        }
        # convert setting name from key to value
        self._setting_for_server_dict = {
            "drop_columns": "cols_to_drop",
            "fold_column": "fold_col",
            "reproducible": "seed",
            "scorer": "score_f_name",
            "target_column": "target_col",
            "time_column": "time_col",
            "weight_column": "weight_col",
            "unavailable_at_prediction_time_columns": (
                "unavailable_columns_at_prediction_time"
            ),
        }
        self._setting_for_api_dict = {
            v: k for k, v in self._setting_for_server_dict.items()
        }

    def _check_api_settings(self, settings: Dict[str, Any]) -> None:
        # check target column exists
        if (
            settings["task"] != "unsupervised"
            and settings["target_column"] not in settings["train_dataset"].columns
        ):
            target_column = settings["target_column"]
            raise ValueError(
                f"Target column '{target_column}' not found in training data."
            )
        # check unsupervised requirements
        if settings["task"] == "unsupervised":
            target_models = settings.get("models", None) or settings.get(
                "included_models", []
            )
            unsupervised_model_names = [
                m.name for m in self._client.recipes.models.list() if m.is_unsupervised
            ]
            # remove Model suffix
            unsupervised_model_names += [
                m[:-5] for m in unsupervised_model_names if m.lower().endswith("model")
            ]
            if len(target_models) != 1 or (
                target_models[0] not in unsupervised_model_names
                and getattr(target_models[0], "name", None)
                not in unsupervised_model_names
            ):
                raise ValueError(
                    "Unsupervised tasks require one unsupervised model to be specified."
                )
        # check params with bool type
        for key in ["enable_gpus", "reproducible"]:
            if key in settings and type(settings[key]) is not bool:
                raise ValueError(
                    f"'{key}' should be a bool, instead found {type(settings[key])}."
                )
        # if custom recipes acceptance jobs are running, wait for them to finish
        if not settings.pop("force_skip_acceptance_tests", False) and hasattr(
            self._client._backend, "_wait_for_custom_recipes_acceptance_tests"
        ):
            self._client._backend._wait_for_custom_recipes_acceptance_tests()

    def _lazy_get(self, key: str) -> "Experiment":
        """Initialize an Experiment object but do not request information from
        the server (possible for experiment key to not exist on server). Useful
        for populating lists without making a bunch of network calls.

        Args:
            key: Driverless AI server's unique ID for the experiment.
        """
        return Experiment(self._client, key)

    def _parse_api_settings(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Convert Python API experiment settings to the format required by the
        Driverless AI server.
        """
        custom_settings: Dict[str, Any] = {}

        tasks = ["classification", "regression", "unsupervised"]

        not_config_overrides = [
            "train_dataset",  # Reflects 'dataset' in backend
            "resumed_model",
            "target_column",  # Reflects 'target_col' in backend
            "weight_column",  # Reflects 'weight_col' in backend
            "fold_column",  # Reflects 'fold_col' in backend
            "orig_time_col",
            "time_column",  # Reflects 'time_col' in backend
            "is_classification",
            "drop_columns",  # Reflects 'cols_to_drop' in backend
            "validset",
            "testset",
            "enable_gpus",
            "reproducible",  # Reflects 'seed' in backend
            "accuracy",
            "time",
            "interpretability",
            "scorer",  # Reflects 'score_f_name' in backend
            "time_groups_columns",
            # Reflects 'unavailable_columns_at_prediction_time' in backend
            "unavailable_at_prediction_time_columns",
            "time_period_in_seconds",
            "num_prediction_periods",
            "num_gap_periods",
            "is_timeseries",
            "is_image",
            "custom_feature",
        ]
        for setting in [
            "config_overrides",
            "validation_dataset",
            "test_dataset",
            "parent_experiment",
        ]:
            if setting not in settings or settings[setting] is None:
                settings[setting] = ""

        def get_ref(desc: str, obj: Any) -> Tuple[str, Any]:
            ref_mapping = {
                "train_dataset": (
                    "dataset",
                    self._client._server_module.references.DatasetReference,
                ),
                "validation_dataset": (
                    "validset",
                    self._client._server_module.references.DatasetReference,
                ),
                "test_dataset": (
                    "testset",
                    self._client._server_module.references.DatasetReference,
                ),
                "parent_experiment": (
                    "resumed_model",
                    self._client._server_module.references.ModelReference,
                ),
            }
            ref_type, ref_class = ref_mapping[desc]
            key = obj if isinstance(obj, str) else obj.key
            ref = ref_class(key)
            return ref_type, ref

        included_models = []
        for m in settings.pop("models", []):
            if isinstance(m, _recipes.ModelRecipe):
                included_models.append(m.name)
            else:
                included_models.append(m)
        if len(included_models) > 0:
            settings.setdefault("included_models", [])
            settings["included_models"] += included_models

        included_transformers = []
        for t in settings.pop("transformers", []):
            if isinstance(t, _recipes.TransformerRecipe):
                included_transformers.append(t.name)
            else:
                included_transformers.append(t)
        if len(included_transformers) > 0:
            settings.setdefault("included_transformers", [])
            settings["included_transformers"] += included_transformers

        custom_settings["is_timeseries"] = False

        reserved_columns = [
            settings.get("target_column", None),
            settings.get("time_column", None),
            settings.get("weight_column", None),
            settings.get("fold_column", None),  # use for fold assignments
            *settings.get("time_groups_columns", []),
            *settings.get("unavailable_at_prediction_time_columns", []),
            *settings.get("drop_columns", []),
        ]
        image_columns = [
            col
            for col in settings["train_dataset"].column_summaries()
            if col.name not in reserved_columns and col.data_type == "image"
        ]
        custom_settings["is_image"] = bool(image_columns)

        custom_settings["enable_gpus"] = self._client._backend.get_gpu_stats().gpus > 0
        config_overrides = toml.loads(settings["config_overrides"])
        for setting, value in settings.items():
            if setting == "task":
                if value not in tasks:
                    raise ValueError("Please set the task to one of:", tasks)
                custom_settings["is_classification"] = "classification" == value
                if value == "unsupervised":
                    config_overrides["recipe"] = "unsupervised"
            elif setting in [
                "train_dataset",
                "validation_dataset",
                "test_dataset",
                "parent_experiment",
            ]:
                ref_type, ref = get_ref(setting, value)
                custom_settings[ref_type] = ref
            elif setting == "time_column":
                custom_settings[self._setting_for_server_dict[setting]] = value
                custom_settings["is_timeseries"] = value is not None
            elif setting == "scorer":
                if isinstance(value, _recipes.ScorerRecipe):
                    value = value.name
                custom_settings[self._setting_for_server_dict[setting]] = value
            elif setting == "enable_gpus":
                if custom_settings[setting]:  # confirm GPUs are present
                    custom_settings[setting] = value
            elif setting in self._setting_for_server_dict:
                custom_settings[self._setting_for_server_dict[setting]] = value
            elif setting in not_config_overrides:
                custom_settings[setting] = value
            elif setting != "config_overrides":
                if setting not in self._default_experiment_settings:
                    raise RuntimeError(
                        f"'{setting}' experiment setting not recognized."
                    )
                config_overrides[setting] = value

        # check config_overrides if seed present mark reproducible as true
        if "seed" in config_overrides and ("seed" not in custom_settings):
            custom_settings["seed"] = True
        custom_settings["config_overrides"] = toml.dumps(config_overrides)

        model_parameters = self._client._server_module.messages.ModelParameters(
            dataset=custom_settings["dataset"],
            resumed_model=custom_settings.get(
                "resumed_model", get_ref("parent_experiment", "")
            ),
            target_col=custom_settings["target_col"],
            weight_col=custom_settings.get("weight_col", None),
            fold_col=custom_settings.get("fold_col", None),
            orig_time_col=custom_settings.get(
                "orig_time_col", custom_settings.get("time_col", None)
            ),
            time_col=custom_settings.get("time_col", None),
            is_classification=custom_settings["is_classification"],
            cols_to_drop=custom_settings.get("cols_to_drop", []),
            validset=custom_settings.get("validset", get_ref("validation_dataset", "")),
            testset=custom_settings.get("testset", get_ref("test_dataset", "")),
            enable_gpus=custom_settings.get("enable_gpus", True),
            seed=custom_settings.get("seed", False),
            accuracy=None,
            time=None,
            interpretability=None,
            score_f_name=None,
            time_groups_columns=custom_settings.get("time_groups_columns", None),
            unavailable_columns_at_prediction_time=custom_settings.get(
                "unavailable_columns_at_prediction_time", []
            ),
            time_period_in_seconds=custom_settings.get("time_period_in_seconds", None),
            num_prediction_periods=custom_settings.get("num_prediction_periods", None),
            num_gap_periods=custom_settings.get("num_gap_periods", None),
            is_timeseries=custom_settings.get("is_timeseries", False),
            cols_imputation=custom_settings.get("cols_imputation", []),
            config_overrides=custom_settings.get("config_overrides", None),
            custom_features=[],
            is_image=custom_settings.get("is_image", False),
        )

        server_settings = self._client._backend.get_experiment_tuning_suggestion(
            model_params=model_parameters
        ).dump()

        server_settings.update(**custom_settings)

        return server_settings

    def _parse_server_settings(self, server_settings: Dict[str, Any]) -> Dict[str, Any]:
        """Convert Driverless AI server experiment settings to Python API format."""
        blacklist = [
            "is_classification",
            "is_timeseries",
            "is_image",
            "dataset",
            "validset",
            "testset",
            "orig_time_col",
            "resumed_model",
            "config_overrides",
        ]
        if self._client._backend.get_gpu_stats().gpus == 0:
            blacklist.append("enable_gpus")
            blacklist.append("num_gpus_per_experiment")
            blacklist.append("num_gpus_per_model")
        elif server_settings["enable_gpus"]:
            blacklist.append("enable_gpus")
        if not server_settings["seed"]:
            blacklist.append("seed")
        if not server_settings["is_timeseries"]:
            blacklist.append("time_col")

        def supervised_task(server_settings: Dict[str, Any]) -> str:
            if server_settings["is_classification"]:
                return "classification"
            else:
                return "regression"

        settings: Dict[str, Any] = {"task": supervised_task(server_settings)}
        for key, value in server_settings.items():
            if key not in blacklist and value not in [None, "", []]:
                settings[self._setting_for_api_dict.get(key, key)] = value
        settings.update(
            _utils.toml_to_api_settings(
                toml_string=server_settings["config_overrides"],
                default_api_settings=self._default_experiment_settings,
                blacklist=blacklist,
            )
        )
        if settings.get("recipe", None) == "unsupervised":
            settings["target_column"] = None
            settings["task"] = "unsupervised"
        if (
            server_settings["resumed_model"]["key"] != ""
            and server_settings["resumed_model"]["display_name"] != ""
        ):
            settings["parent_experiment"] = self.get(
                server_settings["resumed_model"]["key"]
            )
        for setting_names in [
            ("included_models", "models"),
            ("included_transformers", "transformers"),
        ]:
            if setting_names[0] in settings:
                settings[setting_names[1]] = settings.pop(setting_names[0])
                if isinstance(settings[setting_names[1]], str):
                    settings[setting_names[1]] = settings[setting_names[1]].split(",")

        return settings

    def create(
        self,
        train_dataset: "_datasets.Dataset",
        target_column: Optional[str],
        task: str,
        force: bool = False,
        name: str = None,
        description: str = None,
        **kwargs: Any,
    ) -> "Experiment":
        """Creates an experiment in the Driverless AI server.

        Args:
            train_dataset: Dataset object.
            target_column: Name of the column `train_dataset`
                (pass `None` if `task` is `'unsupervised'`).
            task: One of `'regression'`, `'classification'`, or `'unsupervised'`.
            force: Create a new experiment even if experiment with same name
              already exists.
            name: Display the name of experiment.
            description: Description of the experiment.
                (only available from Driverless AI version 2.0 onwards)

        Keyword Args:
            accuracy (int): Accuracy setting [1-10].
            time (int): Time setting [1-10].
            interpretability (int): Interpretability setting [1-10].
            scorer (Union[str,ScorerRecipe]): Metric to optimize for.
            models (Union[str,ModelRecipe]): Limit experiments to these models.
            transformers (Union[str,TransformerRecipe]): Limit experiments to
              these transformers.
            validation_dataset (Dataset): Dataset object.
            test_dataset (Dataset): Dataset object.
            weight_column (str): Name of the column in `train_dataset`.
            fold_column (str): Name of the column in `train_dataset`
            time_column (str): Name of the column in `train_dataset`,
              containing time ordering for timeseries problems
            time_groups_columns (List[str]): List of column names,
              contributing to time ordering.
            unavailable_at_prediction_time_columns (List[str]):
              List of column names, which won't be present at prediction time.
            drop_columns (List[str]): List of column names that need to be dropped.
            enable_gpus (bool): Allow the usage of GPUs in the experiment.
            reproducible (bool): Set the experiment to be reproducible.
            time_period_in_seconds (int): The length of the time period in seconds,
              used in the timeseries problems.
            num_prediction_periods (int): Timeseries forecast horizon in time
              period units.
            num_gap_periods (int): The number of time periods after which
              the forecast starts.
            config_overrides (str): Driverless AI config
                overrides in **TOML** string format.

        ??? example "Example: Create an experiment."
            ```py
            client = driverlessai.Client(address='http://localhost:12345',
            username='py', password='py')
            train_dataset = client.datasets.create(
                data="s3://h2o-public-test-data/smalldata/airlines/AirlinesTrain.csv",
                data_source="s3",
                name="Airlines-data",
                description="My airline dataset",
            )
            test_dataset = client.datasets.create(
                data="s3://h2o-public-test-data/smalldata/airlines/AirlinesTest.csv",
                data_source="s3",
                name="Airlines-data",
                description="My airline dataset",
            )
            experiment = client.experiments.create(
                dataset=train_dataset,
                target_col=train_dataset.columns[-1],
                test_dataset=test_dataset,
                task='classification',
                scorer='F1',
                accuracy=5,
                time=5,
                interpretability=5,
                name='demo_day_experiment'
            )
            ```

        !!! note
            Any expert setting can also be passed as a `kwarg`.
            To search possible expert settings for your server version,
            use `experiments.search_expert_settings(search_term)`.
        """
        return self.create_async(
            train_dataset, target_column, task, force, name, description, **kwargs
        ).result()

    def create_async(
        self,
        train_dataset: "_datasets.Dataset",
        target_column: Optional[str],
        task: str,
        force: bool = False,
        name: str = None,
        description: Optional[str] = None,
        **kwargs: Any,
    ) -> "Experiment":
        """Launches the creation of an experiment in the Driverless AI server and
        returns an experiment object to track the experiment status.

        Args:
            train_dataset: Dataset object.
            target_column: The name of column in `train_dataset`
                (pass `None` if `task` is `'unsupervised'`).
            task: One of `'regression'`, `'classification'`, or `'unsupervised'`.
            force: Create a new experiment even if experiment with same name
              already exists.
            name: The display name for the experiment.
            description: Description of the experiment.
                (only available from Driverless AI version 2.0 onwards)

        Keyword Args:
            accuracy (int): Accuracy setting [1-10].
            time (int): Time setting [1-10].
            interpretability (int): Interpretability setting [1-10].
            scorer (Union[str,ScorerRecipe]): Metric to optimize for.
            models (Union[str,ModelRecipe]): Limit experiments to these models.
            transformers (Union[str,TransformerRecipe]): Limit experiments to
              these transformers.
            validation_dataset (Dataset): Dataset object.
            test_dataset (Dataset): Dataset object.
            weight_column (str): Name of the column in `train_dataset`.
            fold_column (str): Name of the column in `train_dataset`
            time_column (str): Name of the column in `train_dataset`,
              containing time ordering for timeseries problems
            time_groups_columns (List[str]): List of column names,
              contributing to time ordering.
            unavailable_at_prediction_time_columns (List[str]):
              List of column names, which won't be present at prediction time.
            drop_columns (List[str]): List of column names that need to be dropped.
            enable_gpus (bool): Allow the usage of GPUs in the experiment.
            reproducible (bool): Set the experiment to be reproducible.
            time_period_in_seconds (int): The length of the time period in seconds,
              used in the timeseries problems.
            num_prediction_periods (int): Timeseries forecast horizon in time
              period units.
            num_gap_periods (int): The number of time periods after which
              the forecast starts.
            config_overrides (str): Driverless AI config
                overrides in **TOML** string format.

        ??? example "Example: Create an async experiment."
            ```py
            client = driverlessai.Client(address='http://localhost:12345',
            username='py', password='py')
            train_dataset = client.datasets.create(
                data="s3://h2o-public-test-data/smalldata/airlines/AirlinesTrain.csv",
                data_source="s3",
                name="Airlines-data",
                description="My airline dataset",
            )
            test_dataset = client.datasets.create(
                data="s3://h2o-public-test-data/smalldata/airlines/AirlinesTest.csv",
                data_source="s3",
                name="Airlines-data",
                description="My airline dataset",
            )
            experiment = client.experiments.create_async(
                dataset=train_dataset,
                target_col=train_dataset.columns[-1],
                test_dataset=test_dataset,
                task='classification',
                scorer='F1',
                accuracy=5,
                time=5,
                interpretability=5,
                name='demo_day_experiment'
            )
            ```

        !!! note
            Any expert setting can also be passed as a `kwarg`.
            To search possible expert settings for your server version,
            use `experiments.search_expert_settings(search_term)`.
        """
        if not force:
            _utils.error_if_experiment_exists(self._client, name)
        kwargs["task"] = task
        kwargs["train_dataset"] = train_dataset
        kwargs["target_column"] = target_column
        self._check_api_settings(kwargs)
        server_settings = self._parse_api_settings(kwargs)

        if description and self._client.server.version < "2.0":
            raise _exceptions.NotSupportedByServer(
                "'description' parameter requires Driverless AI server"
                " version 2.0 or higher."
            )

        job_key = self._client._backend.start_experiment(
            req=self._client._server_module.messages.ModelParameters(**server_settings),
            experiment_name=name,
        )
        job = self.get(job_key)
        _logging.logger.info(f"Experiment launched at: {job.gui()}")
        return job

    def get(self, key: str) -> "Experiment":
        """Returns an Experiment object corresponding to an experiment on the
        Driverless AI server. If the experiment only exists on H2O.ai Storage,
        it will be imported to the server first.

        Args:
            key: Driverless AI server's unique ID for the experiment.
        """
        if self._client.server.storage_enabled:
            try:
                storage_key = self._client._backend.import_storage_model(model_id=key)
                if storage_key:
                    _logging.logger.info("Importing experiment from storage...")
                    _commons.StorageImportJob(self._client, storage_key).result()
            except self._client._server_module.protocol.RemoteError as e:
                if not _utils.is_key_error(e):
                    raise
        experiment = self._lazy_get(key)
        experiment._update()
        return experiment

    def gui(self) -> _utils.Hyperlink:
        """
        Returns the complete URL to the experiment
        details page in the Driverless AI server.
        """
        return _utils.Hyperlink(
            f"{self._client.server.address}{self._client._gui_sep}experiments"
        )

    def import_dai_file(
        self, path: str, file_system: Optional["fsspec.spec.AbstractFileSystem"] = None
    ) -> "Experiment":
        """
        Imports a DAI file to the Driverless AI server and return a
        corresponding Experiment object.

        Args:
           path: Path to the `.dai` file.
           file_system: The FSSPEC based file system to download from,
            instead of the local file system.
        """
        if self._client.server.version < "1.10.7":
            if file_system:
                raise ValueError(
                    "'fsspec.spec.AbstractFileSystem' support required"
                    "Driverless AI server version 1.10.7 or higher."
                )
            return self.get(
                self._client._backend.import_experiment_sync(file_path=path)
            )
        return self.get(
            self._client._backend.import_experiment_sync(
                file_path=path, file_system=file_system
            )
        )

    def leaderboard(
        self,
        train_dataset: "_datasets.Dataset",
        target_column: Optional[str],
        task: str,
        force: bool = False,
        name: str = None,
        **kwargs: Any,
    ) -> "_projects.Project":
        """Launches an experiment leaderboard in the Driverless AI server and
        return a project object to track experiment statuses.

        Args:
            train_dataset: Dataset object.
            target_column: The name of column in `train_dataset`
             (pass `None` if `task` is `'unsupervised'`).
            task: One of `'regression'`, `'classification'`, or `'unsupervised'`.
            force: Create a new project even if a
                project with the same name already exists.
            name: The display name for the project.

        Keyword Args:
            accuracy (int): Accuracy setting [1-10].
            time (int): Time setting [1-10].
            interpretability (int): Interpretability setting [1-10].
            scorer (Union[str,ScorerRecipe]): Metric to optimize for.
            models (Union[str,ModelRecipe]): Limit experiments to these models.
            transformers (Union[str,TransformerRecipe]): Limit experiments to
              these transformers.
            validation_dataset (Dataset): Dataset object.
            test_dataset (Dataset): Dataset object.
            weight_column (str): Name of the column in `train_dataset`.
            fold_column (str): Name of the column in `train_dataset`
            time_column (str): Name of the column in `train_dataset`,
              containing time ordering for timeseries problems
            time_groups_columns (List[str]): List of column names,
              contributing to time ordering.
            unavailable_at_prediction_time_columns (List[str]):
              List of column names, which won't be present at prediction time.
            drop_columns (List[str]): List of column names that need to be dropped.
            enable_gpus (bool): Allow the usage of GPUs in the experiment.
            reproducible (bool): Set the experiment to be reproducible.
            time_period_in_seconds (int): The length of the time period in seconds,
              used in the timeseries problems.
            num_prediction_periods (int): Timeseries forecast horizon in time
              period units.
            num_gap_periods (int): The number of time periods after which
              the forecast starts.
            config_overrides (str): Driverless AI config
                overrides in **TOML** string format.

        Returns:
            A project object to track experiment statuses.

        !!! note

            Any expert setting can also be passed as a `kwarg`.
            To search possible expert settings for your server version,
            use `experiments.search_expert_settings(search_term)`.
        """
        if not force:
            _utils.error_if_project_exists(self._client, name)
        kwargs["task"] = task
        kwargs["train_dataset"] = train_dataset
        kwargs["target_column"] = target_column
        self._check_api_settings(kwargs)
        server_settings = self._parse_api_settings(kwargs)
        project_key = self._client._backend.start_experiment_leaderboard(
            req=self._client._server_module.messages.ModelParameters(**server_settings),
            leaderboard_name=name,
        )
        project = self._client.projects.get(project_key)
        if name:
            project.rename(name)
        _logging.logger.info(f"Leaderboard launched at: {project.gui()}")
        return project

    def list(self, start_index: int = 0, count: int = None) -> Sequence["Experiment"]:
        """List of Experiment objects available to the user.

        Args:
            start_index: The index number on the
                Driverless AI server of the first experiment in the list.
            count: The number of experiments to request from the Driverless AI server.

        Returns:
            Experiments.
        """
        if count:
            data = self._client._backend.list_models(
                offset=start_index, limit=count
            ).models
        else:
            page_size = 100
            page_position = start_index
            data = []
            while True:
                page = self._client._backend.list_models(
                    offset=page_position, limit=page_size
                ).models
                data += page
                if len(page) < page_size:
                    break
                page_position += page_size
        return _commons.ServerObjectList(
            data=data, get_method=self._lazy_get, item_class_name=Experiment.__name__
        )

    @_utils.beta
    def get_by_name(self, name: str) -> Optional["Experiment"]:
        """Get the experiment specified by the name.

        Args:
            name: Name of the experiment.

        Returns:
            The experiment with the name if exists, otherwise `None`.

        """
        sort_query = self._client._server_module.messages.EntitySortQuery("", "", "")
        template = f'"description": "{name}"'
        data = self._client._backend.search_and_sort_models(
            search_query=template,
            sort_query=sort_query,
            ascending=False,
            offset=0,
            limit=1,
        ).models
        if data:
            return Experiment(self._client, data[0].key)
        else:
            return None

    def preview(
        self,
        train_dataset: "_datasets.Dataset",
        target_column: Optional[str],
        task: str,
        force: Optional[bool] = None,
        name: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Prints a preview of experiment for the given settings.

        Args:
            train_dataset: Dataset object.
            target_column: The name of column in `train_dataset`
                (pass `None` if `task` is `'unsupervised'`).
            task: One of `'regression'`, `'classification'`, or `'unsupervised'`.
            force: Ignored (`preview` accepts the same arguments as `create`).
            name: Ignored (`preview` accepts the same arguments as `create`).

        Keyword Args:
            accuracy (int): Accuracy setting [1-10].
            time (int): Time setting [1-10].
            interpretability (int): Interpretability setting [1-10].
            scorer (Union[str,ScorerRecipe]): Metric to optimize for.
            models (Union[str,ModelRecipe]): Limit experiments to these models.
            transformers (Union[str,TransformerRecipe]): Limit experiments to
              these transformers.
            validation_dataset (Dataset): Dataset object.
            test_dataset (Dataset): Dataset object.
            weight_column (str): Name of the column in `train_dataset`.
            fold_column (str): Name of the column in `train_dataset`
            time_column (str): Name of the column in `train_dataset`,
              containing time ordering for timeseries problems
            time_groups_columns (List[str]): List of column names,
              contributing to time ordering.
            unavailable_at_prediction_time_columns (List[str]):
              List of column names, which won't be present at prediction time.
            drop_columns (List[str]): List of column names that need to be dropped.
            enable_gpus (bool): Allow the usage of GPUs in the experiment.
            reproducible (bool): Set the experiment to be reproducible.
            time_period_in_seconds (int): The length of the time period in seconds,
              used in the timeseries problems.
            num_prediction_periods (int): Timeseries forecast horizon in time
              period units.
            num_gap_periods (int): The number of time periods after which
              the forecast starts.
            config_overrides (str): Driverless AI config
                overrides in **TOML** string format.

        !!! note
            Any expert setting can also be passed as a `kwarg`.
            To search possible expert settings for your server version,
            use `experiments.search_expert_settings(search_term)`.
        """
        kwargs["task"] = task
        kwargs["train_dataset"] = train_dataset
        kwargs["target_column"] = target_column
        for arg in ["force", "name"]:
            # arg is accepted by create but not needed for preview
            kwargs.pop(arg, None)
        self._check_api_settings(kwargs)
        settings = self._parse_api_settings(kwargs)

        model_parameters = self._client._server_module.messages.ModelParameters(
            **settings
        )

        if self._client.server.version < "1.10.5":
            key = self._client._backend.get_experiment_preview(
                model_params=model_parameters
            )
        else:
            # if user manually set enable_gpu set force_gpu to true
            force_gpu = "enable_gpus" in kwargs.keys()
            key = self._client._backend.get_experiment_preview(
                model_params=model_parameters, force_gpu=force_gpu
            )

        while _commons.is_server_job_running(
            self._client._backend.get_experiment_preview_job(key=key).status
        ):
            time.sleep(1)
        preview = self._client._backend.get_experiment_preview_job(key=key).entity.lines
        _logging.logger.info("\n" + "\n".join(preview))

    def search_expert_settings(
        self, search_term: str, show_description: bool = False
    ) -> None:
        """Search expert settings and print results. Useful when looking for
        `kwargs` to use when creating experiments.

        Args:
            search_term: Term to search for (case-insensitive).
            show_description: Include description in results.
        """
        for c in self._client._backend.get_all_config_options():
            if (
                search_term.lower()
                in " ".join([c.name, c.category, c.description, c.comment]).lower()
            ):
                print(
                    self._setting_for_api_dict.get(c.name, c.name),
                    "|",
                    "default_value:",
                    self._default_experiment_settings[c.name.strip()],
                    end="",
                )
                if show_description:
                    description = c.description.strip()
                    comment = " ".join(
                        [s.strip() for s in c.comment.split("\n")]
                    ).strip()
                    print(" |", description)
                    print(" ", comment)
                print()


class FitAndTransformation:
    """Interact with fit and transformed data from the Driverless AI server."""

    def __init__(
        self, client: "_core.Client", transformation_job: "FitAndTransformationJob"
    ):
        self._client = client
        self._transformation_data = transformation_job._get_raw_info().entity

    @property
    def fold_column(self) -> str:
        """Column that creates the stratified validation split."""
        return self._transformation_data.fold_column

    @property
    def seed(self) -> int:
        """Random seed that used to start a random generator."""
        return self._transformation_data.seed

    @property
    def test_dataset(self) -> Optional[_datasets.Dataset]:
        """Test dataset used for this transformation."""
        dataset_key = self._transformation_data.test_dataset_key
        return self._client.datasets.get(dataset_key) if dataset_key else None

    @property
    def training_dataset(self) -> _datasets.Dataset:
        """Training dataset used for this transformation."""
        return self._client.datasets.get(self._transformation_data.training_dataset_key)

    @property
    def validation_dataset(self) -> Optional[_datasets.Dataset]:
        """Validation dataset used for this transformation."""
        dataset_key = self._transformation_data.validation_dataset_key
        return self._client.datasets.get(dataset_key) if dataset_key else None

    @property
    def validation_split_fraction(self) -> float:
        """Fraction of data used for validation."""
        return self._transformation_data.validation_split_fraction

    def download_transformed_test_dataset(
        self,
        dst_dir: str = ".",
        dst_file: Optional[str] = None,
        file_system: Optional["fsspec.spec.AbstractFileSystem"] = None,
        overwrite: bool = False,
        timeout: float = 30,
    ) -> str:
        """Download fit and transformed test dataset in CSV format.

        Args:
            dst_dir: The path to the directory where the CSV file will be saved.
            dst_file: The name of the CSV file (overrides default file name).
            file_system: FSSPEC based file system to download to,
                instead of local file system.
            overwrite: Overwrite the existing file.
            timeout: Connection timeout in seconds.
        """
        transformed_test_dataset_path = self._transformation_data.test_output_csv_path
        if not transformed_test_dataset_path:
            raise _exceptions.InvalidOperationException(
                "This transformation does not contain a transformed test dataset."
            )
        return self._client._download(
            server_path=transformed_test_dataset_path,
            dst_dir=dst_dir,
            dst_file=dst_file,
            file_system=file_system,
            overwrite=overwrite,
            timeout=timeout,
        )

    def download_transformed_training_dataset(
        self,
        dst_dir: str = ".",
        dst_file: Optional[str] = None,
        file_system: Optional["fsspec.spec.AbstractFileSystem"] = None,
        overwrite: bool = False,
        timeout: float = 30,
    ) -> str:
        """Download fit and transformed training dataset in CSV format.

        Args:
            dst_dir: The path to the directory where the CSV file will be saved.
            dst_file: The name of the CSV file (overrides default file name).
            file_system: FSSPEC based file system to download to,
                instead of local file system.
            overwrite: Overwrite the existing file.
            timeout: Connection timeout in seconds.
        """
        return self._client._download(
            server_path=self._transformation_data.training_output_csv_path,
            dst_dir=dst_dir,
            dst_file=dst_file,
            file_system=file_system,
            overwrite=overwrite,
            timeout=timeout,
        )

    def download_transformed_validation_dataset(
        self,
        dst_dir: str = ".",
        dst_file: Optional[str] = None,
        file_system: Optional["fsspec.spec.AbstractFileSystem"] = None,
        overwrite: bool = False,
        timeout: float = 30,
    ) -> str:
        """Download fit and transformed validation dataset in CSV format.

        Args:
            dst_dir: The path to the directory where the CSV file will be saved.
            dst_file: The name of the CSV file (overrides default file name).
            file_system: FSSPEC based file system to download to,
                instead of local file system.
            overwrite: Overwrite the existing file.
            timeout: Connection timeout in seconds.
        """
        transformed_validation_dataset_path = (
            self._transformation_data.validation_output_csv_path
        )
        if not transformed_validation_dataset_path:
            raise _exceptions.InvalidOperationException(
                "This transformation does not contain a transformed validation dataset."
            )
        return self._client._download(
            server_path=self._transformation_data.validation_output_csv_path,
            dst_dir=dst_dir,
            dst_file=dst_file,
            file_system=file_system,
            overwrite=overwrite,
            timeout=timeout,
        )


class FitAndTransformationJob(_commons.ServerJob):
    def __int__(
        self,
        client: "_core.Client",
        transformation_job_key: str,
    ) -> None:
        super().__init__(client=client, key=transformation_job_key)

    def _update(self) -> None:
        self._set_raw_info(self._client._backend.get_transformation_job(key=self.key))

    def result(self, silent: bool = False) -> "FitAndTransformation":
        """Wait for the job to complete, then return self.

        Args:
        silent: If True, do not display status updates.
        """
        status_update = _utils.StatusUpdate()
        if not silent:
            status_update.display(_enums.JobStatus.RUNNING.message)
        self._wait(silent)
        if not silent:
            status_update.display(_enums.JobStatus.COMPLETE.message)
        status_update.end()
        return FitAndTransformation(client=self._client, transformation_job=self)


class Prediction:
    """Interact with predictions from the Driverless AI server."""

    def __init__(
        self,
        prediction_jobs: List["PredictionJob"],
        included_dataset_columns: Optional[List[str]] = None,
        includes_labels: Optional[bool] = None,
        includes_raw_outputs: Optional[bool] = None,
        includes_shap_values_for_original_features: Optional[bool] = None,
        includes_shap_values_for_transformed_features: Optional[bool] = None,
        used_fast_approx_for_shap_values: Optional[bool] = None,
    ) -> None:
        self._client = prediction_jobs[0]._client
        self._file_paths = [
            job._get_raw_info().entity.predictions_csv_path for job in prediction_jobs
        ]
        self._included_dataset_columns = included_dataset_columns
        self._includes_labels = includes_labels
        self._includes_raw_outputs = includes_raw_outputs
        self._includes_shap_values_for_original_features = (
            includes_shap_values_for_original_features
        )
        self._includes_shap_values_for_transformed_features = (
            includes_shap_values_for_transformed_features
        )
        self._keys = prediction_jobs[0].keys
        self._used_fast_approx_for_shap_values = used_fast_approx_for_shap_values

    @property
    def file_paths(self) -> List[str]:
        """Paths to the prediction CSV files on the server."""
        return self._file_paths

    @property
    def included_dataset_columns(self) -> List[str]:
        """Columns from the dataset that are appended to predictions."""
        return self._included_dataset_columns

    @property
    def includes_labels(self) -> bool:
        """Determines whether classification labels are appended to predictions."""
        return self._includes_labels

    @property
    def includes_raw_outputs(self) -> bool:
        """Determines whether predictions as margins (in link space) were appended to
        predictions.
        """
        return self._includes_raw_outputs

    @property
    def includes_shap_values_for_original_features(self) -> bool:
        """Determines whether original feature
        contributions are appended to predictions."""
        return self._includes_shap_values_for_original_features

    @property
    def includes_shap_values_for_transformed_features(self) -> bool:
        """Determines whether transformed feature
        contributions are appended to predictions."""
        return self._includes_shap_values_for_transformed_features

    @property
    def keys(self) -> Dict[str, str]:
        """Dictionary of unique IDs for entities related to the prediction:

        dataset: The unique ID of the dataset used to make predictions.
        experiment: The unique ID of the experiment used to make predictions.
        prediction: The unique ID of the predictions.
        """
        return self._keys

    @property
    def used_fast_approx_for_shap_values(self) -> Optional[bool]:
        """Whether approximation was used to calculate prediction contributions."""
        return self._used_fast_approx_for_shap_values

    def download(
        self,
        dst_dir: str = ".",
        dst_file: Optional[str] = None,
        file_system: Optional["fsspec.spec.AbstractFileSystem"] = None,
        overwrite: bool = False,
        timeout: float = 30,
    ) -> str:
        """Downloads the predictions of the experiment in CSV format.

        Args:
            dst_dir: The path to the directory where the CSV file will be saved.
            dst_file: The name of the CSV file (overrides default file name).
            file_system: FSSPEC based file system to download to,
                instead of local file system.
            overwrite: Overwrite the existing file.
            timeout: Connection timeout in seconds.
        """
        if len(self.file_paths) == 1:
            return self._client._download(
                server_path=self.file_paths[0],
                dst_dir=dst_dir,
                dst_file=dst_file,
                file_system=file_system,
                overwrite=overwrite,
                timeout=timeout,
            )

        if not dst_file:
            dst_file = Path(self.file_paths[0]).name
        dst_path = str(Path(dst_dir, dst_file))

        # concatenate csvs horizontally
        def write_csv(f: IO) -> None:
            csv_writer = csv.writer(f)
            # read in multiple csvs
            texts = [self._client._get_file(p).content for p in self.file_paths]
            csvs = [csv.reader(io.StringIO(t.decode())) for t in texts]
            # unpack and join
            for row_from_each_csv in zip(*csvs):
                row_joined: List[str] = sum(row_from_each_csv, [])
                csv_writer.writerow(row_joined)

        try:
            if file_system is None:
                if overwrite:
                    mode = "w"
                else:
                    mode = "x"
                with open(dst_path, mode) as f:
                    write_csv(f)
                _logging.logger.info(f"Downloaded '{dst_path}'")
            else:
                if not overwrite and file_system.exists(dst_path):
                    raise FileExistsError(f"File exists: {dst_path}")
                with file_system.open(dst_path, "w") as f:
                    write_csv(f)
                _logging.logger.info(f"Downloaded '{dst_path}' to {file_system}")
        except FileExistsError:
            _logging.logger.error(
                f"{dst_path} already exists. Use `overwrite` to force download."
            )
            raise

        return dst_path

    def to_pandas(self) -> "pandas.DataFrame":
        """Transfers the predictions to a local Pandas DataFrame."""
        import pandas as pd

        # read in multiple csvs
        contents = [self._client._get_file(p).content for p in self.file_paths]
        csvs = [csv.reader(io.StringIO(c.decode())) for c in contents]
        # unpack and join
        rows = []
        for row_from_each_csv in zip(*csvs):
            row_joined: List[str] = sum(row_from_each_csv, [])
            rows.append(row_joined)
        df = pd.DataFrame(columns=rows[0], data=rows[1:])
        df = df.apply(pd.to_numeric, errors="ignore")
        return df


class PredictionJob(_commons.ServerJob):
    """Monitor the creation of predictions in the Driverless AI server."""

    def __init__(
        self, client: "_core.Client", key: str, dataset_key: str, experiment_key: str
    ) -> None:
        super().__init__(client=client, key=key)
        self._keys = {
            "dataset": dataset_key,
            "experiment": experiment_key,
            "prediction": key,
        }

    @property
    def keys(self) -> Dict[str, str]:
        """Dictionary of the entity unique IDs:

        Args:
            Dataset: The unique ID of dataset used to make predictions.
            Experiment: The unique ID of experiments used to make predictions.
            Prediction: The unique ID of predictions.
        """
        return self._keys

    def _update(self) -> None:
        self._set_raw_info(self._client._backend.get_prediction_job(key=self.key))

    def result(self, silent: bool = False) -> "PredictionJob":
        """Waits for the job to complete, then returns self.

        Args:
            silent: If True, do not display status updates.
        """
        self._wait(silent)
        return self

    def status(self, verbose: int = None) -> str:
        """Returns a short job status description string."""
        return self._status().message


class PredictionJobs(_commons.ServerJobs):
    """Monitor the creation of predictions in the Driverless AI server."""

    def __init__(
        self,
        client: "_core.Client",
        jobs: List[PredictionJob],
        dataset_key: str,
        experiment_key: str,
        include_columns: List[str],
        include_labels: Optional[bool],
        include_raw_outputs: Optional[bool],
        include_shap_values_for_original_features: Optional[bool],
        include_shap_values_for_transformed_features: Optional[bool],
        use_fast_approx_for_shap_values: Optional[bool],
    ) -> None:
        super().__init__(client=client, jobs=jobs)
        self._included_dataset_columns = include_columns
        self._includes_labels = include_labels
        self._includes_raw_outputs = include_raw_outputs
        self._includes_shap_values_for_original_features = (
            include_shap_values_for_original_features
        )
        self._includes_shap_values_for_transformed_features = (
            include_shap_values_for_transformed_features
        )
        self._keys = {
            "dataset": dataset_key,
            "experiment": experiment_key,
            "prediction": jobs[0].key,
        }
        self._used_fast_approx_for_shap_values = use_fast_approx_for_shap_values

    @property
    def included_dataset_columns(self) -> List[str]:
        """Columns from the dataset that are appended to predictions."""
        return self._included_dataset_columns

    @property
    def includes_labels(self) -> bool:
        """Determines whether classification labels are appended to predictions."""
        if self._includes_labels is None:
            return False
        return self._includes_labels

    @property
    def includes_raw_outputs(self) -> bool:
        """Whether predictions as margins (in link space) are appended to
        predictions.
        """
        if self._includes_raw_outputs is None:
            return False
        return self._includes_raw_outputs

    @property
    def includes_shap_values_for_original_features(self) -> bool:
        """Whether original feature contributions are appended to predictions."""
        if self._includes_shap_values_for_original_features is None:
            return False
        return self._includes_shap_values_for_original_features

    @property
    def includes_shap_values_for_transformed_features(self) -> bool:
        """Whether transformed feature contributions are appended to predictions."""
        if self._includes_shap_values_for_transformed_features is None:
            return False
        return self._includes_shap_values_for_transformed_features

    @property
    def keys(self) -> Dict[str, str]:
        """Dictionary of the entity unique IDs:

        Args:
            Dataset: The unique ID of dataset used to make predictions.
            Experiment: The unique ID of experiments used to make predictions.
            Prediction: The unique ID of predictions.
        """
        return self._keys

    @property
    def used_fast_approx_for_shap_values(self) -> Optional[bool]:
        """Whether approximation was used to calculate prediction contributions."""
        return self._used_fast_approx_for_shap_values

    def result(self, silent: bool = False) -> Prediction:
        """Waits for the job to complete.

        Args:
            silent: If True, do not display status updates.

        Returns:
            The Prediction job results.
        """
        status_update = _utils.StatusUpdate()
        if not silent:
            status_update.display(_enums.JobStatus.RUNNING.message)
        jobs = [job.result(silent=True) for job in self.jobs]
        if not silent:
            status_update.display(_enums.JobStatus.COMPLETE.message)
        status_update.end()
        return Prediction(
            prediction_jobs=jobs,
            included_dataset_columns=self.included_dataset_columns,
            includes_labels=self.includes_labels,
            includes_raw_outputs=self.includes_raw_outputs,
            includes_shap_values_for_original_features=(
                self.includes_shap_values_for_original_features
            ),
            includes_shap_values_for_transformed_features=(
                self.includes_shap_values_for_transformed_features
            ),
            used_fast_approx_for_shap_values=self.used_fast_approx_for_shap_values,
        )


class PreviousPrediction(Prediction):
    """Interact with previous predictions of an experiment
    from the Driverless AI server."""

    def __init__(self, prediction_jobs: List["PredictionJob"]) -> None:
        super().__init__(prediction_jobs)


class Transformation:
    """Interact with transformed data from the Driverless AI server."""

    def __init__(
        self,
        client: "_core.Client",
        transformation_job: "TransformationJob",
        included_dataset_columns: List[str],
        includes_labels: bool,
    ) -> None:
        self._client = client
        self._file_path = transformation_job._get_raw_info().entity.predictions_csv_path
        self._included_dataset_columns = included_dataset_columns
        self._includes_labels = includes_labels
        self._keys = transformation_job.keys

    @property
    def file_path(self) -> str:
        """Paths to the transformed CSV files on the server."""
        return self._file_path

    @property
    def included_dataset_columns(self) -> List[str]:
        """Columns from the dataset that are appended to transformed data."""
        return self._included_dataset_columns

    @property
    def includes_labels(self) -> bool:
        """Determines whether classification labels are appended to transformed data."""
        return self._includes_labels

    @property
    def keys(self) -> Dict[str, str]:
        """Dictionary of unique IDs for entities related to the transformed data:

        dataset: The unique ID of the dataset used to make predictions.
        experiment: The unique ID of the experiment used to make predictions.
        prediction: The unique ID of the predictions.
        """
        return self._keys

    def download(
        self,
        dst_dir: str = ".",
        dst_file: Optional[str] = None,
        file_system: Optional["fsspec.spec.AbstractFileSystem"] = None,
        overwrite: bool = False,
        timeout: float = 30,
    ) -> str:
        """Downloads a CSV of transformed data.

        Args:
            dst_dir: The path to the directory where the CSV file will be saved.
            dst_file: The name of the CSV file (overrides default file name).
            file_system: FSSPEC based file system to download to,
                instead of local file system.
            overwrite: Overwrite the existing file.
            timeout: Connection timeout in seconds.
        """
        return self._client._download(
            server_path=self.file_path,
            dst_dir=dst_dir,
            dst_file=dst_file,
            file_system=file_system,
            overwrite=overwrite,
            timeout=timeout,
        )

    def to_pandas(self) -> "pandas.DataFrame":
        """Transfers the transformed data to a local Pandas DataFrame."""
        import pandas as pd

        # read in multiple csvs
        content = self._client._get_file(self.file_path).content
        df = pd.read_csv(io.StringIO(content.decode()))
        df = df.apply(pd.to_numeric, errors="ignore")
        return df


class TransformationJob(_commons.ServerJob):
    """Monitor the creation of data transformation in the Driverless AI server."""

    def __init__(
        self,
        client: "_core.Client",
        key: str,
        dataset_key: str,
        experiment_key: str,
        include_columns: List[str],
        include_labels: Optional[bool],
    ) -> None:
        super().__init__(client=client, key=key)
        self._included_dataset_columns = include_columns
        self._includes_labels = include_labels
        self._keys = {
            "dataset": dataset_key,
            "experiment": experiment_key,
            "transformed_data": key,
        }

    @property
    def included_dataset_columns(self) -> List[str]:
        """Columns from the dataset that are appended to transformed data."""
        return self._included_dataset_columns

    @property
    def includes_labels(self) -> bool:
        """Determines whether classification labels are appended to transformed data."""
        if self._includes_labels is None:
            return False
        return self._includes_labels

    @property
    def keys(self) -> Dict[str, str]:
        """Dictionary of the entity unique IDs:

        Args:
            Dataset: The unique ID of dataset used to make predictions.
            Experiment: The unique ID of experiments used to make predictions.
            Prediction: The unique ID of predictions.
        """
        return self._keys

    def _update(self) -> None:
        self._set_raw_info(self._client._backend.get_prediction_job(key=self.key))

    def result(self, silent: bool = False) -> "Transformation":
        """Waits for the job to complete, then returns self.

        Args:
            silent: If True, do not display status updates.
        """
        status_update = _utils.StatusUpdate()
        if not silent:
            status_update.display(_enums.JobStatus.RUNNING.message)
        self._wait(silent)
        if not silent:
            status_update.display(_enums.JobStatus.COMPLETE.message)
        status_update.end()
        return Transformation(
            client=self._client,
            transformation_job=self,
            included_dataset_columns=self.included_dataset_columns,
            includes_labels=self.includes_labels,
        )

    def status(self, verbose: int = None) -> str:
        """Returns short job status description string."""
        return self._status().message


class TritonModelArtifact:
    """Interact with a Triton model artifact in the Driverless AI server."""

    def __init__(self, client: "_core.Client", path_in_server: str):
        self._client = client
        self._path_in_server = path_in_server

    def download(
        self,
        dst_dir: str = ".",
        dst_file: Optional[str] = None,
        file_system: Optional["fsspec.spec.AbstractFileSystem"] = None,
        overwrite: bool = False,
        timeout: float = 30,
    ) -> str:
        """Download this Triton model as a zip.

        Args:
            dst_dir: The path to the directory where the CSV file will be saved.
            dst_file: The name of the CSV file (overrides the default file name).
            file_system: FSSPEC based file system to download to,
                instead of local file system.
            overwrite: Overwrite the existing file.
            timeout: Connection timeout in seconds.
        Returns: Downloaded path.
        """
        return self._client._download(
            server_path=self._path_in_server,
            dst_dir=dst_dir,
            dst_file=dst_file,
            file_system=file_system,
            overwrite=overwrite,
            timeout=timeout,
        )
