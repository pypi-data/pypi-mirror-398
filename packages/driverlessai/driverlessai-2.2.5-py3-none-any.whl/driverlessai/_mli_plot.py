import abc
import collections
import enum
import json
import math
import os
from typing import Any
from typing import Dict
from typing import Iterator
from typing import List
from typing import Optional
from typing import Tuple
from typing import Type
from typing import Union

from driverlessai import _commons_mli
from driverlessai import _core
from driverlessai import _enums
from driverlessai import _utils


_KEY_DATA = "data"
_KEY_COLUMNS = "columns"
_KEY_COLUMN_NAME = "column_name"
_KEY_BIAS = "bias"
_KEY_LABEL = "label"
_KEY_VALUE = "value"
_KEY_VALUES = "values"
_KEY_SCOPE = "scope"
_KEY_FILES = "files"
_KEY_FILTERS = "filters"
_KEY_FEATURES = "features"
_KEY_FEATURE_TYPE = "feature_type"
_KEY_TYPE = "type"
_KEY_METRICS = "metrics"
_KEY_Y_AXIS_LABEL = "y_axis_label"
_KEY_X_AXIS_LABEL = "x_axis_label"
_SCOPE_GLOBAL = "global"
_SCOPE_LOCAL = "local"
_KEY_FEATURE_VALUE = "feature_value"
_CLASS_TF_IDF = "None (TF-IDF)"
_KEY_DEFAULT_CLASS = "default_class"
_FILTER_EXPLAIN_FEATURE = "explain_feature"
_FILTER_EXPLAIN_CLASS = "explain_class"
_FILTER_TEXT_FEATURE = "text_feature"
_KEY_PDP_NUM_HIST = "data_histogram_numerical"
_KEY_PDP_CAT_HIST = "data_histogram_categorical"
_KEY_PREDICTION = "prediction"
_KEY_ACTUAL = "actual"
_KEY_BIN = "bin"
_KEY_ICE = "ice"
_KEY_PD = "pd"
_KEY_SD = "sd"
_KEY_OOR = "oor"
_KEY_PDP_CAT_TYPE = "categorical"
_KEY_PDP_NUM_TYPE = "numeric"
_KEY_ALTERNATE_PDP_TYPE = "files_numcat_aspect"
_BAND_TOP = "band_top"
_BAND_BOTTOM = "band_bottom"
_MODEL_PRED = "model_pred"


class MLIExplainerId(enum.Enum):
    """Enumeration representing different MLI explainer IDs."""

    ABSOLUTE_PERMUTATION_BASED_FEATURE_IMPORTANCE = (
        "h2oai.mli.byor.recipes.permutation_feat_imp_absolute_explainer."
        "AbsolutePermutationFeatureImportanceExplainer"
    )
    """Absolute Permutation-Based Feature Importance"""

    DECISION_TREE = (
        "h2oaicore.mli.byor.recipes.surrogates.dt_surrogate_explainer."
        "DecisionTreeSurrogateExplainer"
    )
    """Decision Tree"""

    NLP_LEAVE_ONE_COVARIATE_OUT = (
        "h2oaicore.mli.byor.recipes.text.nlp_loco_explainer_v2.NlpLocoExplainerVersion2"
    )
    """NLP Leave-one-covariate-out (LOCO)"""

    NLP_PARTIAL_DEPENDENCE_PLOT = (
        "h2oaicore.mli.byor.recipes.text.nlp_dai_pd_ice_explainer.NlpDaiPdIceExplainer"
    )
    """NLP Partial Dependence Plot"""

    NLP_TOKENIZER = (
        "h2oaicore.mli.byor.recipes.text.nlp_tokenizer_explainer.NlpTokenizerExplainer"
    )
    """NLP Tokenizer"""

    NLP_VECTORIZER_LINEAR_MODEL = (
        "h2oaicore.mli.byor.recipes.text."
        "nlp_vectorizer_linear_model_explainer.NlpVecLmExplainer"
    )
    """NLP Vectorizer + Linear Model (VLM) Text Feature Importance"""

    ORIGINAL_FEATURE_IMPORTANCE = (
        "h2oaicore.mli.byor.recipes.surrogates."
        "original_feat_imp_explainer.OriginalFeatureImportanceExplainer"
    )
    """Original Feature Importance"""

    PARTIAL_DEPENDENCE_PLOT = (
        "h2oaicore.mli.byor.recipes.dai_pd_ice_explainer.DaiPdIceExplainer"
    )
    """Partial Dependence Plot"""

    RANDOM_FOREST_FEATURE_IMPORTANCE = (
        "h2oaicore.mli.byor.recipes.surrogates."
        "rf_feat_imp_explainer.RandomForestFeatureImportanceExplainer"
    )
    """Random Forest Feature Importance"""

    RANDOM_FOREST_PARTIAL_DEPENDENCE_PLOT = (
        "h2oaicore.mli.byor.recipes.surrogates."
        "rf_pd_explainer.RandomForestPartialDependenceExplainer"
    )
    """Random Forest Partial Dependence Plot"""

    RELATIVE_PERMUTATION_BASED_FEATURE_IMPORTANCE = (
        "h2oai.mli.byor.recipes."
        "permutation_feat_imp_relative_explainer."
        "RelativePermutationFeatureImportanceExplainer"
    )
    """Relative Permutation-Based Feature Importance"""

    SHAPLEY_SUMMARY_PLOT_FOR_ORIGINAL_FEATURES = (
        "h2oaicore.mli.byor.recipes."
        "shapley_summary_explainer.ShapleySummaryOrigFeatExplainer"
    )
    """Shapley Summary Plot for Original Features (Naive Shapley Method)"""

    KERNEL_SHAPLEY_VALUES_FOR_ORIGINAL_FEATURES = (
        "h2oaicore.mli.byor.recipes."
        "orig_kernel_shap_explainer.OriginalKernelShapExplainer"
    )
    """Shapley Values for Original Features (Kernel SHAP Method)"""

    SHAPLEY_VALUES_FOR_ORIGINAL_FEATURES = (
        "h2oaicore.mli.byor.recipes.original_contrib_explainer.NaiveShapleyExplainer"
    )
    """Shapley Values for Original Features (Naive Method)"""

    SHAPLEY_VALUES_FOR_TRANSFORMED_FEATURES = (
        "h2oaicore.mli.byor.recipes."
        "transformed_shapley_explainer.TransformedShapleyExplainer"
    )
    """Shapley Values for Transformed Features"""

    SURROGATE_RANDOM_FOREST_LEAVE_ONE_COVARIATE_OUT = (
        "h2oaicore.mli.byor."
        "recipes.surrogates.rf_loco_explainer.RandomForestLocoExplainer"
    )
    """Surrogate Random Forest Leave-one-covariate-out (LOCO)"""

    TRANSFORMED_FEATURE_IMPORTANCE = (
        "h2oaicore.mli.byor.recipes."
        "transformed_feat_imp_explainer.TransformedFeatureImportanceExplainer"
    )
    """Transformed Feature Importance"""

    FRIEDMAN_H_STATISTIC = (
        "h2oai.mli.byor.recipes.h2o_sonar_explainers_friedman_h_statistic_"
        "explainer_FriedmanHStatisticExplainer"
    )
    """Friedman's H-statistic"""

    @staticmethod
    def from_value(value: str) -> Optional["MLIExplainerId"]:
        try:
            return MLIExplainerId(value)
        except ValueError:
            # This explainer id is not part of the enum thus not supported
            return None


class _ExplanationFormat(enum.Enum):
    JSON = "application/json"
    JAY = "application/vnd.h2oai.json+datatable.jay"


class _ExplanationType(enum.Enum):
    PDP = "global-partial-dependence"
    LOCAL_PDP = "local-individual-conditional-explanation"
    SHAPLEYSUMMARY = "global-summary-feature-importance"
    FIMP = "global-feature-importance"
    LOCAL_FIMP = "local-feature-importance"
    NLP_LOCO = "global-nlp-loco"
    NLP_LOCAL_LOCO = "local-nlp-loco"
    DT = "global-decision-tree"
    LOCAL_DT = "local-decision-tree"


