"""Datasets module."""

import ast
import dataclasses
import os
import re
import tempfile
import time
from pathlib import Path
from typing import Any
from typing import Dict
from typing import Iterable
from typing import List
from typing import Optional
from typing import Sequence
from typing import Tuple
from typing import TYPE_CHECKING
from typing import Union

from driverlessai import _commons
from driverlessai import _core
from driverlessai import _enums
from driverlessai import _experiments
from driverlessai import _logging
from driverlessai import _recipes
from driverlessai import _utils

if TYPE_CHECKING:
    import fsspec  # noqa F401
    import pandas  # noqa F401


class Connectors:
    """Interact with data sources that are enabled in the Driverless AI server."""

    def __init__(self, client: "_core.Client") -> None:
        self._client = client

    def list(self) -> List[str]:
        """
        Returns data sources enabled in the Driverless AI server.

        Returns:
            Names of enabled data sources.

        ??? Example "Example: Check whether the AWS S3 connector is enabled"
            ```py
            enabled_connectors = client.connectors.list()
            if "s3" in enabled_connectors:
                print("AWS S3 connector is enabled")
            ```
        """
        return self._client._backend.list_allowed_file_systems(offset=0, limit=None)


class DataPreviewJob(_commons.ServerJob):
    """Monitor generation of a data preview in the Driverless AI server."""

    def __init__(self, client: "_core.Client", key: str) -> None:
        super().__init__(client=client, key=key)

    def _update(self) -> None:
        self._set_raw_info(self._client._backend.get_data_preview_job(key=self.key))

    def result(self, silent: bool = False) -> "DataPreviewJob":
        """Awaits the completion of the job.

        Args:
            silent: Whether to display status updates or not.

        Returns:
            This job.
        """
        self._wait(silent)
        return self

    def status(self, verbose: int = None) -> str:
        """
        Returns the status of the job.

        Args:
            verbose: Ignored.

        Returns:
            Current status of the job.
        """
        return self._status().message


