# -----------------------------------------------------------------------
#             *** WARNING: DO NOT MODIFY THIS FILE ***
#
#         Instead, modify h2oai/service.proto and run "make proto".
# -----------------------------------------------------------------------

import datetime
import json
import mimetypes
import os.path
import random
import string
import time
from functools import partial
from typing import Any
from typing import Callable
from typing import Dict
from typing import List
from typing import Mapping
from typing import NamedTuple
from typing import Optional
from urllib.request import urlretrieve

import requests

from _h2oai_client_1_10_1_2 import references
from _h2oai_client_1_10_1_2 import validation
from _h2oai_client_1_10_1_2.messages import *

_secure_cookie_key = "_h2oai_sid"


class RequestError(Exception):
    def __init__(self, message: str):
        self.message = message


class RemoteError(Exception):
    def __init__(self, message: str):
        self.message = message


class OAuth2tokenProvider:
    """Provides the token and make sure it's fresh when required."""

    def __init__(
        self,
        refresh_token: str,
        client_id: str,
        token_endpoint_url: str,
        token_introspection_url: Optional[str] = None,
        access_token: Optional[str] = None,
        client_secret: Optional[str] = None,
        *,
        refresh_expiry_threshold_band: datetime.timedelta = datetime.timedelta(
            seconds=5
        ),
    ) -> None:
        self._access_token = access_token
        self._refresh_token = refresh_token
        self._token_expiry = None

        self._client_id = client_id
        self._client_secret = client_secret

        self._token_endpoint_url = token_endpoint_url
        self._token_introspection_url = token_introspection_url

        self._refresh_expiry_threshold_band = refresh_expiry_threshold_band

    def ensure_fresh_token(self) -> str:
        if self.refresh_possible() and self.refresh_required():
            self.do_refresh()
        return self._access_token

    def refresh_required(self) -> bool:
        if self._access_token is None:
            return True

        now = datetime.datetime.now(datetime.timezone.utc)
        return self._token_expiry is None or (
            self._token_expiry <= (now + self._refresh_expiry_threshold_band)
        )

    def refresh_possible(self) -> bool:
        return self._refresh_token is not None

    def do_refresh(self):
        token_data = self._retrieve_token_data()
        self._access_token = token_data["access_token"]
        self._refresh_token = token_data["refresh_token"]

        token_expires_in = token_data.get("expires_in")
        if token_expires_in:
            self._token_expiry = datetime.datetime.now(
                datetime.timezone.utc
            ) + datetime.timedelta(seconds=int(token_expires_in))
            return

        if self._token_introspection_url:
            token_info = self._retrieve_access_token_info()
            expiry_timestamp = int(token_info["exp"])
            self._token_expiry = datetime.datetime.fromtimestamp(
                expiry_timestamp, tz=datetime.timezone.utc
            )

    def _retrieve_token_data(self) -> Mapping[str, str]:
        data = dict(
            client_id=self._client_id,
            grant_type="refresh_token",
            refresh_token=self._refresh_token,
        )
        if self._client_secret:
            data["client_secret"] = self._client_secret

        resp = requests.post(self._token_endpoint_url, data=data)
        resp.raise_for_status()

        return resp.json()

    def _retrieve_access_token_info(self) -> Mapping:
        data = dict(client_id=self._client_id, token=self._access_token)

        if self._client_secret:
            data["client_secret"] = self._client_secret

        resp = requests.post(self._token_introspection_url, data=data)
        resp.raise_for_status()

        return resp.json()