class _VegaPlot:
    @staticmethod
    def create_bar_plot(
        explainer_name: str,
        data: List[Dict[str, Any]],
        x_axis: str,
        y_axis: str,
        x_axis_title: str,
        y_axis_title: str,
        metrics: str,
        show_value_bias: bool,
        width: int = 600,
        height: int = 600,
    ) -> Dict[str, Any]:
        """
        Creates a bar plot using Vega-Lite.

        Returns:
            A dictionary containing the plot configuration.
        """
        vega = {
            "title": {
                "text": explainer_name,
                "subtitle": metrics,
                "align": "right",
            },
            "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
            "width": width,
            "height": height,
            "data": {"values": data},
            "encoding": {
                "y": {
                    "field": y_axis,
                    "type": "nominal",
                    "sort": {"field": "x", "op": "average"},
                    "title": y_axis_title,
                },
                "x": {
                    "field": x_axis,
                    "type": "quantitative",
                    "title": x_axis_title,
                },
                "color": {"field": "scope"},
                "yOffset": {"field": "scope"},
                "tooltip": [
                    {"field": y_axis, "type": "nominal", "title": "Feature name"},
                    {"field": x_axis, "type": "quantitative"},
                ],
            },
            "layer": [
                {"mark": "bar"},
                {
                    "mark": {
                        "type": "text",
                        "align": "left",
                        "baseline": "middle",
                        "dx": 5,
                    },
                    "encoding": {"text": {"field": x_axis, "type": "quantitative"}},
                },
            ],
        }
        if show_value_bias and isinstance(vega["encoding"], dict):
            vega["encoding"]["tooltip"].append(
                {"field": "value+bias", "type": "quantitative"}
            )
        return vega

    @staticmethod
    def create_pdp_categorical_plot(
        explainer_name: str,
        pd_data: List[Dict[str, Any]],
        ice_data: List[Dict[str, Any]],
        histogram_data: List[Dict[str, Any]],
        prediction_value: float,
        metrics: str,
        x_axis: str,
        y_axis: str,
        feature: str,
    ) -> Dict[str, Any]:
        """
        Creates a PDP plot for categorical features using Vega-Lite.

        Returns:
            A dictionary containing the plot configuration.
        """
        plot_data: Dict[str, Any] = {
            "title": {
                "text": explainer_name,
                "subtitle": metrics,
                "align": "center",
            },
            "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
            "vconcat": [
                {
                    "width": 800,
                    "height": 300,
                    "data": {"values": pd_data},
                    "layer": [
                        {
                            "mark": {"type": "bar", "opacity": 0.2},
                            "encoding": {
                                "x": {
                                    "field": x_axis,
                                    "type": "ordinal",
                                    "title": feature,
                                },
                                "y": {
                                    "field": _BAND_TOP,
                                    "type": "quantitative",
                                    "title": "Average prediction",
                                },
                                "y2": {
                                    "field": _BAND_BOTTOM,
                                    "type": "quantitative",
                                    "title": "",
                                },
                                "tooltip": [
                                    {"field": _KEY_BIN, "type": "ordinal"},
                                    {
                                        "field": "pd",
                                        "type": "quantitative",
                                        "title": "Average prediction",
                                    },
                                    {
                                        "field": "sd",
                                        "type": "quantitative",
                                        "title": "Standard deviation",
                                    },
                                ],
                            },
                        },
                        {
                            "mark": {"type": "point"},
                            "encoding": {
                                "y": {"field": y_axis, "type": "quantitative"},
                                "x": {"field": x_axis, "type": "ordinal"},
                            },
                        },
                        {
                            "data": {"values": ice_data},
                            "mark": "point",
                            "encoding": {
                                "x": {
                                    "field": _KEY_BIN,
                                    "type": "ordinal",
                                    "title": feature,
                                },
                                "y": {
                                    "field": _KEY_ICE,
                                    "type": "quantitative",
                                    "title": "Average prediction",
                                },
                                "color": {"value": "grey"},
                                "tooltip": [
                                    {"field": _KEY_BIN, "type": "ordinal"},
                                    {"field": _KEY_ICE, "type": "quantitative"},
                                ],
                            },
                        },
                    ],
                },
            ],
        }

        if histogram_data:
            plot_data["vconcat"].append(
                {
                    "width": 800,
                    "height": 100,
                    "data": {"values": histogram_data},
                    "mark": {"type": "bar"},
                    "encoding": {
                        "x": {
                            "field": "x",
                            "type": "ordinal",
                            "title": "x",
                            "scale": {"zero": "", "nice": ""},
                        },
                        "y": {"field": "frequency", "type": "quantitative"},
                        "tooltip": [{"field": "frequency", "type": "quantitative"}],
                    },
                    "config": {"binSpacing": 0},
                }
            )

        if prediction_value is not None:
            plot_data["vconcat"][0]["layer"].append(
                {
                    "mark": {"type": "rule", "strokeDash": [4, 4]},
                    "encoding": {
                        "y": {"datum": prediction_value},
                        "color": {"value": "red"},
                    },
                }
            )

        return plot_data

    @staticmethod
    def create_pdp_numerical_plot(
        explainer_name: str,
        pd_data: List[Dict[str, Any]],
        ice_data: List[Dict[str, Any]],
        histogram_data: List[Dict[str, Any]],
        prediction_value: float,
        metrics: str,
        x_axis: str,
        y_axis: str,
        feature: str,
        is_temporal: bool,
    ) -> Dict[str, Any]:
        """
        Creates a PDP plot for numerical features using Vega-Lite.

        Returns:
            A dictionary containing the plot configuration.
        """

        x_data_type = "temporal" if is_temporal else "quantitative"

        plot_data: Dict[str, Any] = {
            "title": {
                "text": explainer_name,
                "subtitle": metrics,
                "align": "center",
            },
            "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
            "vconcat": [
                {
                    "width": 800,
                    "height": 300,
                    "data": {"values": pd_data},
                    "layer": [
                        {
                            "mark": "errorband",
                            "encoding": {
                                "y": {
                                    "field": _BAND_TOP,
                                    "type": "quantitative",
                                    "scale": {"zero": ""},
                                    "title": "",
                                },
                                "y2": {"field": _BAND_BOTTOM, "title": ""},
                                "x": {
                                    "field": x_axis,
                                    "axis": "",
                                    "type": x_data_type,
                                },
                                "tooltip": "",
                            },
                        },
                        {
                            "mark": {"type": "line"},
                            "encoding": {
                                "x": {
                                    "field": x_axis,
                                    "type": x_data_type,
                                    "title": feature,
                                    "scale": {"zero": "", "nice": ""},
                                },
                                "y": {
                                    "field": y_axis,
                                    "type": "quantitative",
                                    "title": "Average prediction",
                                },
                                "color": {
                                    "field": _KEY_OOR,
                                    "legend": {"disable": True},
                                },
                            },
                        },
                        {
                            "data": {"values": ice_data},
                            "encoding": {
                                "x": {
                                    "field": _KEY_BIN,
                                    "type": x_data_type,
                                    "scale": {"zero": "", "nice": ""},
                                },
                                "y": {
                                    "field": _KEY_ICE,
                                    "type": "quantitative",
                                    "title": "Average prediction",
                                },
                                "color": {"value": "grey"},
                                "tooltip": [
                                    {"field": _KEY_BIN, "type": "ordinal"},
                                    {"field": _KEY_ICE, "type": "quantitative"},
                                ],
                            },
                            "layer": [
                                {
                                    "mark": {"type": "line"},
                                },
                                {
                                    "mark": {"type": "point"},
                                },
                            ],
                        },
                        {
                            "mark": {"type": "point"},
                            "encoding": {
                                "x": {
                                    "field": x_axis,
                                    "type": x_data_type,
                                    "title": "",
                                    "scale": {"zero": "", "nice": ""},
                                },
                                "y": {
                                    "field": y_axis,
                                    "type": "quantitative",
                                    "title": "",
                                },
                                "tooltip": [
                                    {"field": _KEY_BIN, "type": "quantitative"},
                                    {
                                        "field": "pd",
                                        "type": "quantitative",
                                        "title": "Average prediction",
                                    },
                                    {
                                        "field": "sd",
                                        "type": "quantitative",
                                        "title": "Standard deviation",
                                    },
                                ],
                                "color": {"field": _KEY_OOR},
                            },
                        },
                    ],
                },
            ],
        }
        if histogram_data:
            plot_data["vconcat"].append(
                {
                    "width": 800,
                    "height": 100,
                    "data": {"values": histogram_data},
                    "mark": {"type": "bar", "orient": "vertical"},
                    "encoding": {
                        "x": {
                            "field": "x",
                            "type": x_data_type,
                            "title": "x",
                            "scale": {"zero": "", "nice": ""},
                        },
                        "x2": {
                            "field": "x_continuous",
                            "type": x_data_type,
                            "axis": "",
                        },
                        "y": {"field": "frequency", "type": "quantitative"},
                    },
                }
            )

        if prediction_value is not None:
            plot_data["vconcat"][0]["layer"].append(
                {
                    "mark": {"type": "rule", "strokeDash": [4, 4]},
                    "encoding": {
                        "y": {"datum": prediction_value},
                        "color": {"value": "red"},
                    },
                }
            )
        return plot_data

    @classmethod
    def create_pdp_plot(
        cls,
        explainer_name: str,
        numeric: bool,
        pd_data: List[Dict[str, Any]],
        ice_data: List[Dict[str, Any]],
        histogram_data: List[Dict[str, Any]],
        prediction_value: float,
        metrics: str,
        feature_name: str,
    ) -> Dict[str, Any]:
        """
        Creates a PDP plot using Vega-Lite.

        Returns:
            A dictionary containing the plot configuration.
        """
        if numeric:
            return cls.create_pdp_numerical_plot(
                explainer_name=explainer_name,
                pd_data=pd_data,
                ice_data=ice_data,
                histogram_data=histogram_data,
                prediction_value=prediction_value,
                metrics=metrics,
                x_axis=_KEY_BIN,
                y_axis=_KEY_PD,
                feature=feature_name,
                is_temporal="time" in feature_name.lower(),
            )
        else:
            return cls.create_pdp_categorical_plot(
                explainer_name=explainer_name,
                pd_data=pd_data,
                ice_data=ice_data,
                histogram_data=histogram_data,
                prediction_value=prediction_value,
                metrics=metrics,
                x_axis=_KEY_BIN,
                y_axis=_KEY_PD,
                feature=feature_name,
            )

    @staticmethod
    def create_decision_tree_plot(
        explainer_name: str, data: List[Dict[str, Any]], metrics: str
    ) -> Dict[str, Any]:
        """
        Creates a decision tree plot using Vega.

        Returns:
            A dictionary containing the plot configuration.
        """
        return {
            "title": {"text": explainer_name, "subtitle": metrics, "align": "center"},
            "$schema": "https://vega.github.io/schema/vega/v5.json",
            "width": 800,
            "height": 300,
            "data": [
                {
                    "name": "tree",
                    "values": data,
                    "transform": [
                        {"type": "stratify", "key": "key", "parentKey": "parent"},
                        {
                            "type": "tree",
                            "method": "tidy",
                            "size": [{"signal": "width"}, {"signal": "height"}],
                            "separation": "true",
                            "as": ["x", "y", "depth", "children"],
                        },
                    ],
                },
                {
                    "name": "links",
                    "source": "tree",
                    "transform": [{"type": "treelinks"}, {"type": "linkpath"}],
                },
            ],
            "marks": [
                {
                    "type": "path",
                    "from": {"data": "links"},
                    "encode": {
                        "update": {
                            "path": {"field": "path"},
                            "strokeWidth": {
                                "signal": "2 + 2 * (datum.target.edge_weight / 0.25)"
                            },
                            "opacity": {"value": 0.5},
                        }
                    },
                },
                {
                    "type": "symbol",
                    "from": {"data": "tree"},
                    "encode": {
                        "enter": {"size": {"value": 200}},
                        "update": {"x": {"field": "x"}, "y": {"field": "y"}},
                    },
                },
                {
                    "type": "text",
                    "from": {"data": "tree"},
                    "encode": {
                        "enter": {
                            "text": {"field": "name"},
                            "fontSize": {"value": 16},
                            "baseline": {"value": "middle"},
                            "angle": {"signal": "datum.children ? 0 : 30"},
                            "opacity": {"value": 1},
                            "limit": {"value": 200},
                        },
                        "update": {
                            "x": {"field": "x"},
                            "y": {"field": "y"},
                            "dx": {"signal": "datum.children ? -10 : 10"},
                            "align": {"signal": "datum.children ? 'right' : 'left'"},
                        },
                    },
                },
                {
                    "type": "text",
                    "from": {"data": "links"},
                    "encode": {
                        "enter": {
                            "text": {"field": "target.edgein"},
                            "baseline": {"value": "middle"},
                            "opacity": {"value": 0.9},
                            "limit": {"value": 200},
                        },
                        "update": {
                            "x": {
                                "signal": "datum.source.x + "
                                "((datum.target.x - datum.source.x) / 2)"
                            },
                            "y": {
                                "signal": "datum.source.y + "
                                "((datum.target.y - datum.source.y) / 2)"
                            },
                            "dx": {
                                "signal": "datum.source.x > datum.target.x ? -5 : 5"
                            },
                            "align": {
                                "signal": "datum.source.x > datum.target.x "
                                "? 'right' : 'left'"
                            },
                        },
                    },
                },
            ],
        }

    @staticmethod
    def create_shapley_summary_plot(
        explainer_name: str,
        data_avg_is_none: List[Dict[str, Any]],
        data_avg_higher_than_zero: List[Dict[str, Any]],
        metrics: str,
    ) -> Dict[str, Any]:
        """
        Creates a Shapley summary plot using Vega-Lite.

        Returns:
            A dictionary containing the plot configuration.
        """
        return {
            "title": {"text": explainer_name, "subtitle": metrics, "align": "center"},
            "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
            "width": 700,
            "height": 250,
            "data": {"values": data_avg_higher_than_zero},
            "layer": [
                {
                    "mark": "circle",
                    "encoding": {
                        "x": {"field": "shapley_value", "type": "quantitative"},
                        "y": {"field": "feature", "type": "ordinal", "sort": "-x"},
                        "color": {
                            "field": "avg_high_value",
                            "type": "quantitative",
                            "title": "Normalized feature value",
                            "condition": {
                                "value": "transparent",
                                "test": "datum.count === 0",
                            },
                        },
                        "tooltip": [
                            {"field": "feature", "type": "nominal"},
                            {
                                "field": "shapley_value",
                                "type": "quantitative",
                                "title": "Shapley value",
                            },
                            {
                                "field": "count",
                                "type": "quantitative",
                                "title": "Bin count",
                            },
                            {
                                "field": "avg_high_value",
                                "type": "quantitative",
                                "title": "Avg. normalized feature value",
                            },
                        ],
                    },
                },
                {
                    "data": {"values": data_avg_is_none},
                    "mark": "circle",
                    "encoding": {
                        "x": {"field": "shapley_value", "type": "quantitative"},
                        "y": {
                            "field": "feature",
                            "type": "ordinal",
                            "sort": "-x",
                            "axis": {"grid": "true"},
                        },
                        "color": {
                            "condition": {
                                "value": "transparent",
                                "test": "datum.count === 0",
                            },
                            "value": "grey",
                        },
                        "tooltip": [
                            {"field": "feature", "type": "nominal"},
                            {
                                "field": "shapley_value",
                                "type": "quantitative",
                                "title": "Shapley value",
                            },
                            {
                                "field": "count",
                                "type": "quantitative",
                                "title": "Bin count",
                            },
                        ],
                    },
                },
            ],
        }