class Dataset(_commons.ServerObject):
    """A dataset in the Driverless AI server."""

    def __init__(self, client: "_core.Client", info: Any) -> None:
        super().__init__(client=client, key=info.entity.key)
        self._columns = [c.name for c in info.entity.columns]
        self._logical_types = {
            "categorical": "cat",
            "date": "date",
            "datetime": "datetime",
            "image": "image",
            "id": "id",
            "numerical": "num",
            "text": "text",
        }
        self._shape = (info.entity.row_count, len(info.entity.columns))
        self._set_name(info.entity.name)
        self._set_raw_info(info)
        self._key = info.entity.key
        self._log: Optional[DatasetLog] = None

    @property
    def columns(self) -> List[str]:
        """Column names of the dataset."""
        return self._columns

    @property
    def creation_timestamp(self) -> float:
        """
        Creation timestamp of the dataset in seconds since the epoch (POSIX timestamp).
        """
        return self._get_raw_info().created

    @property
    def data_source(self) -> str:
        """Original data source of the dataset."""
        return self._get_raw_info().entity.data_source

    @property
    def description(self) -> Optional[str]:
        """Description of the dataset."""
        return getattr(self._get_raw_info().entity, "notes", None)

    @property
    def file_path(self) -> str:
        """Path to the dataset bin file in the Driverless AI server."""
        return self._get_raw_info().entity.bin_file_path

    @property
    def file_size(self) -> int:
        """Size in bytes of the dataset bin file in the Driverless AI server."""
        return self._get_raw_info().entity.file_size

    @property
    def shape(self) -> Tuple[int, int]:
        """Dimensions of the dataset in (rows, cols) format."""
        return self._shape

    @property
    def log(self) -> "DatasetLog":
        """Log of the dataset."""
        if not self._log:
            self._log = DatasetLog(self._client, "dataset_" + self.key + ".log")
        return self._log

    def __repr__(self) -> str:
        return f"<class '{self.__class__.__name__}'> {self.key} {self.name}"

    def __str__(self) -> str:
        return f"{self.name} ({self.key})"

    def _create_csv_on_server(self) -> str:
        job = self._client._backend.create_csv_from_dataset(key=self.key)
        while _commons.is_server_job_running(
            self._client._backend.get_create_csv_job(key=job).status.status
        ):
            time.sleep(1)
        finished_job = self._client._backend.get_create_csv_job(key=job)
        if not _commons.is_server_job_complete(finished_job.status.status):
            raise RuntimeError(
                self._client._backend._format_server_error(
                    message=finished_job.status.error
                )
            )
        return finished_job.url

    # NOTE get_raw_data is not stable!
    def _get_data(
        self, start: int = 0, num_rows: int = None
    ) -> List[List[Union[bool, float, str]]]:
        """Retrieve data as a list.

        Args:
            start: index of first row to include
            num_rows: number of rows to include
        """
        num_rows = num_rows or self.shape[0]
        return self._client._backend.get_raw_data(
            key=self.key, offset=start, limit=num_rows
        ).rows

    def _import_modified_datasets(
        self, recipe_job: _recipes.RecipeJob
    ) -> List["Dataset"]:
        data_files = recipe_job._get_raw_info().entity.data_files
        keys = [
            self._client._backend.create_dataset_from_recipe(recipe_path=f)
            for f in data_files
        ]
        datasets = [
            DatasetJob(self._client, key, name=key).result(silent=True) for key in keys
        ]
        return datasets

    def _update(self) -> None:
        self._set_raw_info(self._client._backend.get_dataset_job(key=self.key))
        self._set_name(self._get_raw_info().entity.name)

    def column_summaries(
        self, columns: List[str] = None
    ) -> "DatasetColumnSummaryCollection":
        """
        Returns a collection of column summaries.

        Args:
            columns: Names of columns to include.

        Returns:
            Summaries of the columns of the dataset.
        """
        return DatasetColumnSummaryCollection(self, columns=columns)

    def delete(self) -> None:
        """Permanently deletes the dataset from the Driverless AI server."""
        key = self.key
        self._client._backend.delete_dataset(key=key)
        _logging.logger.info(f"Driverless AI Server reported dataset {key} deleted.")

    def download(
        self,
        dst_dir: str = ".",
        dst_file: Optional[str] = None,
        file_system: Optional["fsspec.spec.AbstractFileSystem"] = None,
        overwrite: bool = False,
        timeout: float = 30,
    ) -> str:
        """
        Downloads the dataset as a CSV file.

        Args:
            dst_dir: The path where the CSV file will be saved.
            dst_file: The name of the CSV file (overrides the default file name).
            file_system: FSSPEC-based file system to download to
                instead of the local file system.
            overwrite: Whether to overwrite or not if a file already exists.
            timeout: Connection timeout in seconds.

        Returns:
            Path to the downloaded CSV file.

        ??? Example
            ```py
            dataset = client.datasets.create(
                data="s3://h2o-public-test-data/smalldata/parser/avro/weather_snappy-compression.avro",
                data_source="s3",
            )
            dataset.download()
            ```
        """
        # _download adds <address>/files/ to start of all paths
        path = re.sub(
            "^.*?/files/",
            "",
            re.sub("^.*?/datasets_files/", "", self._create_csv_on_server()),
        )
        return self._client._download(
            server_path=path,
            dst_dir=dst_dir,
            dst_file=dst_file,
            file_system=file_system,
            overwrite=overwrite,
            timeout=timeout,
            download_type=_enums.DownloadType.DATASETS,
        )

    def export(self, **kwargs: Any) -> str:
        """
        Exports the dataset as a CSV file from the Driverless AI server.
        Note that the export location is configured in the server.
        Refer to the Driverless AI
        [docs](https://docs.h2o.ai/driverless-ai/1-10-lts/docs/userguide/export-artifacts.html)
        for more information.

        Other Parameters:
            storage_destination (str): Exporting destination.
                Possible values are `file_system`, `s3`, `bitbucket`, or `azure`.
            username (str): BitBucket username.
            password (str): BitBucket password.
            branch (str): BitBucket branch.
            user_note (str): BitBucket commit message.

        Returns:
            Relative path to the exported CSV in the export location.
        """
        self._update()
        model_key = "data_set"
        artifact_path = self._create_csv_on_server()
        artifact_file_name = f"{self.name}.csv"
        export_location = self._client._backend.list_experiment_artifacts(
            model_key=model_key,
            storage_destination=kwargs.get("storage_destination", ""),
        ).location
        job_key = self._client._backend.upload_experiment_artifacts(
            model_key=model_key,
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
            self._client, job_key, artifact_path, artifact_file_name, export_location
        ).result()
        return str(Path(export_location, artifact_file_name))

    def gui(self) -> _utils.Hyperlink:
        """
        Returns the full URL to the dataset details page in the Driverless AI server.

        Returns:
            URL to the dataset details page.
        """
        return _utils.Hyperlink(
            f"{self._client.server.address}{self._client._gui_sep}datasets/details"
            f"?dataset_key={self.key}&display_name={self.name}"
        )

    @_utils.min_supported_dai_version("1.10.6")
    def get_used_in_experiments(self) -> Dict[str, List["_experiments.Experiment"]]:
        """
        Retrieves the completed experiments where the dataset has been used
        as the training, testing, or validation dataset.

        Returns:
            A dictionary with three keys, `train`, `test`, and `validation`,
                each containing a list of experiments.
        """
        dataset_types = {
            "train": "Training",
            "test": "Testing",
            "validation": "Validation",
        }
        used_in_experiments = {}

        for dataset_type in dataset_types.keys():
            experiment_keys = self._client._backend.list_experiments_by_dataset(
                dataset_key=self.key,
                dataset_type=dataset_types[dataset_type],
                finished_only=True,
            )
            used_in_experiments[dataset_type] = [
                self._client.experiments.get(key) for key in experiment_keys
            ]

        return used_in_experiments

    def head(self, num_rows: int = 5) -> _utils.Table:
        """
        Returns the column headers and the first `n` number of rows
        of the dataset.

        Args:
            num_rows: Number of rows to retrieve.

        Returns:
            A Table containing the retrieved rows.

        ??? Example
            ```py
            dataset = client.datasets.create(
                data="s3://h2o-public-test-data/smalldata/iris/iris.csv",
                data_source="s3",
            )
            # Print the headers and first 10 rows
            print(dataset.head(num_rows=10))
            ```
        """
        data = self._get_data(0, num_rows)
        return _utils.Table(data, self.columns)

    @_utils.min_supported_dai_version("1.10.6")
    def merge_by_rows(
        self, other_dataset: "Dataset", new_dataset_name: str
    ) -> "Dataset":
        """
        Merges the specified dataset into this dataset.
        Note that the other dataset must have the same columns.

        Args:
            other_dataset: The dataset that will be merged into this.
            new_dataset_name: Name of the resulting dataset.

        Returns:
            Merged dataset.
        """
        key = self._client._backend.merge_datasets_by_row(
            datasets_keys=[self.key, other_dataset.key],
            output_name=new_dataset_name,
        )
        return DatasetsMergeJob(self._client, key).result().result()

    def modify_by_code(
        self, code: str, names: List[str] = None
    ) -> Dict[str, "Dataset"]:
        """
        Creates new dataset(s) by modifying the dataset using a Python script.

        In the Python script

        - The original dataset is available as variable `X` with type
          [`datatable.Frame`](https://datatable.readthedocs.io/en/v1.0.0/api/frame.html).
        - Newly created dataset(s) should be returned as a `datatable.Frame`, or
          a [pandas.DataFrame][], or a [numpy.ndarray][], or a list of those.

        Args:
            code: Python script that modifies `X`.
            names: Names for the new dataset(s).

        Returns:
            A dictionary of newly created datasets with `names` as keys.

        ??? Example
            ```py
            # Import the iris dataset.
            dataset = client.datasets.create(
                data="s3://h2o-public-test-data/smalldata/iris/iris.csv",
                data_source="s3",
            )

            # Create a new dataset only with the first 4 columns.
            new_dataset = dataset.modify_by_code(
                code="return X[:, :4]",
                names=["new_dataset"],
            )

            # Split on 5th column to create 2 datasets.
            new_datasets = dataset.modify_by_code(
                code="return [X[:, :5], X[:, 5:]]",
                names=["new_dataset_1", "new_dataset_2"],
            )
            ```
        """
        # Add recipe to server and get path to recipe file on server
        key = self._client._backend.get_data_recipe_preview(
            dataset_key=self.key,
            code=code,
            live_code=code,
            full_recipe_code=None,
            custom_recipe_key=None,
        )
        completed_preview_job = DataPreviewJob(self._client, key).result(silent=True)
        # Modify the dataset with recipe
        key = self._client._backend.modify_dataset_by_recipe_file(
            key=completed_preview_job._get_raw_info().dataset_key,
            recipe_path=completed_preview_job._get_raw_info().recipe_path,
        )

        recipe_job = _recipes.RecipeJob(self._client, key)
        recipe_job.result()  # wait for completion
        datasets = self._import_modified_datasets(recipe_job)
        for i, d in enumerate(datasets):
            d.rename(f"{i + 1}.{self.name}")
        if names is not None:
            if len(set(names)) != len(datasets):
                raise ValueError(
                    "Number of unique names doesn't match number of new datasets."
                )
            for i, name in enumerate(names):
                datasets[i].rename(name)
        return {d.name: d for d in datasets}

    def modify_by_code_preview(self, code: str) -> _utils.Table:
        """
        Returns a preview of new dataset(s) created by modifying the dataset using
        a Python script.

        In the Python script

        - The original dataset is available as variable `X` with type
          [`datatable.Frame`](https://datatable.readthedocs.io/en/v1.0.0/api/frame.html).
        - Newly created dataset(s) should be returned as a `datatable.Frame`, or
          a [pandas.DataFrame][], or a [numpy.ndarray][], or a list of those
          (only the first dataset in the list is shown in the preview).

        Args:
            code: Python script that modifies `X`.

        Returns:
            A table containing the first 10 rows of the new dataset.

        ??? Example
            ```py
            # Import the iris dataset.
            dataset = client.datasets.create(
                data="s3://h2o-public-test-data/smalldata/iris/iris.csv",
                data_source="s3",
            )

            # A new dataset only with the first 4 columns.
            table = dataset.modify_by_code_preview("return X[:, :4]")
            print(table)
            ```
        """
        key = self._client._backend.get_data_recipe_preview(
            dataset_key=self.key,
            code=code,
            live_code=code,
            full_recipe_code=None,
            custom_recipe_key=None,
        )
        completed_job = DataPreviewJob(self._client, key).result()
        return _utils.Table(
            completed_job._get_raw_info().entity.rows[:10],
            completed_job._get_raw_info().entity.headers,
        )

    def modify_by_recipe(
        self,
        recipe: Union[str, "_recipes.DataRecipe"] = None,
        names: List[str] = None,
    ) -> Dict[str, "Dataset"]:
        """
        Creates new dataset(s) by modifying the dataset using a data
        [recipe](https://docs.h2o.ai/driverless-ai/1-10-lts/docs/userguide/custom-recipes-data-recipes.html).

        Args:
            recipe: The path to the recipe file, or the url for the recipe,
                or the data recipe.
            names: Names for the new dataset(s).

        Returns:
            A dictionary of newly created datasets with `names` as keys.

        ??? Example
            ```py
            # Import the airlines dataset.
            dataset = client.datasets.create(
                data="s3://h2o-public-test-data/smalldata/airlines/allyears2k_headers.zip",
                data_source="s3",
            )

            # Modify the original dataset with a recipe.
            new_datasets = dataset.modify_by_recipe(
                recipe="https://github.com/h2oai/driverlessai-recipes/blob/master/data/airlines_multiple.py",
                names=["new_airlines1", "new_airlines2"],
            )
            ```
        """

        if isinstance(recipe, _recipes.DataRecipe):
            _utils.check_server_support(
                self._client, "1.10.2", "Dataset.modify_by_recipe"
            )
            key = self._client._backend.modify_dataset_by_recipe_key(
                dataset_key=self.key, recipe_key=recipe.key
            )
        elif re.match("^http[s]?://", recipe):
            key = self._client._backend.modify_dataset_by_recipe_url(
                key=self.key, recipe_url=recipe
            )
        else:
            # Add recipe file to server
            path = self._client._backend.perform_upload(
                file_path=recipe, skip_parse=True
            )[0]
            key = self._client._backend.modify_dataset_by_recipe_file(
                key=self.key, recipe_path=path
            )
        recipe_job = _recipes.RecipeJob(self._client, key)
        recipe_job.result()  # wait for completion
        datasets = self._import_modified_datasets(recipe_job)
        for i, d in enumerate(datasets):
            d.rename(f"{i + 1}.{self.name}")
        if names is not None:
            if len(set(names)) != len(datasets):
                raise ValueError(
                    "Number of unique names doesn't match number of new datasets."
                )
            for i, name in enumerate(names):
                datasets[i].rename(name)
        return {d.name: d for d in datasets}

    @_utils.min_supported_dai_version("1.10.7")
    def redescribe(self, description: str) -> "Dataset":
        """Changes the description of the dataset.

        Args:
            description: New description.

        Returns:
            This dataset.
        """
        self._client._backend.annotate_dataset(key=self.key, notes=description)
        self._update()
        return self

    def rename(self, name: str) -> "Dataset":
        """Changes the display name of the dataset.

        Args:
            name: New display name.

        Returns:
            This dataset.
        """
        self._client._backend.update_dataset_name(key=self.key, new_name=name)
        self._update()
        return self

    def set_datetime_format(self, columns: Dict[str, str]) -> None:
        """
        Sets/updates the datetime format for columns of the dataset.

        Args:
            columns: The dictionary where the key is the column name and
                the value is a valid datetime format.

        ??? Example
            ```py
            # Import the Eurodate dataset.
            dataset = client.datasets.create(
                data="s3://h2o-public-test-data/smalldata/jira/v-11-eurodate.csv",
                data_source="s3",
            )

            # Set the date time format for column ‘ds5'
            dataset.set_datetime_format({"ds5": "%d-%m-%y %H:%M"})
            ```
        """
        for k, v in columns.items():
            if v is None:
                v = ""
            self._client._backend.update_dataset_col_format(
                key=self.key, colname=k, datetime_format=v
            )
        self._update()

    def set_logical_types(self, columns: Dict[str, Union[str, List[str]]]) -> None:
        """
        Sets/updates the logical data types of the columns of the dataset.
        The logical type of columns is primarily used to determine which transformers to
        try on the column's data.

        Possible logical types:

        - `categorical`
        - `date`
        - `datetime`
        - `id`
        - `numerical`
        - `text`

        Args:
            columns: A dictionary where the key is the column name and the value
                is the logical type or a list of logical types for the column
                Use `None` to unset all logical types.

        ??? Example
            ```py
            # Import the prostate dataset.
            dataset = client.datasets.create(
                data="s3://h2o-public-test-data/smalldata/prostate/prostate.csv",
                data_source="s3",
            )

            # Set the logical types
            dataset.set_logical_types(
                {"ID": "id", "AGE": ["categorical", "numerical"], "RACE": None}
            )
            ```
        """
        for k, v in columns.items():
            if v is None:
                self._client._backend.update_dataset_col_logical_types(
                    key=self.key, colname=k, logical_types=[]
                )
            else:
                if isinstance(v, str):
                    v = [v]
                for lt in v:
                    if lt not in self._logical_types:
                        raise ValueError(
                            "Please use logical types from: "
                            + str(sorted(self._logical_types.keys()))
                        )
                self._client._backend.update_dataset_col_logical_types(
                    key=self.key,
                    colname=k,
                    logical_types=[self._logical_types[lt] for lt in v],
                )
        self._update()

    def split_to_train_test(
        self,
        train_size: float = 0.5,
        train_name: str = None,
        test_name: str = None,
        target_column: str = None,
        fold_column: str = None,
        time_column: str = None,
        seed: int = 1234,
    ) -> Dict[str, "Dataset"]:
        """
        Splits the dataset into train and test datasets in the Driverless AI server.

        Args:
            train_size: Proportion of the rows to put to the train dataset.
                Rest will be in the test dataset.
            train_name: Name for the train dataset.
            test_name: Name for the test dataset.
            target_column: Column to use for [stratified sampling](https://w.wiki/8V$X).
            fold_column: Column to ensure grouped splitting.
            time_column: Column for time-based splitting.
            seed: A random seed for reproducibility.

        !!! note
            Only one of `target_column`, `fold_column`, or `time_column`
            can be passed at a time.

        Returns:
            A dictionary with keys `train_dataset` and `test_dataset`, containing
                the respective dataset.

        ??? Example
            ```py
            # Import the iris dataset.
            dataset = client.datasets.create(
                data="s3://h2o-public-test-data/smalldata/iris/iris.csv",
                data_source="s3",
            )

            # Split the iris dataset into train/test sets.
            splits = dataset.split_to_train_test(train_size=0.7)
            train_dataset = splits["train_dataset"]
            test_dataset = splits["test_dataset"]
            ```
        """
        return self.split_to_train_test_async(
            train_size,
            train_name,
            test_name,
            target_column,
            fold_column,
            time_column,
            seed,
        ).result()

    def split_to_train_test_async(
        self,
        train_size: float = 0.5,
        train_name: str = None,
        test_name: str = None,
        target_column: str = None,
        fold_column: str = None,
        time_column: str = None,
        seed: int = 1234,
    ) -> "DatasetSplitJob":
        """
        Launches the splitting of the dataset into train and test datasets
        in the Driverless AI server.

        Args:
            train_size: Proportion of the rows to put to the train dataset.
                Rest will be in the test dataset.
            train_name: Name for the train dataset.
            test_name: Name for the test dataset.
            target_column: Column to use for [stratified sampling](https://w.wiki/8V$X).
            fold_column: Column to ensure grouped splitting.
            time_column: Column for time-based splitting.
            seed: A random seed for reproducibility.

        !!! note
            Only one of `target_column`, `fold_column`, or `time_column`
            can be passed at a time.

        Returns:
            Started dataset split job.
        """
        cols = [target_column, fold_column, time_column]
        if sum([1 for x in cols if x is not None]) > 1:
            raise ValueError("Only one column argument allowed.")
        # Don't pass names here since certain file extensions in the name
        # (like .csv) cause errors, rename inside DatasetSplitJob instead
        key = self._client._backend.make_dataset_split(
            dataset_key=self.key,
            output_name1=None,
            output_name2=None,
            target=target_column,
            fold_col=fold_column,
            time_col=time_column,
            ratio=train_size,
            seed=seed,
            split_datetime=None,  # TODO Introduce split_datetime as parameter
        )
        return DatasetSplitJob(self._client, key, train_name, test_name)

    @_utils.beta
    @_utils.min_supported_dai_version("1.10.6")
    def summarize(self) -> "DatasetSummary":
        """
        Summarizes the dataset using a GPT configured in the Driverless AI server.

        Returns:
            Dataset summary.
        """
        return self.summarize_async().result()

    @_utils.beta
    @_utils.min_supported_dai_version("1.10.6")
    def summarize_async(self) -> "DatasetSummarizeJob":
        """
        Launches the summarization of the dataset using a GPT configured
        in the Driverless AI server.

        Returns:
            Started summarization job.
        """
        key = self._client._backend.create_dataset_gpt_summary(dataset_key=self.key)
        return DatasetSummarizeJob(self._client, key)

    def tail(self, num_rows: int = 5) -> _utils.Table:
        """
        Returns the column headers and the last `n` number of rows
        of the dataset.

        Args:
            num_rows: Number of rows to retrieve.

        Returns:
            A Table containing the retrieved rows.

        ??? Example
            ```py
            dataset = client.datasets.create(
                data="s3://h2o-public-test-data/smalldata/iris/iris.csv",
                data_source="s3",
            )
            # Print the headers and last 10 rows
            print(dataset.tail(num_rows=10))
            ```
        """
        data = self._get_data(self.shape[0] - num_rows, num_rows)
        return _utils.Table(data, self.columns)