class Client:
    def __init__(
        self,
        address: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
        verify=True,
        cert=None,
        authentication_method: Optional[str] = None,
        *,
        token_provider: Callable[[], str] = None,
    ) -> None:
        self._autoviz = None
        self.address = address
        self._cid = 0
        self._session = requests.Session()
        self._session.headers["DAI-Client-Type"] = "PYCLIENT"
        self._session.verify = verify
        self._session.cert = cert
        self.authentication_method = authentication_method
        self._token_provider = token_provider

        if not token_provider:
            self._authenticate(username, password)

    def _authenticate(self, username, password):
        use_tls_authentication = self.authentication_method == "tls_certificate"

        if not use_tls_authentication and not username:
            raise ValueError("username needs to be provided")
        if not use_tls_authentication and not password:
            raise ValueError("password needs to be provided")

        if not use_tls_authentication:
            res = self._login(username, password)
        else:
            res = self._tls_auth()

        if res.status_code != requests.codes.ok:
            raise RequestError(
                "Authentication request failed {} (status={}): {}".format(
                    self.address, res.status_code, res.text
                )
            )
        if _secure_cookie_key not in self._session.cookies.keys():
            raise RequestError(
                "Authentication unsuccessful. Unable to obtain authentication token."
            )

    def _tls_auth(self):
        return self._session.get(self.address + "/tls_auth")

    def _login(self, username, password):
        login_url = f"{self.address}/login"
        if self.authentication_method:
            login_url = f"{self.address}/login/{self.authentication_method}"

        headers = {"X-XSRFToken": self._get_xsrf_token(login_url)}
        return self._session.post(
            login_url,
            data=dict(username=username, password=password),
            headers=headers,
        )

    def _get_xsrf_token(self, address: Optional[str] = None) -> str:
        """Retrieves XSRF token from cookie. If missing, tries to make empty request
        to `address` or `/` to acquire the token

        :param address: URL to which GET request is made, which response should contain
                        the XSRF token cookie
        """
        _address = address or self.address
        if "_xsrf" not in self._session.cookies.get_dict():
            # Make empty authenticated call to main page to acquire XSRF cookie
            self._session.get(_address)
        return self._session.cookies.get_dict().get("_xsrf", "")

    def _get_authorization_headers(self) -> Dict[str, str]:
        headers = {"X-XSRFToken": self._get_xsrf_token()}
        if not self._token_provider:
            return headers
        token = self._token_provider()
        headers["Authorization"] = f"Bearer {token}"
        return headers

    def _request(self, method: str, params: dict) -> Any:
        self._cid = self._cid + 1
        req = json.dumps(dict(id=self._cid, method="api_" + method, params=params))
        res = self._session.post(
            self.address + "/rpc", data=req, headers=self._get_authorization_headers()
        )
        if res.status_code != requests.codes.ok:
            raise RequestError(
                "Remote request failed {}#{} (status={}): ".format(
                    self.address, method, res.status_code
                )
            )

        response = res.json()
        if "error" in response:
            raise RemoteError(response["error"])

        return response["result"]

    def download(self, src_path: str, dest_path: str) -> str:
        """Downloads file from DriverlessAI server

        :param src_path: Remote file path
        :param dest_path: Local path, where file will be saved
        """
        url = self.address + "/files/" + src_path
        res = self._session.get(url, headers=self._get_authorization_headers())
        if res.status_code != requests.codes.ok:
            raise RequestError(
                "Download failed {}; {} (status={}): ".format(
                    self.address, src_path, res.status_code
                )
            )
        if os.path.isdir(dest_path):
            dest_path = os.path.join(dest_path, os.path.basename(src_path))
        with open(dest_path, "wb") as f:
            f.write(res.content)

        return dest_path

    @property
    def autoviz(self):
        if not self._autoviz:
            self._autoviz = AutovizClient(self)
        return self._autoviz


    #
    # NOTE: This python file is not used by the server at runtime.
    # These are extension methods that are appended to the _h2oai_client_1_10_1_2 module
    #   at development-time (via make proto).
    #
    # FIXME This is repetitive.

    def create_dataset_sync(self, filepath: str) -> Dataset:
        """Import a dataset.

        :param filepath: A path specifying the location of the data to upload.
        :returns: a new :class:`Dataset` instance.

        """

        key = self.create_dataset_from_file(filepath)
        job = self._wait_for_dataset(key)
        return job.entity

    def start_experiment_sync(self, dataset_key: str, target_col: str, is_classification: bool,
                              accuracy: int, time: int, interpretability: int,
                              scorer=None,
                              score_f_name: str = None, **kwargs) -> Model:
        r"""Start an experiment.

        :param dataset_key: Training dataset key
        :type dataset_key: ``str``
        :param target_col: Name of the targed column
        :type target_col: ``str``
        :param is_classification: `True` for classification problem, `False` for regression
        :type is_classification: ``bool``
        :param accuracy: Accuracy setting [1-10]
        :param time: Time setting [1-10]
        :param interpretability: Interpretability setting [1-10]
        :param score: <same as score_f_name> for backwards compatibiilty
        :type score: ``str``
        :param score_f_name: Name of one of the `available scorers` Default `None` - automatically decided
        :type score_f_name: ``str``
        :param \**kwargs:
            See below

        :Keyword Arguments:
            * *validset_key* (``str``) --
                Validation daset key
            * *testset_key* (``str``) --
                Test daset key
            * *weight_col* (``str``) --
                Weights column name
            * *fold_col* (``str``) --
                Fold column name
            * *cols_to_drop* (``list``) --
                List of column to be dropped
            * *enable_gpus* (``bool``) --
                Allow GPU usage in experiment. Default `True`
            * *seed* (``int``) --
                Seed for PRNG. Default `False`
            * *time_col* (``str``) --
                Time column name, containing time ordering for timeseries problems
            * *is_timeseries* (``bool``) --
                Specifies whether problem is timeseries. Default `False`
            * *time_groups_columns* (``list``) --
                List of column names, contributing to time ordering
            * *unavailable_columns_at_prediction_time* (``list``) --
                List of column names, which won't be present at prediction time
                in the testing dataset
            * *time_period_in_seconds* (``int``) --
                The length of the time period in seconds, used in timeseries problems
            * *num_prediction_periods* (``int``) --
                Timeseries forecast horizont in time period units
            * *num_gap_periods* (``int``) --
                Number of time periods after which forecast starts
            * *config_overrides* (``str``) --
                Driverless AI config overrides for separate experiment in TOML string format
            * *resumed_model_key* (``str``) --
                Experiment key, used for retraining/re-ensembling/starting from checkpoint
            * *force_skip_acceptance_tests* (``bool``) --
                Force experiment to skip custom recipes acceptance tests to finish,
                which may lead to not having all expected custom recipes
            * *experiment_name* (``str``) --
                Display name of newly started experiment
            * *cols_imputation* (``List[ColumnImputation]``) --
                List of column imputations for dataset. Ref `messages::ColumnImputation`
            * *is_image* (``bool``) --
                Specifies whether problem is image based. Default `False`

        :returns: a new :class:`Model` instance.
        """
        if scorer is not None:
            score_f_name = scorer
        params = ModelParameters(
            dataset=references.DatasetReference(dataset_key),
            resumed_model=references.ModelReference(
                kwargs.get('resumed_model_key', '')),
            target_col=target_col,
            weight_col=kwargs.get('weight_col', None),
            fold_col=kwargs.get('fold_col', None),
            orig_time_col=kwargs.get('orig_time_col',
                kwargs.get('time_col', None)),
            time_col=kwargs.get('time_col', None),
            is_classification=is_classification,
            cols_to_drop=kwargs.get('cols_to_drop', []),
            validset=references.DatasetReference(
                kwargs.get('validset_key', '')),
            testset=references.DatasetReference(
                kwargs.get('testset_key', '')),
            enable_gpus=kwargs.get('enable_gpus', True),
            seed=kwargs.get('seed', False),
            accuracy=accuracy,
            time=time,
            interpretability=interpretability,
            score_f_name=score_f_name,
            time_groups_columns=kwargs.get('time_groups_columns', None),
            unavailable_columns_at_prediction_time=kwargs.get(
                'unavailable_columns_at_prediction_time', []),
            time_period_in_seconds=kwargs.get('time_period_in_seconds', None),
            num_prediction_periods=kwargs.get('num_prediction_periods', None),
            num_gap_periods=kwargs.get('num_gap_periods', None),
            is_timeseries=kwargs.get('is_timeseries', False),
            cols_imputation=kwargs.get('cols_imputation', []),
            config_overrides=kwargs.get('config_overrides', None),
            custom_features=[],
            is_image=kwargs.get('is_image', False),
        )
        # If custom recipes acceptance jobs are running, wait for them to finish
        if not kwargs.get('force_skip_acceptance_tests', False):
            self._wait_for_custom_recipes_acceptance_tests()
        key = self.start_experiment(params, kwargs.get('experiment_name', ''))
        job = self._wait_for_model(key)
        return job.entity

    def make_prediction_sync(self, model_key: str, dataset_key: str, output_margin: bool,
                             pred_contribs: bool, pred_contribs_original: bool = False,
                             enable_mojo: bool = True,
                             fast_approx: bool = False,
                             fast_approx_contribs: bool = False,
                             keep_non_missing_actuals: bool = False, include_columns: list = [],
                             pred_labels: bool = False):
        """Make a prediction from a model.

        :param model_key: Model key.
        :param dataset_key: Dataset key on which prediction will be made
        :param output_margin: Whether to return predictions as margins (in link space)
        :param pred_contribs: Whether to return prediction contributions (transformed or original space)
        :param pred_contribs_original: Whether to return prediction contributions in original feature space
        :param enable_mojo: Whether to use MOJO (if available) to make predictions
        :param fast_approx: Whether to speed up prediction with approximation
        :param fast_approx_contribs: Whether to speed up prediction contributions with approximation
        :param keep_non_missing_actuals:
        :param include_columns: List of column names, which should be included in output csv
        :param pred_labels: Whether to return labels in addition to probabilities for classification (last column). Ignored for regression.
        :returns: a new :class:`Predictions` instance.

        """
        key = self.make_prediction(
            model_key=model_key, dataset_key=dataset_key, output_margin=output_margin,
            pred_contribs=pred_contribs, pred_contribs_original=pred_contribs_original,
            enable_mojo=enable_mojo,
            fast_approx=fast_approx,
            fast_approx_contribs=fast_approx_contribs,
            keep_non_missing_actuals=keep_non_missing_actuals, include_columns=include_columns,
            pred_labels=pred_labels,
        )
        job = self._wait_for_prediction(key)
        return job.entity

    def download_prediction_sync(self, dest_path: str, model_key: str, dataset_type: str, include_columns: list):
        """ Downloads train/valid/test set predictions into csv file

        :param dest_path: Destination path, where csv will be downloaded
        :param model_key: Model key for which predictions will be downloaded
        :param dataset_type: Type of dataset for which predictions will be downloaded. Available options are "train", "valid" or "test"
        :param include_columns: List of columns from dataset, which will be included in predictions csv
        :returns: Local path to csv
        """
        if dataset_type not in ['train', 'valid', 'test']:
            raise ValueError('`dataset_type` param can only be "train", "valid" or "test"')

        key = self.download_prediction(model_key, dataset_type, include_columns)
        job = self._wait_for_prediction(key)
        local_path = self.download(job.entity.predictions_csv_path, dest_path)
        return local_path

    def make_autodoc_sync(self, *args, **kwargs):
        """Alternative method for creating AutoDoc, as name Autoreport will
        become deprecated

        Further description in `make_autoreport_sync`
        """
        return self.make_autoreport_sync(*args, **kwargs)

    def make_autoreport_sync(self, model_key: str, template_path: str = '',
                             config_overrides: str = '',
                             **kwargs):
        """Make an autoreport from a Driverless AI experiment.

        :param model_key: Model key.
        :param template_path: Path to custom autoreport template, which will be uploaded and used during rendering
        :param config_overrides: TOML string format with configurations overrides for AutoDoc
        :param \**kwargs:
            See below

        :Keyword Arguments:
            * *mli_key* (``str``) --
                MLI instance key
            * *autoviz_key* (``str``) --
                Visualization key
            * *individual_rows* (``list``) --
                List of row indices for rows of interest in training dataset,
                for which additional information can be shown (ICE, LOCO,
                KLIME)
            * *placeholders* (``dict``) --
                Additional text to be added to documentation in dict format,
                key is the name of the placeholder in template, value is the
                text content to be added in place of placeholder
            * *external_dataset_keys* (``list``) --
                List of additional dataset keys, to be used for computing
                different statistics and generating plots.

        :returns: a new :class:`AutoReport` instance.

        """
        if template_path:
            paths = self.perform_upload(template_path, skip_parse=True)
            template_path = paths[0] if paths and len(
                paths) > 0 else template_path

        key = self.make_autoreport(
            model_key,
            kwargs.get('mli_key'),
            kwargs.get('individual_rows'),
            kwargs.get('autoviz_key'),
            template_path,
            kwargs.get('placeholders', {}),
            kwargs.get('external_dataset_keys', []),
            config_overrides,
            kwargs.get('reuse_model_key', False),
        )
        job = self._wait_for_autoreport(key)
        return job.entity

    def create_and_download_autodoc(self, *args, **kwargs):
        """Alternative method for creating AutoDoc, as name Autoreport will
        become deprecated

        Further description in `create_and_download_autoreport`
        """
        return self.create_and_download_autoreport(*args, **kwargs)

    def create_and_download_autoreport(self, model_key: str,
                                       template_path: str = '',
                                       config_overrides: str = '',
                                       dest_path: str = '.', **kwargs):

        """Make and download an autoreport from a Driverless AI experiment.

        :param model_key: Model key.
        :param template_path: Path to custom autoreport template, which will be uploaded and used during rendering
        :param config_overrides: TOML string format with configurations overrides for AutoDoc
        :param dest_path: The local path where the AutoReport should be saved.
        :param \**kwargs:
            See below

        :Keyword Arguments:
            * *mli_key* (``str``) --
                MLI instance key
            * *autoviz_key* (``str``) --
                Visualization key
            * *individual_rows* (``list``) --
                List of row indices for rows of interest in training dataset,
                for which additional information can be shown (ICE, LOCO,
                KLIME)
            * *placeholders* (``dict``) --
                Additional text to be added to documentation in dict format,
                key is the name of the placeholder in template, value is the
                text content to be added in place of placeholder
            * *external_dataset_keys* (``list``) --
                List of additional dataset keys, to be used for computing
                different statistics and generating plots.

        :returns: str: the path to the saved AutoReport

        """
        # Create autoreport
        autoreport = self.make_autoreport_sync(model_key, template_path,
                                               config_overrides, **kwargs)

        # Download autoreport to dest_path
        local_path = self.download(autoreport.report_path, dest_path)

        return local_path

    def fit_transform_batch_sync(
        self,
        model_key,
        training_dataset_key,
        validation_dataset_key,
        test_dataset_key,
        validation_split_fraction,
        seed,
        fold_column
    ) -> Transformation:
        """
        Use model feature engineering to transform provided dataset
        and get engineered feature in output CSV

        :param model_key: Key of the model to use for transformation
        :param training_dataset_key: Dataset key which will be used for training
        :param validation_dataset_key: Dataset key which will be used for validation
        :param test_dataset_key: Dataset key which will be used for testing
        :param validation_split_fraction: If not having valid dataset,
            split ratio for splitting training dataset
        :param seed: Random seed for splitting
        :param fold_column: Fold column used for splitting

        """
        key = self.fit_transform_batch(
            model_key,
            training_dataset_key,
            validation_dataset_key,
            test_dataset_key,
            validation_split_fraction,
            seed,
            fold_column,
        )
        job = self._wait_for_transformation(key)
        return job.entity

    def make_model_diagnostic_sync(self, model_key: str, dataset_key: str) -> Dataset:
        """Make model diagnostics from a model and dataset

        :param model_key: Model key.
        :param dataset_key: Dataset key
        :returns: a new :class:`ModelDiagnostic` instance.

        """

        key = self.get_model_diagnostic(model_key, dataset_key)
        job = self._wait_for_model_diagnostic(key)
        return job.entity

    def run_interpretation_sync(self, dai_model_key: str, dataset_key: str, target_col: str, **kwargs):
        r"""Run MLI.

        :param dai_model_key: Driverless AI Model key, which will be interpreted
        :param dataset_key: Dataset key
        :param target_col: Target column name
        :param \**kwargs:
            See below

        :Keyword Arguments:
            * *use_raw_features* (``bool``) --
                Show interpretation based on the original columns. Default True
            * *prediction_col* (``str``) --
                Prediction column used used for interpretation
            * *weight_col* (``str``) --
                Weight column used by Driverless AI experiment
            * *drop_cols* (``list``) --
                List of columns not used for interpretation
            * *klime_cluster_col* (``str``) --
                Column used to split data into k-LIME clusters
            * *nfolds* (``int``) --
                Number of folds used by the surrogate models. Default 0
            * *sample* (``bool``) --
                Whether the training dataset should be sampled down for the interpretation
            * *sample_num_rows* (``int``) --
                Number of sampled rows. Default -1 == specified by config.toml
            * *qbin_cols* (``list``) --
                List of numeric columns to convert to quantile bins (can help fit surrogate models)
            * *qbin_count* (``int``) --
                Number of quantile bins for the quantile bin columns. Default 0
            * *lime_method* (``str``) --
                LIME method type from ['k-LIME', 'LIME_SUP']. Default 'k-LIME'
            * *dt_tree_depth* (``int``) --
                Max depth of decision tree surrogate model. Default 3
            * *vars_to_pdp* (``int``) --
                Number of variables to use for DAI PDP based on DAI feature importance
                and number of variables to use for surrogate Random Forest PDP based on
                surrogate Random Forest feature importance
            * *dia_cols* (``list``) --
                List of categorical columns to use for disparate impact analysis
            * *debug_model_errors* (``bool``) --
                Whether to build surrogate models on model residuals as a prediction
                column (squared residuals for regression and logloss residuals for
                classification)
            * *debug_model_errors_class* (``str``) --
                Class used to calculate logloss residuals if `debug_model_errors` is
                `True` and the model is a classification model
            * *config_overrides* (``str``) --
                Driverless AI config overrides for separate experiment in TOML string format

        :returns: a new :class:`Interpretation` instance.
        """
        params = InterpretParameters(
            dai_model=references.ModelReference(dai_model_key),
            dataset=references.DatasetReference(dataset_key),
            target_col=target_col,
            use_raw_features=kwargs['use_raw_features'] if 'use_raw_features' in kwargs else True,
            prediction_col=kwargs['prediction_col'] if 'prediction_col' in kwargs else '',
            weight_col=kwargs['weight_col'] if 'weight_col' in kwargs else '',
            drop_cols=kwargs['drop_cols'] if 'drop_cols' in kwargs else [],
            klime_cluster_col=kwargs['klime_cluster_col'] if 'klime_cluster_col' in kwargs else '',
            nfolds=kwargs['nfolds'] if 'nfolds' in kwargs else 0,
            sample=kwargs['sample'] if 'sample' in kwargs else True,
            sample_num_rows=kwargs['sample_num_rows'] if 'sample_num_rows' in kwargs else -1,
            qbin_cols=kwargs['qbin_cols'] if 'qbin_cols' in kwargs else [],
            qbin_count=kwargs['qbin_count'] if 'qbin_count' in kwargs else 0,
            lime_method=kwargs['lime_method'] if 'lime_method' in kwargs else "k-LIME",
            dt_tree_depth=kwargs['dt_tree_depth'] if 'dt_tree_depth' in kwargs else 3,
            vars_to_pdp=kwargs['vars_to_pdp'] if 'vars_to_pdp' in kwargs else 10,
            config_overrides=kwargs['config_overrides'] if 'config_overrides' in kwargs else None,
            dia_cols=kwargs['dia_cols'] if 'dia_cols' in kwargs else [],
            testset=references.DatasetReference(''),
            debug_model_errors=kwargs['debug_model_errors'] if 'debug_model_errors' in kwargs else False,
            debug_model_errors_class=kwargs['debug_model_errors_class'] if 'debug_model_errors_class' in kwargs else '',
        )
        key = self.run_interpretation(params)
        job = self._wait_for_interpretation(key)
        return job.entity

    def run_interpret_timeseries_sync(self, dai_model_key: str, **kwargs):
        r"""Run Interpretation for Time Series

        :param dai_model_key: Driverless AI Time Series Model key, which will be interpreted
        :param \**kwargs:
            See below

        :Keyword Arguments
            * *sample_num_rows* (``int``) --
               Number of rows to sample to generate metrics. Default -1 (All rows)
            * *testset_key* (``int``) --
               Test set key

        :returns: a new :class: `InterpretTimeSeries` instance.

        """

        params = InterpretParameters(
            dataset=references.ModelReference(''),
            target_col=None,
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
            debug_model_errors_class='',
            dai_model=references.ModelReference(dai_model_key),
            testset=references.DatasetReference(kwargs['testset_key'] if 'testset_key' in kwargs else ''),
            sample_num_rows=kwargs['sample_num_rows'] if 'sample_num_rows' in kwargs else -1,
            config_overrides="",
        )
        key = self.run_interpret_timeseries(params)
        job = self._wait_for_interpret_timeseries(key)
        return job.entity

    def build_scoring_pipeline_sync(self, model_key: str, force: bool=False) -> ScoringPipeline:
        """Build scoring pipeline.

        :param model_key: Model key.
        :returns: a new :class:`ScoringPipeline` instance.

        """
        key = self.build_scoring_pipeline(model_key, force)
        job = self._wait_for_scoring_pipeline(key)
        return job.entity

    def build_mojo_pipeline_sync(self, model_key: str, force: bool=False) -> MojoPipeline:
        """Build MOJO pipeline.

        :param model_key: Model key.
        :returns: a new :class:`ScoringPipeline` instance.

        """
        key = self.build_mojo_pipeline(model_key, force)
        job = self._wait_for_mojo_pipeline(key)
        return job.entity

    def perform_upload(self, file_path, skip_parse=False):
        url = self.address + "/upload"
        if skip_parse:
            url += "?noparse=1"

        with open(file_path, 'rb') as f:
            res = self._session.post(
                url,
                files={"dataset": f},
                headers=self._get_authorization_headers(),
            )

            if res.status_code == requests.codes.ok:
                return res.json()
            else:
                return None

    def perform_chunked_upload(self, file_path, skip_parse=False):
        url = self.address + "/chunkedupload"
        if skip_parse:
            url += "?noparse=1"

        chunk_start = 0
        chunk_size = 1024 * 1024
        chunk_end = chunk_size
        total_size = os.path.getsize(file_path)
        file_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=16))
        with open(file_path, 'rb') as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk or len(chunk) <= 0:
                    break

                chunk_end = chunk_start + len(chunk)
                headers = {
                    'Content-Type': 'application/octet-stream',
                    'DAI-File-Id': file_id,
                    'DAI-Filename': os.path.basename(file_path),
                    'DAI-Content-Range': 'bytes {}-{}/{}'.format(chunk_start, chunk_end, total_size),
                }
                headers.update(self._get_authorization_headers())
                res = self._session.post(url, data=chunk, headers=headers)

                if res.status_code == requests.codes.forbidden:
                    raise RequestError(
                        "Remote request failed (status=403): Uploading of dataset is forbidden. Enabled it in config.",
                    )
                elif res.status_code != requests.codes.ok:
                    raise RequestError(
                        "Remote request failed (status={}): ".format(res.status_code),
                    )
                chunk_start += chunk_size

            if res.status_code == requests.codes.ok:
                return [res.text]
            else:
                raise RequestError(
                    "Remote request failed (status={}): ".format(res.status_code),
                )

    def upload_dataset(self, file_path: str) -> str:
        """Upload a dataset

        :param file_path: A path specifying the location of the data to upload.
        :returns: str: REST response

        """
        return self.perform_chunked_upload(file_path)

    def upload_dataset_sync(self, file_path):
        """Upload a dataset and wait for the upload to complete.

        :param file_path: A path specifying the location of the file to upload.
        :returns: a Dataset instance.

        """
        keys = self.upload_dataset(file_path)
        job = self._wait_for_dataset(keys[0])
        return job.entity

    def create_dataset_from_hadoop_sync(self, filepath: str) -> Dataset:
        """Import a dataset.

        :param filepath: A path specifying the location of the data to upload.
        :returns: a new :class:`Dataset` instance.

        """

        key = self.create_dataset_from_hadoop(filepath)
        job = self._wait_for_dataset(key)
        return job.entity

    def create_dataset_from_dtap_sync(self, filepath: str) -> Dataset:
        """Import a dataset.

         :param filepath: A path specifying the location of the data to upload.
         :returns: a new :class:`Dataset` instance.

        """

        key = self.create_dataset_from_dtap(filepath)
        job = self._wait_for_dataset(key)
        return job.entity

    def create_dataset_from_s3_sync(self, filepath: str) -> Dataset:
        """Import a dataset.

        :param filepath: A path specifying the location of the data to upload.
        :returns: a new :class:`Dataset` instance.

        """

        key = self.create_dataset_from_s3(filepath)
        job = self._wait_for_dataset(key)
        return job.entity

    def create_dataset_from_minio_sync(self, filepath: str) -> Dataset:
        """Import a dataset from Minio.

        :param filepath: A path specifying the location of the data to upload.
        :returns: a new :class:`Dataset` instance.

        """

        key = self.create_dataset_from_minio(filepath)
        job = self._wait_for_dataset(key)
        return job.entity

    def create_dataset_from_azure_blob_store_sync(self, filepath: str) -> Dataset:
        """Import a dataset from Azure Blob Storage

        :param: filepath: A path specifying the location of the data to upload.
        :returns: a new :class: `Dataset` instance.

        """

        key = self.create_dataset_from_azr_blob(filepath)
        job = self._wait_for_dataset(key)
        return job.entity

    def create_dataset_from_gcs_sync(self, filepath: str) -> Dataset:
        """Import a dataset from Google Cloud Storage.

        :param filepath: A path specifying the location of the data to upload.
        :returns: a new :class:`Dataset` instance.

        """

        key = self.create_dataset_from_gcs(filepath)
        job = self._wait_for_dataset(key)
        return job.entity

    def create_dataset_from_bigquery_sync(
        self,
        datasetid: str,
        dst: str,
        query: str,
        project: Optional[str] = None,
        location: Optional[str] = None,
    ) -> Dataset:
        """Import a dataset using BigQuery Query

        :param datasetid: Name of BQ Dataset to use for tmp tables
        :param dst: destination filepath within GCS (gs://<bucket>/<file.csv>)
        :param query: SQL query to pass to BQ
        :returns a new :class:`Dataset` instance.
        """
        base_path = dst.replace("gs://", "")
        bucket_name = base_path.split("/")[0]
        dataset_name = (
            base_path.replace(bucket_name, "").replace(".csv", "").strip("/")
        )
        args = GbqCreateDatasetArgs(
            datasetid, bucket_name, dataset_name, query, project, location
        )
        key = self.create_dataset_from_gbq(args)
        job = self._wait_for_dataset(key)
        return job.entity

    def create_dataset_from_snowflake_sync(self, region: str, database: str, warehouse: str, schema: str, role: str, optional_file_formatting: str, dst: str, query: str, sf_user: str = "", password: str = "") -> Dataset:
        """Import a dataset using Snowflake Query.

        :param region: (Optional) Region where Snowflake warehouse exists
        :param database: Name of Snowflake database to query
        :param warehouse: Name of Snowflake warehouse to query
        :param schema: Schema to use during query
        :param role: (Optional) Snowflake role to be used for query
        :param optional_file_formatting: (Optional) Additional arguments for formatting the output SQL query to csv file. See snowflake documentation for "Create File Format"
        :param dst: Destination within local file system for resulting dataset
        :param query: SQL query to pass to Snowflake
        """
        args = SnowCreateDatasetArgs(region, database, warehouse, schema, role, dst, query, optional_file_formatting, sf_user, password)
        key = self.create_dataset_from_snowflake(args)
        job = self._wait_for_dataset(key)
        return job.entity

    def create_dataset_from_kdb_sync(self, destination: str, query: str):
        """Import a dataset using KDB+ Query.

        :param destination: Destination for KDB+ Query to be stored on the local filesystem
        :param query: KDB query. Use standard q queries.
        """
        args = KdbCreateDatasetArgs(destination, query)
        key = self.create_dataset_from_kdb(args)
        job = self._wait_for_dataset(key)
        return job.entity

    def create_dataset_from_jdbc_sync(self, jdbc_user: str, password: str, query: str, id_column: str, destination: str,
                                      db_name: str = "", jdbc_jar: str = "", jdbc_url: str = "", jdbc_driver: str = "") -> Dataset:
        """ Import a dataset using JDBC drivers and SQL Query

        :param jdbc_user: (String) username to authenticate query with
        :param password: (String) password of user to authenticate query with

        :param query: (String) SQL query
        :param id_column: (String) name of id column in dataset
        :param destination: (String) name for resulting dataset. ex. my_dataset or credit_fraud_data_train
        :return: (Dataset) dataset object containing information regarding resultant dataset
        :param db_name: Optional (String) name of database configuration in config.toml to use.
                ex. {"postgres": {configurations for postgres jdbc connection},
                     "sqlite": {configurations for sqlite jdbc connection}}
                db_name could be "postgres" or "sqlite"
                If provided will ignore jdbc_jar, jdbc_url, jdbc_driver arguments.
                Takes these parameters directly from config.toml configuration
        :param jdbc_jar: Optional (String) path to JDBC driver jar. Uses this if db_name parameter not provided.
                Requires jdbc_url and jdbc_driver to be provided, in addition to this parameter
        :param jdbc_url: Optional (String) JDBC connection url. Uses this if db_name parameter not provided
                Requires jdbc_jar and jdbc_driver to be provided, in addition to this parameter
        :param jdbc_driver: Optional (String) classpath of JDBC driver. Uses this if db_name not provided
                Requires jdbc_jar and jdbc_url to be provided, in addition to this parameter
        """
        args = JdbcCreateDatasetArgs(destination, query, id_column, jdbc_user, password, url=jdbc_url,
                                     classpath=jdbc_driver, jarpath=jdbc_jar, database=db_name)
        key = self.create_dataset_from_spark_jdbc(args)
        job = self._wait_for_dataset(key)
        return job.entity

    def create_dataset_from_hive_sync(self, destination: str, query: str, hadoop_conf_path: str = "", auth_type: str = "",
                                      keytab_path: str = "", principal_user: str = "", db_name: str = ""):
        """ Import a dataset from Hive using a Hive Query

        :param hadoop_conf_path: (String) local path to hadoop configuration directory. Ex. /home/ubuntu/hadoop/conf
        :param auth_type: (String) type of authentication to use, can be [noauth, keytab, keytabimpersonation]
        :param destination: (String) name for resultant dataset, Ex. 'my_hive_query_result'
        :param query: (String) SQL hive query
        :param keytab_path: Optional (String) path to keytab if using keytab authentication. Ex. /home/ubuntu/hive.keytab
        :param principal_user: Optional (String) user id authorized by keytab to make queries. Ex. hive/localhost@H2O.AI
        :param db_name: Optional (String) name of database configuration in config.toml to use.
                ex. {"hive_1": {configurations for hive #1},
                     "hive_config_2": {configurations for alternative hive db #2}}
                db_name could be "hive_1" or "hive_config_2"
                if provided will ignore all other optional arguments, and will take them directly from config.toml
        :return: (Dataset) dataset object containing information regarding resultant dataset
        """
        args = HiveCreateDatasetArgs(destination, query, hadoop_conf_path=hadoop_conf_path, keytab_path=keytab_path,
                                     auth_type=auth_type, principal_user=principal_user, database=db_name)
        key = self.create_dataset_from_spark_hive(args)
        job = self._wait_for_dataset(key)
        return job.entity

    def create_local_rest_scorer_sync(self, model_key: str, deployment_name: str, port_number: int,
                                      max_heap_size: int = None):
        """ Deploy REST server locally on Driverless AI server.
        NOTE: This function is primarily for testing & ci purposes.

        :param model_key: Name of model generated by experiment
        :param deployment_name: Name to apply to deployment
        :param port_number: port number on which the deployment REST service will be exposed
        :param: max_heap_size: maximum heap size (Gb) for rest server deployment. Used to set Xmx_g
        :return Deployment: Class Deployment with attributes associated with the successful deployment of
        local rest scorer to Driverless AI server
        """
        local_rest_scorer_parameters = LocalRestScorerParameters(
            deployment_name=deployment_name,
            port=port_number,
            heap_size=max_heap_size or ""
        )
        key = self.create_local_rest_scorer(model_key=model_key,
                                            local_rest_scorer_parameters=local_rest_scorer_parameters)
        job = self._wait_for_create_deployment(key)
        return job.entity

    def destroy_local_rest_scorer_sync(self, deployment_key):
        """ Function to take down REST server that was deployed locally on Driverless AI server

        :param deployment_key: Name of deployment as generated by function `create_local_rest_scorer_sync`
        :return: job status, should be 0
        """
        key = self.destroy_local_rest_scorer(deployment_key)
        job = self._wait_for_destroy_deployment(key)
        return job.status

    def get_experiment_preview_sync(
        self,
        dataset_key: str,
        validset_key: str,
        classification: bool,
        dropped_cols: List[str],
        target_col: str,
        is_time_series: bool,
        time_col: str,
        enable_gpus: bool,
        accuracy: int,
        time: int,
        interpretability: int,
        fold_column: str,
        reproducible: bool,
        resumed_experiment_id: str,
        config_overrides: str,
        **kwargs,
    ):
        """Get explanation text for experiment settings

        :param str dataset_key: Training dataset key
        :param str validset_key: Validation dataset key if any
        :param bool classification: Indicating whether problem is classification or regression. Pass **True** for classification
        :param dropped_cols: List of column names, which won't be used in training
        :type dropped_cols: list of strings
        :param str target_col: Name of the target column for training
        :param bool is_time_series: Whether it's a time-series problem
        :param bool enable_gpus: Specifies whether experiment will use GPUs for training
        :param int accuracy: Accuracy parameter value
        :param int time: Time parameter value
        :param int interpretability: Interpretability parameter value
        :param fold_column: Fold column used for splitting
        :param bool reproducbile: Set experiment to be reproducible
        :param str resumed_experiment_id: Name of resumed experiment
        :param str config_overrides: Raw config.toml file content (UTF8-encoded string)
        :returns: List of strings describing the experiment properties
        :rtype: list of strings

        """
        model_parameters = ModelParameters(
            dataset=references.DatasetReference(dataset_key),
            resumed_model=references.ModelReference(resumed_experiment_id, ''),
            target_col=target_col,
            weight_col=kwargs.get('weight_col', None),
            fold_col=fold_column,
            orig_time_col=kwargs.get('orig_time_col', time_col),
            time_col=time_col,
            is_classification=classification,
            cols_to_drop=dropped_cols,
            validset=references.DatasetReference(validset_key),
            testset=references.DatasetReference(kwargs.get('testset_key', '')),
            enable_gpus=enable_gpus,
            seed=reproducible,
            accuracy=accuracy,
            time=time,
            interpretability=interpretability,
            score_f_name=kwargs.get("score_f_name", None),
            time_groups_columns=kwargs.get('time_groups_columns', None),
            unavailable_columns_at_prediction_time=kwargs.get(
                'unavailable_columns_at_prediction_time', []),
            time_period_in_seconds=kwargs.get('time_period_in_seconds', None),
            num_prediction_periods=kwargs.get('num_prediction_periods', None),
            num_gap_periods=kwargs.get('num_gap_periods', None),
            is_timeseries=is_time_series,
            cols_imputation=kwargs.get('cols_imputation', []),
            config_overrides=config_overrides,
            custom_features=[],
            is_image=kwargs.get('is_image', False),
        )
        key = self.get_experiment_preview(model_parameters)
        job = self._wait_for_preview(key)
        return job.entity.lines

    def upload_custom_recipe_sync(self, file_path: str) -> CustomRecipe:
        """Upload a custom recipe

        :param file_path: A path specifying the location of the python file containing custom transformer classes
        :returns: `CustomRecipe`: which contains `models`, `transformers`
            and `scorers` lists to see newly loaded recipes
        """
        key = self._perform_recipe_upload(file_path)
        job = self._wait_for_recipe_load(key)
        return job.entity

    def make_dataset_split_sync(self, dataset_key: str, output_name1: str, output_name2: str, target: str, fold_col: str, time_col: str, ratio: float, seed: int) -> str:
        key = self.make_dataset_split(dataset_key, output_name1, output_name2, target, fold_col, time_col, ratio, seed)
        job = self._wait_for_dataset_split(key)
        for dataset_key in job.entity:
            self._wait_for_dataset(dataset_key)
        return job.entity

    def export_experiment_sync(self, dest_path: str, experiment_key: str) -> str:
        """Export DriverlessAI experiment and save it as dest_path location

        :param dest_path: Filesystem location where experiment binary file will be saved
        :type dest_path: str
        :param experiment_key: Experiment ID to be exported
        :type experiment_key: str
        :return: Path to downloaded experiment file
        :rtype: str
        """
        key = self.export_experiment(experiment_key)
        job = self._wait_for_entity_job(
            lambda: self.get_export_experiment_job(experiment_key)
        )
        return self.download(job.experiment_zip_path, dest_path)


    def import_experiment_sync(self, file_path: str) -> str:
        """Imports the experiment file to DriverlessAI instance

        :param file_path: Local path to experiment file, which will be uploaded to
            DriverlessAI instance
        :type file_path: str
        :return: New key assigned to imported experiment
        :rtype: str
        """
        remote_file_paths = self.perform_upload(file_path, skip_parse=True)
        return self.import_experiment(remote_file_paths[0])

    # -------------------------------------Utility Functions-------------------------------------

    def _format_server_error(self, message):
        return 'Driverless AI Server reported an error: ' + message

    def _wait_for_entity_job(self, job_getter: Callable[[str], Any]):
        while True:
            time.sleep(1)
            job = job_getter()
            if job.status >= 0:  # done
                if job.status > 0:  # canceled or failed
                    raise RuntimeError(self._format_server_error(job.error))
                return job

    def _wait_for_dataset(self, key):
        while True:
            time.sleep(1)
            job = self.get_dataset_job(key)
            if job.status >= 0:  # done
                if job.status > 0:  # canceled or failed
                    raise RuntimeError(self._format_server_error(job.error))
                return job

    def _wait_for_model(self, key):
        while True:
            time.sleep(1)
            job = self.get_model_job(key)
            if job.status >= 0:  # done
                if job.status > 0:  # canceled or failed
                    raise RuntimeError(self._format_server_error(job.error))
                return job

    def _wait_for_prediction(self, key):
        while True:
            time.sleep(1)
            job = self.get_prediction_job(key)
            if job.status >= 0:  # done
                if job.status > 0:  # canceled or failed
                    raise RuntimeError(self._format_server_error(job.error))
                return job

    def _wait_for_autoreport(self, key):
        while True:
            time.sleep(1)
            job = self.get_autoreport_job(key)
            if job.status >= 0:  # done
                if job.status > 0:  # canceled or failed
                    raise RuntimeError(self._format_server_error(job.error))
                return job

    def _wait_for_transformation(self, key):
        while True:
            time.sleep(1)
            job = self.get_transformation_job(key)
            if job.status >= 0:  # done
                if job.status > 0:  # canceled or failed
                    raise RuntimeError(self._format_server_error(job.error))
                return job

    def _wait_for_model_diagnostic(self, key):
        while True:
            time.sleep(1)
            job = self.get_model_diagnostic_job(key)
            if job.status >= 0:  # done
                if job.status > 0:  # canceled or failed
                    raise RuntimeError(self._format_server_error(job.error))
                return job

    def _wait_for_interpretation_main_job_only(self, key: str):
        """Wait for main (bulk) interpretation job ONLY - do NOT wait for
        runner-based and/or BYOR explainers (like DIA or PD/ICE).

        """
        while True:
            time.sleep(1)
            job = self.get_interpretation_job(key)
            if job.status >= 0:  # done
                if job.status > 0:  # canceled or failed
                    raise RuntimeError(self._format_server_error(job.error))
                return job

    def _wait_for_interpret_timeseries(self, key):
        while True:
            time.sleep(1)
            job = self.get_interpret_timeseries_job(key)
            if job.status >= 0:  # done
                if job.status > 0:  # canceled or failed
                    raise RuntimeError(self._format_server_error(job.error))
                return job

    def _wait_for_scoring_pipeline(self, key):
        while True:
            time.sleep(1)
            job = self.get_scoring_pipeline_job(key)
            if job.status >= 0:  # done
                if job.status > 0:  # canceled or failed
                    raise RuntimeError(self._format_server_error(job.error))
                return job

    def _wait_for_mojo_pipeline(self, key):
        while True:
            time.sleep(1)
            job = self.get_mojo_pipeline_job(key)
            if job.status >= 0:  # done
                if job.status > 0:  # canceled or failed
                    raise RuntimeError(self._format_server_error(job.error))
                return job

    def _wait_for_create_deployment(self, key):
        while True:
            time.sleep(1)
            job = self.get_create_deployment_job(key)
            if job.status >= 0: # done
                if job.status > 0: # cancelled or failed
                    raise RuntimeError(self._format_server_error(job.error))
                return job

    def _wait_for_destroy_deployment(self, key):
        while True:
            time.sleep(1)
            job = self.get_destroy_deployment_job(key)
            if job.status >= 0:
                if job.status > 0:
                    raise RuntimeError(self._format_server_error(job.error))
                self.drop_local_rest_scorer_from_database(key)
                return job

    def _wait_for_preview(self, key):
        while True:
            time.sleep(1)
            job = self.get_experiment_preview_job(key)
            if job.status >= 0:  # done
                if job.status > 0:  # canceled or failed
                    raise RuntimeError(self._format_server_error(job.error))
                return job

    def _wait_for_recipe_load(self, key):
        while True:
            time.sleep(1)
            job = self.get_custom_recipe_job(key)
            if job.status >= 0:  # done
                if job.status > 0:  # canceled or failed
                    raise RuntimeError(self._format_server_error(job.error))
                return job

    def _perform_recipe_upload(self, file_path) -> bool:
        url = self.address + "/uploadrecipe"
        with open(file_path, 'rb') as f:
            res = self._session.post(
                url,
                files={"dataset": f},
                headers=self._get_authorization_headers(),
            )

            if res.status_code == requests.codes.ok:
                return res.json()
            elif res.status_code == requests.codes.method_not_allowed:
                raise RuntimeError("Uploading of recipes is disabled in config")
            else:
                raise RuntimeError("Uploading of custom recipe failed")

    def _wait_for_custom_recipes_acceptance_tests(self):
        while True:
            time.sleep(1)
            job = self.get_custom_recipes_acceptance_job()
            if job:
                if job.status >= 0:
                    return
            else:
                # Assume acceptance tests just failed or weren't run at all and move on
                return

    def _wait_for_dataset_split(self, key):
        while True:
            time.sleep(1)
            job = self.get_dataset_split_job(key)
            if job.status >= 0:  # done
                if job.status > 0:  # canceled or failed
                    raise RuntimeError(self._format_server_error(job.error))
                return job

    #
    # MLI
    #

    # 1y timeout: 31_556_926
    MLI_WAIT_TIMEOUT = 31_556_926
    MLI_WAIT_STEP = 3

    @staticmethod
    def build_common_dai_explainer_params(
        target_col: Optional[str] = None,
        weight_col: Optional[str] = None,
        prediction_col: Optional[str] = None,
        drop_cols: Optional[List[str]] = None,
        sample_num_rows: Optional[int] = None,
        model_key: Optional[str] = None,
        dataset_key: Optional[str] = None,
        testset_key: Optional[str] = None,
        validset_key: Optional[str] = None,
        use_raw_features: bool = False,
        config_overrides: Optional[str] = None,
        sequential_execution: Optional[bool] = None,
        debug_model_errors: Optional[bool] = False,
        debug_model_errors_class: Optional[str] = "",
    ) -> CommonDaiExplainerParameters:
        return CommonDaiExplainerParameters(
            common_params=CommonExplainerParameters(
                target_col=target_col,
                weight_col=weight_col,
                prediction_col=prediction_col,
                drop_cols=drop_cols,
                sample_num_rows=sample_num_rows,
            ),
            model=ModelReference(key=model_key),
            dataset=DatasetReference(key=dataset_key),
            testset=DatasetReference(key=testset_key),
            validset=DatasetReference(key=validset_key),
            use_raw_features=use_raw_features,
            config_overrides=config_overrides,
            sequential_execution=(
                True if sequential_execution in [None, True] else False
            ),
            debug_model_errors=True if debug_model_errors else False,
            debug_model_errors_class=(
                "" if not debug_model_errors_class else debug_model_errors_class
            ),
        )

    def _wait_for_explainer_run(
            self,
            key: str,
            timeout: int = MLI_WAIT_TIMEOUT,
            step: int = MLI_WAIT_STEP,
    ) -> ExplainerRunJob:
        elapsed: int = timeout
        while elapsed >= 0:
            time.sleep(step)
            elapsed -= step
            job = self.get_explainer_run_job(key)
            if job.status >= 0:  # done
                if job.status > 0:  # canceled or failed
                    raise RuntimeError(self._format_server_error(job.error))
                return job

        raise RuntimeError(
            f"Sync explainer {key} run timed out after {timeout}s"
        )

    def run_explainers_sync(
            self,
            explainers: List[Explainer],
            params: CommonDaiExplainerParameters,
    ) -> List[ExplainerRunJob]:
        r"""Run MLI explainers."""
        run_job: ExplainersRunJob = self.run_explainers(explainers, params)
        return self.wait_for_explainers(run_job.mli_key)

    def wait_for_explainers(
        self,
        key: str,
        timeout: int = MLI_WAIT_TIMEOUT,
        step: int = MLI_WAIT_STEP,
    ) -> list:
        """Wait for ALL explainers to finish (succeed or fail) w/ timeout.

        Parameters
        ----------
        key: str
          MLI key.
        timeout: int
          Wait for given number of seconds, default indicates no timeout (wait
          indefinitely ~ 1 year).
        step: int
          Wait iteration in seconds.

        Returns
        -------
        List[ExplainerJobStatus]:
          Statuses w/ descriptors

        """
        wip_jobs: list = []
        elapsed: int = timeout
        while elapsed >= 0:
            time.sleep(step)
            elapsed -= step

            explainer_job_statuses = self.get_explainer_job_statuses(
                mli_key=key, explainer_job_keys=None
            )

            err_msg: str = ""
            failed_jobs = dict()
            wip_jobs.clear()
            for job_status in explainer_job_statuses:
                if job_status.explainer_job.status == -1:  # running
                    wip_jobs.append(job_status.explainer_job.entity.name)
                    break
                elif job_status.explainer_job.status > 0:  # canceled or failed
                    failed_jobs[job_status.explainer_job.entity.name] = (
                        f"    EXPLAINER ERROR ({job_status.explainer_job.entity.name}):"
                        f" {job_status.explainer_job.error}"
                    )
            if len(wip_jobs) > 0:
                continue
            # done done
            if len(failed_jobs) > 0:  # failed
                err_msg = err_msg if not len(err_msg) else f"{err_msg}, "
                err_msg = f"{err_msg}{len(failed_jobs)} explainer(s) failed ("
                for fj in failed_jobs:
                    err_msg = f"{err_msg}{fj}, "
                err_msg = err_msg[:-2] + ")"
            if len(err_msg):
                err_msg = (
                    f"{err_msg} in interpretation {key} ({timeout-elapsed}s)\n"
                )
                # error details
                for fj in failed_jobs:
                    err_msg = f"{err_msg}\n{failed_jobs[fj]}"
                raise RuntimeError(err_msg)

            return explainer_job_statuses

        err_msg = (
            f"Sync interpretation {key} run timed out after {timeout}s with "
            f"{len(wip_jobs)} unfinished jobs: "
        )
        for wj in wip_jobs:
            err_msg = f"{err_msg}{wj}, "
        err_msg = err_msg[:-2]

        raise RuntimeError(err_msg)

    # legacy MLI interpretation (main) job
    def _wait_for_interpretation(
            self,
            key: str,
            timeout: int = MLI_WAIT_TIMEOUT,
            step: int = MLI_WAIT_STEP,
    ):
        """Wait for ALL (main job, runner and BYOR based) explainers to finish
        (succeed or fail) w/ timeout.

        Parameters
        ----------
        key: str
          MLI key.
        timeout: int
          Wait for given number of seconds, default indicates no timeout (wait
          indefinitely ~ 1 year).
        step: int
          Wait iteration in seconds.

        """
        # wait for all explainers to finish w/ success or failure
        self.wait_for_explainers(
            key=key,
            timeout=timeout,
            step=step
        )
        # return legacy job to report status(es)
        return self.get_interpretation_job(key)

    def get_explainer_run_log_url(
            self,
            mli_key: str,
            explainer_job_key: str,
    ) -> str:
        return (
            f"{self.address}/"
            f"{self.get_explainer_run_log_url_path(mli_key, explainer_job_key)}"
        )

    def get_explainer_result_url(
            self,
            mli_key: str,
            explainer_job_key: str,
            explanation_type: str,
            explanation_format: str,
    ) -> str:
        return (
            f"{self.address}/"
            f"{self.get_explainer_result_url_path(mli_key, explainer_job_key)}"
        )

    def get_explainer_snapshot_url(
            self,
            mli_key: str,
            explainer_job_key: str,
    ) -> str:
        return (
            f"{self.address}/"
            f"{self.get_explainer_snapshot_url_path(mli_key, explainer_job_key)}"
        )

    def start_echo(self, message: str, repeat: int, key: str) -> str:
        """

        """
        req_ = dict(message=message, repeat=repeat, key=key)
        res_ = self._request('start_echo', req_)
        return res_

    def stop_echo(self, key: str) -> None:
        """

        """
        req_ = dict(key=key)
        self._request('stop_echo', req_)
        return None

    def get_app_version(self) -> AppVersion:
        """
        Returns the application version.

        :returns: The application version.
        """
        req_ = dict()
        res_ = self._request('get_app_version', req_)
        return AppVersion.load(res_)

    def get_gpu_stats(self) -> GPUStats:
        """
        Returns gpu stats as if called by get_gpu_info_safe (systemutils)

        """
        req_ = dict()
        res_ = self._request('get_gpu_stats', req_)
        return GPUStats.load(res_)

    def get_disk_stats(self) -> DiskStats:
        """
        Returns the server's disk usage as if called by diskinfo (systemutils)

        """
        req_ = dict()
        res_ = self._request('get_disk_stats', req_)
        return DiskStats.load(res_)

    def get_experiments_stats(self) -> ExperimentsStats:
        """
        Returns stats about experiments

        """
        req_ = dict()
        res_ = self._request('get_experiments_stats', req_)
        return ExperimentsStats.load(res_)

    def get_config_options(self, keys: List[str]) -> List[ConfigItem]:
        """
        Get metadata and current value for specified options

        """
        req_ = dict(keys=keys)
        res_ = self._request('get_config_options', req_)
        return [ConfigItem.load(b_) for b_ in res_]

    def get_configurable_options(self, tag: str) -> List[ConfigItem]:
        """
        Get all config options configurable through expert settings

        """
        req_ = dict(tag=tag)
        res_ = self._request('get_configurable_options', req_)
        return [ConfigItem.load(b_) for b_ in res_]

    def get_all_config_options(self) -> List[ConfigItem]:
        """
        Get metadata and current value for all exposed options

        """
        req_ = dict()
        res_ = self._request('get_all_config_options', req_)
        return [ConfigItem.load(b_) for b_ in res_]

    def set_config_option_dummy(self, key: str, value: Any, config_overrides: str) -> List[ConfigItem]:
        """
        Set value for a given option on local copy of config, without touching the global config
        Returns list of settings modified byt config rules application

        :param config_overrides: Used to initialize local config
        """
        validation.validate_toml(config_overrides, 'config_overrides')
        req_ = dict(key=key, value=value, config_overrides=config_overrides)
        res_ = self._request('set_config_option_dummy', req_)
        return [ConfigItem.load(b_) for b_ in res_]

    def set_config_option(self, key: str, value: Any) -> List[ConfigItem]:
        """
        Set value for a given option
        Returns list of settings modified byt config rules application

        """
        req_ = dict(key=key, value=value)
        res_ = self._request('set_config_option', req_)
        return [ConfigItem.load(b_) for b_ in res_]

    def start_experiment(self, req: ModelParameters, experiment_name: str) -> str:
        """
        Start a new experiment.

        :param req: The experiment's parameters.
        :param experiment_name: Display name of newly started experiment
        :returns: The experiment's key.
        """
        req_ = dict(req=req.dump(), experiment_name=experiment_name)
        res_ = self._request('start_experiment', req_)
        return res_

    def start_experiment_leaderboard(self, req: ModelParameters, leaderboard_name: str) -> str:
        """
        Start a new experiment leaderboard. This procedure triggers multiple smaller experiments
        and creates a new project, populating it with these experiments

        :param req: The experiment's parameters.
        :param leaderboard_name: Display name of newly created project
        :returns: The project's key.
        """
        req_ = dict(req=req.dump(), leaderboard_name=leaderboard_name)
        res_ = self._request('start_experiment_leaderboard', req_)
        return res_

    def stop_experiment(self, key: str) -> None:
        """
        Stop the experiment.

        :param key: The experiment's key.
        """
        req_ = dict(key=key)
        self._request('stop_experiment', req_)
        return None

    def abort_experiment(self, key: str) -> None:
        """
        Abort the experiment.

        :param key: The experiment's key.
        """
        req_ = dict(key=key)
        self._request('abort_experiment', req_)
        return None

    def export_experiment(self, key: str) -> str:
        """
        Export experiment as zipfile
        returns `ExportExperimentJob` key

        :param key: Experiment key
        """
        req_ = dict(key=key)
        res_ = self._request('export_experiment', req_)
        return res_

    def get_export_experiment_job(self, key: str) -> ExportExperimentJob:
        """

        """
        req_ = dict(key=key)
        res_ = self._request('get_export_experiment_job', req_)
        return ExportExperimentJob.load(res_)

    def import_experiment(self, file_path: str) -> str:
        """
        Import experiment from zipfile
        returns new experiment key after import

        :param file_path: Path to experiment metadata zipfile
        """
        req_ = dict(file_path=file_path)
        res_ = self._request('import_experiment', req_)
        return res_

    def stop_interpretation(self, key: str) -> None:
        """
        Softly stops the interpretation and its jobs

        :param key: Interpretation key
        """
        req_ = dict(key=key)
        self._request('stop_interpretation', req_)
        return None

    def abort_interpretation(self, key: str) -> None:
        """
        Abort MLI experiment

        :param key: The interpretation key.
        """
        req_ = dict(key=key)
        self._request('abort_interpretation', req_)
        return None

    def list_datasets(self, offset: int, limit: int, include_inactive: bool) -> ListDatasetQueryResponse:
        """

        :param include_inactive: Whether to include datasets in failed, cancelled or in-progress state.
        """
        req_ = dict(offset=offset, limit=limit, include_inactive=include_inactive)
        res_ = self._request('list_datasets', req_)
        return ListDatasetQueryResponse.load(res_)

    def search_and_sort_datasets(self, search_query: str, sort_query: EntitySortQuery, ascending: bool, offset: int, limit: int, include_inactive: bool) -> ListDatasetQueryResponse:
        """
        List, search and sort datasets based on some Dataset field or date of creation

        :param search_query: String which is used for full-text search in dataset entity
        :param sort_query: Entity sort query specifying path to nested field
        :param include_inactive: Whether to include datasets in failed, cancelled or in-progress state.
        """
        req_ = dict(search_query=search_query, sort_query=sort_query.dump(), ascending=ascending, offset=offset, limit=limit, include_inactive=include_inactive)
        res_ = self._request('search_and_sort_datasets', req_)
        return ListDatasetQueryResponse.load(res_)

    def list_datasets_with_similar_name(self, name: str) -> List[str]:
        """

        """
        req_ = dict(name=name)
        res_ = self._request('list_datasets_with_similar_name', req_)
        return res_

    def get_persistent_custom_recipe(self, key: str) -> GetPersistentCustomRecipeResponse:
        """

        """
        req_ = dict(key=key)
        res_ = self._request('get_persistent_custom_recipe', req_)
        return GetPersistentCustomRecipeResponse.load(res_)

    def search_and_sort_custom_recipes(self, search_query: str, sort_query: EntitySortQuery, ascending: bool, offset: int, limit: int, include_inactive: bool) -> ListCustomRecipeResponse:
        """

        :param search_query: String which is used for full-text search in dataset entity
        :param sort_query: Entity sort query specifying path to nested field
        :param include_inactive: Whether to include datasets in failed, cancelled or in-progress state.
        """
        req_ = dict(search_query=search_query, sort_query=sort_query.dump(), ascending=ascending, offset=offset, limit=limit, include_inactive=include_inactive)
        res_ = self._request('search_and_sort_custom_recipes', req_)
        return ListCustomRecipeResponse.load(res_)

    def update_custom_recipe_note(self, key: str, note: str) -> bool:
        """

        """
        req_ = dict(key=key, note=note)
        res_ = self._request('update_custom_recipe_note', req_)
        return res_

    def update_custom_recipe_code(self, key: str, code: str, in_file_update: bool) -> UpdateCustomRecipeResponse:
        """

        """
        req_ = dict(key=key, code=code, in_file_update=in_file_update)
        res_ = self._request('update_custom_recipe_code', req_)
        return UpdateCustomRecipeResponse.load(res_)

    def get_descendant_recipe(self, key: str) -> PersistentCustomRecipe:
        """

        """
        req_ = dict(key=key)
        res_ = self._request('get_descendant_recipe', req_)
        return PersistentCustomRecipe.load(res_)

    def get_recipes_from_recipe_file(self, target_file: List[str]) -> List[PersistentCustomRecipe]:
        """

        """
        req_ = dict(target_file=target_file)
        res_ = self._request('get_recipes_from_recipe_file', req_)
        return [PersistentCustomRecipe.load(b_) for b_ in res_]

    def deactivate_custom_recipes(self, keys: List[str]) -> None:
        """

        """
        req_ = dict(keys=keys)
        self._request('deactivate_custom_recipes', req_)
        return None

    def list_models(self, offset: int, limit: int) -> ListModelQueryResponse:
        """

        """
        req_ = dict(offset=offset, limit=limit)
        res_ = self._request('list_models', req_)
        return ListModelQueryResponse.load(res_)

    def search_and_sort_models(self, search_query: str, sort_query: EntitySortQuery, ascending: bool, offset: int, limit: int) -> ListModelQueryResponse:
        """
        List, search and sort experiments based on some ModelSummary field or date of creation

        :param search_query: String which is used for full-text search in ModelSummary entity
        :param sort_query: Entity sort query specifying path to nested field
        """
        req_ = dict(search_query=search_query, sort_query=sort_query.dump(), ascending=ascending, offset=offset, limit=limit)
        res_ = self._request('search_and_sort_models', req_)
        return ListModelQueryResponse.load(res_)

    def list_models_with_similar_name(self, name: str) -> List[str]:
        """
        List all model names with display_name similar as `name`, e.g. to prevent display_name collision
        :returns: List of similar model names

        """
        req_ = dict(name=name)
        res_ = self._request('list_models_with_similar_name', req_)
        return res_

    def list_interpret_timeseries(self, offset: int, limit: int) -> List[InterpretSummary]:
        """

        """
        req_ = dict(offset=offset, limit=limit)
        res_ = self._request('list_interpret_timeseries', req_)
        return [InterpretSummary.load(b_) for b_ in res_]

    def list_interpretations(self, offset: int, limit: int) -> ListInterpretationQueryResponse:
        """

        """
        req_ = dict(offset=offset, limit=limit)
        res_ = self._request('list_interpretations', req_)
        return ListInterpretationQueryResponse.load(res_)

    def search_and_sort_interpretations(self, search_query: str, sort_query: EntitySortQuery, ascending: bool, offset: int, limit: int) -> ListInterpretationQueryResponse:
        """
        List, search and sort interpretations based on search and sort query

        :param search_query: String which is used for full-text search
        :param sort_query: Entity sort query specifying path to nested field
        """
        req_ = dict(search_query=search_query, sort_query=sort_query.dump(), ascending=ascending, offset=offset, limit=limit)
        res_ = self._request('search_and_sort_interpretations', req_)
        return ListInterpretationQueryResponse.load(res_)

    def list_visualizations(self, offset: int, limit: int) -> ListVisualizationQueryResponse:
        """

        """
        req_ = dict(offset=offset, limit=limit)
        res_ = self._request('list_visualizations', req_)
        return ListVisualizationQueryResponse.load(res_)

    def search_and_sort_visualizations(self, search_query: str, sort_query: EntitySortQuery, ascending: bool, offset: int, limit: int) -> ListVisualizationQueryResponse:
        """
        List, search and sort visualizations based

        :param search_query: String which is used for full-text search
        :param sort_query: Entity sort query specifying path to nested field
        """
        req_ = dict(search_query=search_query, sort_query=sort_query.dump(), ascending=ascending, offset=offset, limit=limit)
        res_ = self._request('search_and_sort_visualizations', req_)
        return ListVisualizationQueryResponse.load(res_)

    def list_projects(self, offset: int, limit: int) -> ListProjectQueryResponse:
        """

        """
        req_ = dict(offset=offset, limit=limit)
        res_ = self._request('list_projects', req_)
        return ListProjectQueryResponse.load(res_)

    def search_and_sort_projects(self, search_query: str, sort_query: EntitySortQuery, ascending: bool, offset: int, limit: int) -> ListProjectQueryResponse:
        """
        List, search and sort projects

        :param search_query: String which is used for full-text search
        :param sort_query: Entity sort query specifying path to nested field
        """
        req_ = dict(search_query=search_query, sort_query=sort_query.dump(), ascending=ascending, offset=offset, limit=limit)
        res_ = self._request('search_and_sort_projects', req_)
        return ListProjectQueryResponse.load(res_)

    def get_oauth2_client_tokens(self) -> OAuth2ClientTokens:
        """

        """
        req_ = dict()
        res_ = self._request('get_oauth2_client_tokens', req_)
        return OAuth2ClientTokens.load(res_)

    def list_storage_projects(self, offset: int, limit: int) -> ListStorageProjectQueryResponse:
        """
        List h2oai-storage projects from USER_PROJECTS root location.

        """
        req_ = dict(offset=offset, limit=limit)
        res_ = self._request('list_storage_projects', req_)
        return ListStorageProjectQueryResponse.load(res_)

    def export_dataset_to_storage(self, key: str, project_id: str) -> str:
        """
        Export a local dataset to the h2oai-storage location.
        An async job returning key of ExportEntityJob.

        :param key: Key of the dataset to export.
        """
        req_ = dict(key=key, project_id=project_id)
        res_ = self._request('export_dataset_to_storage', req_)
        return res_

    def export_model_to_storage(self, key: str, project_id: str) -> str:
        """
        Export a local model to the h2oai-storage location.
        An async job returning key of ExportEntityJob.

        :param key: Key of the model to export.
        """
        req_ = dict(key=key, project_id=project_id)
        res_ = self._request('export_model_to_storage', req_)
        return res_

    def get_export_entity_job(self, key: str) -> ExportEntityJob:
        """

        """
        req_ = dict(key=key)
        res_ = self._request('get_export_entity_job', req_)
        return ExportEntityJob.load(res_)

    def import_storage_dataset(self, dataset_id: str) -> str:
        """
        Import dataset from the h2oai-storage locally.
        An async job returning key of ImportEntityJob.

        :param dataset_id: The h2oai-storage ID of the dataset to import.
        """
        req_ = dict(dataset_id=dataset_id)
        res_ = self._request('import_storage_dataset', req_)
        return res_

    def import_storage_model(self, model_id: str) -> str:
        """
        Import model from the h2oai-storage locally.
        An async job returning key of ImportEntityJob.

        :param model_id: The h2oai-storage ID of the model to import.
        """
        req_ = dict(model_id=model_id)
        res_ = self._request('import_storage_model', req_)
        return res_

    def get_import_entity_job(self, key: str) -> ImportEntityJob:
        """

        """
        req_ = dict(key=key)
        res_ = self._request('get_import_entity_job', req_)
        return ImportEntityJob.load(res_)

    def list_project_sharings(self, project_id: str) -> List[Sharing]:
        """
        List sharings of a h2oai-storage project.

        :param project_id: The h2oai-storage ID of the project to list the sharings of.
        """
        req_ = dict(project_id=project_id)
        res_ = self._request('list_project_sharings', req_)
        return [Sharing.load(b_) for b_ in res_]

    def list_storage_roles(self) -> List[Role]:
        """
        List roles known to h2oai-storage.

        """
        req_ = dict()
        res_ = self._request('list_storage_roles', req_)
        return [Role.load(b_) for b_ in res_]

    def list_storage_users(self, offset: int, limit: int) -> List[StorageUser]:
        """
        List users known to h2oai-storage.

        """
        req_ = dict(offset=offset, limit=limit)
        res_ = self._request('list_storage_users', req_)
        return [StorageUser.load(b_) for b_ in res_]

    def search_files(self, pattern: str) -> FileSearchResults:
        """

        """
        req_ = dict(pattern=pattern)
        res_ = self._request('search_files', req_)
        return FileSearchResults.load(res_)

    def search_hdfs_files(self, pattern: str) -> FileSearchResults:
        """

        """
        req_ = dict(pattern=pattern)
        res_ = self._request('search_hdfs_files', req_)
        return FileSearchResults.load(res_)

    def search_dtap_files(self, pattern: str) -> FileSearchResults:
        """

        """
        req_ = dict(pattern=pattern)
        res_ = self._request('search_dtap_files', req_)
        return FileSearchResults.load(res_)

    def search_s3_files(self, pattern: str) -> FileSearchResults:
        """

        """
        req_ = dict(pattern=pattern)
        res_ = self._request('search_s3_files', req_)
        return FileSearchResults.load(res_)

    def search_gcs_files(self, pattern: str) -> FileSearchResults:
        """

        """
        req_ = dict(pattern=pattern)
        res_ = self._request('search_gcs_files', req_)
        return FileSearchResults.load(res_)

    def search_minio_files(self, pattern: str) -> FileSearchResults:
        """

        """
        req_ = dict(pattern=pattern)
        res_ = self._request('search_minio_files', req_)
        return FileSearchResults.load(res_)

    def search_azr_blob_store_files(self, pattern: str) -> FileSearchResults:
        """

        """
        req_ = dict(pattern=pattern)
        res_ = self._request('search_azr_blob_store_files', req_)
        return FileSearchResults.load(res_)

    def create_dataset_from_kdb(self, args: KdbCreateDatasetArgs) -> str:
        """

        """
        req_ = dict(args=args.dump())
        res_ = self._request('create_dataset_from_kdb', req_)
        return res_

    def get_jdbc_config(self, db_name: str) -> SparkJDBCConfig:
        """

        """
        req_ = dict(db_name=db_name)
        res_ = self._request('get_jdbc_config', req_)
        return SparkJDBCConfig.load(res_)

    def create_dataset_from_spark_jdbc(self, args: JdbcCreateDatasetArgs) -> str:
        """

        """
        req_ = dict(args=args.dump())
        res_ = self._request('create_dataset_from_spark_jdbc', req_)
        return res_

    def get_hive_config(self, db_name: str) -> HiveConfig:
        """

        """
        req_ = dict(db_name=db_name)
        res_ = self._request('get_hive_config', req_)
        return HiveConfig.load(res_)

    def create_dataset_from_spark_hive(self, args: HiveCreateDatasetArgs) -> str:
        """

        """
        req_ = dict(args=args.dump())
        res_ = self._request('create_dataset_from_spark_hive', req_)
        return res_

    def create_dataset_from_recipe(self, recipe_path: str) -> str:
        """

        """
        req_ = dict(recipe_path=recipe_path)
        res_ = self._request('create_dataset_from_recipe', req_)
        return res_

    def list_s3_buckets(self, offset: int, limit: int) -> List[str]:
        """

        """
        req_ = dict(offset=offset, limit=limit)
        res_ = self._request('list_s3_buckets', req_)
        return res_

    def list_gcs_buckets(self, offset: int, limit: int) -> List[str]:
        """

        """
        req_ = dict(offset=offset, limit=limit)
        res_ = self._request('list_gcs_buckets', req_)
        return res_

    def list_minio_buckets(self, offset: int, limit: int) -> List[str]:
        """

        """
        req_ = dict(offset=offset, limit=limit)
        res_ = self._request('list_minio_buckets', req_)
        return res_

    def list_azr_blob_store_buckets(self, offset: int, limit: int) -> List[str]:
        """

        """
        req_ = dict(offset=offset, limit=limit)
        res_ = self._request('list_azr_blob_store_buckets', req_)
        return res_

    def list_allowed_file_systems(self, offset: int, limit: int) -> List[str]:
        """

        """
        req_ = dict(offset=offset, limit=limit)
        res_ = self._request('list_allowed_file_systems', req_)
        return res_

    def create_dataset(self, filepath: str) -> str:
        """

        """
        req_ = dict(filepath=filepath)
        res_ = self._request('create_dataset', req_)
        return res_

    def create_dataset_from_file(self, filepath: str) -> str:
        """

        """
        req_ = dict(filepath=filepath)
        res_ = self._request('create_dataset_from_file', req_)
        return res_

    def create_dataset_from_upload(self, filepath: str) -> str:
        """

        """
        req_ = dict(filepath=filepath)
        res_ = self._request('create_dataset_from_upload', req_)
        return res_

    def create_dataset_from_hadoop(self, filepath: str) -> str:
        """

        """
        req_ = dict(filepath=filepath)
        res_ = self._request('create_dataset_from_hadoop', req_)
        return res_

    def create_dataset_from_dtap(self, filepath: str) -> str:
        """

        """
        req_ = dict(filepath=filepath)
        res_ = self._request('create_dataset_from_dtap', req_)
        return res_

    def create_dataset_from_s3(self, filepath: str) -> str:
        """

        """
        req_ = dict(filepath=filepath)
        res_ = self._request('create_dataset_from_s3', req_)
        return res_

    def create_dataset_from_gcs(self, filepath: str) -> str:
        """

        """
        req_ = dict(filepath=filepath)
        res_ = self._request('create_dataset_from_gcs', req_)
        return res_

    def create_dataset_from_gbq(self, args: GbqCreateDatasetArgs) -> str:
        """

        """
        req_ = dict(args=args.dump())
        res_ = self._request('create_dataset_from_gbq', req_)
        return res_

    def create_dataset_from_minio(self, filepath: str) -> str:
        """

        """
        req_ = dict(filepath=filepath)
        res_ = self._request('create_dataset_from_minio', req_)
        return res_

    def create_dataset_from_snowflake(self, args: SnowCreateDatasetArgs) -> str:
        """

        """
        req_ = dict(args=args.dump())
        res_ = self._request('create_dataset_from_snowflake', req_)
        return res_

    def create_dataset_from_azr_blob(self, filepath: str) -> str:
        """

        """
        req_ = dict(filepath=filepath)
        res_ = self._request('create_dataset_from_azr_blob', req_)
        return res_

    def delete_dataset(self, key: str) -> None:
        """

        """
        req_ = dict(key=key)
        self._request('delete_dataset', req_)
        return None

    def get_connector_ui_config(self, connector_type: str) -> ConnectorProperties:
        """

        """
        req_ = dict(connector_type=connector_type)
        res_ = self._request('get_connector_ui_config', req_)
        return ConnectorProperties.load(res_)

    def get_connector_config_options(self, connector_type: str) -> List[str]:
        """

        """
        req_ = dict(connector_type=connector_type)
        res_ = self._request('get_connector_config_options', req_)
        return res_

    def get_dataset_job(self, key: str) -> DatasetJob:
        """

        """
        req_ = dict(key=key)
        res_ = self._request('get_dataset_job', req_)
        return DatasetJob.load(res_)

    def update_dataset_name(self, key: str, new_name: str) -> None:
        """

        """
        req_ = dict(key=key, new_name=new_name)
        self._request('update_dataset_name', req_)
        return None

    def update_dataset_col_format(self, key: str, colname: str, datetime_format: str) -> None:
        """

        """
        req_ = dict(key=key, colname=colname, datetime_format=datetime_format)
        self._request('update_dataset_col_format', req_)
        return None

    def update_dataset_col_logical_types(self, key: str, colname: str, logical_types: List[str]) -> None:
        """

        """
        req_ = dict(key=key, colname=colname, logical_types=logical_types)
        self._request('update_dataset_col_logical_types', req_)
        return None

    def update_dataset_training_params(self, key: str, colname: str, training_params: TrainingFeature) -> None:
        """

        """
        req_ = dict(key=key, colname=colname, training_params=training_params.dump())
        self._request('update_dataset_training_params', req_)
        return None

    def modify_dataset_by_recipe_url(self, key: str, recipe_url: str) -> str:
        """
        Returns custom recipe job key

        :param key: Dataset key
        :param recipe_url: Url of the recipe
        """
        req_ = dict(key=key, recipe_url=recipe_url)
        res_ = self._request('modify_dataset_by_recipe_url', req_)
        return res_

    def modify_dataset_by_recipe_file(self, key: str, recipe_path: str) -> str:
        """
        Returns custom recipe job key

        :param key: Dataset key
        :param recipe_path: Recipe file path
        """
        req_ = dict(key=key, recipe_path=recipe_path)
        res_ = self._request('modify_dataset_by_recipe_file', req_)
        return res_

    def delete_model(self, key: str) -> None:
        """

        """
        req_ = dict(key=key)
        self._request('delete_model', req_)
        return None

    def delete_interpretation(self, key: str) -> None:
        """

        """
        req_ = dict(key=key)
        self._request('delete_interpretation', req_)
        return None

    def import_model(self, filepath: str) -> str:
        """

        """
        req_ = dict(filepath=filepath)
        res_ = self._request('import_model', req_)
        return res_

    def get_importmodel_job(self, key: str) -> ImportModelJob:
        """

        """
        req_ = dict(key=key)
        res_ = self._request('get_importmodel_job', req_)
        return ImportModelJob.load(res_)

    def get_dataset_summary(self, key: str) -> DatasetSummary:
        """

        """
        req_ = dict(key=key)
        res_ = self._request('get_dataset_summary', req_)
        return DatasetSummary.load(res_)

    def get_model_job(self, key: str) -> ModelJob:
        """

        """
        req_ = dict(key=key)
        res_ = self._request('get_model_job', req_)
        return ModelJob.load(res_)

    def get_variable_importance(self, key: str) -> VarImpTable:
        """

        """
        req_ = dict(key=key)
        res_ = self._request('get_variable_importance', req_)
        return VarImpTable.load(res_)

    def get_mli_variable_importance(self, key: str, mli_job_key: str, original: bool) -> VarImpTable:
        """

        """
        req_ = dict(key=key, mli_job_key=mli_job_key, original=original)
        res_ = self._request('get_mli_variable_importance', req_)
        return VarImpTable.load(res_)

    def get_iteration_data(self, key: str) -> AutoDLProgress:
        """

        """
        req_ = dict(key=key)
        res_ = self._request('get_iteration_data', req_)
        return AutoDLProgress.load(res_)

    def get_model_job_partial(self, key: str, from_iteration: int) -> ModelJob:
        """

        """
        req_ = dict(key=key, from_iteration=from_iteration)
        res_ = self._request('get_model_job_partial', req_)
        return ModelJob.load(res_)

    def get_model_summary(self, key: str) -> ModelSummary:
        """

        """
        req_ = dict(key=key)
        res_ = self._request('get_model_summary', req_)
        return ModelSummary.load(res_)

    def get_model_summary_with_diagnostics(self, key: str) -> ModelSummaryWithDiagnostics:
        """

        """
        req_ = dict(key=key)
        res_ = self._request('get_model_summary_with_diagnostics', req_)
        return ModelSummaryWithDiagnostics.load(res_)

    def update_model_description(self, key: str, new_description: str) -> None:
        """

        """
        req_ = dict(key=key, new_description=new_description)
        self._request('update_model_description', req_)
        return None

    def has_mojo_available(self, model_key: str) -> bool:
        """
        Return `True` if MOJO can be built for the model specified

        """
        req_ = dict(model_key=model_key)
        res_ = self._request('has_mojo_available', req_)
        return res_

    def update_mli_description(self, key: str, new_description: str) -> None:
        """

        """
        req_ = dict(key=key, new_description=new_description)
        self._request('update_mli_description', req_)
        return None

    def get_autoviz(self, dataset_key: str, maximum_number_of_plots: int) -> str:
        """

        """
        req_ = dict(dataset_key=dataset_key, maximum_number_of_plots=maximum_number_of_plots)
        res_ = self._request('get_autoviz', req_)
        return res_

    def get_autoviz_summary(self, key: str) -> AutoVizSummary:
        """

        """
        req_ = dict(key=key)
        res_ = self._request('get_autoviz_summary', req_)
        return AutoVizSummary.load(res_)

    def get_1d_vega_plot(self, dataset_key: str, plot_type: str, x_variable_name: str, kwargs: Any) -> str:
        """

        """
        req_ = dict(dataset_key=dataset_key, plot_type=plot_type, x_variable_name=x_variable_name, kwargs=kwargs)
        res_ = self._request('get_1d_vega_plot', req_)
        return res_

    def get_2d_vega_plot(self, dataset_key: str, plot_type: str, x_variable_name: str, y_variable_name: str, kwargs: Any) -> str:
        """

        """
        req_ = dict(dataset_key=dataset_key, plot_type=plot_type, x_variable_name=x_variable_name, y_variable_name=y_variable_name, kwargs=kwargs)
        res_ = self._request('get_2d_vega_plot', req_)
        return res_

    def get_vega_plot(self, dataset_key: str, plot_type: str, variable_names: List[str], kwargs: Any) -> str:
        """

        """
        req_ = dict(dataset_key=dataset_key, plot_type=plot_type, variable_names=variable_names, kwargs=kwargs)
        res_ = self._request('get_vega_plot', req_)
        return res_

    def get_vega_plot_job(self, key: str) -> VegaPlotJob:
        """

        """
        req_ = dict(key=key)
        res_ = self._request('get_vega_plot_job', req_)
        return VegaPlotJob.load(res_)

    def get_scatterplot(self, dataset_key: str, x_variable_name: str, y_variable_name: str) -> str:
        """

        """
        req_ = dict(dataset_key=dataset_key, x_variable_name=x_variable_name, y_variable_name=y_variable_name)
        res_ = self._request('get_scatterplot', req_)
        return res_

    def get_scatterplot_job(self, key: str) -> ScatterPlotJob:
        """

        """
        req_ = dict(key=key)
        res_ = self._request('get_scatterplot_job', req_)
        return ScatterPlotJob.load(res_)

    def get_histogram(self, dataset_key: str, variable_name: str, number_of_bars: Any, transform: str) -> str:
        """

        """
        req_ = dict(dataset_key=dataset_key, variable_name=variable_name, number_of_bars=number_of_bars, transform=transform)
        res_ = self._request('get_histogram', req_)
        return res_

    def get_histogram_job(self, key: str) -> HistogramJob:
        """

        """
        req_ = dict(key=key)
        res_ = self._request('get_histogram_job', req_)
        return HistogramJob.load(res_)

    def get_vis_stats(self, dataset_key: str) -> str:
        """

        """
        req_ = dict(dataset_key=dataset_key)
        res_ = self._request('get_vis_stats', req_)
        return res_

    def get_vis_stats_job(self, key: str) -> VisStatsJob:
        """

        """
        req_ = dict(key=key)
        res_ = self._request('get_vis_stats_job', req_)
        return VisStatsJob.load(res_)

    def get_boxplot(self, dataset_key: str, variable_name: str) -> str:
        """

        """
        req_ = dict(dataset_key=dataset_key, variable_name=variable_name)
        res_ = self._request('get_boxplot', req_)
        return res_

    def get_boxplot_job(self, key: str) -> BoxplotJob:
        """

        """
        req_ = dict(key=key)
        res_ = self._request('get_boxplot_job', req_)
        return BoxplotJob.load(res_)

    def get_grouped_boxplot(self, datset_key: str, variable_name: str, group_variable_name: str) -> str:
        """

        """
        req_ = dict(datset_key=datset_key, variable_name=variable_name, group_variable_name=group_variable_name)
        res_ = self._request('get_grouped_boxplot', req_)
        return res_

    def get_grouped_boxplot_job(self, key: str) -> BoxplotJob:
        """

        """
        req_ = dict(key=key)
        res_ = self._request('get_grouped_boxplot_job', req_)
        return BoxplotJob.load(res_)

    def get_dotplot(self, key: str, variable_name: str, digits: int) -> str:
        """

        """
        req_ = dict(key=key, variable_name=variable_name, digits=digits)
        res_ = self._request('get_dotplot', req_)
        return res_

    def get_dotplot_job(self, key: str) -> DotplotJob:
        """

        """
        req_ = dict(key=key)
        res_ = self._request('get_dotplot_job', req_)
        return DotplotJob.load(res_)

    def get_parallel_coordinates_plot(self, key: str, variable_names: List[str]) -> str:
        """

        """
        req_ = dict(key=key, variable_names=variable_names)
        res_ = self._request('get_parallel_coordinates_plot', req_)
        return res_

    def get_parallel_coordinates_plot_job(self, key: str) -> ParallelCoordinatesPlotJob:
        """

        """
        req_ = dict(key=key)
        res_ = self._request('get_parallel_coordinates_plot_job', req_)
        return ParallelCoordinatesPlotJob.load(res_)

    def get_heatmap(self, key: str, variable_names: List[str], matrix_type: str, normalize: bool, permute: bool, missing: bool) -> str:
        """

        """
        req_ = dict(key=key, variable_names=variable_names, matrix_type=matrix_type, normalize=normalize, permute=permute, missing=missing)
        res_ = self._request('get_heatmap', req_)
        return res_

    def get_heatmap_job(self, key: str) -> HeatMapJob:
        """

        """
        req_ = dict(key=key)
        res_ = self._request('get_heatmap_job', req_)
        return HeatMapJob.load(res_)

    def get_scale(self, dataset_key: str, data_min: float, data_max: float) -> H2OScale:
        """

        """
        req_ = dict(dataset_key=dataset_key, data_min=data_min, data_max=data_max)
        res_ = self._request('get_scale', req_)
        return H2OScale.load(res_)

    def get_outliers(self, dataset_key: str, variable_names: List[str], alpha: float) -> str:
        """

        """
        req_ = dict(dataset_key=dataset_key, variable_names=variable_names, alpha=alpha)
        res_ = self._request('get_outliers', req_)
        return res_

    def get_outliers_job(self, key: str) -> OutliersJob:
        """

        """
        req_ = dict(key=key)
        res_ = self._request('get_outliers_job', req_)
        return OutliersJob.load(res_)

    def get_barchart(self, dataset_key: str, variable_name: str) -> str:
        """

        """
        req_ = dict(dataset_key=dataset_key, variable_name=variable_name)
        res_ = self._request('get_barchart', req_)
        return res_

    def get_barchart_job(self, key: str) -> BarchartJob:
        """

        """
        req_ = dict(key=key)
        res_ = self._request('get_barchart_job', req_)
        return BarchartJob.load(res_)

    def get_network(self, dataset_key: str, matrix_type: str, normalize: bool) -> str:
        """

        """
        req_ = dict(dataset_key=dataset_key, matrix_type=matrix_type, normalize=normalize)
        res_ = self._request('get_network', req_)
        return res_

    def get_network_job(self, key: str) -> NetworkJob:
        """

        """
        req_ = dict(key=key)
        res_ = self._request('get_network_job', req_)
        return NetworkJob.load(res_)

    def add_autoviz_custom_plot(self, autoviz_key: str, vega_plot_key: str) -> None:
        """
        Add custom vega plot to autoviz, so that next time you open the visualization, you can see it

        """
        req_ = dict(autoviz_key=autoviz_key, vega_plot_key=vega_plot_key)
        self._request('add_autoviz_custom_plot', req_)
        return None

    def remove_autoviz_custom_plot(self, autoviz_key: str, vega_plot_key: str) -> None:
        """
        Remove custom vega plot from autoviz

        """
        req_ = dict(autoviz_key=autoviz_key, vega_plot_key=vega_plot_key)
        self._request('remove_autoviz_custom_plot', req_)
        return None

    def get_recipe_activation(self, parent_experiment_key: str) -> RecipeActivation:
        """

        """
        req_ = dict(parent_experiment_key=parent_experiment_key)
        res_ = self._request('get_recipe_activation', req_)
        return RecipeActivation.load(res_)

    def list_scorers(self, config_overrides: str) -> List[Scorer]:
        """

        """
        req_ = dict(config_overrides=config_overrides)
        res_ = self._request('list_scorers', req_)
        return [Scorer.load(b_) for b_ in res_]

    def list_all_scorers(self) -> List[Scorer]:
        """

        """
        req_ = dict()
        res_ = self._request('list_all_scorers', req_)
        return [Scorer.load(b_) for b_ in res_]

    def list_compatible_scorers(self, model_parameters: ModelParameters, config_overrides: str) -> List[Scorer]:
        """
        Returns list of scorers compatible with current experiment setup

        """
        req_ = dict(model_parameters=model_parameters.dump(), config_overrides=config_overrides)
        res_ = self._request('list_compatible_scorers', req_)
        return [Scorer.load(b_) for b_ in res_]

    def list_transformers(self, config_overrides: str) -> List[TransformerWrapper]:
        """

        """
        req_ = dict(config_overrides=config_overrides)
        res_ = self._request('list_transformers', req_)
        return [TransformerWrapper.load(b_) for b_ in res_]

    def list_pretransformers(self, config_overrides: str) -> List[PreTransformerWrapper]:
        """

        """
        req_ = dict(config_overrides=config_overrides)
        res_ = self._request('list_pretransformers', req_)
        return [PreTransformerWrapper.load(b_) for b_ in res_]

    def list_model_estimators(self, config_overrides: str) -> List[ModelEstimatorWrapper]:
        """

        """
        req_ = dict(config_overrides=config_overrides)
        res_ = self._request('list_model_estimators', req_)
        return [ModelEstimatorWrapper.load(b_) for b_ in res_]

    def list_datas(self, config_overrides: str) -> List[DataWrapper]:
        """

        """
        req_ = dict(config_overrides=config_overrides)
        res_ = self._request('list_datas', req_)
        return [DataWrapper.load(b_) for b_ in res_]

    def run_custom_recipes_db_sync(self) -> None:
        """

        """
        req_ = dict()
        self._request('run_custom_recipes_db_sync', req_)
        return None

    def get_custom_recipes_db_sync_job(self) -> CustomRecipeDbSyncJob:
        """

        """
        req_ = dict()
        res_ = self._request('get_custom_recipes_db_sync_job', req_)
        return CustomRecipeDbSyncJob.load(res_)

    def get_model_trace(self, key: str, offset: int, limit: int) -> ModelTraceEvents:
        """

        """
        req_ = dict(key=key, offset=offset, limit=limit)
        res_ = self._request('get_model_trace', req_)
        return ModelTraceEvents.load(res_)

    def list_model_iteration_data(self, key: str, offset: int, limit: int, num_var_imp: int) -> List[AutoDLProgress]:
        """

        """
        req_ = dict(key=key, offset=offset, limit=limit, num_var_imp=num_var_imp)
        res_ = self._request('list_model_iteration_data', req_)
        return [AutoDLProgress.load(b_) for b_ in res_]

    def list_model_notifications(self, model_key: str, keys: List[str]) -> List[AutoDLNotification]:
        """

        """
        req_ = dict(model_key=model_key, keys=keys)
        res_ = self._request('list_model_notifications', req_)
        return [AutoDLNotification.load(b_) for b_ in res_]

    def make_prediction(self, model_key: str, dataset_key: str, output_margin: bool, pred_contribs: bool, pred_contribs_original: bool, enable_mojo: bool, fast_approx: bool, fast_approx_contribs: bool, keep_non_missing_actuals: bool, include_columns: List[str], pred_labels: bool) -> str:
        """

        """
        req_ = dict(model_key=model_key, dataset_key=dataset_key, output_margin=output_margin, pred_contribs=pred_contribs, pred_contribs_original=pred_contribs_original, enable_mojo=enable_mojo, fast_approx=fast_approx, fast_approx_contribs=fast_approx_contribs, keep_non_missing_actuals=keep_non_missing_actuals, include_columns=include_columns, pred_labels=pred_labels)
        res_ = self._request('make_prediction', req_)
        return res_

    def get_prediction_job(self, key: str) -> PredictionJob:
        """

        """
        req_ = dict(key=key)
        res_ = self._request('get_prediction_job', req_)
        return PredictionJob.load(res_)

    def abort_prediction(self, key: str) -> None:
        """
        Abort running prediction job

        :param key: PredictionJob key
        """
        req_ = dict(key=key)
        self._request('abort_prediction', req_)
        return None

    def download_prediction(self, model_key: str, dataset_type: str, include_columns: List[str]) -> str:
        """

        :param model_key: Model Key
        :param dataset_type: Type of dataset [train/valid/test]
        :param include_columns: List of columns, which should be included in predictions csv
        """
        req_ = dict(model_key=model_key, dataset_type=dataset_type, include_columns=include_columns)
        res_ = self._request('download_prediction', req_)
        return res_

    def make_autoreport(self, model_key: str, mli_key: str, individual_rows: List[int], autoviz_key: str, template_path: str, placeholders: Any, external_dataset_keys: List[str], config_overrides: str, reuse_model_key: bool) -> str:
        """

        :param reuse_model_key: If `True`, autoreport will reuse model key as job key, so that multiple autoreport are not triggered
        """
        validation.validate_toml(config_overrides, 'config_overrides')
        req_ = dict(model_key=model_key, mli_key=mli_key, individual_rows=individual_rows, autoviz_key=autoviz_key, template_path=template_path, placeholders=placeholders, external_dataset_keys=external_dataset_keys, config_overrides=config_overrides, reuse_model_key=reuse_model_key)
        res_ = self._request('make_autoreport', req_)
        return res_

    def abort_autoreport(self, key: str) -> None:
        """

        """
        req_ = dict(key=key)
        self._request('abort_autoreport', req_)
        return None

    def get_autoreport_job(self, key: str) -> AutoReportJob:
        """

        """
        req_ = dict(key=key)
        res_ = self._request('get_autoreport_job', req_)
        return AutoReportJob.load(res_)

    def is_autoreport_active(self, key: str) -> bool:
        """
        Indicates whether there is some active autoreport job with such key

        """
        req_ = dict(key=key)
        res_ = self._request('is_autoreport_active', req_)
        return res_

    def fit_transform_batch(self, model_key: str, training_dataset_key: str, validation_dataset_key: str, test_dataset_key: str, validation_split_fraction: float, seed: int, fold_column: str) -> str:
        """

        """
        req_ = dict(model_key=model_key, training_dataset_key=training_dataset_key, validation_dataset_key=validation_dataset_key, test_dataset_key=test_dataset_key, validation_split_fraction=validation_split_fraction, seed=seed, fold_column=fold_column)
        res_ = self._request('fit_transform_batch', req_)
        return res_

    def get_transformation_job(self, key: str) -> TransformationJob:
        """

        """
        req_ = dict(key=key)
        res_ = self._request('get_transformation_job', req_)
        return TransformationJob.load(res_)

    def abort_transformation(self, key: str) -> None:
        """
        Abort transformation job

        :param key: TransformationJob key
        """
        req_ = dict(key=key)
        self._request('abort_transformation', req_)
        return None

    def run_interpret_timeseries(self, interpret_timeseries_params: InterpretParameters) -> str:
        """

        """
        req_ = dict(interpret_timeseries_params=interpret_timeseries_params.dump())
        res_ = self._request('run_interpret_timeseries', req_)
        return res_

    def get_interpret_timeseries_job(self, key: str) -> InterpretTimeSeriesJob:
        """

        """
        req_ = dict(key=key)
        res_ = self._request('get_interpret_timeseries_job', req_)
        return InterpretTimeSeriesJob.load(res_)

    def run_interpretation(self, interpret_params: InterpretParameters) -> str:
        """

        """
        req_ = dict(interpret_params=interpret_params.dump())
        res_ = self._request('run_interpretation', req_)
        return res_

    def get_interpretation_job(self, key: str) -> InterpretationJob:
        """

        """
        req_ = dict(key=key)
        res_ = self._request('get_interpretation_job', req_)
        return InterpretationJob.load(res_)

    def get_orig_shapley_zip_archive_url(self, key: str, use_kernel: bool) -> str:
        """

        """
        req_ = dict(key=key, use_kernel=use_kernel)
        res_ = self._request('get_orig_shapley_zip_archive_url', req_)
        return res_

    def get_transformed_shapley_zip_archive_url(self, key: str) -> str:
        """

        """
        req_ = dict(key=key)
        res_ = self._request('get_transformed_shapley_zip_archive_url', req_)
        return res_

    def get_kernel_shapley_path(self, key: str) -> str:
        """

        """
        req_ = dict(key=key)
        res_ = self._request('get_kernel_shapley_path', req_)
        return res_

    def get_interpretation_summary(self, key: str) -> InterpretSummary:
        """

        """
        req_ = dict(key=key)
        res_ = self._request('get_interpretation_summary', req_)
        return InterpretSummary.load(res_)

    def build_scoring_pipeline(self, model_key: str, force: bool) -> str:
        """

        """
        req_ = dict(model_key=model_key, force=force)
        res_ = self._request('build_scoring_pipeline', req_)
        return res_

    def build_mojo_pipeline(self, model_key: str, force: bool) -> str:
        """

        """
        req_ = dict(model_key=model_key, force=force)
        res_ = self._request('build_mojo_pipeline', req_)
        return res_

    def list_experiment_artifacts(self, model_key: str) -> ExperimentArtifactSummary:
        """

        """
        req_ = dict(model_key=model_key)
        res_ = self._request('list_experiment_artifacts', req_)
        return ExperimentArtifactSummary.load(res_)

    def upload_experiment_artifacts(self, model_key: str, user_note: str, artifact_path: str, name_override: str, repo: str, branch: str, username: str, password: str) -> str:
        """

        """
        req_ = dict(model_key=model_key, user_note=user_note, artifact_path=artifact_path, name_override=name_override, repo=repo, branch=branch, username=username, password=password)
        res_ = self._request('upload_experiment_artifacts', req_)
        return res_

    def get_artifact_upload_job(self, key: str, artifact_path: str) -> ArtifactsExportJob:
        """

        """
        req_ = dict(key=key, artifact_path=artifact_path)
        res_ = self._request('get_artifact_upload_job', req_)
        return ArtifactsExportJob.load(res_)

    def get_scoring_pipeline_job(self, key: str) -> ScoringPipelineJob:
        """

        """
        req_ = dict(key=key)
        res_ = self._request('get_scoring_pipeline_job', req_)
        return ScoringPipelineJob.load(res_)

    def get_mojo_pipeline_job(self, key: str) -> MojoPipelineJob:
        """

        """
        req_ = dict(key=key)
        res_ = self._request('get_mojo_pipeline_job', req_)
        return MojoPipelineJob.load(res_)

    def get_autoviz_job(self, key: str) -> AutoVizJob:
        """

        """
        req_ = dict(key=key)
        res_ = self._request('get_autoviz_job', req_)
        return AutoVizJob.load(res_)

    def delete_autoviz_job(self, key: str) -> None:
        """

        """
        req_ = dict(key=key)
        self._request('delete_autoviz_job', req_)
        return None

    def have_valid_license(self) -> License:
        """

        """
        req_ = dict()
        res_ = self._request('have_valid_license', req_)
        return License.load(res_)

    def is_valid_license_key(self, license_key: str) -> License:
        """

        """
        req_ = dict(license_key=license_key)
        res_ = self._request('is_valid_license_key', req_)
        return License.load(res_)

    def type_of_mli(self, mli_job_key: str) -> str:
        """

        """
        req_ = dict(mli_job_key=mli_job_key)
        res_ = self._request('type_of_mli', req_)
        return res_

    def save_license_key(self, license_key: str) -> License:
        """

        """
        req_ = dict(license_key=license_key)
        res_ = self._request('save_license_key', req_)
        return License.load(res_)

    def get_experiment_summary_for_mli_key(self, mli_job_key: str) -> str:
        """

        """
        req_ = dict(mli_job_key=mli_job_key)
        res_ = self._request('get_experiment_summary_for_mli_key', req_)
        return res_

    def get_frame_rows(self, frame_name: str, row_offset: int, num_rows: int, mli_job_key: str, orig_feat_shapley: bool, clazz: str) -> str:
        """

        """
        req_ = dict(frame_name=frame_name, row_offset=row_offset, num_rows=num_rows, mli_job_key=mli_job_key, orig_feat_shapley=orig_feat_shapley, clazz=clazz)
        res_ = self._request('get_frame_rows', req_)
        return res_

    def get_frame_row_offset_by_value(self, feature_name: str, feature_value: str, mli_job_key: str) -> int:
        """

        """
        req_ = dict(feature_name=feature_name, feature_value=feature_value, mli_job_key=mli_job_key)
        res_ = self._request('get_frame_row_offset_by_value', req_)
        return res_

    def get_frame_row_by_value(self, frame_name: str, feature_name: str, feature_value: str, num_rows: int, mli_job_key: str) -> str:
        """

        """
        req_ = dict(frame_name=frame_name, feature_name=feature_name, feature_value=feature_value, num_rows=num_rows, mli_job_key=mli_job_key)
        res_ = self._request('get_frame_row_by_value', req_)
        return res_

    def get_original_mli_frame_rows(self, row_offset: int, num_rows: int, mli_job_key: str) -> str:
        """

        """
        req_ = dict(row_offset=row_offset, num_rows=num_rows, mli_job_key=mli_job_key)
        res_ = self._request('get_original_mli_frame_rows', req_)
        return res_

    def is_original_shapley_available(self, mli_job_key: str) -> bool:
        """

        """
        req_ = dict(mli_job_key=mli_job_key)
        res_ = self._request('is_original_shapley_available', req_)
        return res_

    def get_shapley_plot_description(self, mli_job_key: str, orig_feat_shapley: bool) -> str:
        """

        """
        req_ = dict(mli_job_key=mli_job_key, orig_feat_shapley=orig_feat_shapley)
        res_ = self._request('get_shapley_plot_description', req_)
        return res_

    def get_json(self, json_name: str, job_key: str) -> str:
        """

        """
        req_ = dict(json_name=json_name, job_key=job_key)
        res_ = self._request('get_json', req_)
        return res_

    def get_individual_conditional_expectation(self, row_offset: int, mli_job_key: str) -> str:
        """

        """
        req_ = dict(row_offset=row_offset, mli_job_key=mli_job_key)
        res_ = self._request('get_individual_conditional_expectation', req_)
        return res_

    def track_subsystem_event(self, subsystem_name: str, event_name: str) -> None:
        """

        """
        req_ = dict(subsystem_name=subsystem_name, event_name=event_name)
        self._request('track_subsystem_event', req_)
        return None

    def get_raw_data(self, key: str, offset: int, limit: int) -> ExemplarRowsResponse:
        """

        """
        req_ = dict(key=key, offset=offset, limit=limit)
        res_ = self._request('get_raw_data', req_)
        return ExemplarRowsResponse.load(res_)

    def get_exemplar_rows(self, key: str, exemplar_id: int, offset: int, limit: int, variable_id: int) -> ExemplarRowsResponse:
        """

        """
        req_ = dict(key=key, exemplar_id=exemplar_id, offset=offset, limit=limit, variable_id=variable_id)
        res_ = self._request('get_exemplar_rows', req_)
        return ExemplarRowsResponse.load(res_)

    def get_experiment_tuning_suggestion(self, model_params: ModelParameters) -> ModelParameters:
        """
        Returns recommended experiment parameters based on dataset/target/config/... params

        """
        req_ = dict(model_params=model_params.dump())
        res_ = self._request('get_experiment_tuning_suggestion', req_)
        return ModelParameters.load(res_)

    def get_experiment_preview(self, model_params: ModelParameters) -> str:
        """

        """
        req_ = dict(model_params=model_params.dump())
        res_ = self._request('get_experiment_preview', req_)
        return res_

    def get_experiment_preview_job(self, key: str) -> ExperimentPreviewJob:
        """

        """
        req_ = dict(key=key)
        res_ = self._request('get_experiment_preview_job', req_)
        return ExperimentPreviewJob.load(res_)

    def get_current_user_info(self) -> UserInfo:
        """

        """
        req_ = dict()
        res_ = self._request('get_current_user_info', req_)
        return UserInfo.load(res_)

    def get_timeseries_split_suggestion(self, train_key: str, time_col: str, time_groups_columns: List[str], test_key: str, config_overrides: str) -> str:
        """

        """
        validation.validate_toml(config_overrides, 'config_overrides')
        req_ = dict(train_key=train_key, time_col=time_col, time_groups_columns=time_groups_columns, test_key=test_key, config_overrides=config_overrides)
        res_ = self._request('get_timeseries_split_suggestion', req_)
        return res_

    def get_timeseries_split_suggestion_job(self, key: str) -> TimeSeriesSplitSuggestionJob:
        """

        """
        req_ = dict(key=key)
        res_ = self._request('get_timeseries_split_suggestion_job', req_)
        return TimeSeriesSplitSuggestionJob.load(res_)

    def create_aws_lambda(self, model_key: str, aws_credentials: AwsCredentials, aws_lambda_parameters: AwsLambdaParameters) -> str:
        """
        Creates a new AWS lambda deployment for the specified model using the given AWS credentials.

        """
        req_ = dict(model_key=model_key, aws_credentials=aws_credentials.dump(), aws_lambda_parameters=aws_lambda_parameters.dump())
        res_ = self._request('create_aws_lambda', req_)
        return res_

    def create_local_rest_scorer(self, model_key: str, local_rest_scorer_parameters: LocalRestScorerParameters) -> str:
        """
        Creates new local rest scorer deployment for specified model

        """
        req_ = dict(model_key=model_key, local_rest_scorer_parameters=local_rest_scorer_parameters.dump())
        res_ = self._request('create_local_rest_scorer', req_)
        return res_

    def restart_deployment(self, deployment_key: str) -> str:
        """

        """
        req_ = dict(deployment_key=deployment_key)
        res_ = self._request('restart_deployment', req_)
        return res_

    def generate_local_rest_scorer_sample_data(self, model_key: str) -> str:
        """

        """
        req_ = dict(model_key=model_key)
        res_ = self._request('generate_local_rest_scorer_sample_data', req_)
        return res_

    def get_create_deployment_job(self, key: str) -> CreateDeploymentJob:
        """

        """
        req_ = dict(key=key)
        res_ = self._request('get_create_deployment_job', req_)
        return CreateDeploymentJob.load(res_)

    def destroy_aws_lambda(self, deployment_key: str) -> str:
        """
        Shuts down an AWS lambda deployment removing it entirely from the associated AWS account.
        Any new deployment will result in a different endpoint URL using a different api_key.

        """
        req_ = dict(deployment_key=deployment_key)
        res_ = self._request('destroy_aws_lambda', req_)
        return res_

    def destroy_local_rest_scorer(self, deployment_key: str) -> str:
        """

        """
        req_ = dict(deployment_key=deployment_key)
        res_ = self._request('destroy_local_rest_scorer', req_)
        return res_

    def get_destroy_deployment_job(self, key: str) -> DestroyDeploymentJob:
        """

        """
        req_ = dict(key=key)
        res_ = self._request('get_destroy_deployment_job', req_)
        return DestroyDeploymentJob.load(res_)

    def get_deployment(self, key: str) -> Deployment:
        """

        """
        req_ = dict(key=key)
        res_ = self._request('get_deployment', req_)
        return Deployment.load(res_)

    def list_deployments(self, offset: int, limit: int) -> ListDeploymentQueryResponse:
        """

        """
        req_ = dict(offset=offset, limit=limit)
        res_ = self._request('list_deployments', req_)
        return ListDeploymentQueryResponse.load(res_)

    def search_and_sort_deployments(self, search_query: str, sort_query: EntitySortQuery, ascending: bool, offset: int, limit: int) -> ListDeploymentQueryResponse:
        """
        List, search and sort deployment

        :param search_query: String which is used for full-text search
        :param sort_query: Entity sort query specifying path to nested field
        """
        req_ = dict(search_query=search_query, sort_query=sort_query.dump(), ascending=ascending, offset=offset, limit=limit)
        res_ = self._request('search_and_sort_deployments', req_)
        return ListDeploymentQueryResponse.load(res_)

    def check_rest_scorer_deployment_health(self) -> bool:
        """

        """
        req_ = dict()
        res_ = self._request('check_rest_scorer_deployment_health', req_)
        return res_

    def drop_local_rest_scorer_from_database(self, key: str) -> None:
        """

        """
        req_ = dict(key=key)
        self._request('drop_local_rest_scorer_from_database', req_)
        return None

    def list_aws_regions(self, aws_credentials: AwsCredentials) -> List[str]:
        """
        List supported AWS regions.

        """
        req_ = dict(aws_credentials=aws_credentials.dump())
        res_ = self._request('list_aws_regions', req_)
        return res_

    def list_keys_by_name(self, kind: str, display_name: str) -> List[str]:
        """
        List all keys of caller's entities with the given display_name and kind.
        Note that display_names are not unique so this call returns a list of keys.

        :param kind: Kind of entities to be listed.
        :param display_name: Display name of the entities to be listed.
        """
        req_ = dict(kind=kind, display_name=display_name)
        res_ = self._request('list_keys_by_name', req_)
        return res_

    def get_model_diagnostic(self, model_key: str, dataset_key: str) -> str:
        """
        Makes model diagnostic from DAI model, containing logic for creating the predictions

        """
        req_ = dict(model_key=model_key, dataset_key=dataset_key)
        res_ = self._request('get_model_diagnostic', req_)
        return res_

    def get_model_diagnostic_job(self, key: str) -> ModelDiagnosticJob:
        """

        """
        req_ = dict(key=key)
        res_ = self._request('get_model_diagnostic_job', req_)
        return ModelDiagnosticJob.load(res_)

    def list_model_diagnostic(self, offset: int, limit: int) -> ListModelDiagnosticQueryResponse:
        """

        """
        req_ = dict(offset=offset, limit=limit)
        res_ = self._request('list_model_diagnostic', req_)
        return ListModelDiagnosticQueryResponse.load(res_)

    def search_and_sort_model_diagnostic(self, search_query: str, sort_query: EntitySortQuery, ascending: bool, offset: int, limit: int) -> ListModelDiagnosticQueryResponse:
        """
        List, search and sort model diagnostics

        :param search_query: String which is used for full-text search
        :param sort_query: Entity sort query specifying path to nested field
        """
        req_ = dict(search_query=search_query, sort_query=sort_query.dump(), ascending=ascending, offset=offset, limit=limit)
        res_ = self._request('search_and_sort_model_diagnostic', req_)
        return ListModelDiagnosticQueryResponse.load(res_)

    def delete_model_diagnostic_job(self, key: str) -> None:
        """

        """
        req_ = dict(key=key)
        self._request('delete_model_diagnostic_job', req_)
        return None

    def get_diagnostic_cm_for_threshold(self, diagnostic_key: str, threshold: float) -> str:
        """
        Returns Model diagnostic Job, where only argmax_cm will be populated

        """
        req_ = dict(diagnostic_key=diagnostic_key, threshold=threshold)
        res_ = self._request('get_diagnostic_cm_for_threshold', req_)
        return res_

    def get_project(self, key: str) -> Project:
        """

        """
        req_ = dict(key=key)
        res_ = self._request('get_project', req_)
        return Project.load(res_)

    def list_project_experiments(self, project_key: str) -> ListProjectExperimentsResponse:
        """

        """
        req_ = dict(project_key=project_key)
        res_ = self._request('list_project_experiments', req_)
        return ListProjectExperimentsResponse.load(res_)

    def get_datasets_for_project(self, project_key: str, dataset_type: str) -> List[DatasetSummary]:
        """

        """
        req_ = dict(project_key=project_key, dataset_type=dataset_type)
        res_ = self._request('get_datasets_for_project', req_)
        return [DatasetSummary.load(b_) for b_ in res_]

    def create_project(self, name: str, description: str) -> str:
        """

        """
        req_ = dict(name=name, description=description)
        res_ = self._request('create_project', req_)
        return res_

    def link_dataset_to_project(self, project_key: str, dataset_key: str, dataset_type: str, link_dataset_experiments: bool) -> bool:
        """

        :param link_dataset_experiments: If true, also link experiments that use this dataset as train/valid/test set
        """
        req_ = dict(project_key=project_key, dataset_key=dataset_key, dataset_type=dataset_type, link_dataset_experiments=link_dataset_experiments)
        res_ = self._request('link_dataset_to_project', req_)
        return res_

    def unlink_dataset_from_project(self, project_key: str, dataset_key: str, dataset_type: str) -> bool:
        """

        """
        req_ = dict(project_key=project_key, dataset_key=dataset_key, dataset_type=dataset_type)
        res_ = self._request('unlink_dataset_from_project', req_)
        return res_

    def link_experiment_to_project(self, project_key: str, experiment_key: str) -> bool:
        """

        """
        req_ = dict(project_key=project_key, experiment_key=experiment_key)
        res_ = self._request('link_experiment_to_project', req_)
        return res_

    def unlink_experiment_from_project(self, project_key: str, experiment_key: str) -> bool:
        """

        """
        req_ = dict(project_key=project_key, experiment_key=experiment_key)
        res_ = self._request('unlink_experiment_from_project', req_)
        return res_

    def relink_experiment_from_local_to_remote(self, project_key: str, experiment_key: str) -> bool:
        """

        """
        req_ = dict(project_key=project_key, experiment_key=experiment_key)
        res_ = self._request('relink_experiment_from_local_to_remote', req_)
        return res_

    def update_project_name(self, key: str, name: str) -> bool:
        """

        """
        req_ = dict(key=key, name=name)
        res_ = self._request('update_project_name', req_)
        return res_

    def update_project_description(self, key: str, description: str) -> bool:
        """

        """
        req_ = dict(key=key, description=description)
        res_ = self._request('update_project_description', req_)
        return res_

    def delete_project(self, key: str) -> None:
        """

        """
        req_ = dict(key=key)
        self._request('delete_project', req_)
        return None

    def share_project(self, project_id: str, user_id: str, restriction_role_id: str) -> None:
        """
        Grant an access to a project.

        """
        req_ = dict(project_id=project_id, user_id=user_id, restriction_role_id=restriction_role_id)
        self._request('share_project', req_)
        return None

    def unshare_project(self, project_id: str, sharing_id: str) -> None:
        """

        """
        req_ = dict(project_id=project_id, sharing_id=sharing_id)
        self._request('unshare_project', req_)
        return None

    def get_dataset_split_timeseries_preview(self, dataset_key: str, time_column: str, split_ratio: float) -> float:
        """
        Get estimated split ratio for number of rows in timeseries data

        """
        req_ = dict(dataset_key=dataset_key, time_column=time_column, split_ratio=split_ratio)
        res_ = self._request('get_dataset_split_timeseries_preview', req_)
        return res_

    def make_dataset_split(self, dataset_key: str, output_name1: str, output_name2: str, target: str, fold_col: str, time_col: str, ratio: float, seed: int) -> str:
        """

        """
        req_ = dict(dataset_key=dataset_key, output_name1=output_name1, output_name2=output_name2, target=target, fold_col=fold_col, time_col=time_col, ratio=ratio, seed=seed)
        res_ = self._request('make_dataset_split', req_)
        return res_

    def get_dataset_split_job(self, key: str) -> DatasetSplitJob:
        """

        """
        req_ = dict(key=key)
        res_ = self._request('get_dataset_split_job', req_)
        return DatasetSplitJob.load(res_)

    def get_users(self) -> List[str]:
        """

        """
        req_ = dict()
        res_ = self._request('get_users', req_)
        return res_

    def create_csv_from_dataset(self, key: str) -> str:
        """
        Create csv version of dataset in it's folder.
        Returns url to created file.

        """
        req_ = dict(key=key)
        res_ = self._request('create_csv_from_dataset', req_)
        return res_

    def get_create_csv_job(self, key: str) -> CreateCsvJob:
        """

        """
        req_ = dict(key=key)
        res_ = self._request('get_create_csv_job', req_)
        return CreateCsvJob.load(res_)

    def get_custom_recipe_job(self, key: str) -> CustomRecipeJob:
        """

        """
        req_ = dict(key=key)
        res_ = self._request('get_custom_recipe_job', req_)
        return CustomRecipeJob.load(res_)

    def create_custom_recipe_from_url(self, url: str) -> str:
        """

        """
        req_ = dict(url=url)
        res_ = self._request('create_custom_recipe_from_url', req_)
        return res_

    def abort_custom_recipe_job(self, key: str) -> None:
        """

        """
        req_ = dict(key=key)
        self._request('abort_custom_recipe_job', req_)
        return None

    def run_custom_recipes_acceptance_checks(self) -> None:
        """

        """
        req_ = dict()
        self._request('run_custom_recipes_acceptance_checks', req_)
        return None

    def get_custom_recipes_acceptance_job(self) -> CustomRecipeJob:
        """

        """
        req_ = dict()
        res_ = self._request('get_custom_recipes_acceptance_job', req_)
        return CustomRecipeJob.load(res_)

    def get_dia_summary(self, key: str) -> DiaSummary:
        """

        """
        req_ = dict(key=key)
        res_ = self._request('get_dia_summary', req_)
        return DiaSummary.load(res_)

    def get_dia_avp(self, key: str, dia_variable: str) -> DiaAvp:
        """

        """
        req_ = dict(key=key, dia_variable=dia_variable)
        res_ = self._request('get_dia_avp', req_)
        return DiaAvp.load(res_)

    def get_dia(self, dia_key: str, dia_variable: str, dia_ref_levels: List[str], offset: int, count: int, sort_column: str, sort_order: str) -> Dia:
        """

        """
        req_ = dict(dia_key=dia_key, dia_variable=dia_variable, dia_ref_levels=dia_ref_levels, offset=offset, count=count, sort_column=sort_column, sort_order=sort_order)
        res_ = self._request('get_dia', req_)
        return Dia.load(res_)

    def get_all_dia_parity_ui(self, dia_key: str, dia_variable: str, low_threshold: float, high_threshold: float, offset: int, count: int, sort_column: str, sort_order: str) -> List[DiaNamedMatrix]:
        """

        """
        req_ = dict(dia_key=dia_key, dia_variable=dia_variable, low_threshold=low_threshold, high_threshold=high_threshold, offset=offset, count=count, sort_column=sort_column, sort_order=sort_order)
        res_ = self._request('get_all_dia_parity_ui', req_)
        return [DiaNamedMatrix.load(b_) for b_ in res_]

    def get_dia_parity_ui(self, dia_key: str, dia_variable: str, ref_level: str, low_threshold: float, high_threshold: float, offset: int, count: int, sort_column: str, sort_order: str) -> DiaMatrix:
        """

        """
        req_ = dict(dia_key=dia_key, dia_variable=dia_variable, ref_level=ref_level, low_threshold=low_threshold, high_threshold=high_threshold, offset=offset, count=count, sort_column=sort_column, sort_order=sort_order)
        res_ = self._request('get_dia_parity_ui', req_)
        return DiaMatrix.load(res_)

    def get_explainer_interpretation_status(self, mli_key: str) -> JobStatus:
        """

        """
        req_ = dict(mli_key=mli_key)
        res_ = self._request('get_explainer_interpretation_status', req_)
        return JobStatus.load(res_)

    def get_mli_importance(self, model_type: str, importance_type: str, mli_key: str, row_idx: int, code_offset: int, number_of_codes: int) -> List[MliVarImpTable]:
        """

        """
        req_ = dict(model_type=model_type, importance_type=importance_type, mli_key=mli_key, row_idx=row_idx, code_offset=code_offset, number_of_codes=number_of_codes)
        res_ = self._request('get_mli_importance', req_)
        return [MliVarImpTable.load(b_) for b_ in res_]

    def get_mli_train_residual_path(self, mli_key: str) -> str:
        """

        """
        req_ = dict(mli_key=mli_key)
        res_ = self._request('get_mli_train_residual_path', req_)
        return res_

    def get_data_recipe_preview(self, dataset_key: str, code: str) -> str:
        """
        Gets the preview of recipe on subset of data
        Returns DataPreviewJob

        :param dataset_key: Dataset key on which recipe is run
        :param code: Raw code of the recipe
        """
        req_ = dict(dataset_key=dataset_key, code=code)
        res_ = self._request('get_data_recipe_preview', req_)
        return res_

    def get_data_recipe_code(self, code: str) -> str:
        """

        :param code: Raw code of the recipe
        """
        req_ = dict(code=code)
        res_ = self._request('get_data_recipe_code', req_)
        return res_

    def get_data_preview_job(self, key: str) -> DataPreviewJob:
        """

        """
        req_ = dict(key=key)
        res_ = self._request('get_data_preview_job', req_)
        return DataPreviewJob.load(res_)

    def is_sa_enabled(self) -> bool:
        """
        Sensitivity analysis: REST RPC

        """
        req_ = dict()
        res_ = self._request('is_sa_enabled', req_)
        return res_

    def create_sa(self, mli_key: str) -> str:
        """

        """
        req_ = dict(mli_key=mli_key)
        res_ = self._request('create_sa', req_)
        return res_

    def get_sa_create_progress(self, sa_key: str) -> int:
        """

        """
        req_ = dict(sa_key=sa_key)
        res_ = self._request('get_sa_create_progress', req_)
        return res_

    def get_sas_for_mli(self, mli_key: str) -> List[str]:
        """

        """
        req_ = dict(mli_key=mli_key)
        res_ = self._request('get_sas_for_mli', req_)
        return res_

    def get_complete_sa(self, sa_key: str, hist_entry: int, main_chart_feature: Any) -> Sa:
        """

        """
        req_ = dict(sa_key=sa_key, hist_entry=hist_entry, main_chart_feature=main_chart_feature)
        res_ = self._request('get_complete_sa', req_)
        return Sa.load(res_)

    def get_sa(self, sa_key: str, hist_entry: int, ws_features: List[Any], main_chart_feature: Any) -> Sa:
        """
        This procedure provides type safe functionality to frontend.

        """
        req_ = dict(sa_key=sa_key, hist_entry=hist_entry, ws_features=ws_features, main_chart_feature=main_chart_feature)
        res_ = self._request('get_sa', req_)
        return Sa.load(res_)

    def get_sa_dataset_summary(self, sa_key: str) -> SaDatasetSummary:
        """

        """
        req_ = dict(sa_key=sa_key)
        res_ = self._request('get_sa_dataset_summary', req_)
        return SaDatasetSummary.load(res_)

    def get_sa_ws_summary(self, sa_key: str, hist_entry: int) -> SaWorkingSetSummary:
        """

        """
        req_ = dict(sa_key=sa_key, hist_entry=hist_entry)
        res_ = self._request('get_sa_ws_summary', req_)
        return SaWorkingSetSummary.load(res_)

    def get_sa_ws(self, sa_key: str, hist_entry: int, features: List[Any], page_offset: int, page_size: int) -> SaWorkingSet:
        """

        """
        req_ = dict(sa_key=sa_key, hist_entry=hist_entry, features=features, page_offset=page_offset, page_size=page_size)
        res_ = self._request('get_sa_ws', req_)
        return SaWorkingSet.load(res_)

    def get_sa_ws_complete_summary_row(self, sa_key: str, hist_entry: int) -> SaWorkingSetRow:
        """
        This procedure provides type safe functionality to frontend.

        """
        req_ = dict(sa_key=sa_key, hist_entry=hist_entry)
        res_ = self._request('get_sa_ws_complete_summary_row', req_)
        return SaWorkingSetRow.load(res_)

    def get_sa_ws_summary_row(self, sa_key: str, hist_entry: int, features: List[Any]) -> SaWorkingSetRow:
        """

        """
        req_ = dict(sa_key=sa_key, hist_entry=hist_entry, features=features)
        res_ = self._request('get_sa_ws_summary_row', req_)
        return SaWorkingSetRow.load(res_)

    def get_sa_ws_summary_for_column(self, sa_key: str, hist_entry: int, column: str) -> SaFeatureMeta:
        """

        """
        req_ = dict(sa_key=sa_key, hist_entry=hist_entry, column=column)
        res_ = self._request('get_sa_ws_summary_for_column', req_)
        return SaFeatureMeta.load(res_)

    def get_sa_ws_summary_for_row(self, sa_key: str, hist_entry: int, row: int) -> SaWorkingSetRow:
        """

        """
        req_ = dict(sa_key=sa_key, hist_entry=hist_entry, row=row)
        res_ = self._request('get_sa_ws_summary_for_row', req_)
        return SaWorkingSetRow.load(res_)

    def filter_sa_ws(self, sa_key: str, row_from: Any, row_to: Any, expr_feature: str, expr_op: str, expr_value: str, f_expr: Any) -> SaShape:
        """
        filter the last history entry

        """
        req_ = dict(sa_key=sa_key, row_from=row_from, row_to=row_to, expr_feature=expr_feature, expr_op=expr_op, expr_value=expr_value, f_expr=f_expr)
        res_ = self._request('filter_sa_ws', req_)
        return SaShape.load(res_)

    def reset_sa_ws(self, sa_key: str) -> SaShape:
        """

        """
        req_ = dict(sa_key=sa_key)
        res_ = self._request('reset_sa_ws', req_)
        return SaShape.load(res_)

    def change_sa_ws(self, sa_key: str, action: str, target_col: str, target_row: Any, value: Any) -> SaShape:
        """

        """
        req_ = dict(sa_key=sa_key, action=action, target_col=target_col, target_row=target_row, value=value)
        res_ = self._request('change_sa_ws', req_)
        return SaShape.load(res_)

    def score_sa(self, sa_key: str, hist_entry: int) -> int:
        """

        """
        req_ = dict(sa_key=sa_key, hist_entry=hist_entry)
        res_ = self._request('score_sa', req_)
        return res_

    def get_sa_score_progress(self, sa_key: str, hist_entry: int) -> int:
        """

        """
        req_ = dict(sa_key=sa_key, hist_entry=hist_entry)
        res_ = self._request('get_sa_score_progress', req_)
        return res_

    def abort_sa_action(self, sa_key: str) -> bool:
        """

        """
        req_ = dict(sa_key=sa_key)
        res_ = self._request('abort_sa_action', req_)
        return res_

    def get_sa_predictions(self, sa_key: str, hist_entry: int) -> SaWorkingSetPreds:
        """

        """
        req_ = dict(sa_key=sa_key, hist_entry=hist_entry)
        res_ = self._request('get_sa_predictions', req_)
        return SaWorkingSetPreds.load(res_)

    def get_sa_statistics(self, sa_key: str, hist_entry: int) -> SaStatistics:
        """

        """
        req_ = dict(sa_key=sa_key, hist_entry=hist_entry)
        res_ = self._request('get_sa_statistics', req_)
        return SaStatistics.load(res_)

    def get_sa_preds_history_chart_data(self, sa_key: str) -> SaPredsHistoryChartData:
        """

        """
        req_ = dict(sa_key=sa_key)
        res_ = self._request('get_sa_preds_history_chart_data', req_)
        return SaPredsHistoryChartData.load(res_)

    def get_sa_main_chart_data(self, sa_key: str, hist_entry: int, feature: Any, page_offset: int, page_size: int, aggregate: bool) -> SaMainChartData:
        """

        """
        req_ = dict(sa_key=sa_key, hist_entry=hist_entry, feature=feature, page_offset=page_offset, page_size=page_size, aggregate=aggregate)
        res_ = self._request('get_sa_main_chart_data', req_)
        return SaMainChartData.load(res_)

    def get_sa_history(self, sa_key: str) -> SaHistory:
        """

        """
        req_ = dict(sa_key=sa_key)
        res_ = self._request('get_sa_history', req_)
        return SaHistory.load(res_)

    def get_sa_history_entry(self, sa_key: str, hist_entry: int) -> SaHistoryItem:
        """

        """
        req_ = dict(sa_key=sa_key, hist_entry=hist_entry)
        res_ = self._request('get_sa_history_entry', req_)
        return SaHistoryItem.load(res_)

    def pop_sa_history(self, sa_key: str) -> bool:
        """

        """
        req_ = dict(sa_key=sa_key)
        res_ = self._request('pop_sa_history', req_)
        return res_

    def remove_sa_history_entry(self, sa_key: str, hist_entry: int) -> bool:
        """

        """
        req_ = dict(sa_key=sa_key, hist_entry=hist_entry)
        res_ = self._request('remove_sa_history_entry', req_)
        return res_

    def clear_sa_history(self, sa_key: str) -> bool:
        """

        """
        req_ = dict(sa_key=sa_key)
        res_ = self._request('clear_sa_history', req_)
        return res_

    def list_explainable_datasets(self, model_to_explain: str, offset: int, size: int) -> ListDatasetQueryResponse:
        """

        """
        req_ = dict(model_to_explain=model_to_explain, offset=offset, size=size)
        res_ = self._request('list_explainable_datasets', req_)
        return ListDatasetQueryResponse.load(res_)

    def filter_explainable_datasets(self, model_to_explain: str, search_query: str, sort_query: EntitySortQuery, ascending: bool, offset: int, size: int, include_inactive: bool, dataset_filter: List[FilterEntry]) -> ListDatasetQueryResponse:
        """
        List, search and sort EXPLAINABLE datasets

        """
        req_ = dict(model_to_explain=model_to_explain, search_query=search_query, sort_query=sort_query.dump(), ascending=ascending, offset=offset, size=size, include_inactive=include_inactive, dataset_filter=[a_.dump() for a_ in dataset_filter])
        res_ = self._request('filter_explainable_datasets', req_)
        return ListDatasetQueryResponse.load(res_)

    def get_health(self) -> HealthResponse:
        """

        """
        req_ = dict()
        res_ = self._request('get_health', req_)
        return HealthResponse.load(res_)

    def get_experiments_queue(self) -> TaskQueueResponse:
        """
        Returns list of exeriment IDs in Task queue

        """
        req_ = dict()
        res_ = self._request('get_experiments_queue', req_)
        return TaskQueueResponse.load(res_)

    def get_column_stat(self, dataset_key: str, column_name: str, stat_type: str, meta: Any) -> str:
        """
        Gets column statistics like mean, median or specific percentile

        :param stat_type: Statistics type ref. `h2oaicore/imputation_utils.py:ImputationType`
        :param meta: Can be e.g. percentile rank
        """
        req_ = dict(dataset_key=dataset_key, column_name=column_name, stat_type=stat_type, meta=meta)
        res_ = self._request('get_column_stat', req_)
        return res_

    def add_pending_jobs_item(self, item: PendingJobsListItem) -> str:
        """

        """
        req_ = dict(item=item.dump())
        res_ = self._request('add_pending_jobs_item', req_)
        return res_

    def update_pending_jobs_item(self, key: str, item: PendingJobsListItem) -> None:
        """

        """
        req_ = dict(key=key, item=item.dump())
        self._request('update_pending_jobs_item', req_)
        return None

    def delete_pending_jobs_item(self, key: str) -> None:
        """

        """
        req_ = dict(key=key)
        self._request('delete_pending_jobs_item', req_)
        return None

    def list_pending_jobs(self) -> List[PendingJobsListItem]:
        """

        """
        req_ = dict()
        res_ = self._request('list_pending_jobs', req_)
        return [PendingJobsListItem.load(b_) for b_ in res_]

    def list_explainers(self, experiment_types: List[str], explanation_scopes: List[str], dai_model_key: str, keywords: List[str], explainer_filter: List[FilterEntry]) -> List[ExplainerDescriptor]:
        """

        """
        req_ = dict(experiment_types=experiment_types, explanation_scopes=explanation_scopes, dai_model_key=dai_model_key, keywords=keywords, explainer_filter=[a_.dump() for a_ in explainer_filter])
        res_ = self._request('list_explainers', req_)
        return [ExplainerDescriptor.load(b_) for b_ in res_]

    def list_explainable_models(self, explainer_id: str, offset: int, size: int) -> ListModelQueryResponse:
        """

        """
        req_ = dict(explainer_id=explainer_id, offset=offset, size=size)
        res_ = self._request('list_explainable_models', req_)
        return ListModelQueryResponse.load(res_)

    def get_explainer(self, explainer_id: str) -> ExplainerDescriptor:
        """

        """
        req_ = dict(explainer_id=explainer_id)
        res_ = self._request('get_explainer', req_)
        return ExplainerDescriptor.load(res_)

    def run_explainers(self, explainers: List[Explainer], params: CommonDaiExplainerParameters) -> ExplainersRunJob:
        """

        :param explainers: explainers to run
        :param params: common DAI explainer run parameters
        """
        req_ = dict(explainers=[a_.dump() for a_ in explainers], params=params.dump())
        res_ = self._request('run_explainers', req_)
        return ExplainersRunJob.load(res_)

    def run_interpretation_with_explainers(self, explainers: List[Explainer], params: CommonDaiExplainerParameters, interpret_params: InterpretParameters, display_name: str) -> ExplainersRunJob:
        """

        :param explainers: explainers to run
        :param params: common DAI explainer run parameters
        """
        req_ = dict(explainers=[a_.dump() for a_ in explainers], params=params.dump(), interpret_params=interpret_params.dump(), display_name=display_name)
        res_ = self._request('run_interpretation_with_explainers', req_)
        return ExplainersRunJob.load(res_)

    def get_explainer_run_job(self, explainer_job_key: str) -> ExplainerRunJob:
        """

        """
        req_ = dict(explainer_job_key=explainer_job_key)
        res_ = self._request('get_explainer_run_job', req_)
        return ExplainerRunJob.load(res_)

    def abort_explainer_run_jobs(self, mli_key: str, explainer_job_keys: List[str]) -> None:
        """

        """
        req_ = dict(mli_key=mli_key, explainer_job_keys=explainer_job_keys)
        self._request('abort_explainer_run_jobs', req_)
        return None

    def get_explainers_run_params(self, mli_key: str) -> str:
        """

        """
        req_ = dict(mli_key=mli_key)
        res_ = self._request('get_explainers_run_params', req_)
        return res_

    def get_explainer_job_status(self, mli_key: str, explainer_job_key: str) -> ExplainerJobStatus:
        """

        """
        req_ = dict(mli_key=mli_key, explainer_job_key=explainer_job_key)
        res_ = self._request('get_explainer_job_status', req_)
        return ExplainerJobStatus.load(res_)

    def get_explainer_job_statuses(self, mli_key: str, explainer_job_keys: List[str]) -> List[ExplainerJobStatus]:
        """

        """
        req_ = dict(mli_key=mli_key, explainer_job_keys=explainer_job_keys)
        res_ = self._request('get_explainer_job_statuses', req_)
        return [ExplainerJobStatus.load(b_) for b_ in res_]

    def get_explainer_job_keys_by_id(self, mli_key: str, explainer_id: str) -> List[str]:
        """

        """
        req_ = dict(mli_key=mli_key, explainer_id=explainer_id)
        res_ = self._request('get_explainer_job_keys_by_id', req_)
        return res_

    def get_explainer_run_log_url_path(self, mli_key: str, explainer_job_key: str) -> str:
        """

        """
        req_ = dict(mli_key=mli_key, explainer_job_key=explainer_job_key)
        res_ = self._request('get_explainer_run_log_url_path', req_)
        return res_

    def list_explainer_results(self, explainer_job_key: str) -> ExplainerDescriptor:
        """

        """
        req_ = dict(explainer_job_key=explainer_job_key)
        res_ = self._request('list_explainer_results', req_)
        return ExplainerDescriptor.load(res_)

    def get_explainer_result_url_path(self, mli_key: str, explainer_job_key: str, explanation_type: str, explanation_format: str) -> str:
        """

        """
        req_ = dict(mli_key=mli_key, explainer_job_key=explainer_job_key, explanation_type=explanation_type, explanation_format=explanation_format)
        res_ = self._request('get_explainer_result_url_path', req_)
        return res_

    def get_explainer_snapshot_url_path(self, mli_key: str, explainer_job_key: str) -> str:
        """

        """
        req_ = dict(mli_key=mli_key, explainer_job_key=explainer_job_key)
        res_ = self._request('get_explainer_snapshot_url_path', req_)
        return res_

    def get_explainer_result(self, mli_key: str, explainer_job_key: str, explanation_type: str, explanation_format: str, page_offset: int, page_size: int, result_format: str, explanation_filter: List[FilterEntry]) -> str:
        """

        """
        req_ = dict(mli_key=mli_key, explainer_job_key=explainer_job_key, explanation_type=explanation_type, explanation_format=explanation_format, page_offset=page_offset, page_size=page_size, result_format=result_format, explanation_filter=[a_.dump() for a_ in explanation_filter])
        res_ = self._request('get_explainer_result', req_)
        return res_

    def get_explainer_local_result(self, mli_key: str, explainer_job_key: str, explanation_type: str, explanation_format: str, id_column_name: str, id_column_value: str, page_offset: int, page_size: int, result_format: str, explanation_filter: List[FilterEntry]) -> str:
        """

        """
        req_ = dict(mli_key=mli_key, explainer_job_key=explainer_job_key, explanation_type=explanation_type, explanation_format=explanation_format, id_column_name=id_column_name, id_column_value=id_column_value, page_offset=page_offset, page_size=page_size, result_format=result_format, explanation_filter=[a_.dump() for a_ in explanation_filter])
        res_ = self._request('get_explainer_local_result', req_)
        return res_

    def update_explainer_global_result(self, mli_key: str, explainer_job_key: str, params: CommonDaiExplainerParameters, explainer_params: str, explanation_type: str, explanation_format: str, update_params: str) -> str:
        """

        """
        req_ = dict(mli_key=mli_key, explainer_job_key=explainer_job_key, params=params.dump(), explainer_params=explainer_params, explanation_type=explanation_type, explanation_format=explanation_format, update_params=update_params)
        res_ = self._request('update_explainer_global_result', req_)
        return res_

    def filter_interpret_timeseries_frame_data(self, interpretation_key: str, frame_name: str, queries: List[ColumnQuery]) -> str:
        """
        Filter dataset rows searching for values in specific columns

        :param queries: List of dataset queries which will be concatenated using AND operator
        """
        req_ = dict(interpretation_key=interpretation_key, frame_name=frame_name, queries=[a_.dump() for a_ in queries])
        res_ = self._request('filter_interpret_timeseries_frame_data', req_)
        return res_

    def get_runtime_task_information(self, cpu_queue: bool, gpu_queue: bool, local_queue: bool) -> RuntimeTaskInformation:
        """

        """
        req_ = dict(cpu_queue=cpu_queue, gpu_queue=gpu_queue, local_queue=local_queue)
        res_ = self._request('get_runtime_task_information', req_)
        return RuntimeTaskInformation.load(res_)

    def is_mli_legacy_interpretation(self, mli_key: List[str]) -> List[bool]:
        """
        Check if legacy MLI.

        :param mli_key: The MLI experiment's key.
        """
        req_ = dict(mli_key=mli_key)
        res_ = self._request('is_mli_legacy_interpretation', req_)
        return res_

    def is_mli_legacy_interpretation_migratable(self, mli_key: List[str]) -> List[bool]:
        """
        Check if legacy MLI is migratable.

        :param mli_key: The MLI experiment's key.
        """
        req_ = dict(mli_key=mli_key)
        res_ = self._request('is_mli_legacy_interpretation_migratable', req_)
        return res_

    def migrate_legacy_mli(self, mli_key: str) -> bool:
        """
        Migrate legacy MLI.

        :param mli_key: The MLI experiment's key.
        """
        req_ = dict(mli_key=mli_key)
        res_ = self._request('migrate_legacy_mli', req_)
        return res_

    def abort_task(self, task_id: str) -> None:
        """
        Universal procedure to abort any running system task for a user

        :param task_id: Task ID or a Key
        """
        req_ = dict(task_id=task_id)
        self._request('abort_task', req_)
        return None

