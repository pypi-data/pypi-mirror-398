"""AutoViz module."""
import math
import time
import types
from typing import Any, Dict, List, Optional
from typing import Sequence
from typing import TYPE_CHECKING

from driverlessai import _commons
from driverlessai import _core
from driverlessai import _datasets
from driverlessai import _logging
from driverlessai import _utils

if TYPE_CHECKING:
    import fsspec  # noqa F401


class AutoViz:
    """
    Interact with dataset
    [visualizations](https://docs.h2o.ai/driverless-ai/1-10-lts/docs/userguide/autoviz.html)
    in the Driverless AI server.
    """

    def __init__(self, client: "_core.Client") -> None:
        self._client = client
        self._patch_autoviz_client(self._client._backend.autoviz)

    @staticmethod
    def _patch_autoviz_client(autoviz_client: Any) -> None:
        # Patch AutovizClient._wait_for_job to return the whole job object.
        def _wait_for_job(self, key: str) -> dict:  # type: ignore
            """Long polling to wait for async job to finish"""
            while True:
                job = self.client.get_vega_plot_job(key=key)
                if job.status >= 0:  # done
                    if job.status > 0:  # canceled or failed
                        raise RuntimeError(
                            self.client._format_server_error(message=job.error)
                        )
                    return job  # return the whole job object
                time.sleep(1)

        autoviz_client._wait_for_job = types.MethodType(_wait_for_job, autoviz_client)

    def create(self, dataset: _datasets.Dataset) -> "Visualization":
        """Creates a dataset visualization.

        Args:
            dataset: The dataset to be visualized.

        Returns:
            Created visualization.
        """
        return self.create_async(dataset).result()

    def create_async(self, dataset: _datasets.Dataset) -> "VisualizationJob":
        """Launches the creation of a dataset visualization.

        Args:
            dataset: The dataset to be visualized.

        Returns:
            Started visualization job.
        """
        key = self._client._backend.get_autoviz(
            dataset_key=dataset.key, maximum_number_of_plots=50
        )
        return VisualizationJob(self._client, key)

    def get(self, key: str) -> "Visualization":
        """
        Retrieves a dataset visualization in the Driverless AI server.

        Args:
            key: The unique ID of the visualization.

        Returns:
            The visualization corresponding to the key.
        """
        return Visualization(self._client, key)

    def gui(self) -> _utils.Hyperlink:
        """
        Returns the full URL to the AutoViz page in the Driverless AI server.

        Returns:
            The full URL to the AutoViz page.
        """
        return _utils.Hyperlink(
            f"{self._client.server.address}{self._client._gui_sep}visualizations"
        )

    def list(
        self, start_index: int = 0, count: int = None
    ) -> Sequence["Visualization"]:
        """Retrieves dataset visualizations in the Driverless AI server.

        Args:
            start_index: The index of the first visualization to retrieve.
            count: The maximum number of visualizations to retrieve.
                If `None`, retrieves all available visualizations.

        Returns:
            Dataset visualizations.
        """
        if count:
            data = self._client._backend.list_visualizations(
                offset=start_index, limit=count
            ).items
        else:
            page_size = 100
            page_position = start_index
            data = []
            while True:
                page = self._client._backend.list_visualizations(
                    offset=page_position, limit=page_size
                ).items
                data += page
                if len(page) < page_size:
                    break
                page_position += page_size
        return _commons.ServerObjectList(
            data=data, get_method=self.get, item_class_name=Visualization.__name__
        )

    @_utils.beta
    def get_by_name(self, name: str) -> Optional["Visualization"]:
        """
        Retrieves a dataset visualization by its display name from
        the Driverless AI server.

        Args:
            name: Name of the visualization.

        Returns:
            The visualization with the specified name if it exists, otherwise `None`.
        """
        sort_query = self._client._server_module.messages.EntitySortQuery("", "", "")
        template = f'"display_name": "{name}"'
        data = self._client._backend.search_and_sort_visualizations(
            search_query=template,
            sort_query=sort_query,
            ascending=False,
            offset=0,
            limit=1,
        ).items
        if data:
            return Visualization(self._client, data[0].key)
        else:
            return None