class DatasetLog(_commons.ServerLog):
    """A dataset log file in the Driverless AI server."""

    def __init__(self, client: "_core.Client", file_path: str) -> None:
        super().__init__(client, file_path)

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
        )


class DatasetColumnSummary:
    """
    Summary of a column in a dataset.

    ??? Example
        ```py
        c1_summary = dataset.column_summaries()["C1"]
        # Print the summary for a histogram along with column statistics.
        print(c1_summary)
        ```
        Sample output:
        ```
        --- C1 ---

         4.3|███████
            |█████████████████
            |██████████
            |████████████████████
            |████████████
            |███████████████████
            |█████████████
            |████
            |████
         7.9|████

        Data Type: real
        Logical Types: ['categorical', 'numerical']
        Datetime Format:
        Count: 150
        Missing: 0
        Mean: 5.84
        SD: 0.828
        Min: 4.3
        Max: 7.9
        Unique: 35
        Freq: 10
        ```
    """

    def __init__(self, column_summary: Dict[str, Any]) -> None:
        self._column_summary = column_summary

    @property
    def count(self) -> int:
        """Non-missing values count in the column."""
        return self._column_summary["count"]

    @property
    def data_type(self) -> str:
        """
        Raw data type of the column as detected by the Driverless AI server
        when the dataset was imported.
        """
        return self._column_summary["data_type"]

    @property
    def datetime_format(self) -> str:
        """
        Datetime format of the column. See also
        [Dataset.set_datetime_format][driverlessai._datasets.Dataset.set_datetime_format].
        """
        return self._column_summary["datetime_format"]

    @property
    def freq(self) -> int:
        """Count of most frequent value in the column."""
        return self._column_summary["freq"]

    @property
    def logical_types(self) -> List[str]:
        """
        User defined data types for the column to be used by Driverless AI server. This
        precedes the [data_type][driverlessai._datasets.DatasetColumnSummary.data_type].
        See also
        [Dataset.set_logical_types][driverlessai._datasets.Dataset.set_logical_types].
        """
        return self._column_summary["logical_types"]

    @property
    def max(self) -> Optional[Union[bool, float, int]]:
        """Maximum value in the column if it contains binary/numeric data."""
        return self._column_summary["max"]

    @property
    def mean(self) -> Optional[float]:
        """Mean value of the column if it contains binary/numeric data."""
        return self._column_summary["mean"]

    @property
    def min(self) -> Optional[Union[bool, float, int]]:
        """Minimum value in the column if it contains binary/numeric data."""
        return self._column_summary["min"]

    @property
    def missing(self) -> int:
        """Missing values count in the column."""
        return self._column_summary["missing"]

    @property
    def name(self) -> str:
        """Column name."""
        return self._column_summary["name"]

    @property
    def sd(self) -> Optional[float]:
        """Standard deviation of the column if it contains binary/numeric data."""
        return self._column_summary["std"]

    @property
    def unique(self) -> int:
        """Unique values count of the column."""
        return self._column_summary["unique"]

    def __repr__(self) -> str:
        return f"<{self.name} Summary>"

    def __str__(self) -> str:
        s = [
            f"--- {self.name} ---\n",
            f"{self._column_summary['hist']}",
            f"Data Type: {self.data_type}",
            f"Logical Types: {self.logical_types!s}",
            f"Datetime Format: {self.datetime_format}",
            f"Count: {self.count!s}",
            f"Missing: {self.missing!s}",
        ]
        if self.mean not in [None, ""]:
            # mean/sd could be NaN
            s.append(
                f"Mean: {self.mean:{'0.3g' if _utils.is_number(self.mean) else ''}}"
            )
            s.append(f"SD: {self.sd:{'0.3g' if _utils.is_number(self.sd) else ''}}")
        if self.min not in [None, ""]:
            # min/max could be datetime string
            s.append(f"Min: {self.min:{'0.3g' if _utils.is_number(self.min) else ''}}")
            s.append(f"Max: {self.max:{'0.3g' if _utils.is_number(self.max) else ''}}")
        s.append(f"Unique: {self.unique!s}")
        s.append(f"Freq: {self.freq!s}")
        return "\n".join(s)