class ExplanationPlot(abc.ABC):
    """This abstract class serves as the foundation for all explanation plot classes
    to inherit from."""

    COMPATIBLE_EXPLAINERS: List[MLIExplainerId] = []

    def __init__(
        self,
        client: "_core.Client",
        mli_key: str,
        experiment_key: str,
        explainer_info: _commons_mli._ExplainerInfo,
        explanation_type: _ExplanationType = None,
        explanation_format: _ExplanationFormat = None,
    ) -> None:
        if not self._is_compatible(explainer_info):
            raise Exception(f"Explainer {explainer_info.name} is not compatible.")

        self._client = client
        self._mli_key = mli_key
        self._explainer_info = explainer_info
        self._experiment_key = experiment_key
        self._explanation_type: _ExplanationType = explanation_type
        self._explanation_format: _ExplanationFormat = explanation_format
        self._index_file: Optional[Dict[str, Any]] = None
        self._index_file_url: Optional[str] = None

        self._explainer_job_key = explainer_info.key
        self._explainer_id = MLIExplainerId.from_value(explainer_info.id)

    @classmethod
    def _is_compatible(cls, explainer_info: _commons_mli._ExplainerInfo) -> bool:
        return MLIExplainerId.from_value(explainer_info.id) in cls.COMPATIBLE_EXPLAINERS

    def _get_json(self, json_name: str) -> Dict[str, Any]:
        json_str: str = self._client._backend.get_json(
            json_name=json_name,
            job_key=self._mli_key,
        )
        return json.loads(json_str)

    @classmethod
    def _create_explanation_plots(
        cls,
        explainer_infos: List[_commons_mli._ExplainerInfo],
        client: "_core.Client",
        mli_key: str,
        experiment_key: str,
    ) -> List["ExplanationPlot"]:
        available_plot_classes: List[Type["ExplanationPlot"]] = [
            FeatureImportanceGlobalExplanationPlot,
            ShapleyExplanationPlot,
            NLPTokenizerExplanationPlot,
            NLPFeatureImportanceExplanationPlot,
            DAIFeatureImportanceExplanationPlot,
            RandomForestFeatureImportanceExplanationPlot,
            PDPExplanationPlot,
            RandomForestPDPExplanationPlot,
            DecisionTreeExplanationPlot,
            ShapleySummaryExplanationPlot,
        ]
        plots: List["ExplanationPlot"] = []
        for ei in explainer_infos:
            if ei.status != _enums.JobStatus.COMPLETE:
                continue
            for plot_class in available_plot_classes:
                if plot_class._is_compatible(ei):
                    plots.append(
                        plot_class(
                            client=client,
                            mli_key=mli_key,
                            explainer_info=ei,
                            experiment_key=experiment_key,
                        )
                    )
        return plots

    @abc.abstractmethod
    def get_plot(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        raise NotImplementedError

    def __repr__(self) -> str:
        return (
            f"<class '{self.__class__.__name__}'> {self._explainer_id.value}, "
            f"{self._explainer_info.name}"
        )


class _SurrogateExplanationPlot(ExplanationPlot):
    def __init__(
        self,
        client: "_core.Client",
        mli_key: str,
        experiment_key: str,
        explainer_info: _commons_mli._ExplainerInfo,
    ) -> None:
        super().__init__(
            client=client,
            mli_key=mli_key,
            experiment_key=experiment_key,
            explainer_info=explainer_info,
            explanation_type=None,
            explanation_format=None,
        )
        self._feature_names: Optional[List[str]] = None

    def _get_local_result(
        self,
        row_number: int,
        frame_name: str,
    ) -> Dict[str, Any]:
        local_result: str = self._client._backend.get_frame_rows(
            clazz="",
            frame_name=frame_name,
            mli_job_key=self._mli_key,
            num_rows=1,
            orig_feat_shapley=False,
            row_offset=row_number,
        )
        return json.loads(local_result)


class _ByorExplanationPlot(ExplanationPlot):
    def __init__(
        self,
        client: "_core.Client",
        mli_key: str,
        experiment_key: str,
        explainer_info: _commons_mli._ExplainerInfo,
        explanation_type: _ExplanationType = None,
        explanation_format: _ExplanationFormat = None,
    ) -> None:
        super().__init__(
            client=client,
            mli_key=mli_key,
            experiment_key=experiment_key,
            explainer_info=explainer_info,
            explanation_type=explanation_type,
            explanation_format=explanation_format,
        )
        self._classes: Optional[List[str]] = None
        self._feature_names: Optional[List[str]] = None

    def _get_index_file_url(self) -> Optional[str]:
        if self._explanation_format is None or self._explanation_format is None:
            return None
        if not self._index_file_url:
            self._index_file_url = self._client._backend.get_explainer_result_url_path(
                self._mli_key,
                self._explainer_job_key,
                self._explanation_type.value,
                self._explanation_format.value,
            )
        return self._index_file_url

    def _get_index_file(self) -> Optional[Dict[str, Any]]:
        if self._get_index_file_url() is None:
            return None
        if not self._index_file:
            self._index_file = self._client._get_file(self._get_index_file_url()).json()
        return self._index_file

    @staticmethod
    def _get_metric_info_string(metrics: Optional[List[Dict[str, Any]]]) -> str:
        if not metrics:
            return ""

        info_strings = []
        for metric in metrics:
            for key, value in metric.items():
                info_strings.append(f"{key}: {value}")
        return ",".join(info_strings)

    def _determine_class_name(self, class_name: str) -> str:
        classes = self.get_classes()
        if class_name is None:
            class_name = str(self._get_index_file().get(_KEY_DEFAULT_CLASS, classes[0]))
        elif class_name not in classes:
            raise ValueError(
                f"Invalid class name '{class_name}'. Possible values are {classes}."
            )
        return class_name

    def _determine_feature_name(self, feature_name: str) -> str:
        feature_names = self.get_feature_names()
        if feature_name is None:
            feature_name = feature_names[0]
        elif feature_name not in feature_names:
            raise ValueError(
                f"Invalid feature name '{feature_name}'. Possible values are "
                f"{feature_names}."
            )
        return feature_name

    def _determine_explanation_filters(
        self,
        explain_feature: Optional[str] = None,
        explain_class: Optional[str] = None,
        text_feature: Optional[str] = None,
    ) -> List[Any]:
        explanation_filters = []
        if explain_feature is not None:
            explanation_filters.append(
                self._client._server_module.messages.FilterEntry(
                    filter_by=_FILTER_EXPLAIN_FEATURE, value=explain_feature
                )
            )
        if explain_class is not None:
            explanation_filters.append(
                self._client._server_module.messages.FilterEntry(
                    filter_by=_FILTER_EXPLAIN_CLASS, value=explain_class
                )
            )
        if text_feature is not None:
            explanation_filters.append(
                self._client._server_module.messages.FilterEntry(
                    filter_by=_FILTER_TEXT_FEATURE, value=text_feature
                )
            )
        return explanation_filters

    def get_classes(self) -> List[str]:
        if not self._classes:
            index_file = self._get_index_file()
            if _KEY_FILES in index_file:
                self._classes = list(self._get_index_file()[_KEY_FILES].keys())
            elif _KEY_FEATURES in index_file:
                features: Dict[str, Any] = index_file[_KEY_FEATURES]
                a_feature_name = next(iter(features))
                feature = features[a_feature_name]
                self._classes = list(feature[_KEY_FILES])
            else:
                raise ValueError(
                    f"The index file should contain {_KEY_FILES} or "
                    f"{_KEY_FEATURES} key"
                )
        return self._classes

    def get_feature_names(self) -> List[str]:
        if not self._feature_names:
            index_file = self._get_index_file()
            if _KEY_FEATURES in index_file:
                features: Dict[str, Any] = index_file[_KEY_FEATURES]
                self._feature_names = list(features.keys())
            else:
                raise ValueError(
                    f"The index file should contain the {_KEY_FEATURES} key."
                )
        return self._feature_names

    def _get_feature_dict(self, feature_name: str) -> Dict[str, Any]:
        index_file = self._get_index_file()
        if _KEY_FEATURES in index_file:
            return index_file[_KEY_FEATURES][feature_name]
        else:
            raise ValueError(f"The index file should contain the {_KEY_FEATURES} key.")

    def _get_local_result(
        self,
        explanation_filter: List[Any],
        row_number: int,
        local_explanation_format: _ExplanationFormat,
        local_explanation_type: _ExplanationType,
        page_size: int = 0,
        page_offset: int = 0,
    ) -> Dict[str, Any]:
        local_result: str = self._client._backend.get_explainer_local_result(
            explainer_job_key=self._explainer_job_key,
            explanation_filter=explanation_filter,
            explanation_format=local_explanation_format.value,
            explanation_type=local_explanation_type.value,
            id_column_name="",
            id_column_value=str(row_number),
            mli_key=self._mli_key,
            page_size=page_size,
            page_offset=page_offset,
            result_format=local_explanation_format.value,
            row_limit=1,
        )
        return json.loads(local_result)

    def _get_global_explanation_file(
        self,
        class_name: str,
        feature_name: Optional[str] = None,
        class_key_name: str = _KEY_FILES,
        shap_sum_page: Optional[int] = None,
    ) -> Dict[str, Any]:
        server_path_root = os.path.dirname(self._get_index_file_url())
        index_file = self._get_index_file()
        if class_key_name in index_file:
            filename = (
                index_file[class_key_name][class_name]
                if shap_sum_page is None
                else list(index_file[class_key_name][class_name].values())[
                    shap_sum_page
                ]
            )
            server_path = os.path.join(server_path_root, filename)
        elif _KEY_FEATURES in index_file:
            if feature_name is None:
                raise ValueError("feature_name cannot be None")
            feature = self._get_feature_dict(feature_name)
            server_path = os.path.join(
                server_path_root, feature[class_key_name][class_name]
            )
        else:
            raise ValueError(
                f"The index file should contain {class_key_name} or "
                f"{_KEY_FEATURES} keys"
            )
        return self._client._get_file(server_path).json()

    def _get_global_explanation_result(
        self, explanation_filter: Any, page_size: int = 0, page_offset: int = 0
    ) -> Dict[str, Any]:
        result: str = self._client._backend.get_explainer_result(
            explainer_job_key=self._explainer_job_key,
            explanation_filter=explanation_filter,
            explanation_format=self._explanation_format.value,
            explanation_type=self._explanation_type.value,
            mli_key=self._mli_key,
            page_size=page_size,
            page_offset=page_offset,
            result_format=self._explanation_format.value,
        )
        return json.loads(result)


class _FeatureImportanceExplanationPlotCommon(_ByorExplanationPlot):
    def __init__(
        self,
        client: "_core.Client",
        mli_key: str,
        experiment_key: str,
        explainer_info: _commons_mli._ExplainerInfo,
    ) -> None:
        super().__init__(
            client=client,
            mli_key=mli_key,
            experiment_key=experiment_key,
            explainer_info=explainer_info,
            explanation_type=_ExplanationType.FIMP,
            explanation_format=_ExplanationFormat.JSON,
        )
        self._local_explanation_type = _ExplanationType.LOCAL_FIMP
        self._local_explanation_format = (
            _ExplanationFormat.JAY
            if self._explainer_id != MLIExplainerId.NLP_TOKENIZER
            else _ExplanationFormat.JSON
        )
        self._explain_class = (
            _CLASS_TF_IDF if self._explainer_id == MLIExplainerId.NLP_TOKENIZER else ""
        )

    def _transform_data(self, data: List[Dict[str, Any]]) -> None:
        if self._explainer_id != MLIExplainerId.SHAPLEY_VALUES_FOR_ORIGINAL_FEATURES:
            return

        # format the label into the format of `<Feature> = <Feature value>`
        for index, point in enumerate(data):
            label_name = point[_KEY_LABEL]
            for _point in data[index + 1 :]:
                if _point[_KEY_LABEL] == label_name:
                    _point[_KEY_LABEL] = (
                        f"{_point[_KEY_LABEL]} = " f"{_point[_KEY_FEATURE_VALUE]}"
                    )
                    point[
                        _KEY_LABEL
                    ] = f"{point[_KEY_LABEL]} = {_point[_KEY_FEATURE_VALUE]}"
                    break

    def _shapley_metrics(
        self, data: List[Dict[str, Any]], bias: float, prediction: float, actual: str
    ) -> str:
        metrics = ""
        if bias is not None:
            local_shap_val = [
                feat.get(_KEY_VALUE)
                for feat in data
                if feat.get(_KEY_SCOPE) == _SCOPE_LOCAL
            ]
            if local_shap_val:
                local_shap_sum = sum(local_shap_val)
                bias_plus_contributions = local_shap_sum + bias
                metrics += f"Bias + Contributions: {bias_plus_contributions:.5f}"
            metrics += ", " if metrics else ""
            metrics += f"Global bias: {bias:.5f}"
            interpretation_job: Any = self._client._backend.get_interpretation_job(
                key=self._mli_key
            )
            target_transformation: str = (
                interpretation_job.entity.dai_target_transformation
            )
            if target_transformation:
                metrics += f", Target Transformation: {target_transformation}"

        if prediction is not None:
            metrics += ", " if metrics else ""
            metrics += f"Prediction: {prediction:.5f}"
        if actual is not None:
            metrics += ", " if metrics else ""
            metrics += f"Actual: {actual}"
        return metrics

    def _plot_from_feat_imp_explanation(
        self,
        row_number: Optional[int] = None,
        class_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        data: List[Dict[str, Any]]
        bias: Optional[float] = None
        prediction: Optional[float] = None
        actual: Optional[str] = None
        if row_number is not None:
            if row_number < 0:
                raise ValueError("Row number must be a positive integer.")

            explanation_filter = self._determine_explanation_filters(
                explain_feature="", explain_class=class_name
            )

            local_result = self._get_local_result(
                explanation_filter=explanation_filter,
                row_number=row_number,
                local_explanation_format=self._local_explanation_format,
                local_explanation_type=self._local_explanation_type,
            )
            data = local_result[_KEY_DATA]
            bias = local_result.get(_KEY_BIAS)
            prediction = local_result.get(_KEY_PREDICTION)
            actual = local_result.get(_KEY_ACTUAL)

            self._transform_data(data)

        else:
            global_result = self._get_global_explanation_file(class_name=class_name)

            data = global_result[_KEY_DATA]
            bias = global_result.get(_KEY_BIAS)

        for point in data:
            point[_KEY_VALUE] = round(point[_KEY_VALUE], 6)
            if bias is not None:
                point["value+bias"] = point[_KEY_VALUE] + bias

        index_file = self._get_index_file()
        metrics = self._shapley_metrics(data, bias, prediction, actual)
        metrics_extra = self._get_metric_info_string(index_file.get(_KEY_METRICS))
        if metrics and metrics_extra:
            metrics = f"{metrics_extra}, {metrics}"
        elif metrics_extra:
            metrics = metrics_extra

        y_axis_label = index_file.get(_KEY_Y_AXIS_LABEL, "Feature name")
        x_axis_label = index_file.get(_KEY_X_AXIS_LABEL, "Value")

        return _VegaPlot.create_bar_plot(
            explainer_name=self._explainer_info.name,
            data=data,
            x_axis=_KEY_VALUE,
            y_axis=_KEY_LABEL,
            x_axis_title=x_axis_label,
            y_axis_title=y_axis_label,
            metrics=metrics,
            show_value_bias=bias is not None,
            height=len(data) * 30,
        )


class ShapleyExplanationPlot(_FeatureImportanceExplanationPlotCommon):
    """Handles plots for the following explainers:

    * Shapley Values for Original Features (Naive Method)
    * Shapley Values for Transformed Features
    * Shapley Values for Original Features (Kernel SHAP Method)
    """

    COMPATIBLE_EXPLAINERS: List[MLIExplainerId] = [
        MLIExplainerId.KERNEL_SHAPLEY_VALUES_FOR_ORIGINAL_FEATURES,
        MLIExplainerId.SHAPLEY_VALUES_FOR_ORIGINAL_FEATURES,
        MLIExplainerId.SHAPLEY_VALUES_FOR_TRANSFORMED_FEATURES,
    ]

    def get_plot(
        self,
        *,
        class_name: Optional[str] = None,
        row_number: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Plots the explanation.

        Args:
            row_number: Local explanation for the given row_number.
            class_name: The name of the class in multinomial classification,
                if not provided the first class from the set of available classes in
                the model will be selected (use the method `get_classes()` to view
                available classes).

        Returns:
            The plot in Vega Lite (v5) format
        """
        class_name = self._determine_class_name(class_name)

        return self._plot_from_feat_imp_explanation(
            row_number=row_number, class_name=class_name
        )


class NLPTokenizerExplanationPlot(_FeatureImportanceExplanationPlotCommon):
    """Handles plots for the following explainers:

    * NLP Tokenizer
    """

    COMPATIBLE_EXPLAINERS: List[MLIExplainerId] = [
        MLIExplainerId.NLP_TOKENIZER,
    ]

    def get_plot(
        self,
        *,
        row_number: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Plots the explanation.

        Args:
            row_number: Local explanation for the given row_number.

        Returns:
            The plot in Vega Lite (v5) format
        """
        class_name = self._determine_class_name(None)

        return self._plot_from_feat_imp_explanation(
            row_number=row_number, class_name=class_name
        )


class FeatureImportanceGlobalExplanationPlot(_FeatureImportanceExplanationPlotCommon):
    """Handles plots for the following explainers:

    * Absolute Permutation-Based Feature Importance
    * Relative Permutation-Based Feature Importance
    * Friedman's H-statistic
    """

    COMPATIBLE_EXPLAINERS: List[MLIExplainerId] = [
        MLIExplainerId.ABSOLUTE_PERMUTATION_BASED_FEATURE_IMPORTANCE,
        MLIExplainerId.RELATIVE_PERMUTATION_BASED_FEATURE_IMPORTANCE,
        MLIExplainerId.FRIEDMAN_H_STATISTIC,
    ]

    def __init__(
        self,
        client: "_core.Client",
        mli_key: str,
        experiment_key: str,
        explainer_info: _commons_mli._ExplainerInfo,
    ) -> None:
        super().__init__(
            client=client,
            mli_key=mli_key,
            experiment_key=experiment_key,
            explainer_info=explainer_info,
        )

    def get_plot(
        self,
        *,
        class_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Plots the explanation.

        Args:
            class_name: The name of the class in multinomial classification,
                if not provided the first class from the set of available classes in
                the model will be selected (use the method `get_classes()` to view
                available classes).

        Returns:
            The plot in Vega Lite (v5) format
        """
        class_name = self._determine_class_name(class_name)

        return self._plot_from_feat_imp_explanation(
            row_number=None, class_name=class_name
        )


class DAIFeatureImportanceExplanationPlot(ExplanationPlot):
    """Handles plots for the following explainers:

    * Original Feature Importance
    * Transformed Feature Importance
    """

    COMPATIBLE_EXPLAINERS: List[MLIExplainerId] = [
        MLIExplainerId.ORIGINAL_FEATURE_IMPORTANCE,
        MLIExplainerId.TRANSFORMED_FEATURE_IMPORTANCE,
    ]

    def __init__(
        self,
        client: "_core.Client",
        mli_key: str,
        experiment_key: str,
        explainer_info: _commons_mli._ExplainerInfo,
    ) -> None:
        if not experiment_key:
            raise ValueError("Must have experiment_key")

        super().__init__(
            client=client,
            mli_key=mli_key,
            experiment_key=experiment_key,
            explainer_info=explainer_info,
            explanation_type=None,
            explanation_format=None,
        )

    def _get_global_explanation_data(self, original: bool) -> List[Dict[str, Any]]:
        var_imp: Any = self._client._backend.get_mli_variable_importance(
            key=self._experiment_key,
            mli_job_key=self._mli_key,
            original=original,
        )
        feat_imp: List[Dict[str, Any]] = []
        for gain, interaction in zip(var_imp.gain, var_imp.interaction):
            feat_imp.append(
                {
                    _KEY_LABEL: interaction,
                    _KEY_VALUE: round(gain, 4),
                    _KEY_SCOPE: (_SCOPE_GLOBAL),
                }
            )
        return feat_imp

    def get_plot(self) -> Dict[str, Any]:
        """Plots the explanation.

        Returns:
            The plot in Vega Lite (v5) format
        """
        data = self._get_global_explanation_data(
            self._explainer_id == MLIExplainerId.ORIGINAL_FEATURE_IMPORTANCE
        )
        return _VegaPlot.create_bar_plot(
            explainer_name=self._explainer_info.name,
            data=data,
            x_axis=_KEY_VALUE,
            y_axis=_KEY_LABEL,
            x_axis_title="Feature importance",
            y_axis_title="Feature name (Ordered by feature importance value)",
            metrics="",
            show_value_bias=False,
            height=len(data) * 30,
        )


class RandomForestFeatureImportanceExplanationPlot(_SurrogateExplanationPlot):
    """Handles plots for the following explainers:

    * Random Forest Feature Importance
    * Surrogate Random Forest Leave-one-covariate-out (LOCO)
    """

    COMPATIBLE_EXPLAINERS: List[MLIExplainerId] = [
        MLIExplainerId.RANDOM_FOREST_FEATURE_IMPORTANCE,
        MLIExplainerId.SURROGATE_RANDOM_FOREST_LEAVE_ONE_COVARIATE_OUT,
    ]

    def __init__(
        self,
        client: "_core.Client",
        mli_key: str,
        experiment_key: str,
        explainer_info: _commons_mli._ExplainerInfo,
    ) -> None:
        super().__init__(
            client=client,
            mli_key=mli_key,
            experiment_key=experiment_key,
            explainer_info=explainer_info,
        )

    def _get_global_rf_loco_data(self) -> List[Dict[str, Any]]:
        rf_loco = self._get_json("surrogate_shapley_global.json")
        feat_imp = [
            {
                _KEY_LABEL: key,
                _KEY_VALUE: round(value, 4),
                _KEY_SCOPE: _SCOPE_GLOBAL,
            }
            for key, value in rf_loco.items()
            if key != _KEY_BIAS
        ]
        return feat_imp

    def _get_global_rf_feat_imp_data(self) -> List[Dict[str, Any]]:
        var_imp = self._get_json("varImp.json")
        keys = var_imp["rowHeaders"]

        def _get_float(x: Any) -> Optional[float]:
            try:
                return float(x)
            except (ValueError, TypeError):
                pass
            try:
                return float(x[1]["d"])
            except (ValueError, TypeError):
                pass
            try:
                return float(x[1]["f"])
            except (ValueError, TypeError):
                return None

        values = [_get_float(x) for x in var_imp["cellValues"]]
        feat_imp = [
            {
                _KEY_LABEL: key,
                _KEY_VALUE: round(value, 4),
                _KEY_SCOPE: _SCOPE_GLOBAL,
            }
            for key, value in zip(keys, values)
        ]

        return feat_imp

    def _add_local_result(
        self, row_number: int, feat_imp: bool, global_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        local_result = self._get_local_result(
            row_number=row_number, frame_name="loco_frame.bin"
        )
        values = [abs(v) for v in local_result[_KEY_DATA][0]]
        columns = local_result[_KEY_COLUMNS]
        local_data = dict(zip(columns, values))

        max_val = max(values)

        def _compute_val(val: float) -> float:
            if feat_imp:
                return round(val / max_val, 4)
            else:
                return round(val, 4)

        joined_data: List[Dict[str, Any]] = []
        for feat_data in global_data:
            joined_data.append(feat_data)
            label = feat_data[_KEY_LABEL]
            val = local_data[label]
            joined_data.append(
                {
                    _KEY_LABEL: label,
                    _KEY_VALUE: _compute_val(val),
                    _KEY_SCOPE: _SCOPE_LOCAL,
                }
            )

        return joined_data

    def _get_rf_metrics(self) -> str:
        drf_meta = self._get_json("drfMetaData.json")
        if "_training_metrics" not in drf_meta:
            return ""
        drf_train = (
            drf_meta["_training_metrics"]["_sigma"]
            * drf_meta["_training_metrics"]["_sigma"]
        )
        rmse_train = round(math.sqrt(drf_meta["_training_metrics"]["_MSE"]), 4)
        r_squared_train = round(
            1 - drf_meta["_training_metrics"]["_MSE"] / drf_train, 2
        )
        return f"R2: {r_squared_train} RMSE: {rmse_train}"

    def get_plot(self, *, row_number: Optional[int] = None) -> Dict[str, Any]:
        """Plots the explanation.

        Args:
            row_number: Local explanation for the given row_number.

        Returns:
            The plot in Vega Lite (v5) format
        """
        rf_feat_imp = (
            self._explainer_id == MLIExplainerId.RANDOM_FOREST_FEATURE_IMPORTANCE
        )
        if rf_feat_imp:
            data = self._get_global_rf_feat_imp_data()
        else:
            data = self._get_global_rf_loco_data()

        data = sorted(data, key=lambda item: item[_KEY_VALUE], reverse=True)

        if row_number is not None:
            if row_number < 0:
                raise ValueError("Row number must be a positive integer.")
            data = self._add_local_result(
                row_number=row_number, feat_imp=rf_feat_imp, global_data=data
            )

        return _VegaPlot.create_bar_plot(
            explainer_name=self._explainer_info.name,
            data=data,
            x_axis=_KEY_VALUE,
            y_axis=_KEY_LABEL,
            x_axis_title="Gain Value" if rf_feat_imp else "LOCO value",
            y_axis_title=(
                "Feature name (Ordered by "
                f"{'gain' if rf_feat_imp else 'average LOCO'} value)"
            ),
            metrics=self._get_rf_metrics(),
            show_value_bias=False,
            height=len(data) * 30,
        )


class NLPFeatureImportanceExplanationPlot(_ByorExplanationPlot):
    """Handles plots for the following explainers:

    * NLP Vectorizer + Linear Model (VLM) Text Feature Importance
    * NLP Leave-one-covariate-out (LOCO)
    """

    COMPATIBLE_EXPLAINERS: List[MLIExplainerId] = [
        MLIExplainerId.NLP_VECTORIZER_LINEAR_MODEL,
        MLIExplainerId.NLP_LEAVE_ONE_COVARIATE_OUT,
    ]

    def __init__(
        self,
        client: "_core.Client",
        mli_key: str,
        experiment_key: str,
        explainer_info: _commons_mli._ExplainerInfo,
    ) -> None:
        super().__init__(
            client=client,
            mli_key=mli_key,
            experiment_key=experiment_key,
            explainer_info=explainer_info,
            explanation_type=_ExplanationType.NLP_LOCO,
            explanation_format=_ExplanationFormat.JSON,
        )
        self._local_explanation_type = _ExplanationType.NLP_LOCAL_LOCO

        self._local_explanation_format = _ExplanationFormat.JSON
        self._text_features: Optional[List[str]] = None

    def get_text_features(self) -> List[str]:
        if not self._text_features:
            filters = self._get_index_file()[_KEY_FILTERS]
            text_feature_filter = [
                fltr for fltr in filters if fltr[_KEY_TYPE] == _FILTER_TEXT_FEATURE
            ]
            self._text_features = text_feature_filter[0][_KEY_VALUES]
        return self._text_features

    def get_plot(
        self,
        *,
        row_number: Optional[int] = None,
        class_name: Optional[str] = None,
        text_feature: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Plots the explanation.

        Args:
            row_number: Local explanation for the given row_number.
            class_name: The name of the class in multinomial classification,
                if not provided the first class from the set of available classes in
                the model will be selected (use the method `get_classes()` to view
                available classes).
            text_feature: Select the text feature to plot, if not provided all
                text features will be selected (use the method `get_text_features`
                to view available text features)

        Returns:
            The plot in Vega Lite (v5) format
        """
        class_name = self._determine_class_name(class_name)
        return self._plot_from_feat_imp_explanation(
            row_number=row_number, class_name=class_name, text_feature=text_feature
        )

    def _plot_from_feat_imp_explanation(
        self,
        row_number: Optional[int] = None,
        class_name: Optional[str] = None,
        text_feature: str = "",
    ) -> Dict[str, Any]:
        data: List[Dict[str, Any]]
        if row_number is not None:
            if row_number < 0:
                raise ValueError("Row number must be a positive integer.")

            if not text_feature:
                text_feature = self.get_text_features()[0]
            explanation_filter = self._determine_explanation_filters(
                explain_feature="", explain_class=class_name, text_feature=text_feature
            )
            local_result = self._get_local_result(
                explanation_filter=explanation_filter,
                row_number=row_number,
                local_explanation_format=self._local_explanation_format,
                local_explanation_type=self._local_explanation_type,
                page_size=1000,
            )
            data = local_result[_KEY_DATA]

        else:
            explanation_filter = self._determine_explanation_filters(
                explain_feature="", explain_class=class_name
            )
            global_result = self._get_global_explanation_result(
                explanation_filter=explanation_filter, page_size=1000
            )

            data = global_result[_KEY_DATA]

        for point in data:
            point[_KEY_VALUE] = round(point[_KEY_VALUE], 6)

        index_file = self._get_index_file()
        metrics = self._get_metric_info_string(index_file.get(_KEY_METRICS))
        y_axis_label = index_file.get(_KEY_Y_AXIS_LABEL, "Feature name")
        x_axis_label = index_file.get(_KEY_X_AXIS_LABEL, "Value")

        return _VegaPlot.create_bar_plot(
            explainer_name=self._explainer_info.name,
            data=data,
            x_axis=_KEY_VALUE,
            y_axis=_KEY_LABEL,
            x_axis_title=x_axis_label,
            y_axis_title=y_axis_label,
            metrics=metrics,
            show_value_bias=False,
            height=len(data) * 30,
        )


class PDPExplanationPlot(_ByorExplanationPlot):
    """Handles plots for the following explainers:

    * Partial Dependence Plot
    * NLP Partial Dependence Plot
    """

    COMPATIBLE_EXPLAINERS: List[MLIExplainerId] = [
        MLIExplainerId.PARTIAL_DEPENDENCE_PLOT,
        MLIExplainerId.NLP_PARTIAL_DEPENDENCE_PLOT,
    ]

    def __init__(
        self,
        client: "_core.Client",
        mli_key: str,
        experiment_key: str,
        explainer_info: _commons_mli._ExplainerInfo,
    ) -> None:
        super().__init__(
            client=client,
            mli_key=mli_key,
            experiment_key=experiment_key,
            explainer_info=explainer_info,
            explanation_type=_ExplanationType.PDP,
            explanation_format=_ExplanationFormat.JSON,
        )
        self._local_explanation_type = _ExplanationType.LOCAL_PDP
        self._local_explanation_format = _ExplanationFormat.JAY

    def get_plot(
        self,
        *,
        row_number: Optional[int] = None,
        class_name: Optional[str] = None,
        feature_name: Optional[str] = None,
        partial_dependence_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Plots the explanation.

        Args:
            row_number: Local explanation for the given row_number.
            class_name: The name of the class in multinomial classification,
                if not provided the first class from the set of available classes in
                the model will be selected (use the method `get_classes()` to view
                available classes).
            feature_name: The name of the feature to plot, if not provided the
                first feature from the set of available features in the model will be
                selected (use the method `get_feature_names()` to view available
                feature names)
            partial_dependence_type: Override default plot type, available
                options are categorical and numeric

        Returns:
            The plot in Vega Lite (v5) format
        """
        class_name = self._determine_class_name(class_name)
        feature_name = self._determine_feature_name(feature_name)
        return self._plot_pdp(
            row_number=row_number,
            class_name=class_name,
            feature_name=feature_name,
            partial_dependence_type=partial_dependence_type,
        )

    @staticmethod
    def _get_pdp_histogram_values(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        for index, point in enumerate(data):
            if index != len(data) - 1:
                point["x_continuous"] = data[index + 1]["x"]

            if point["frequency"] is None:
                point["frequency"] = 0

        return data

    def _plot_pdp(
        self,
        row_number: Optional[int] = None,
        class_name: Optional[str] = None,
        feature_name: Optional[str] = None,
        partial_dependence_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        feature = self._get_feature_dict(feature_name)
        default_pd_type: str = feature[_KEY_FEATURE_TYPE][0]

        available_pd_types: List[str]
        if _KEY_ALTERNATE_PDP_TYPE in feature:
            available_pd_types = [_KEY_PDP_NUM_TYPE, _KEY_PDP_CAT_TYPE]
        else:
            available_pd_types = [default_pd_type]

        if not partial_dependence_type:
            partial_dependence_type = default_pd_type
        elif partial_dependence_type not in available_pd_types:
            raise ValueError(
                f"Invalid partial dependency type '{partial_dependence_type}'. "
                f"Possible values are {available_pd_types}."
            )

        pdp_explanation = self._get_global_explanation_file(
            class_name=class_name,
            feature_name=feature_name,
            class_key_name=_KEY_FILES
            if default_pd_type == partial_dependence_type
            else _KEY_ALTERNATE_PDP_TYPE,
        )
        global_data = pdp_explanation[_KEY_DATA]
        for point in global_data:
            if not point[_KEY_OOR]:
                # point not out of range
                point[_BAND_TOP] = point[_KEY_PD] + point[_KEY_SD]
                point[_BAND_BOTTOM] = point[_KEY_PD] - point[_KEY_SD]

        local_data: List[Dict[str, Any]] = []
        local_result: Dict[str, Any] = {_KEY_PREDICTION: None, _KEY_DATA: local_data}
        if row_number is not None:
            if row_number < 0:
                raise ValueError("Row number must be a positive integer.")

            explanation_filter = self._determine_explanation_filters(
                explain_feature=feature_name, explain_class=class_name
            )
            local_result = self._get_local_result(
                explanation_filter=explanation_filter,
                row_number=row_number,
                local_explanation_format=self._local_explanation_format,
                local_explanation_type=self._local_explanation_type,
            )
            local_data = local_result[_KEY_DATA]
            for point in local_data:
                if isinstance(point[_KEY_BIN], str) and point[_KEY_BIN].isdigit():
                    point[_KEY_BIN] = float(point[_KEY_BIN])

        histogram_data: List[Dict[str, Any]] = []
        numeric = partial_dependence_type == _KEY_PDP_NUM_TYPE
        if numeric:
            if _KEY_PDP_NUM_HIST in pdp_explanation:
                histogram_data = self._get_pdp_histogram_values(
                    pdp_explanation[_KEY_PDP_NUM_HIST]
                )
        else:
            # partial_dependence_type is categorical
            if _KEY_PDP_CAT_HIST in pdp_explanation:
                histogram_data = pdp_explanation[_KEY_PDP_CAT_HIST]

        return _VegaPlot.create_pdp_plot(
            explainer_name=self._explainer_info.name,
            numeric=numeric,
            pd_data=global_data,
            ice_data=local_data,
            histogram_data=histogram_data,
            prediction_value=local_result[_KEY_PREDICTION],
            metrics="",
            feature_name=feature_name,
        )


class RandomForestPDPExplanationPlot(_SurrogateExplanationPlot):
    """Handles plots for the following explainer:

    * Random Forest Partial Dependence Plot
    """

    COMPATIBLE_EXPLAINERS: List[MLIExplainerId] = [
        MLIExplainerId.RANDOM_FOREST_PARTIAL_DEPENDENCE_PLOT,
    ]

    def __init__(
        self,
        client: "_core.Client",
        mli_key: str,
        experiment_key: str,
        explainer_info: _commons_mli._ExplainerInfo,
    ) -> None:
        super().__init__(
            client=client,
            mli_key=mli_key,
            experiment_key=experiment_key,
            explainer_info=explainer_info,
        )
        self._pdp_data: Optional[List[Dict[str, Any]]] = None

    def _get_pdp_data(self) -> List[Dict[str, Any]]:
        if not self._pdp_data:
            pdp = self._get_json("pdp.json")
            self._pdp_data = pdp["partial_dependence_data"]
        return self._pdp_data

    def get_feature_names(self) -> List[str]:
        pdp_data = self._get_pdp_data()
        return [feat["columns"][0]["description"] for feat in pdp_data]

    def _get_rf_pdp_global_data(
        self, feature_name: str
    ) -> Tuple[List[Dict[str, Any]], str, bool]:
        pdp_data_list = self._get_pdp_data()
        numeric: bool = True
        out_pdp_data: List[Dict[str, Any]] = []
        for pdp_data in pdp_data_list:
            data = pdp_data[_KEY_DATA]
            variableLabel = pdp_data["columns"][0]["description"]
            if variableLabel == feature_name:
                numeric = pdp_data["columns"][0]["type"] != "string"
                for bin_, pd, sd, _sd_err in zip(*data):
                    out_pdp_data.append(
                        {
                            _KEY_BIN: bin_,
                            _KEY_PD: pd,
                            _KEY_SD: sd,
                            _BAND_TOP: pd + sd,
                            _BAND_BOTTOM: pd - sd,
                            _KEY_OOR: False,
                        }
                    )
                break
        return out_pdp_data, feature_name, numeric

    def _get_rf_ice(self, row_number: int, feature_name: str) -> List[Dict[str, Any]]:
        local_result_str: str = (
            self._client._backend.get_individual_conditional_expectation(
                row_offset=row_number, mli_job_key=self._mli_key
            )
        )
        local_rf_pdp: List[Dict[str, Any]] = json.loads(local_result_str)

        ice_data: List[Dict[str, Any]] = []
        for per_feat in local_rf_pdp:
            if per_feat[_KEY_COLUMN_NAME] != feature_name:
                continue
            data = per_feat[_KEY_DATA]
            for bin_name, ice_val in zip(*data):
                bin_name = bin_name if not bin_name.isdigit() else float(bin_name)
                ice_data.append({_KEY_BIN: bin_name, _KEY_ICE: ice_val})
        return ice_data

    def _get_prediction_value(self, row_number: int) -> float:
        pred_data = self._get_local_result(
            row_number=row_number, frame_name="modelpreds_frame.bin"
        )
        columns = pred_data[_KEY_COLUMNS]
        if columns and columns[0] == _MODEL_PRED:
            data = pred_data[_KEY_DATA]
            return float(data[0][0])
        else:
            raise ValueError(f"Invalid prediction data for {self._explainer_info.name}")

    def get_plot(
        self, *, row_number: Optional[int] = None, feature_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Plots the explanation.

        Args:
            row_number: Local explanation for the given row_number.
            feature_name: The name of the feature to plot, if not provided the
                first feature from the set of available features in the model will be
                selected (use the method `get_feature_names()` to view available
                feature names)

        Returns:
            The plot in Vega Lite (v5) format
        """
        feature_names = self.get_feature_names()
        if feature_name and feature_name not in feature_names:
            raise ValueError(
                f"invalid feature name '{feature_name}'. possible values are "
                f"{feature_names}."
            )
        feature_name = feature_name or feature_names[0]
        pdp_data, feature_name, numeric = self._get_rf_pdp_global_data(feature_name)
        local_data: List[Dict[str, Any]] = []
        prediction_value: Optional[float] = None
        if row_number is not None:
            if row_number < 0:
                raise ValueError("Row number must be a positive integer.")
            local_data = self._get_rf_ice(
                row_number=row_number, feature_name=feature_name
            )
            prediction_value = self._get_prediction_value(row_number=row_number)
        histogram_data: List[Dict[str, Any]] = []

        return _VegaPlot.create_pdp_plot(
            explainer_name=self._explainer_info.name,
            numeric=numeric,
            pd_data=pdp_data,
            ice_data=local_data,
            histogram_data=histogram_data,
            prediction_value=prediction_value,
            metrics="",
            feature_name=feature_name,
        )


class DecisionTreeExplanationPlot(_ByorExplanationPlot):
    """Handles plots for the following explainer:

    * Decision Tree
    """

    COMPATIBLE_EXPLAINERS: List[MLIExplainerId] = [
        MLIExplainerId.DECISION_TREE,
    ]

    def __init__(
        self,
        client: "_core.Client",
        mli_key: str,
        experiment_key: str,
        explainer_info: _commons_mli._ExplainerInfo,
    ) -> None:
        super().__init__(
            client=client,
            mli_key=mli_key,
            experiment_key=experiment_key,
            explainer_info=explainer_info,
            explanation_type=_ExplanationType.DT,
            explanation_format=_ExplanationFormat.JSON,
        )
        self._local_explanation_type = _ExplanationType.LOCAL_DT
        self._local_explanation_format = _ExplanationFormat.JSON

    def get_plot(
        self,
        *,
        row_number: Optional[int] = None,
        class_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Plots the explanation.

        Args:
            row_number: Local explanation for the given row_number.
            class_name: The name of the class in multinomial classification,
                if not provided the first class from the set of available classes in
                the model will be selected (use the method `get_classes()` to view
                available classes).

        Returns:
            The plot in Vega Lite (v5) format
        """
        class_name = self._determine_class_name(class_name)

        if row_number is not None:
            if row_number < 0:
                raise ValueError("Row number must be a positive integer.")
            local_result = self._get_local_result(
                explanation_filter=self._determine_explanation_filters(
                    explain_class=class_name
                ),
                local_explanation_format=self._local_explanation_format,
                local_explanation_type=self._local_explanation_type,
                row_number=row_number,
            )
            data = local_result[_KEY_DATA]
        else:
            result = self._get_global_explanation_file(class_name=class_name)
            data = result[_KEY_DATA]
        metrics = self._get_metric_info_string(self._get_index_file().get(_KEY_METRICS))
        return _VegaPlot.create_decision_tree_plot(
            explainer_name=self._explainer_info.name, data=data, metrics=metrics
        )


class ShapleySummaryExplanationPlot(_ByorExplanationPlot):
    """Handles plots for the following explainer:

    * Shapley Summary Plot for Original Features
    """

    COMPATIBLE_EXPLAINERS: List[MLIExplainerId] = [
        MLIExplainerId.SHAPLEY_SUMMARY_PLOT_FOR_ORIGINAL_FEATURES,
    ]

    def __init__(
        self,
        client: "_core.Client",
        mli_key: str,
        experiment_key: str,
        explainer_info: _commons_mli._ExplainerInfo,
    ) -> None:
        super().__init__(
            client=client,
            mli_key=mli_key,
            experiment_key=experiment_key,
            explainer_info=explainer_info,
            explanation_type=_ExplanationType.SHAPLEYSUMMARY,
            explanation_format=_ExplanationFormat.JSON,
        )

    def get_total_pages(self, class_name: str) -> int:
        return len(self._get_index_file()[_KEY_FILES][class_name].keys())

    def get_plot(
        self, *, class_name: Optional[str] = None, page_num: int = 1
    ) -> Dict[str, Any]:
        """Plots the explanation.

        Args:
            class_name: The name of the class in multinomial classification,
                if not provided the first class from the set of available classes in
                the model will be selected (use the method `get_classes()` to view
                available classes).
            page_num: Select the page (use the method `get_total_pages()` to
                view the total available number of pages)

        Returns:
            The plot in Vega Lite (v5) format
        """
        class_name = self._determine_class_name(class_name)

        total_pages = self.get_total_pages(class_name)
        if page_num <= 0 or page_num > total_pages:
            err_msg = "Invalid page number, "
            err_msg += (
                "There is only one page available."
                if total_pages == 1
                else f"Available pages: 1 - {total_pages}"
            )
            raise ValueError(err_msg)

        page_num -= 1

        data_points = self._get_global_explanation_file(
            class_name, shap_sum_page=page_num
        ).get(_KEY_DATA)
        data_avg_higher_than_zero = []
        data_avg_is_none = []
        for index, point in enumerate(data_points):
            if point["avg_high_value"] is None:
                point.pop("avg_high_value")
                data_avg_is_none.append(point)
            else:
                data_avg_higher_than_zero.append(data_points[index])

        plot_metrics_info = self._get_metric_info_string(
            self._get_index_file().get(_KEY_METRICS)
        )
        return _VegaPlot.create_shapley_summary_plot(
            explainer_name=self._explainer_info.name,
            data_avg_is_none=data_avg_is_none,
            data_avg_higher_than_zero=data_avg_higher_than_zero,
            metrics=plot_metrics_info,
        )


class ExplanationPlots(collections.abc.Mapping):
    """This class acts as a container for the available explanation plots. Users can
    retrieve the plot object using the squire brackets"""

    def __init__(
        self,
        explainer_infos: List[_commons_mli._ExplainerInfo],
        client: "_core.Client",
        mli_key: str,
        experiment_key: str,
    ):
        self._explanations_plots = ExplanationPlot._create_explanation_plots(
            client=client,
            mli_key=mli_key,
            explainer_infos=explainer_infos,
            experiment_key=experiment_key,
        )

        self._id_to_plot: Dict[
            MLIExplainerId, List[ExplanationPlot]
        ] = collections.defaultdict(list)
        self._name_to_eid: Dict[str, MLIExplainerId] = {}
        for plot in self._explanations_plots:
            self._id_to_plot[plot._explainer_id].append(plot)
            self._name_to_eid[plot._explainer_info.name] = plot._explainer_id

        headers = ["Explainer Id", "Explainer Name"]
        data = []
        for name, eid in self._name_to_eid.items():
            data.append(
                [
                    eid.name,
                    name,
                ]
            )
        self._table = _utils.Table(headers=headers, data=data)

    def __len__(self) -> int:
        return len(self._explanations_plots)

    def __getitem__(self, ref: Union[str, MLIExplainerId]) -> List[ExplanationPlot]:
        plots = []
        if isinstance(ref, str):
            try:
                eid = MLIExplainerId.from_value(ref)
            except ValueError:
                pass
            else:
                plots = self._id_to_plot.get(eid)

            if not plots:
                try:
                    eid = getattr(MLIExplainerId, ref)
                except AttributeError:
                    pass
                else:
                    plots = self._id_to_plot.get(eid)

            if not plots and ref in self._name_to_eid:
                plots = self._id_to_plot[self._name_to_eid[ref]]

        elif isinstance(ref, MLIExplainerId):
            plots = self._id_to_plot.get(ref)

        if not plots:
            raise KeyError(f"{ref} is not a valid explainer id or explainer name")
        return plots

    def __iter__(self) -> Iterator[ExplanationPlot]:
        return iter(self._explanations_plots)

    def __repr__(self) -> str:
        return self._table.__repr__()

    def _repr_html_(self) -> str:
        return self._table._repr_html_()