class CustomPlot(_commons.ServerObject):
    """A custom plot added to a dataset visualization in the Driverless AI server."""

    def __init__(self, client: "_core.Client", raw_info: Any) -> None:
        super().__init__(client=client, key=raw_info.key)
        self._set_raw_info(raw_info)
        self._set_name(raw_info.description)
        self._visualization_key = raw_info.dataset.key

    @property
    def plot_data(self) -> Dict[str, Any]:
        """
        Plot data of the custom plot.

        Returns:
            The plot in [Vega Lite (v3)](https://vega.github.io/vega-lite-v3/) format.
        """
        return self._get_raw_info().entity

    def _update(self) -> None:
        self._set_raw_info(self._client._backend.get_vega_plot_job(key=self.key))
        self._set_name(self._get_raw_info().description)


class PlotJob(_commons.ServerJob):
    """
    Monitor the creation of a plot in a dataset visualization
    in the Driverless AI server.
    """

    def __init__(
        self, client: "_core.Client", key: str, job_retrieve_function_name: str
    ) -> None:
        super().__init__(client=client, key=key)
        if not hasattr(self._client._backend, job_retrieve_function_name):
            raise ValueError(f"Cannot find '{job_retrieve_function_name}' API.")
        self._job_retrieve_function_name = job_retrieve_function_name

    def _update(self) -> None:
        job_retrieve_function = getattr(
            self._client._backend, self._job_retrieve_function_name
        )
        if job_retrieve_function:
            self._set_raw_info(job_retrieve_function(self.key))

    def result(self, silent: bool = False) -> Any:
        """Awaits the job's completion before returning the created plot.

        Args:
            silent: Whether to display status updates or not.

        Returns:
            Created plot by the job.
        """
        self._wait(silent)
        return self._get_raw_info()