class DatasetColumnSummaryCollection:
    """
    A collection of column summaries of a dataset.

    A column summary can be retrieved,

    - by the column index `dataset.column_summaries()[0]`
    - by the column name `dataset.column_summaries()["C1"]`
    - Or slice it to get multiple summaries `dataset.column_summaries()[0:3]`
    """

    def __init__(self, dataset: "Dataset", columns: List[str] = None):
        self._columns = columns or dataset.columns
        self._dataset = dataset
        self._update()

    def __getitem__(
        self, columns: Union[int, slice, str, List[str]]
    ) -> Union["DatasetColumnSummary", "DatasetColumnSummaryCollection"]:
        self._update()
        if isinstance(columns, str):
            return DatasetColumnSummary(self._column_summaries[columns])
        elif isinstance(columns, int):
            columns = self._columns[columns]
            return DatasetColumnSummary(self._column_summaries[columns])
        elif isinstance(columns, slice):
            columns = self._columns[columns]
        return DatasetColumnSummaryCollection(self._dataset, columns=columns)

    def __iter__(self) -> Iterable["DatasetColumnSummary"]:
        self._update()
        yield from [
            DatasetColumnSummary(self._column_summaries[c]) for c in self._columns
        ]

    def __repr__(self) -> str:
        string = "<"
        for c in self._columns[:-1]:
            string += "<" + c + " Summary>, "
        string += "<" + self._columns[-1] + " Summary>>"
        return string

    def __str__(self) -> str:
        string = ""
        for c in self._columns:
            string += str(DatasetColumnSummary(self._column_summaries[c])) + "\n"
        return string

    def _create_column_summary_dict(self, column: Any) -> Dict[str, Any]:
        summary = {}
        summary["name"] = column.name
        summary["data_type"] = column.data_type
        summary["logical_types"] = [
            k
            for k, v in self._dataset._logical_types.items()
            if v in column.logical_types
        ]
        summary["datetime_format"] = column.datetime_format
        if column.stats.is_numeric:
            stats = column.stats.numeric.dump()
        else:
            stats = column.stats.non_numeric.dump()
        summary["count"] = stats.get("count", 0)
        summary["missing"] = self._dataset.shape[0] - summary["count"]
        summary["mean"] = stats.get("mean", None)
        summary["std"] = stats.get("std", None)
        summary["min"] = stats.get("min", None)
        summary["max"] = stats.get("max", None)
        summary["unique"] = stats.get("unique")
        summary["freq"] = stats.get("freq")
        summary["hist"] = self._create_histogram_string(column)
        return summary

    def _create_histogram_string(self, column: Any) -> str:
        hist = ""
        block = chr(9608)
        if column.stats.is_numeric:
            ht = column.stats.numeric.hist_ticks
            if not ht:
                return "  N/A\n"
            hc = column.stats.numeric.hist_counts
            ht = [f"{ast.literal_eval(t):0.3g}" for t in ht]
            hc = [round(c / max(hc) * 20) for c in hc]
            max_len = max(len(ht[0]), len(ht[-1])) + 1
            hist += f"{ht[0].rjust(max_len)}|{block * hc[0]}\n"
            for c in hc[1:-1]:
                hist += f"{'|'.rjust(max_len + 1)}{block * c}\n"
            hist += f"{ht[-1].rjust(max_len)}|{block * hc[-1]}\n"
        else:
            ht = column.stats.non_numeric.hist_ticks
            if not ht:
                return "  N/A\n"
            hc = column.stats.non_numeric.hist_counts
            hc = [round(c / max(hc) * 20) for c in hc]
            max_len = max([len(t) for t in ht]) + 1
            for i, c in enumerate(hc):
                hist += f"{ht[i].rjust(max_len)}|{block * c}\n"
        return hist

    def _update(self) -> None:
        self._dataset._update()
        self._column_summaries: Dict[str, Dict[str, Union[float, int, str]]] = {
            c.name: self._create_column_summary_dict(c)
            for c in self._dataset._get_raw_info().entity.columns
            if c.name in self._columns
        }