class AutovizClient:
    """
    Class wrapper for autoviz Python client functionality
    Provides set of methods for obtaining autoviz supported plots in Vega format.
    """

    def __init__(self, _h2oai_client_1_10_1_2):
        self.client = _h2oai_client_1_10_1_2

    def get_histogram(
        self,
        dataset_key: str,
        variable_name: str,
        number_of_bars: int = 0,
        transformation: str = "none",
        mark: str = "bar",
    ) -> dict:
        """
        ---------------------------
        Required Keyword arguments:
        ---------------------------
        dataset_key -- str, Key of visualized dataset in DriverlessAI
        variable_name -- str, name of variable

        ---------------------------
        Optional Keyword arguments:
        ---------------------------
        number_of_bars -- int, number of bars
        transformation -- str, default value is "none"
            (otherwise, "log" or "square_root")
        mark -- str, default value is "bar" (use "area" to get a density polygon)
        """
        kwargs = dict(
            variable_name=variable_name,
            number_of_bars=number_of_bars,
            transformation=transformation,
            mark=mark,
        )
        key = self.client.get_1d_vega_plot(
            dataset_key, "histogram", variable_name, kwargs
        )
        return self._wait_for_job(key)

    def get_scatterplot(
        self,
        dataset_key: str,
        x_variable_name: str,
        y_variable_name: str,
        mark: str = "point",
    ) -> dict:
        """
        ---------------------------
        Required Keyword arguments:
        ---------------------------
        dataset_key -- str, Key of visualized dataset in DriverlessAI
        x_variable_name -- str, name of x variable
            (y variable assumed to be counts if no y variable specified)
        y_variable_name -- str, name of y variable

        ---------------------------
        Optional Keyword arguments:
        ---------------------------
        mark -- str, default value is "point" (alternative is "square")
        """
        kwargs = dict(
            x_variable_name=x_variable_name,
            y_variable_name=y_variable_name,
            mark=mark,
        )
        key = self.client.get_2d_vega_plot(
            dataset_key, "scatterplot", x_variable_name, y_variable_name, kwargs
        )
        return self._wait_for_job(key)

    def get_bar_chart(
        self,
        dataset_key: str,
        x_variable_name: str,
        y_variable_name: str = "",
        transpose: bool = False,
        sort: bool = False,
        mark: str = "bar",
    ) -> dict:
        """
        ---------------------------
        Required Keyword arguments:
        ---------------------------
        dataset_key -- str, Key of visualized dataset in DriverlessAI
        x_variable_name -- str, name of x variable
            (y variable assumed to be counts if no y variable specified)

        ---------------------------
        Optional Keyword arguments:
        ---------------------------
        y_variable_name -- str, name of y variable
        transpose -- Boolean, default value is false
        sort -- Boolean, default value is false
        mark -- str, default value is "bar" (use "point" to get a Cleveland dot plot)
        """
        kwargs = dict(
            x_variable_name=x_variable_name,
            y_variable_name=y_variable_name,
            transpose=transpose,
            mark=mark,
        )
        if y_variable_name:
            key = self.client.get_2d_vega_plot(
                dataset_key,
                "bar_chart",
                x_variable_name,
                y_variable_name,
                kwargs,
            )
        else:
            key = self.client.get_1d_vega_plot(
                dataset_key, "bar_chart", x_variable_name, kwargs
            )
        return self._wait_for_job(key)

    def get_parallel_coordinates_plot(
        self,
        dataset_key: str,
        variable_names: list = [],
        permute: bool = False,
        transpose: bool = False,
        cluster: bool = False,
    ) -> dict:
        """
        ---------------------------
        Required Keyword arguments:
        ---------------------------
        dataset_key -- str, Key of visualized dataset in DriverlessAI

        ---------------------------
        Optional Keyword arguments:
        ---------------------------
        variable_names -- str, name of variables
            (if no variables specified, all in dataset will be used)
        permute -- Boolean, default value is false
            (if true, use SVD to permute variables)
        transpose -- Boolean, default value is false
        cluster -- Boolean, k-means cluster variables and color plot by cluster IDs,
            default value is false
        """
        kwargs = dict(
            variable_names=variable_names,
            permute=permute,
            transpose=transpose,
            cluster=cluster,
        )
        key = self.client.get_vega_plot(
            dataset_key, "parallel_coordinates_plot", variable_names, kwargs
        )
        return self._wait_for_job(key)

    def get_heatmap(
        self,
        dataset_key: str,
        variable_names: list = [],
        permute: bool = False,
        transpose: bool = False,
        matrix_type: str = "rectangular",
    ) -> dict:
        """
        ---------------------------
        Required Keyword arguments:
        ---------------------------
        dataset_key -- str, Key of visualized dataset in DriverlessAI

        ---------------------------
        Optional Keyword arguments:
        ---------------------------
        variable_names -- str, name of variables
            (if no variables specified, all in dataset will be used)
        permute -- Boolean, default value is false
            (if true, use SVD to permute rows and columns)
        transpose -- Boolean, default value is false
        matrix_type -- str, default value is "rectangular" (alternative is "symmetric")
        """
        kwargs = dict(
            variable_names=variable_names,
            permute=permute,
            transpose=transpose,
            matrix_type=matrix_type,
        )
        key = self.client.get_vega_plot(
            dataset_key, "heatmap", variable_names, kwargs
        )
        return self._wait_for_job(key)

    def get_principal_components_plot(
        self, dataset_key: str, variable_names: list = [], cluster: bool = False
    ) -> dict:
        """
        ---------------------------
        Required Keyword arguments:
        ---------------------------
        dataset_key -- str, Key of visualized dataset in DriverlessAI

        ---------------------------
        Optional Keyword arguments:
        ---------------------------
        variable_names -- str, name of variables
            (if no variables specified, all in dataset will be used)
        cluster -- Boolean, k-means cluster variables and color plot by cluster IDs,
            default value is false
        """
        pass

    def get_boxplot(
        self,
        dataset_key: str,
        variable_name: str,
        group_variable_name: str = "",
        transpose: bool = False,
    ) -> dict:
        """
        ---------------------------
        Required Keyword arguments:
        ---------------------------
        dataset_key -- str, Key of visualized dataset in DriverlessAI
        variable_name -- str, name of variable for box

        ---------------------------
        Optional Keyword arguments:
        ---------------------------
        group_variable_name -- str, name of grouping variable
        transpose -- Boolean, default value is false
        """
        kwargs = dict(
            variable_name=variable_name,
            group_variable_name=group_variable_name,
            transpose=transpose,
        )
        if group_variable_name:
            key = self.client.get_2d_vega_plot(
                dataset_key,
                "grouped_boxplot",
                variable_name,
                group_variable_name,
                kwargs,
            )
        else:
            key = self.client.get_1d_vega_plot(
                dataset_key, "boxplot", variable_name, kwargs
            )
        return self._wait_for_job(key)

    def get_linear_regression(
        self,
        dataset_key: str,
        x_variable_name: str,
        y_variable_name: str,
        mark: str = "point",
    ) -> dict:
        """
        ---------------------------
        Required Keyword arguments:
        ---------------------------
        dataset_key -- str, Key of visualized dataset in DriverlessAI
        x_variable_name -- str, name of x variable
            (y variable assumed to be counts if no y variable specified)
        y_variable_name -- str, name of y variable

        ---------------------------
        Optional Keyword arguments:
        ---------------------------
        mark -- str, default value is "point" (alternative is "square")
        """
        kwargs = dict(
            x_variable_name=x_variable_name,
            y_variable_name=y_variable_name,
            mark=mark,
        )
        key = self.client.get_2d_vega_plot(
            dataset_key, "linear_regression", x_variable_name, y_variable_name, kwargs
        )
        return self._wait_for_job(key)

    def get_loess_regression(
        self,
        dataset_key: str,
        x_variable_name: str,
        y_variable_name: str,
        mark: str = "point",
        bandwidth: float = 0.5,
    ) -> dict:
        """
        ---------------------------
        Required Keyword arguments:
        ---------------------------
        dataset_key -- str, Key of visualized dataset in DriverlessAI
        x_variable_name -- str, name of x variable
            (y variable assumed to be counts if no y variable specified)
        y_variable_name -- str, name of y variable

        ---------------------------
        Optional Keyword arguments:
        ---------------------------
        mark -- str, default value is "point" (alternative is "square")
        bandwidth -- float, number in the (0,1)
            interval denoting proportion of cases in smoothing window (default is 0.5)
        """
        kwargs = dict(
            x_variable_name=x_variable_name,
            y_variable_name=y_variable_name,
            mark=mark,
            bandwidth=bandwidth,
        )
        key = self.client.get_2d_vega_plot(
            dataset_key, "loess_regression", x_variable_name, y_variable_name, kwargs
        )
        return self._wait_for_job(key)

    def get_dotplot(
        self, dataset_key: str, variable_name: str, mark: str = "point"
    ) -> dict:
        """
        ---------------------------
        Required Keyword arguments:
        ---------------------------
        dataset_key -- str, Key of visualized dataset in DriverlessAI
        variable_name -- str, name of variable on which dots are calculated

        ---------------------------
        Optional Keyword arguments:
        ---------------------------
        mark -- str, default value is "point" (alternative is "square" or "bar")
        """
        kwargs = dict(
            variable_name=variable_name,
            mark=mark,
        )
        key = self.client.get_1d_vega_plot(
            dataset_key, "dotplot", variable_name, kwargs
        )
        return self._wait_for_job(key)

    def get_distribution_plot(
        self,
        dataset_key: str,
        x_variable_name: str,
        y_variable_name: str = "",
        subtype: str = "probability_plot",
        distribution: str = "normal",
        mark: str = "point",
        transpose: bool = False,
    ) -> dict:
        """
        ---------------------------
        Required Keyword arguments:
        ---------------------------
        dataset_key -- str, Key of visualized dataset in DriverlessAI
        x_variable_name -- str, name of x variable

        ---------------------------
        Optional Keyword arguments:
        ---------------------------
        y_variable_name -- str, name of y variable for quantile plot
        subtype -- str "probability_plot" or "quantile_plot"
            (default is "probability_plot" done on x variable)
        distribution -- str, type of distribution, "normal" or "uniform"
            ("normal" is default)
        mark -- str, default value is "point" (alternative is "square")
        transpose -- Boolean, default value is false
        """
        kwargs = dict(
            x_variable_name=x_variable_name,
            y_variable_name=y_variable_name,
            subtype=subtype,
            distribution=distribution,
            mark=mark,
            transpose=transpose,
        )
        if y_variable_name:
            key = self.client.get_2d_vega_plot(
                dataset_key,
                "distribution_plot",
                x_variable_name,
                y_variable_name,
                kwargs,
            )
        else:
            key = self.client.get_1d_vega_plot(
                dataset_key, "distribution_plot", x_variable_name, kwargs
            )

        return self._wait_for_job(key)

    def _wait_for_job(self, key: str) -> dict:
        """Long polling to wait for async job to finish"""
        while True:
            time.sleep(1)
            job = self.client.get_vega_plot_job(key)
            if job.status >= 0:  # done
                if job.status > 0:  # canceled or failed
                    raise RuntimeError(
                        self.client._format_server_error(job.error)
                    )
                return job.entity