class Visualization(_commons.ServerObject):
    """A dataset visualization in the Driverless AI server."""

    def __init__(self, client: "_core.Client", key: str) -> None:
        super().__init__(client=client, key=key)
        self._box_plots: Optional[Dict[str, List[Dict[str, Any]]]] = None
        self._dataset: Optional[_datasets.Dataset] = None
        self._custom_plots: Optional[List[CustomPlot]] = None
        self._log: Optional[VisualizationLog] = None
        self._outliers: List[Dict[str, Any]] = []

    @property
    def box_plots(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Disparate box plots and heteroscedastic box plots of the visualization.

        Returns:
            A dictionary with two keys, `disparate` and `heteroscedastic`,
                each containing a list of plots in
                [Vega Lite (v3)](https://vega.github.io/vega-lite-v3/) format.
        """
        if not self._box_plots:
            plots_info = self._get_raw_info().entity.boxplots
            self._box_plots = {
                "disparate": [
                    self._get_vega_grouped_boxplot(vn, gvn, False).entity
                    for gvn, vn in _utils.get_or_default(plots_info, "disparate", [])
                ],
                "heteroscedastic": [
                    self._get_vega_grouped_boxplot(vn, gvn, False).entity
                    for gvn, vn in _utils.get_or_default(
                        plots_info, "heteroscedastic", []
                    )
                ],
            }
        return self._box_plots

    @property
    def custom_plots(self) -> List[CustomPlot]:
        """Custom plots added to the visualization."""
        if not self._custom_plots:
            self._update()
        return self._custom_plots

    @property
    def dataset(self) -> _datasets.Dataset:
        """Visualized dataset."""
        if self._dataset is None:
            try:
                self._dataset = self._client.datasets.get(self._get_dataset_key())
            except self._client._server_module.protocol.RemoteError:
                # assuming a key error means deleted dataset, if not the error
                # will still propagate to the user else where
                self._dataset = self._get_raw_info().dataset.dump()
        return self._dataset

    @property
    def heatmaps(self) -> Dict[str, Dict[str, Any]]:
        """
        Data heatmap and Missing values heatmap of the visualization.

        Returns:
            A dictionary with two keys, `data_heatmap` and `missing_values_heatmap`,
                each containing a plot in
                [Vega Lite (v3)](https://vega.github.io/vega-lite-v3/) format.
        """
        projected_cols = [
            col for col in self._get_stats().column_names if col != "missing_count"
        ]

        # data heatmap
        data_heatmap_key = self._client._backend.get_heatmap(
            key=self.dataset.key,
            variable_names=projected_cols,
            matrix_type="rectangular",
            normalize=True,
            permute=True,
            missing=False,
        )
        meta_data = (
            PlotJob(self._client, data_heatmap_key, "get_heatmap_job").result().entity
        )
        data_points = self._get_heatmap_data(meta_data, "data_heatmap")

        data_heatmap = self._get_vega_heatmap(
            data=data_points, plot_name="Data Heatmap"
        )

        # missing values heatmap
        missing_heatmap_key = self._client._backend.get_heatmap(
            key=self.dataset.key,
            variable_names=projected_cols,
            matrix_type="rectangular",
            normalize=True,
            permute=True,
            missing=True,
        )
        meta_data = (
            PlotJob(self._client, missing_heatmap_key, "get_heatmap_job")
            .result()
            .entity
        )
        data_points = self._get_heatmap_data(meta_data, "missing_values_heatmap")

        missing_values_heatmap = self._get_vega_heatmap(
            data=data_points, plot_name="Missing Heatmap"
        )

        return {
            "data_heatmap": data_heatmap,
            "missing_values_heatmap": missing_values_heatmap,
        }

    @property
    def histograms(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Spikes, skewed, and gaps histograms of the visualization.

        Returns:
            A dictionary with three keys, `spikes`, `skewed`, and `gaps`,
                each containing a list of plots in
                [Vega Lite (v3)](https://vega.github.io/vega-lite-v3/) format.
        """
        histograms_info = self._get_raw_info().entity.histograms
        categorized_plots = {
            "spikes": [
                self._get_vega_histogram(col, 0, "none", "bar").entity
                for col in _utils.get_or_default(histograms_info, "spikes", [])
            ],
            "skewed": [
                self._get_vega_histogram(col, 0, "none", "bar").entity
                for col in _utils.get_or_default(histograms_info, "skewed", [])
            ],
            "gaps": [
                self._get_vega_histogram(col, 0, "none", "bar").entity
                for col in _utils.get_or_default(histograms_info, "gaps", [])
            ],
        }
        return categorized_plots

    @property
    def is_deprecated(self) -> bool:
        """
        Whether the visualization was created by an older Driverless AI server version
        and no longer fully compatible with the current server version.

        Returns:
            `True` if not compatible, otherwise `False`.
        """
        return self._get_raw_info().deprecated

    @property
    def outliers(self) -> List[Dict[str, Any]]:
        """
        Outlier plots of the visualization.

        Returns:
            Outlier plots in [Vega Lite (v3)](https://vega.github.io/vega-lite-v3/)
                format.
        """
        if not self._outliers:

            # compute outlier plot for each feature
            for feature in self._get_raw_info().entity.outliers.keys():
                job_key = self._client._backend.get_dotplot(
                    key=self.dataset.key, variable_name=feature, digits=3
                )
                meta_data = (
                    PlotJob(self._client, job_key, "get_dotplot_job").result().entity
                )

                histogram_data = meta_data.histogram
                x_min = histogram_data.scale_min
                x_max = histogram_data.scale_max
                bar_size = (x_max - x_min) / histogram_data.number_of_bars
                plot_data = [
                    {
                        "bin_start": x_min + bar_size * index,
                        "bin_end": x_min + bar_size * (index + 1),
                        "y_value": count,
                        "opacity": 1,
                    }
                    for index, count in enumerate(histogram_data.counts)
                ]

                var_outliers = [
                    index
                    for index_array in meta_data.outliers.row_indices
                    for index in index_array
                ]
                stacks_with_outliers = []
                for stack in meta_data.stacks:
                    if isinstance(stack, list):
                        stacks_with_outliers.append(
                            any(map(lambda item: item in var_outliers, stack))
                        )
                    else:
                        stacks_with_outliers.append(stack in var_outliers)
                outliers_x_values = [
                    x_value
                    for index, x_value in enumerate(meta_data.x_values)
                    if stacks_with_outliers[index]
                ]
                outliers_x_coordinates = [
                    (x_value * (x_max - x_min) + x_min) for x_value in outliers_x_values
                ]

                # Hide columns that overlaps with outlier markers.
                for x_value in outliers_x_coordinates:
                    overlapping_column_index = math.floor((x_value - x_min) / bar_size)
                    plot_data[overlapping_column_index]["opacity"] = 0

                self._outliers.append(
                    self._get_vega_outlier_plot(
                        width=580,
                        height=300,
                        data=plot_data,
                        outlier_x_coordinates=outliers_x_coordinates,
                        feature_name=feature,
                    )
                )

        return self._outliers

    @property
    def parallel_coordinates_plot(self) -> Dict[str, Any]:
        """
        Parallel coordinates plot of the visualization.

        Returns:
            Parallel coordinates plot in
                [Vega Lite (v3)](https://vega.github.io/vega-lite-v3/) format.
        """
        column_names = self._get_stats().column_names
        return self._get_vega_parallel_coordinates_plot(
            column_names,
            False,
            False,
            False,
        ).entity

    @property
    def recommendations(self) -> Optional[Dict[str, Dict[str, str]]]:
        """
        Recommended feature transformations and deletions based on the
        visualization analysis.

        Returns:
            A dictionary with two keys, `transforms` and `deletions`,
                each containing a dictionary of recommended actions for features.
                Or `None` if no recommendations are present.
        """
        recommendations_info = _utils.get_or_default(
            self._get_raw_info().entity, "transformations", None
        )
        if recommendations_info is None:
            return None
        return {
            "transforms": _utils.get_or_default(recommendations_info, "transforms", {}),
            "deletions": _utils.get_or_default(recommendations_info, "deletions", {}),
        }

    @property
    def scatter_plot(self) -> Optional[Dict[str, Any]]:
        """
        Scatter plot of the visualization.

        Returns:
            Scatter plot in [Vega Lite (v3)](https://vega.github.io/vega-lite-v3/)
                format if correlated features exist, otherwise `None`.
        """
        scatter_plot_info = self._get_raw_info().entity.scatterplots
        if scatter_plot_info.correlated and len(scatter_plot_info.correlated) > 0:
            return self._get_vega_scatter_plot(
                scatter_plot_info.correlated[0][0],
                scatter_plot_info.correlated[0][1],
                "point",
            ).entity

        return None

    @property
    def log(self) -> "VisualizationLog":
        """
        Log file associated with the visualization.

        Returns:
            Log of the visualization.
        """
        if not self._log:
            self._log = VisualizationLog(self._client, self.key)
        return self._log

    def __repr__(self) -> str:
        return f"<class '{self.__class__.__name__}'> {self.key} {self.name}"

    def __str__(self) -> str:
        return f"{self.name} ({self.key})"

    def _add_custom_plot(self, vega_plot_job: Any) -> CustomPlot:
        custom_plot = CustomPlot(self._client, vega_plot_job)
        self._client._backend.add_autoviz_custom_plot(
            autoviz_key=self.key, vega_plot_key=custom_plot.key
        )
        self._custom_plots = None  # next time we will fetch all from the server
        return custom_plot

    def _get_dataset_key(self) -> str:
        return self._get_raw_info().dataset.key

    def _get_heatmap_data(self, meta_data: Any, plot_type: str) -> List[Dict[str, Any]]:
        # columns
        num_of_bins = 60  # make 60 bins to simulate the UI behaviour
        chunk_size = meta_data.number_of_rows / num_of_bins
        if plot_type == "missing_values_heatmap":
            chunk_size = (
                chunk_size if math.floor(chunk_size) == 0 else math.floor(chunk_size)
            )
        grouped_columns = []
        for col in meta_data.columns:
            groups: Dict[str, List[float]] = {}
            for _id, c in enumerate(col):
                key = str(math.floor(_id / chunk_size))
                if c is None:
                    c = 0
                if key in groups:
                    groups[key].append(c)
                else:
                    groups[key] = [c]
            grouped_columns.append([max(group) for key, group in groups.items()])

        # counts
        grouped_counts = []
        groups = {}
        for _id, count in enumerate(meta_data.counts):
            key = str(math.floor(_id / chunk_size))
            if key in groups:
                groups[key].append(count)
            else:
                groups[key] = [count]
            grouped_counts = [sum(group) for key, group in groups.items()]

        # create the data objects for plotting
        data = []
        for _id, col in enumerate(meta_data.column_names):
            for __id, value in enumerate(grouped_columns[_id]):
                data.append(
                    {
                        "id": __id,
                        "column_name": col,
                        "value": value,
                        "count": grouped_counts[__id],
                    }
                )

        return data

    def _get_stats(self) -> "VisualizationStats":
        key = self._client._backend.get_vis_stats(dataset_key=self._get_dataset_key())
        return VisualizationStatsJob(self._client, key).result()

    def _get_vega_grouped_boxplot(
        self, variable_name: str, group_variable_name: str, transpose: bool
    ) -> Any:
        return self._client._backend.autoviz.get_boxplot(
            dataset_key=self._get_dataset_key(),
            variable_name=variable_name,
            group_variable_name=group_variable_name,
            transpose=transpose,
        )

    @staticmethod
    def _get_vega_heatmap(data: list, plot_name: str) -> Dict[str, Any]:
        return {
            "schema": "https://vega.github.io/schema/vega-lite/v3.json",
            "title": plot_name,
            "width": 600,
            "height": 600,
            "data": {"values": data},
            "mark": "rect",
            "encoding": {
                "x": {"field": "id", "type": "nominal", "axis": False},
                "y": {
                    "field": "column_name",
                    "type": "ordinal",
                    "title": False,
                    "sort": None,
                },
                "color": {"field": "value", "type": "quantitative", "legend": None},
                "stroke": {"value": "black"},
                "strokeWidth": {"value": 0.02},
                "tooltip": [
                    {"field": "count", "type": "quantitative", "title": "Counts"}
                ],
            },
        }

    def _get_vega_histogram(
        self, variable_name: str, number_of_bars: int, transformation: str, mark: str
    ) -> Any:
        return self._client._backend.autoviz.get_histogram(
            dataset_key=self._get_dataset_key(),
            variable_name=variable_name,
            number_of_bars=number_of_bars,
            transformation=transformation,
            mark=mark,
        )

    def _get_vega_parallel_coordinates_plot(
        self, variable_names: List[str], permute: bool, transpose: bool, cluster: bool
    ) -> Any:
        return self._client._backend.autoviz.get_parallel_coordinates_plot(
            dataset_key=self._get_dataset_key(),
            variable_names=variable_names,
            permute=permute,
            transpose=transpose,
            cluster=cluster,
        )

    @staticmethod
    def _get_vega_outlier_plot(
        width: int,
        height: int,
        data: Any,
        outlier_x_coordinates: list,
        feature_name: str,
    ) -> Dict[str, Any]:
        return {
            "schema": "https://vega.github.io/schema/vega-lite/v3.json",
            "width": width,
            "height": height,
            "title": "Outliers Plot",
            "layer": [
                {
                    "data": {"values": data},
                    "mark": "bar",
                    "encoding": {
                        "x": {
                            "field": "bin_start",
                            "bin": {"binned": True},
                            "title": feature_name,
                        },
                        "x2": {"field": "bin_end"},
                        "y": {
                            "field": "y_value",
                            "type": "quantitative",
                            "axis": False,
                        },
                        "color": {
                            "field": "opacity",
                            "type": "quantitative",
                            "condition": {
                                "value": "transparent",
                                "test": "datum.opacity === 0",
                            },
                            "legend": None,
                        },
                    },
                },
                {
                    "data": {
                        "values": [
                            {"x": point, "y": 0} for point in outlier_x_coordinates
                        ]
                    },
                    "mark": {"type": "circle", "color": "red"},
                    "encoding": {
                        "x": {"field": "x", "type": "quantitative"},
                        "y": {"field": "y", "type": "quantitative", "axis": None},
                    },
                },
            ],
        }

    def _get_vega_scatter_plot(
        self, x_variable_name: str, y_variable_name: str, mark: str
    ) -> Any:
        return self._client._backend.autoviz.get_scatterplot(
            dataset_key=self._get_dataset_key(),
            x_variable_name=x_variable_name,
            y_variable_name=y_variable_name,
            mark=mark,
        )

    def _set_custom_plots(self, custom_plots: List[Any]) -> None:
        self._custom_plots = [
            CustomPlot(self._client, plot_info) for plot_info in custom_plots
        ]

    def _update(self) -> None:
        self._set_raw_info(self._client._backend.get_autoviz_job(key=self.key))
        self._set_custom_plots(
            _utils.get_or_default(self._get_raw_info().entity, "custom_plots", [])
        )
        self._set_name(self._get_raw_info().name)

    def add_bar_chart(
        self,
        x_variable_name: str,
        y_variable_name: str = "",
        transpose: bool = False,
        mark: str = "bar",
    ) -> CustomPlot:
        """
        Adds a custom bar chart to the visualization.

        Args:
            x_variable_name: Column for the X axis.
            y_variable_name: Column for the Y axis.
                If omitted then the number of occurrences is considered.
            transpose: Whether to flip axes or not.
            mark: The type of mark to use in the chart. Accepts `bar` for a standard
                bar chart or `point` for a [Cleveland dot plot](https://w.wiki/8Thn).

        Returns:
            Added custom bar chart.
        """

        vega_plot_job = self._client._backend.autoviz.get_bar_chart(
            dataset_key=self._get_dataset_key(),
            x_variable_name=x_variable_name,
            y_variable_name=y_variable_name,
            transpose=transpose,
            mark=mark,
        )
        return self._add_custom_plot(vega_plot_job)

    def add_box_plot(self, variable_name: str, transpose: bool = False) -> CustomPlot:
        """
        Adds a custom box plot to the visualization.

        Args:
            variable_name: The column for the plot.
            transpose: Whether to flip axes or not.

        Returns:
            Added custom box plot.
        """

        kwargs = dict(variable_name=variable_name, transpose=transpose)
        job_key = self._client._backend.get_1d_vega_plot(
            dataset_key=self._get_dataset_key(),
            plot_type="boxplot",
            x_variable_name=variable_name,
            kwargs=kwargs,
        )
        vega_plot_job = self._client._backend.autoviz._wait_for_job(key=job_key)
        return self._add_custom_plot(vega_plot_job)

    def add_dot_plot(self, variable_name: str, mark: str = "point") -> CustomPlot:
        """
        Adds a custom dot plot to the visualization.

        Args:
            variable_name: The column for the plot.
            mark: The type of mark to represent each data point in the plot.
                Accepts `point`, `square`, or `bar`.

        Returns:
            Added custom dot plot.
        """

        vega_plot_job = self._client._backend.autoviz.get_dotplot(
            dataset_key=self._get_dataset_key(), variable_name=variable_name, mark=mark
        )
        return self._add_custom_plot(vega_plot_job)

    def add_grouped_box_plot(
        self, variable_name: str, group_variable_name: str, transpose: bool = False
    ) -> CustomPlot:
        """
        Adds a custom grouped box plot to the visualization.

        Args:
            variable_name: The column for the plot.
            group_variable_name: The grouping column.
            transpose: Whether to flip axes or not.

        Returns:
            Added custom grouped box plot.
        """

        vega_plot_job = self._get_vega_grouped_boxplot(
            variable_name, group_variable_name, transpose
        )
        return self._add_custom_plot(vega_plot_job)

    def add_heatmap(
        self,
        variable_names: Optional[List[str]] = None,
        permute: bool = False,
        transpose: bool = False,
        matrix_type: str = "rectangular",
    ) -> CustomPlot:
        """
        Adds a custom heatmap to the visualization.

        Args:
            variable_names: Columns for the Heatmap,
                if omitted then all columns are used.
            permute: Whether to permute rows and columns using
                [singular value decomposition (SVD)](https://w.wiki/3poQ) or not.
            transpose: Whether to flip axes or not.
            matrix_type: The type of matrix to be used.
                Possible values are `rectangular` or `symmetric`.

        Returns:
            Added custom heatmap.
        """

        vega_plot_job = self._client._backend.autoviz.get_heatmap(
            dataset_key=self._get_dataset_key(),
            variable_names=variable_names or [],
            permute=permute,
            transpose=transpose,
            matrix_type=matrix_type,
        )
        return self._add_custom_plot(vega_plot_job)

    def add_histogram(
        self,
        variable_name: str,
        number_of_bars: int = 0,
        transformation: str = "none",
        mark: str = "bar",
    ) -> CustomPlot:
        """
        Adds a custom histogram to the visualization.

        Args:
            variable_name: Column for the histogram.
            number_of_bars: Number of bars in the histogram. If set to `0`,
                the number of bars is automatically determined
            transformation: A transformation applied to the column.
                Possible values are `none`, `log` or `square_root`.
            mark: The type of mark to use in the histogram.
                Accepts `bar` for a standard histogram or `area` for a density polygon.

        Returns:
            Added custom histogram.
        """

        vega_plot_job = self._get_vega_histogram(
            variable_name, number_of_bars, transformation, mark
        )
        return self._add_custom_plot(vega_plot_job)

    def add_linear_regression(
        self,
        x_variable_name: str,
        y_variable_name: str,
        mark: str = "point",
    ) -> CustomPlot:
        """
        Adds a custom linear regression to the visualization.

        Args:
            x_variable_name: Column for the X axis.
            y_variable_name: Column for the Y axis.
            mark: The type of mark to use in the plot. Accepts `point` or `square`.

        Returns:
            Added custom linear regression.
        """

        vega_plot_job = self._client._backend.autoviz.get_linear_regression(
            dataset_key=self._get_dataset_key(),
            x_variable_name=x_variable_name,
            y_variable_name=y_variable_name,
            mark=mark,
        )
        return self._add_custom_plot(vega_plot_job)

    def add_loess_regression(
        self,
        x_variable_name: str,
        y_variable_name: str,
        mark: str = "point",
        bandwidth: float = 0.5,
    ) -> CustomPlot:
        """
        Adds a custom loess regression to the visualization.

        Args:
            x_variable_name: Column for the X axis.
            y_variable_name: Column for the Y axis.
                If omitted then the number of occurrences is considered.
            mark: The type of mark to use in the plot. Accepts `point` or `square`.
            bandwidth: Interval denoting proportion of cases in smoothing window.

        Returns:
            Added custom loess regression.
        """

        vega_plot_job = self._client._backend.autoviz.get_loess_regression(
            dataset_key=self._get_dataset_key(),
            x_variable_name=x_variable_name,
            y_variable_name=y_variable_name,
            mark=mark,
            bandwidth=bandwidth,
        )
        return self._add_custom_plot(vega_plot_job)

    def add_parallel_coordinates_plot(
        self,
        variable_names: List[str] = None,
        permute: bool = False,
        transpose: bool = False,
        cluster: bool = False,
    ) -> CustomPlot:
        """
        Adds a custom parallel coordinates plot to the visualization.

        Args:
            variable_names: Columns for the plot,
                if omitted then all columns will be used.
            permute:  Whether to permute rows and columns using
                [singular value decomposition (SVD)](https://w.wiki/3poQ) or not.
            transpose: Whether to flip axes or not.
            cluster: Set to `True` to k-means cluster variables and
                color the plot by cluster IDs.

        Returns:
            Added custom parallel coordinates plot.
        """

        vega_plot_job = self._get_vega_parallel_coordinates_plot(
            variable_names or [],
            permute,
            transpose,
            cluster,
        )
        return self._add_custom_plot(vega_plot_job)

    def add_probability_plot(
        self,
        x_variable_name: str,
        distribution: str = "normal",
        mark: str = "point",
        transpose: bool = False,
    ) -> CustomPlot:
        """
        Adds a custom probability plot to the visualization.

        Args:
            x_variable_name: Column for the X axis.
            distribution: Type of distribution. Accepts `normal` or `uniform`.
            mark: The type of mark to use in the plot. Accepts `point` or `square`.
            transpose: Whether to flip axes or not.

        Returns:
            Added custom probability plot.
        """

        kwargs = dict(
            x_variable_name=x_variable_name,
            subtype="probability_plot",
            distribution=distribution,
            mark=mark,
            transpose=transpose,
        )
        job_key = self._client._backend.get_1d_vega_plot(
            dataset_key=self._get_dataset_key(),
            plot_type="probability_plot",
            x_variable_name=x_variable_name,
            kwargs=kwargs,
        )
        vega_plot_job = self._client._backend.autoviz._wait_for_job(key=job_key)
        return self._add_custom_plot(vega_plot_job)

    def add_quantile_plot(
        self,
        x_variable_name: str,
        y_variable_name: str,
        distribution: str = "normal",
        mark: str = "point",
        transpose: bool = False,
    ) -> CustomPlot:
        """
        Adds a custom quantile plot to the visualization.

        Args:
            x_variable_name: Column for the X axis.
            y_variable_name: Column for the Y axis.
            distribution: Type of distribution. Accepts `normal` or `uniform`.
            mark: The type of mark to use in the plot. Accepts `point` or `square`.
            transpose: Whether to flip axes or not.

        Returns:
            Added custom quantile plot.
        """

        kwargs = dict(
            x_variable_name=x_variable_name,
            y_variable_name=y_variable_name,
            subtype="quantile_plot",
            distribution=distribution,
            mark=mark,
            transpose=transpose,
        )
        job_key = self._client._backend.get_2d_vega_plot(
            dataset_key=self._get_dataset_key(),
            plot_type="quantile_plot",
            x_variable_name=x_variable_name,
            y_variable_name=y_variable_name,
            kwargs=kwargs,
        )
        vega_plot_job = self._client._backend.autoviz._wait_for_job(key=job_key)
        return self._add_custom_plot(vega_plot_job)

    def add_scatter_plot(
        self,
        x_variable_name: str,
        y_variable_name: str,
        mark: str = "point",
    ) -> CustomPlot:
        """
        Adds a custom scatter plot to the visualization.

        Args:
            x_variable_name: Column for the X axis.
            y_variable_name: Column for the Y axis.
                If omitted then the number of occurrences is considered.
            mark: The type of mark to use in the plot. Accepts `point` or `square`.

        Returns:
            Added custom scatter plot.
        """

        vega_plot_job = self._get_vega_scatter_plot(
            x_variable_name, y_variable_name, mark
        )
        return self._add_custom_plot(vega_plot_job)

    def delete(self) -> None:
        """Permanently deletes the visualization from the Driverless AI server."""
        key = self.key
        self._client._backend.delete_autoviz_job(key=key)
        _logging.logger.info(
            f"Driverless AI Server reported visualization {key} deleted."
        )

    def gui(self) -> _utils.Hyperlink:
        """
        Returns the full URL to the visualization's page in the Driverless AI server.

        Returns:
            URL to the visualization page.
        """
        return _utils.Hyperlink(
            f"{self._client.server.address}{self._client._gui_sep}"
            f"auto_viz?&datasetKey={self._get_dataset_key()}"
            f"&dataset_name={self._get_raw_info().dataset.display_name}"
        )

    def remove_custom_plot(self, custom_plot: CustomPlot) -> None:
        """
        Removes a previously added custom plot from the visualization.

        Args:
            custom_plot: Custom plot to be removed & deleted.
        """

        if self.key != custom_plot._visualization_key:
            raise ValueError(
                f"Custom plot {custom_plot} does not belong to this visualization."
            )

        self._client._backend.remove_autoviz_custom_plot(
            autoviz_key=self.key, vega_plot_key=custom_plot.key
        )
        self._custom_plots = None  # next time we will fetch all from the server


class VisualizationLog(_commons.ServerLog):
    """The AutoViz log file in the Driverless AI server."""

    def __init__(self, client: "_core.Client", key: str) -> None:
        file_path = key + "/dataset/vis-data-server.log"
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


class VisualizationJob(_commons.ServerJob):
    """Monitor the creation of a dataset visualization in the Driverless AI server."""

    def __init__(self, client: "_core.Client", key: str) -> None:
        super().__init__(client=client, key=key)

    def _update(self) -> None:
        self._set_raw_info(self._client._backend.get_autoviz_job(key=self.key))

    def result(self, silent: bool = False) -> Visualization:
        """Awaits the job's completion before returning the created visualization.

        Args:
            silent: Whether to display status updates or not.

        Returns:
            Created visualization by the job.
        """
        self._wait(silent)
        return Visualization(self._client, self.key)


class VisualizationStats(_commons.ServerObject):
    """A dataset visualization stats in the Driverless AI server."""

    def __init__(self, client: "_core.Client", key: str, raw_info: Any) -> None:
        super().__init__(client=client, key=key)
        self._set_raw_info(raw_info)

    @property
    def column_names(self) -> List[str]:
        """Column names of the visualization."""
        column_names = self._get_raw_info().entity.column_names
        return [name for name in column_names if name != "members_count"]

    def _update(self) -> None:
        self._set_raw_info(self._client._backend.get_autoviz_job(key=self.key))


class VisualizationStatsJob(_commons.ServerJob):
    """
    Monitor the creation of a dataset visualization stats in the Driverless AI server.
    """

    def __init__(self, client: "_core.Client", key: str) -> None:
        super().__init__(client=client, key=key)

    def _update(self) -> None:
        self._set_raw_info(self._client._backend.get_vis_stats_job(key=self.key))

    def result(self, silent: bool = False) -> VisualizationStats:
        """Awaits the job's completion before returning the created visualization stats.

        Args:
            silent: Whether to display status updates or not.

        Returns:
            Created visualization stats by the job.
        """
        self._wait(silent)
        return VisualizationStats(self._client, self.key, self._get_raw_info())