class DatasetJob(_commons.ServerJob):
    """Monitor the creation of a dataset in the Driverless AI server."""

    def __init__(
        self,
        client: "_core.Client",
        key: str,
        name: str = None,
        description: str = None,
    ) -> None:
        super().__init__(client=client, key=key)
        self._set_name(name)
        self._description = description

    def _update(self) -> None:
        self._set_raw_info(self._client._backend.get_dataset_job(key=self.key))

    def result(self, silent: bool = False) -> "Dataset":
        """
        Awaits the job's completion before returning the created dataset.

        Args:
            silent: Whether to display status updates or not.

        Returns:
            Created dataset by the job.
        """
        self._wait(silent)
        if self.name:
            self._client._backend.update_dataset_name(key=self.key, new_name=self.name)
        if self._description:
            self._client._backend.annotate_dataset(
                key=self.key, notes=self._description
            )
        return self._client.datasets.get(self.key)


class Datasets:
    """
    Interact with
    [datasets](https://docs.h2o.ai/driverless-ai/1-10-lts/docs/userguide/datasets.html)
    in the Driverless AI server.
    """

    def __init__(self, client: "_core.Client") -> None:
        self._client = client
        self._simple_connectors = {
            "dtap": self._client._backend.create_dataset_from_dtap,
            "file": self._client._backend.create_dataset_from_file,
            "gcs": self._client._backend.create_dataset_from_gcs,
            "hdfs": self._client._backend.create_dataset_from_hadoop,
        }
        if self._client.server.version >= "1.10.3":
            self._simple_connectors[
                "h2o_drive"
            ] = self._client._backend.create_dataset_from_h2o_drive

    def _dataset_create(
        self,
        data: Union[str, "pandas.DataFrame"],
        data_source: str,
        data_source_config: Dict[str, str] = None,
        force: bool = False,
        name: str = None,
        description: Optional[str] = None,
    ) -> "DatasetJob":
        if data_source not in self._client.connectors.list():
            raise ValueError(
                "Please use one of the available connectors: "
                f"{self._client.connectors.list()}"
            )
        if not force:
            if name:
                _utils.error_if_dataset_exists(self._client, name)
            elif isinstance(data, str):
                # if data is not Pandas DataFrame
                _utils.error_if_dataset_exists(self._client, Path(data).name)
        if data_source in self._simple_connectors:
            key = self._simple_connectors[data_source](data)
        elif data_source == "upload":
            if data.__class__.__name__ == "DataFrame":
                with tempfile.TemporaryDirectory() as temp_dir:
                    temp_csv_path = Path(
                        temp_dir, f"DataFrame_{os.urandom(4).hex()}.csv"
                    )
                    data.to_csv(temp_csv_path, index=False)  # type: ignore
                    key = self._client._backend.upload_dataset(file_path=temp_csv_path)[
                        0
                    ]
            else:
                valid_extensions = self._client.server.configurations[
                    "supported_file_types"
                ]
                _, extension = os.path.splitext(data)
                if extension[1:] not in valid_extensions:
                    raise ValueError(
                        f"Please use a file with one of the valid "
                        f"extensions: {valid_extensions}"
                    )
                key = self._client._backend.upload_dataset(file_path=data)[0]
        elif data_source == "s3":
            if (
                data_source_config
                and data_source_config.get("aws_access_key_id")
                and data_source_config.get("aws_secret_access_key")
            ):
                if self._client.server.version < "1.10.4":
                    raise ValueError(
                        "data_source_config arg for s3 import is not supported for "
                        "DAI version < 1.10.4"
                    )

                self._client._backend.set_user_config_option(
                    key="aws_access_key_id",
                    value=data_source_config["aws_access_key_id"],
                )
                self._client._backend.set_user_config_option(
                    key="aws_secret_access_key",
                    value=data_source_config["aws_secret_access_key"],
                )

            if self._client.server.version < "2.1.0":
                key = self._client._backend.create_dataset_from_s3(data)
            else:
                data_source_config = data_source_config or {}
                args = self._client._server_module.messages.S3CreateDatasetArgs(
                    access_key_id=data_source_config.get("aws_access_key_id", ""),
                    secret_access_key=data_source_config.get(
                        "aws_secret_access_key", ""
                    ),
                    assumed_role_arn=data_source_config.get("aws_assumed_role_arn", ""),
                    session_token=data_source_config.get("aws_session_token", ""),
                )
                key = self._client._backend.create_dataset_from_s3(data, args)
        elif data_source == "azrbs":
            if (
                data_source_config
                and data_source_config.get("azure_blob_account_name")
                and data_source_config.get("azure_blob_account_key")
                and data_source_config.get("azure_connection_string")
            ):
                if self._client.server.version < "1.10.5":

                    raise ValueError(
                        "data_source_config arg for azure import is not supported for "
                        "DAI version < 1.10.5"
                    )

                self._client._backend.set_user_config_option(
                    key="azure_blob_account_name",
                    value=data_source_config["azure_blob_account_name"],
                )
                self._client._backend.set_user_config_option(
                    key="azure_blob_account_key",
                    value=data_source_config["azure_blob_account_key"],
                )
                self._client._backend.set_user_config_option(
                    key="azure_connection_string",
                    value=data_source_config["azure_connection_string"],
                )

            key = self._client._backend.create_dataset_from_azr_blob(filepath=data)
        elif data_source == "minio":
            if (
                data_source_config
                and data_source_config.get("minio_access_key_id")
                and data_source_config.get("minio_secret_access_key")
            ):
                if self._client.server.version < "1.10.4":
                    raise ValueError(
                        "data_source_config arg for minio import is not supported for "
                        "DAI version < 1.10.4"
                    )

                self._client._backend.set_user_config_option(
                    key="minio_access_key_id",
                    value=data_source_config["minio_access_key_id"],
                )
                self._client._backend.set_user_config_option(
                    key="minio_secret_access_key",
                    value=data_source_config["minio_secret_access_key"],
                )

            key = self._client._backend.create_dataset_from_minio(filepath=data)
        elif data_source == "gbq":
            if name is None:
                raise ValueError(
                    "Google Big Query connector requires a `name` argument."
                )
            if (
                data_source_config.get("gbq_location")
                and self._client.server.version < "1.10.1"
            ):
                raise ValueError(
                    "'gbq_location' parameter for the 'gbq' connector requires "
                    "Driverless AI server version 1.10.1 or higher."
                )
            args = self._client._server_module.messages.GbqCreateDatasetArgs(
                dataset_id=data_source_config["gbq_dataset_name"],
                bucket_name=data_source_config["gbq_bucket_name"],
                dst=name,
                query=data,
                location=data_source_config.get("gbq_location", None),
                project=data_source_config.get("gbq_project", None),
            )
            key = self._client._backend.create_dataset_from_gbq(args=args)
        elif data_source == "hive":
            if name is None:
                raise ValueError("Hive connector requires a `name` argument.")
            args = self._client._server_module.messages.HiveCreateDatasetArgs(
                dst=name,
                query=data,
                hive_conf_path=data_source_config.get("hive_conf_path", ""),
                keytab_path=data_source_config.get("hive_keytab_path", ""),
                auth_type=data_source_config.get("hive_auth_type", ""),
                principal_user=data_source_config.get("hive_principal_user", ""),
                database=data_source_config.get("hive_default_config", ""),
            )
            key = self._client._backend.create_dataset_from_spark_hive(args=args)
        elif data_source == "jdbc":
            if name is None:
                raise ValueError("JDBC connector requires a `name` argument.")
            args = self._client._server_module.messages.JdbcCreateDatasetArgs(
                dst=name,
                query=data,
                id_column=data_source_config.get("id_column", ""),
                jdbc_user=data_source_config["jdbc_username"],
                password=data_source_config["jdbc_password"],
                url=data_source_config.get("jdbc_url", ""),
                classpath=data_source_config.get("jdbc_driver", ""),
                jarpath=data_source_config.get("jdbc_jar", ""),
                database=data_source_config.get("jdbc_default_config", ""),
                keytab_path=data_source_config.get("jdbc_keytab_path", ""),
                user_principal=data_source_config.get("jdbc_user_principal", ""),
            )
            key = self._client._backend.create_dataset_from_spark_jdbc(args=args)
        elif data_source == "kdb":
            if name is None:
                raise ValueError("KDB connector requires a `name` argument.")
            args = self._client._server_module.messages.KdbCreateDatasetArgs(
                dst=name, query=data
            )
            key = self._client._backend.create_dataset_from_kdb(args=args)
        elif data_source == "recipe_file":
            data_file = self._client._backend.upload_custom_recipe_sync(
                file_path=data
            ).data_files[0]
            key = self._client._backend.create_dataset_from_recipe(
                recipe_path=data_file
            )
        elif data_source == "recipe_url":
            recipe_key = self._client._backend.create_custom_recipe_from_url(url=data)
            recipe_job = _recipes.RecipeJob(self._client, recipe_key)
            recipe_job.result()  # wait for completion
            data_file = recipe_job._get_raw_info().entity.data_files[0]
            key = self._client._backend.create_dataset_from_recipe(
                recipe_path=data_file
            )
        elif data_source == "snow":
            if name is None:
                raise ValueError("Snowflake connector requires a `name` argument.")
            if (
                data_source_config.get("snowflake_account")
                and self._client.server.version < "1.10.2"
            ):
                raise ValueError(
                    "'snowflake_account' parameter for the 'snow' connector requires "
                    "Driverless AI server version 1.10.2 or higher."
                )
            if self._client.server.version < "2.2.0":
                args = self._client._server_module.messages.SnowCreateDatasetArgs(
                    region=data_source_config.get("snowflake_region", ""),
                    database=data_source_config["snowflake_database"],
                    warehouse=data_source_config["snowflake_warehouse"],
                    schema=data_source_config["snowflake_schema"],
                    role=data_source_config.get("snowflake_role", ""),
                    dst=name,
                    query=data,
                    optional_formatting=data_source_config.get(
                        "snowflake_formatting", ""
                    ),
                    sf_user=data_source_config.get("snowflake_username", ""),
                    password=data_source_config.get("snowflake_password", ""),
                    account=data_source_config.get("snowflake_account", ""),
                )
            else:
                args = self._client._server_module.messages.SnowCreateDatasetArgs(
                    region=data_source_config.get("snowflake_region", ""),
                    database=data_source_config["snowflake_database"],
                    warehouse=data_source_config["snowflake_warehouse"],
                    schema=data_source_config["snowflake_schema"],
                    role=data_source_config.get("snowflake_role", ""),
                    dst=name,
                    query=data,
                    optional_formatting=data_source_config.get(
                        "snowflake_formatting", ""
                    ),
                    sf_user=data_source_config.get("snowflake_username", ""),
                    password=data_source_config.get("snowflake_password", ""),
                    account=data_source_config.get("snowflake_account", ""),
                    private_key_file_path=data_source_config.get(
                        "snowflake_private_key_file_path", ""
                    ),
                    private_key_file_password=data_source_config.get(
                        "snowflake_private_key_file_password", ""
                    ),
                )
            key = self._client._backend.create_dataset_from_snowflake(args=args)
        elif data_source == "feature_store":
            if self._client.server.version >= "1.10.4":
                args = (
                    self._client._server_module.messages.FeatureStoreCreateDatasetArgs(
                        project=data_source_config["feature_store_project"],
                        feature_set=data,
                    )
                )
                key = self._client._backend.create_dataset_from_feature_store(args=args)
        elif data_source == "databricks":
            if self._client.server.version < "2.0":
                raise ValueError(
                    "'databricks' connector requires Driverless AI server version "
                    "2.0 or higher."
                )
            if not name:
                raise ValueError("Databricks connector requires a name.")
            args = self._client._server_module.messages.DatabricksCreateDatasetArgs(
                warehouse_id=data_source_config["databricks_warehouse_id"],
                catalog=data_source_config.get("databricks_catalog", ""),
                schema=data_source_config.get("databricks_schema", ""),
                query=data,
                dst=name,
                workspace_instance_name=data_source_config[
                    "databricks_workspace_instance_name"
                ],
                personal_access_token=data_source_config.get(
                    "databricks_personal_access_token",
                    "",
                ),
            )
            key = self._client._backend.create_dataset_from_databricks(args=args)
        elif data_source == "delta_table":
            if self._client.server.version < "2.1":
                raise ValueError(
                    "'delta_table' connector requires Driverless AI server version "
                    "2.1 or higher."
                )
            if not name:
                raise ValueError("Delta Table connector requires a name.")
            args = self._client._server_module.messages.DeltaTableCreateDatasetArgs(
                table_path=data_source_config.get("table_path", ""),
                query=data,
                dst=name,
            )
            key = self._client._backend.create_dataset_from_delta_table(args=args)
        else:
            raise ValueError(f"Data source '{data_source}' is not supported.")

        if description and self._client.server.version < "1.10.7":
            raise ValueError(
                "'description' parameter requires Driverless AI server"
                " version 1.10.7 or higher."
            )

        return DatasetJob(self._client, key, name, description)

    def create(
        self,
        data: Union[str, "pandas.DataFrame"],
        data_source: str = "upload",
        data_source_config: Dict[str, str] = None,
        force: bool = False,
        name: str = None,
        description: Optional[str] = None,
    ) -> "Dataset":
        """
        Creates a dataset in the Driverless AI server.

        Args:
            data: Path to the data file(s), or path to a directory,
                or a SQL query, or a pandas Dataframe.
            data_source: Name of the connector to import data from.
                Use `driverlessai.connectors.list()` to get
                enabled connectors in the server.
            data_source_config: A dictionary of
                configuration options for advanced connectors.
            force: Whether to create the dataset even when a dataset
                already exists with the same name.
            name: Name for the created dataset.
            description: Description for the created dataset.
                (only available from Driverless AI version 1.10.7 onwards)

        Returns:
            Created dataset.

        ??? Example
            ```py
            dataset = client.datasets.create(
                data="s3://h2o-public-test-data/smalldata/iris/iris.csv",
                data_source="s3",
                name="iris-data",
                description="My Iris dataset",
            )
            ```
        """
        return self.create_async(
            data, data_source, data_source_config, force, name, description
        ).result()

    def create_async(
        self,
        data: Union[str, "pandas.DataFrame"],
        data_source: str = "upload",
        data_source_config: Dict[str, str] = None,
        force: bool = False,
        name: str = None,
        description: Optional[str] = None,
    ) -> "DatasetJob":
        """
        Launches the creation of a dataset in the Driverless AI server.

        Args:
            data: Path to the data file(s), or path to a directory,
                or a SQL query, or a pandas Dataframe.
            data_source: Name of the connector to import data from.
                Use `driverlessai.connectors.list()` to get
                enabled connectors in the server.
            data_source_config: A dictionary of
                configuration options for advanced connectors.
            force: Whether to create the dataset even when a dataset
                already exists with the same name.
            name: Name for the created dataset.
            description: Description for the created dataset.
                (only available from Driverless AI version 1.10.7 onwards)

        Returns:
            Started the dataset job.

        ??? Example
            ```py
            dataset = client.datasets.create(
                data="SELECT * FROM creditcard",
                data_source="jdbc",
                data_source_config=dict(
                    jdbc_jar="/opt/jdbc-drivers/mysql/mysql-connector-java-8.0.23.jar",
                    jdbc_driver="com.mysql.cj.jdbc.Driver",
                    jdbc_url="jdbc:mysql://localhost:3306/datasets",
                    jdbc_username="root",
                    jdbc_password="root"
                ),
                name="creditcard",
                description="Sample creditcard data",
                force=True,
            )
            ```
        """
        return self._dataset_create(
            data, data_source, data_source_config, force, name, description
        )

    def get(self, key: str) -> "Dataset":
        """
        Retrieves a dataset in the Driverless AI server. If the dataset only exists in
        H2O Storage then it will be imported into the server first.

        Args:
            key: The unique ID of the dataset.

        Returns:
            The dataset corresponding to the key.

        ??? Example
            ```py
            key = "e7de8630-dbfb-11ea-9f69-0242ac110002"
            dataset = client.datasets.get(key=key)
            ```
        """
        if self._client.server.storage_enabled:
            try:
                storage_key = self._client._backend.import_storage_dataset(
                    dataset_id=key
                )
                if storage_key:
                    _logging.logger.info("Importing dataset from storage...")
                    _commons.StorageImportJob(self._client, storage_key).result()
            except self._client._server_module.protocol.RemoteError as e:
                if not _utils.is_key_error(e):
                    raise
        info = self._client._backend.get_dataset_job(key=key)
        return Dataset(self._client, info)

    def gui(self) -> _utils.Hyperlink:
        """
        Returns the full URL to the Datasets page in the Driverless AI server.

        Returns:
            The full URL to the Datasets page.
        """
        return _utils.Hyperlink(
            f"{self._client.server.address}{self._client._gui_sep}datasets"
        )

    def list(self, start_index: int = 0, count: int = None) -> Sequence["Dataset"]:
        """
        Retrieves datasets in the Driverless AI server.

        Args:
            start_index: The index of the first dataset to retrieve.
            count: The maximum number of datasets to retrieve.
                If `None`, retrieves all available datasets.

        Returns:
            Datasets.
        """
        if count:
            data = self._client._backend.list_datasets(
                offset=start_index, limit=count, include_inactive=False
            ).datasets
        else:
            page_size = 100
            page_position = start_index
            data = []
            while True:
                page = self._client._backend.list_datasets(
                    offset=page_position, limit=page_size, include_inactive=True
                ).datasets
                data.extend(
                    d for d in page if _commons.is_server_job_complete(d.import_status)
                )
                if len(page) < page_size:
                    break
                page_position += page_size
        return _commons.ServerObjectList(
            data=data, get_method=self.get, item_class_name=Dataset.__name__
        )

    @_utils.beta
    def get_by_name(self, name: str) -> Optional["Dataset"]:
        """
        Retrieves a dataset by its display name from the Driverless AI server.

        Args:
            name: Name of the dataset.

        Returns:
            The dataset with the specified name if it exists, otherwise `None`.
        """
        sort_query = self._client._server_module.messages.EntitySortQuery("", "", "")
        template = f'"name": "{name}"'
        data = self._client._backend.search_and_sort_datasets(
            search_query=template,
            sort_query=sort_query,
            ascending=False,
            offset=0,
            limit=1,
            include_inactive=True,
        ).datasets
        if data:
            info = self._client._backend.get_dataset_job(key=data[0].key)
            return Dataset(self._client, info)
        else:
            return None


