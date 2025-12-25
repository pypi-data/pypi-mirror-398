"""Common metric plots module."""

import math
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from driverlessai import _core

if TYPE_CHECKING:
    import fsspec  # noqa F401


class CommonMetricPlots(ABC):
    """
    Interact with metric plots of an experiment or a model diagnostic
    in the Driverless AI server.
    """

    def __init__(
        self,
        client: "_core.Client",
        key: str,
        is_classification: bool,
    ) -> None:
        self._client = client
        self._key = key
        self._is_classification = is_classification

    def _make_detailed_confusion_matrix(self, cm: Any) -> Dict[str, Any]:
        result = {
            "tp": cm.matrix[0][0],
            "fp": cm.matrix[0][1],
            "tn": cm.matrix[1][1],
            "fn": cm.matrix[1][0],
        }
        result["prec"] = result["tp"] / (result["tp"] + result["fp"])
        result["recall"] = result["tp"] / (result["tp"] + result["fn"])
        result["tpr"] = result["tp"] / (result["tp"] + result["fn"])
        result["fpr"] = result["fp"] / (result["fp"] + result["tn"])

        return result

    def _calculate_f1_mcc_acc(
        self,
        matrix: Dict[str, Any],
        coordinate: Dict[str, Any],
        scorers: Dict[str, Any],
        scorer_points: Dict[str, Any],
    ) -> List[Dict[str, Any]]:

        f1 = self._f_score(1, matrix["prec"], matrix["recall"])

        if f1 > scorers["best_f1"]:
            scorers["best_f1"] = f1
            scorer_points["best_f1_dot"] = coordinate.copy()
            scorer_points["best_f1_dot"]["label"] = "Best F1"

        try:
            mcc = (
                matrix["tp"] * matrix["tn"] - matrix["fp"] * matrix["fn"]
            ) / math.sqrt(
                (matrix["tp"] + matrix["fp"])
                * (matrix["fn"] + matrix["tn"])
                * (matrix["fp"] + matrix["tn"])
                * (matrix["tp"] + matrix["fn"])
            )
        except ZeroDivisionError:
            mcc = float("nan")

        if mcc > scorers["best_mcc"]:
            scorers["best_mcc"] = mcc
            scorer_points["best_mcc_dot"] = coordinate.copy()
            scorer_points["best_mcc_dot"]["label"] = "Best MCC"

        accuracy = (matrix["tp"] + matrix["tn"]) / (
            matrix["tp"] + matrix["tn"] + matrix["fp"] + matrix["fn"]
        )

        if accuracy > scorers["best_acc"]:
            scorers["best_acc"] = accuracy
            scorer_points["best_acc_dot"] = coordinate.copy()
            scorer_points["best_acc_dot"]["label"] = "Best ACC"

        return [scorers, scorer_points]

    def _f_score(self, beta: float, prec: float, recall: float) -> float:
        try:
            return ((1 + beta * beta) * (prec * recall)) / (beta * beta * prec + recall)
        except ZeroDivisionError:
            return float("nan")

    def _get_single_layer_vega_plot(
        self,
        name: str,
        data: list,
        x_axis: str,
        y_axis: str,
        marks: list,
    ) -> Dict[str, Any]:
        """Plot in Vega Lite (v3) format.

        Args:
            name: name of the plot
            data: a list of coordinates of the plots
            x_axis: a common x-axis
            y_axis: a common y-axis
            marks: a list of marks for the plots
        """

        plot_data: Dict[str, Any] = {
            "title": name,
            "schema": "https://vega.github.io/schema/vega-lite/v3.json",
            "data": {"values": data},
        }

        if name == "Residual Histogram":
            plot_data["mark"] = marks[0]
            plot_data["encoding"] = {
                "x": {"field": x_axis, "type": "nominal"},
                "y": {"field": y_axis, "type": "quantitative", "axis": ""},
                "tooltip": [
                    {"field": y_axis, "type": "nominal"},
                    {"field": "label", "type": "nominal", "title": "Residual"},
                ],
            }
        else:
            plot_data["mark"] = {"type": marks[0], "tooltip": {"content": "data"}}
            plot_data["encoding"] = {
                "x": {"field": x_axis, "type": "quantitative"},
                "y": {"field": y_axis, "type": "quantitative"},
            }

        return plot_data

    def _get_multi_layer_vega_plot(
        self,
        name: str,
        data: list,
        x_axis: str,
        y_axis: str,
        marks: list,
        enable_labels: bool,
    ) -> Dict[str, Any]:
        """Plot in Vega Lite (v3) format.

        Args:
            name: name of the plot
            data: a list of coordinates of the plots
            x_axis: a common x-axis
            y_axis: a common y-axis
            marks: a list of marks for the plots
            enable_labels: if labels are needed to mark special points
        """
        plot_data: Dict[str, Any] = {
            "title": name,
            "schema": "https://vega.github.io/schema/vega-lite/v3.json",
            "layer": [
                {
                    "data": {"values": data[i]},
                    "mark": marks[i],
                    "encoding": {
                        "x": {"field": x_axis, "type": "quantitative"},
                        "y": {"field": y_axis, "type": "quantitative"},
                    },
                }
                for i in range(len(data))
            ],
        }

        for i in range(len(data)):
            if data[i] and "x_label" in list(data[i][0].keys()):
                plot_data["layer"][i]["encoding"]["tooltip"] = [
                    {
                        "field": "x_label_value",
                        "type": "nominal",
                        "title": data[i][0]["x_label"],
                    },
                    {
                        "field": "y_label_value",
                        "type": "nominal",
                        "title": data[i][0]["y_label"],
                    },
                ]

        if enable_labels:
            plot_data["layer"][-1]["encoding"]["text"] = {
                "field": "label",
                "type": "nominal",
            }

        return plot_data

    @abstractmethod
    def _get_act_vs_pred_data(self) -> Any:
        raise NotImplementedError

    @abstractmethod
    def _get_gains(self) -> Any:
        raise NotImplementedError

    @abstractmethod
    def _get_roc_data(self) -> Any:
        raise NotImplementedError

    @abstractmethod
    def _get_residual_plot_data(self) -> Any:
        raise NotImplementedError

    @abstractmethod
    def _get_residual_loess_data(self) -> Any:
        raise NotImplementedError

    @property
    def actual_vs_predicted_chart(self) -> Optional[Dict[str, Any]]:
        """
        Actual vs predicted chart for the model.

        Returns:
            An actual vs predicted chart in
                [Vega Lite (v3)](https://vega.github.io/vega-lite-v3/) format,
                or `None` is the model is a classification model.
        """
        if self._is_classification:
            return None

        raw_info = self._get_act_vs_pred_data()

        x_values = raw_info.x_values
        y_values = raw_info.y_values
        values = [
            {"Predicted": x_values[point], "Actual": y_values[point]}
            for point in range(len(x_values))
        ]

        return self._get_single_layer_vega_plot(
            name="Actual vs predicted Chart",
            data=values,
            marks=["point"],
            x_axis="Predicted",
            y_axis="Actual",
        )

    @property
    def gains_chart(self) -> Optional[Dict[str, Any]]:
        """
        Cumulative gains chart for the model.

        Returns:
            A cumulative gains chart in
                [Vega Lite (v3)](https://vega.github.io/vega-lite-v3/) format,
                or `None` is the model is a classification model.
        """
        if not self._is_classification:
            return None

        raw_info = self._get_gains()

        gains = raw_info.gains
        quantiles = raw_info.quantiles
        values = [
            {
                "Quantile": quantiles[point],
                "Gains": gains[point],
                "x_label": "Quantile",
                "y_label": "Cumulative Gain",
                "x_label_value": f"{round(quantiles[point] * 100, 4)}%",
                "y_label_value": f"{round(gains[point] * 100, 4)}%",
            }
            for point in range(len(gains))
        ]

        return self._get_multi_layer_vega_plot(
            name="Cumulative Gain Chart",
            data=[values, values],
            marks=["line", "point"],
            x_axis="Quantile",
            y_axis="Gains",
            enable_labels=False,
        )

    @property
    def ks_chart(self) -> Optional[Dict[str, Any]]:
        """
        Kolmogorov-Smirnov chart of the model.

        Returns:
            A Kolmogorov-Smirnov chart in
                [Vega Lite (v3)](https://vega.github.io/vega-lite-v3/) format,
                or `None` if the model is not a classification model.
        """
        if not self._is_classification:
            return None

        raw_info = self._get_gains()

        cum_right = raw_info.cum_right
        cum_wrong = raw_info.cum_wrong
        max_cum_right = max(cum_right)
        max_cum_wrong = max(cum_wrong)
        rel_cum_rights = [
            0 if max_cum_right == 0 else x / max_cum_right for x in cum_right
        ]
        rel_cum_wrongs = [
            0 if max_cum_wrong == 0 else x / max_cum_wrong for x in cum_wrong
        ]
        quantiles = raw_info.quantiles
        points_rights = [
            {
                "Quantile": quantiles[point],
                "Gains": rel_cum_rights[point],
                "x_label": "Quantile",
                "y_label": "Kolmogorov-Smirnov",
                "x_label_value": f"{round(quantiles[point] * 100)}%",
                "y_label_value": round(
                    abs(rel_cum_rights[point] - rel_cum_wrongs[point]), 4
                ),
            }
            for point in range(len(rel_cum_rights))
        ]

        points_wrongs = [
            {
                "Quantile": quantiles[point],
                "Gains": rel_cum_wrongs[point],
                "x_label": "Quantile",
                "y_label": "Kolmogorov-Smirnov",
                "x_label_value": f"{round(quantiles[point] * 100)}%",
                "y_label_value": round(
                    abs(rel_cum_rights[point] - rel_cum_wrongs[point]), 4
                ),
            }
            for point in range(len(rel_cum_wrongs))
        ]

        return self._get_multi_layer_vega_plot(
            name="Kolmogorov-Smirnov Chart",
            data=[points_rights, points_wrongs, points_rights, points_wrongs],
            marks=["line", "line", "point", "point"],
            x_axis="Quantile",
            y_axis="Gains",
            enable_labels=False,
        )

    @property
    def lift_chart(self) -> Optional[Dict[str, Any]]:
        """
        Lift chart of the model.

        Returns:
            A lift chart in
                [Vega Lite (v3)](https://vega.github.io/vega-lite-v3/) format,
                or `None` is the model is a classification model.
        """
        if not self._is_classification:
            return None

        raw_info = self._get_gains()

        lifts = raw_info.lifts
        quantiles = raw_info.quantiles
        values = [
            {
                "Quantile": quantiles[point],
                "Lift": lifts[point],
                "x_label": "Quantile",
                "y_label": "Cumulative Lift",
                "x_label_value": f"{round(quantiles[point] * 100)}%",
                "y_label_value": round(lifts[point], 4),
            }
            for point in range(len(lifts))
        ]

        return self._get_multi_layer_vega_plot(
            name="Lift Chart",
            data=[values, values],
            marks=["line", "point"],
            x_axis="Quantile",
            y_axis="Lift",
            enable_labels=False,
        )

    @property
    def prec_recall_curve(self) -> Optional[Dict[str, Any]]:
        """
        Precision-recall curve of the model.

        Returns:
            A precision-recall curve in
                [Vega Lite (v3)](https://vega.github.io/vega-lite-v3/) format,
                or `None` is the model is a classification model.
        """
        if not self._is_classification:
            return None

        values = []
        scorers = {"best_f1": 0, "best_mcc": 0, "best_acc": 0}

        scorer_points = {
            "best_f1_dot": None,
            "best_mcc_dot": None,
            "best_acc_dot": None,
        }

        for confusion_matrix in self._get_roc_data().threshold_cms:
            matrix = self._make_detailed_confusion_matrix(confusion_matrix)
            coordinate = {
                "Recall": matrix["recall"],
                "Precision": matrix["prec"],
            }
            values.append(coordinate)

            scorers, scorer_points = self._calculate_f1_mcc_acc(
                matrix, coordinate, scorers, scorer_points
            )

        return self._get_multi_layer_vega_plot(
            name="Precision-Recall Curve",
            data=[values, list(scorer_points.values()), list(scorer_points.values())],
            marks=["line", "point", "text"],
            x_axis="Recall",
            y_axis="Precision",
            enable_labels=True,
        )

    @property
    def residual_plot(self) -> Optional[Dict[str, Any]]:
        """
        Residual plot with LOESS curve of the model.

        Returns:
            A residual plot in
                [Vega Lite (v3)](https://vega.github.io/vega-lite-v3/) format,
                or `None` is the model is a classification model.
        """
        if self._is_classification:
            return None

        residual_plot = self._get_residual_plot_data()
        residual_loess = self._get_residual_loess_data()
        plot_points = [
            {
                "Predicted": residual_plot.x_values[point],
                "Residual": residual_plot.y_values[point],
                "x_label": "Predicted",
                "y_label": "Residual",
                "x_label_value": residual_plot.x_values[point],
                "y_label_value": residual_plot.y_values[point],
            }
            for point in range(len(residual_plot.x_values))
        ]

        if residual_loess is not None:
            curve_points = [
                {
                    "Predicted": residual_loess.x_values[point],
                    "Residual": residual_loess.predicted_values[point],
                    "x_label": "Predicted",
                    "y_label": "Residual",
                    "x_label_value": residual_loess.x_values[point],
                    "y_label_value": residual_loess.predicted_values[point],
                }
                for point in range(len(residual_loess.x_values))
            ]

            return self._get_multi_layer_vega_plot(
                name="Residual Plot with LOESS Curve",
                data=[plot_points, curve_points],
                marks=["point", "line"],
                x_axis="Predicted",
                y_axis="Residual",
                enable_labels=False,
            )

        return self._get_single_layer_vega_plot(
            name="Residual Plot with LOESS Curve",
            data=plot_points,
            marks=["point"],
            x_axis="Predicted",
            y_axis="Residual",
        )

    @property
    def roc_curve(self) -> Optional[Dict[str, Any]]:
        """
        ROC curve of the model.

        Returns:
            A ROC curve in
                [Vega Lite (v3)](https://vega.github.io/vega-lite-v3/) format,
                or `None` is the model is a classification model
        """
        if not self._is_classification:
            return None

        values = []
        scorers = {"best_f1": 0, "best_mcc": 0, "best_acc": 0}

        scorer_points = {
            "best_f1_dot": None,
            "best_mcc_dot": None,
            "best_acc_dot": None,
        }

        for confusion_matrix in self._get_roc_data().threshold_cms:
            matrix = self._make_detailed_confusion_matrix(confusion_matrix)
            coordinate = {
                "False Positive Rate": matrix["fpr"],
                "True Positive Rate": matrix["tpr"],
            }
            values.append(coordinate)
            scorers, scorer_points = self._calculate_f1_mcc_acc(
                matrix, coordinate, scorers, scorer_points
            )

        return self._get_multi_layer_vega_plot(
            name="ROC Curve",
            data=[values, list(scorer_points.values()), list(scorer_points.values())],
            marks=["line", "point", "text"],
            x_axis="False Positive Rate",
            y_axis="True Positive Rate",
            enable_labels=True,
        )

    def confusion_matrix(self, threshold: float = None) -> Optional[List[List[Any]]]:
        """
        Confusion matrix of the model.

        Args:
            threshold: The threshold value.

        Returns:
            A confusion matrix as a 2D list,
                or `None` is the model is a classification model
        """
        if not self._is_classification:
            return None

        raw_info = self._get_roc_data()

        default_threshold = (
            raw_info.default_threshold
            if hasattr(raw_info, "default_threshold")
            else 0.5
        )
        labels = raw_info.argmax_cm.labels
        current_threshold = default_threshold if threshold is None else threshold

        data = raw_info.argmax_cm

        if current_threshold == threshold:
            diagnostic_id = self._client._backend.get_diagnostic_cm_for_threshold(
                diagnostic_key=self._key, threshold=current_threshold
            )
            data = self._client._backend.get_model_diagnostic_job(
                key=diagnostic_id
            ).entity.roc.argmax_cm

        # construct the matrix as a 2D-list along with the row and column headers
        result = [
            ["", labels[0], labels[1], "Total", "Error"],
            [labels[0]] + data.matrix[0],
            [labels[1]] + data.matrix[1],
            ["Total"] + data.col_counts + [sum(data.col_counts)],
            ["Error"]
            + [
                round((data.col_counts[i] - data.matrix[i][i]) / data.col_counts[i], 4)
                for i in range(len(data.col_counts))
            ]
            + [""]
            + [round(sum(data.miss_counts) / sum(data.row_counts), 4)],
        ]

        for row in result[1:3]:
            index = result.index(row) - 1
            row.append(data.row_counts[index])
            row.append(round(data.miss_counts[index] / data.row_counts[index], 4))

        return result