class DatasetsMergeJob(_commons.ServerJob):
    """Monitor merging of two datasets in the Driverless AI server."""

    def __init__(
        self,
        client: "_core.Client",
        key: str,
    ) -> None:
        super().__init__(client=client, key=key)

    def _update(self) -> None:
        self._set_raw_info(self._client._backend.get_dataset_merge_job(key=self.key))

    def result(self, silent: bool = False) -> DatasetJob:
        """
        Awaits the job's completion before returning the job of the merged dataset.

        Args:
            silent: Whether to display status updates or not.

        Returns:
            Dataset job of the merged dataset created by the job.
        """
        self._wait(silent)
        return DatasetJob(self._client, self._get_raw_info().merge_dataset)


class DatasetSplitJob(_commons.ServerJob):
    """Monitor splitting of a dataset in the Driverless AI server."""

    def __init__(
        self,
        client: "_core.Client",
        key: str,
        train_name: str = None,
        test_name: str = None,
    ) -> None:
        super().__init__(client=client, key=key)
        self._test_name = test_name
        self._train_name = train_name

    def _update(self) -> None:
        self._set_raw_info(self._client._backend.get_dataset_split_job(key=self.key))

    def result(self, silent: bool = False) -> Dict[str, "Dataset"]:
        """
        Awaits the job's completion before returning the split datasets.

        Args:
            silent: Whether to display status updates or not.

        Returns:
            A dictionary with keys `train_dataset` and `test_dataset`, containing
                the respective dataset created by the job.
        """
        status_update = _utils.StatusUpdate()
        if not silent:
            status_update.display(_enums.JobStatus.RUNNING.message)
        self._wait(silent=True)
        ds1_key, ds2_key = self._get_raw_info().entity
        ds1 = DatasetJob(self._client, ds1_key, name=self._train_name).result(
            silent=True
        )
        ds2 = DatasetJob(self._client, ds2_key, name=self._test_name).result(
            silent=True
        )
        if not silent:
            status_update.display(_enums.JobStatus.COMPLETE.message)
        status_update.end()
        return {"train_dataset": ds1, "test_dataset": ds2}

    def status(self, verbose: int = None) -> str:
        """
        Returns the status of the job.

        Args:
            verbose: Ignored.

        Returns:
            Current status of the job.
        """
        return self._status().message


@dataclasses.dataclass(frozen=True)
class DatasetSummary:
    """A summary of a dataset."""

    provider: str
    """GPT provider that generated the dataset summary."""
    summary: str
    """Dataset summary."""


class DatasetSummarizeJob(_commons.ServerJob):
    """Monitor the creation of a dataset summary in the Driverless AI server."""

    def __init__(self, client: "_core.Client", key: str):
        super().__init__(client, key)

    def _update(self) -> None:
        self._set_raw_info(self._client._backend.get_gpt_summary_job(key=self.key))

    def result(self, silent: bool = False) -> DatasetSummary:
        """
        Awaits the job's completion before returning the created dataset summary.

        Args:
            silent: Whether to display status updates or not.

        Returns:
            Created dataset summary by the job.
        """
        self._wait(silent)
        summary = self._get_raw_info().entity
        return DatasetSummary(summary.provider, summary.summary)
