"""Recipe module of official Python client for Driverless AI."""

import inspect
import re
from collections import OrderedDict
from typing import Any, Optional
from typing import Dict
from typing import List
from typing import Sequence
from typing import Tuple
from typing import Union

from driverlessai import _commons
from driverlessai import _commons_mli
from driverlessai import _core
from driverlessai import _enums
from driverlessai import _exceptions
from driverlessai import _logging
from driverlessai import _utils


class Recipe(_commons.ServerObject):
    """A recipe in the Driverless AI server."""

    def __init__(self, client: "_core.Client", info: Any) -> None:
        super().__init__(client=client)
        self._code = None
        self._key = None
        self._is_active = True
        self._is_custom: Optional[bool] = None
        self._hashed_name = info.name
        # Only custom recipes have an unhashed name, otherwise use the hashed name.
        self._set_name(getattr(info, "unhashed_name", info.name))
        self._set_raw_info(info)

    def __repr__(self) -> str:
        return f"<class '{self.__class__.__name__}'> {self!s}"

    def __str__(self) -> str:
        return self.name

    def _set_is_active(self, value: bool) -> None:
        self._is_active = value

    def _set_is_custom(self, value: bool) -> None:
        self._is_custom = value

    def _update(self) -> None:
        if not self.is_custom:
            raise _exceptions.InvalidOperationException(
                "Not available for non-custom recipes."
            )
        if self._code is None:
            self._code = self._client._backend.get_persistent_custom_recipe(
                key=self.key
            ).code

    def activate(self) -> "Recipe":
        """
        Activates the custom recipe if it is inactive,
        and returns the newly activated custom recipe.

        Returns:
            Activated custom recipe.

        Raises:
            _exceptions.InvalidOperationException: If the recipe is a non-custom recipe.
            _exceptions.InvalidStateException: If the recipe is already active.
        """
        if self.is_active:
            raise _exceptions.InvalidStateException("This recipe is already active.")
        return self.update_code(self.code)

    @property
    @_utils.min_supported_dai_version("1.10.3")
    def code(self) -> str:
        """Python code of the custom recipe."""
        if not self.is_custom:
            raise _exceptions.InvalidOperationException(
                "Not applicable for non-custom recipes."
            )
        if not self._code:
            self._update()
        return self._code

    @_utils.min_supported_dai_version("1.10.3")
    def deactivate(self) -> None:
        """
        Deactivates the custom recipe if it is active.

        Raises:
            _exceptions.InvalidOperationException: If the recipe is a non-custom recipe.
            _exceptions.InvalidStateException: If the recipe is already inactive.
        """
        if not self.is_active:
            raise _exceptions.InvalidStateException("This recipe is already inactive.")
        if not self.is_custom:
            raise _exceptions.InvalidOperationException(
                "Non-custom recipes cannot be deactivated."
            )
        self._client._backend.deactivate_custom_recipes(keys=[self.key])
        self._set_is_active(False)

    @property
    def is_active(self) -> bool:
        """Whether the recipe is active or not."""
        return self._is_active

    @property
    def is_custom(self) -> bool:
        """Whether the recipe is a custom recipe or not."""
        if self._is_custom is None:
            raise _exceptions.InvalidOperationException(
                "Custom recipe detection is not available."
            )
        return self._is_custom

    @property
    @_utils.min_supported_dai_version("1.10.3")
    def key(self) -> str:
        """Unique key of the recipe."""
        if not self.is_custom:
            raise _exceptions.InvalidOperationException(
                "Non-custom recipes do not have a key."
            )
        if self._key is None:
            self._key = (
                self._client._backend.get_persistent_custom_recipe_by_display_name(
                    display_name=self._hashed_name
                ).key
            )
        return self._key

    def update_code(self, code: str) -> "Recipe":
        """
        Updates the code of the custom recipe.

        Returns:
            The newly created recipe with the updated code.

        Raises:
            _exceptions.InvalidOperationException: if the recipe is not a custom one.
        """
        if not self.is_custom:
            raise _exceptions.InvalidOperationException(
                "Not applicable for non-custom recipes."
            )

        key = self._client._backend.update_custom_recipe_code(
            key=self.key, code=code, in_file_update=False
        ).job_key
        new_recipe = RecipeJob(self._client, key).result()
        self._set_is_active(False)
        return new_recipe


class DataRecipe(Recipe):
    """A data recipe in the Driverless AI server."""

    def __init__(self, client: "_core.Client", info: Any) -> None:
        super().__init__(client=client, info=info)
        self._set_is_custom(info.is_custom)


class DataRecipes:
    """Interact with data recipes in the Driverless AI server."""

    def __init__(self, client: "_core.Client") -> None:
        self._client = client

    def list(self) -> Sequence["DataRecipe"]:
        """
        Retrieves data recipes in the Driverless AI server.

        Returns:
            Data recipes.

        ??? Example
            ```py
            # Get names of all data recipes.
            data_recipes = [r.name for r in client.recipes.data.list()]

            # Get custom data recipes.
            custom_data_recipes = [
                r for r in client.recipes.data.list() if r.is_custom
            ]
            ```
        """
        return _commons.ServerObjectList(
            data=[
                DataRecipe(self._client, t)
                for t in self._client._backend.list_datas(
                    config_overrides="",
                )
            ],
            get_method=None,
            item_class_name=DataRecipe.__name__,
        )


class ExplainerRecipe(Recipe):
    """An explainer recipe in the Driverless AI server."""

    def __init__(self, client: "_core.Client", info: Any) -> None:
        super().__init__(client=client, info=info)

        def _construct_config_item_tuple(
            dai_config_item: Any,
        ) -> Tuple[str, _commons_mli.ConfigItem]:
            ci = _commons_mli.ConfigItem.create_from_dai_config_item(
                dai_config_item=dai_config_item,
                alias=self._to_pythonic_name(dai_config_item.name),
            )
            return ci.name, ci

        self._config_items: Dict[str, _commons_mli.ConfigItem] = dict(
            _construct_config_item_tuple(p) for p in info.parameters
        )
        self._pythonic_name_map = {
            p.name: self._to_pythonic_name(p.name) for p in info.parameters
        }
        self._raw_name_map = {
            pythonic_name: name
            for name, pythonic_name in self._pythonic_name_map.items()
        }
        self._default_settings = {p.name: p.val for p in info.parameters}
        self._set_is_custom(not info.id.startswith("h2oai"))
        self._settings: Dict[str, Any] = {}

        _commons_mli.update_method_doc(
            obj=self,
            method_to_update="with_settings",
            new_signature=self._get_with_settings_signature(),
        )

    @property
    def for_binomial(self) -> bool:
        """`True` if explainer works for binomial models."""
        return "binomial" in self._get_raw_info().can_explain

    @property
    def for_iid(self) -> bool:
        """`True` if explainer works for I.I.D. models."""
        return "iid" in self._get_raw_info().model_types

    @property
    def for_multiclass(self) -> bool:
        """`True` if explainer works for multiclass models."""
        return "multiclass" in self._get_raw_info().can_explain

    @property
    def for_regression(self) -> bool:
        """`True` if explainer works for regression models."""
        return "regression" in self._get_raw_info().can_explain

    @property
    def for_timeseries(self) -> bool:
        """`True` if explainer works for time series models."""
        return "time_series" in self._get_raw_info().model_types

    @property
    def id(self) -> str:
        """The identifier of the explainer."""
        return self._get_raw_info().id

    @property
    def settings(self) -> Dict[str, Any]:
        """Settings of the explainer."""
        return self._settings

    def _get_with_settings_signature(self) -> inspect.Signature:
        params: List[inspect.Parameter] = []
        for ci in self._config_items.values():
            params.append(ci.to_method_parameter())
        return _commons_mli.get_updated_signature(
            func=ExplainerRecipe.with_settings, new_params=params, delete_kwargs=True
        )

    @staticmethod
    def _to_pythonic_name(name: str) -> str:
        return name.replace(" ", "_").replace("-", "_")

    def search_settings(
        self,
        search_term: str = "",
        show_description: bool = False,
        show_dai_name: bool = False,
        show_valid_values: bool = False,
    ) -> _utils.Table:
        """
        Searches for explainer settings.

        Args:
            search_term: Case insensitive term to search for.
            show_description: Whether to include description of the setting in results.
            show_dai_name: Whether to include setting name used by
                the Driverless AI server.
            show_valid_values: Whether to include the valid values that can be set for
                each setting.

        Returns:
            Matching explainer settings in a table.

        ??? Example
            ```py
            results = explainer_recipe.search_settings(search_term)
            print(results)
            ```
        """
        headers = ["Name", "Default Value"]
        if show_dai_name:
            headers.insert(1, "Raw Name")
        if show_valid_values:
            headers.append("Valid Values")
        if show_description:
            headers.append("Description")
        data = []
        for _, ci in self._config_items.items():
            if ci.matches_search_term(search_term):
                row = [ci.name, ci.default]
                if show_dai_name:
                    row.insert(1, ci.raw_name)
                if show_valid_values:
                    row.append(ci.formatted_valid_values)
                if show_description:
                    row.append(ci.formatted_description)
                data.append(row)
        return _utils.Table(headers=headers, data=data)

    def show_settings(self, show_dai_name: bool = False) -> _utils.Table:
        """
        Displays the settings of the explainer with their corresponding values.

        Args:
            show_dai_name: Whether to include setting name used by
                the Driverless AI server.

        Returns:
            Settings of the explainer in a table.

        ??? Example
            ```py
            settings = explainer_recipe.show_settings()
            print(settings)
            ```
        """
        headers = ["Name", "Value"]
        if show_dai_name:
            headers.insert(1, "Raw Name")
        data = []
        for key, value in self._settings.items():
            row = [self._pythonic_name_map.get(key), value]
            if show_dai_name:
                row.insert(1, key)
            data.append(row)
        return _utils.Table(headers=headers, data=data)

    def with_settings(
        self, validate_value: bool = True, **kwargs: Any
    ) -> "ExplainerRecipe":
        """
        Updates the current settings of the explainer recipe.

        Args:
            validate_value: Whether to validate new setting values or not.
            kwargs: New explainer settings.
                Use [driverlessai._recipes.ExplainerRecipe.search_settings][]
                to search for possible settings.

        Returns:
            The updated explainer recipe.
        """
        self._settings = {}

        for k, v in kwargs.items():
            if k in self._config_items:
                if validate_value:
                    ci = self._config_items[k]
                    ci.validate_value(v)
                self._settings[k] = v
            else:
                raise ValueError(f"Setting '{k}' not recognized.")
        return self


class ExplainerRecipes:
    """Interact with explainer recipes in the Driverless AI server."""

    # in DAI it's h2oaicore.mli.oss.commons.ExplainerFilter.TIME_SERIES
    _FILTER_TS = "time_series"

    def __init__(self, client: "_core.Client") -> None:
        self._client = client

    def list(self) -> Sequence["ExplainerRecipe"]:
        """
        Retrieves explainer recipes in the Driverless AI server.

        ??? Example
            ```py
            # Get all binomial explainer recipes.
            binomial_explainers = [
                r for r in client.recipes.explainers.list() if r.for_binomial
            ]

            # Get all multiclass explainer recipes.
            multiclass_explainers = [
                r for r in client.recipes.explainers.list() if r.for_multiclass
            ]

            # Get all regression explainer recipes.
            regression_explainers = [
                r for r in client.recipes.explainers.list() if r.for_regression
            ]

            # Get all IID explainer recipes.
            iid_explainers = [
                r for r in client.recipes.explainers.list() if r.for_iid
            ]

            # Get all time series explainer recipes.
            time_series_explainers = [
                r for r in client.recipes.explainers.list() if r.for_timeseries
            ]

            # Get all custom explainer recipes.
            custom_explainers = [
                r for r in client.recipes.explainers.list() if r.is_custom
            ]
            ```
        """
        return _commons.ServerObjectList(
            data=self._get_all_recipes(),
            get_method=None,
            item_class_name=ExplainerRecipe.__name__,
        )

    def _get_all_recipes(self) -> List[ExplainerRecipe]:
        iid = self._client._backend.list_explainers(
            experiment_types=[],
            explanation_scopes=[],
            dai_model_key="",
            keywords=[],
            explainer_filter=[],
        )

        iid_ids = [e.id for e in iid]
        # Get all explainers that support time series model
        ts = [
            e
            for e in self._client._backend.list_explainers(
                experiment_types=[],
                explanation_scopes=[],
                dai_model_key="",
                keywords=[],
                explainer_filter=[
                    self._client._server_module.messages.FilterEntry(
                        filter_by=ExplainerRecipes._FILTER_TS, value=True
                    )
                ],
            )
            if e.id not in iid_ids
        ]
        # Add any time series related explainer to end of the list
        explainers = iid + ts
        return [ExplainerRecipe(self._client, e) for e in explainers]


class IndividualRecipe(Recipe):
    """An individual recipe in the Driverless AI server."""

    def __init__(self, client: "_core.Client", info: Any) -> None:
        super().__init__(client=client, info=info)
        self._set_is_custom(info.is_custom)

    @property
    def experiment_id(self) -> str:
        """Recipe experiment ID."""
        return self._get_raw_info().experiment_id

    @property
    def experiment_description(self) -> str:
        """Recipe experiment description."""
        return self._get_raw_info().experiment_description

    @property
    def for_regression(self) -> bool:
        """`True` if the recipe is for regression."""
        return self._get_raw_info().for_regression

    @property
    def for_binary(self) -> bool:
        """`True` if the recipe is for binary."""
        return self._get_raw_info().for_binary

    @property
    def for_multiclass(self) -> bool:
        """`True` if the recipe is for multiclass."""
        return self._get_raw_info().for_multiclass


class IndividualRecipes:
    """Interact with individual recipes in the Driverless AI server."""

    def __init__(self, client: "_core.Client") -> None:
        self._client = client

    def list(self) -> Sequence["IndividualRecipe"]:
        """
        Retrieves individual recipes in the Driverless AI server.

        Returns:
            Individual recipes.

        ??? Example
            ```py
            # Get all binary individual recipes.
            binomial_individuals = [
                r for r in client.recipes.individuals.list() if r.for_binary
            ]

            # Get all multiclass individual recipes.
            multiclass_individuals = [
                r for r in client.recipes.individuals.list() if r.for_multiclass
            ]

            # Get all regression individual recipes.
            regression_individuals = [
                r for r in client.recipes.individuals.list() if r.for_regression
            ]

            # Get all custom individual recipes.
            custom_individuals = [
                r for r in client.recipes.individuals.list() if r.is_custom
            ]
            ```
        """
        return _commons.ServerObjectList(
            data=[
                IndividualRecipe(self._client, t)
                for t in self._client._backend.list_individuals(
                    config_overrides="",
                )
            ],
            get_method=None,
            item_class_name=IndividualRecipe.__name__,
        )


class ModelRecipe(Recipe):
    """A model recipe in the Driverless AI server."""

    def __init__(self, client: "_core.Client", info: Any) -> None:
        super().__init__(client=client, info=info)
        self._set_is_custom(info.is_custom)
        self._is_unsupervised = getattr(info, "is_unsupervised", False)

    @property
    def is_unsupervised(self) -> bool:
        """`True` if recipe doesn't require a target column."""
        return self._is_unsupervised


class ModelRecipes:
    """Interact with model recipes in the Driverless AI server."""

    def __init__(self, client: "_core.Client") -> None:
        self._client = client

    def list(self) -> Sequence["ModelRecipe"]:
        """
        Retrieves model recipes in the Driverless AI server.

        Returns:
            Model recipes.

        ??? Example
            ```py
            # Get all model recipes.
            model_recipes = [
                r for r in client.recipes.models.list() if r.for_regression
            ]

            # Get all custom model recipes.
            custom_model_recipes = [
                r for r in client.recipes.models.list() if r.is_custom
            ]
            ```
        """
        return _commons.ServerObjectList(
            data=[
                ModelRecipe(self._client, m)
                for m in self._client._backend.list_model_estimators(
                    config_overrides=""
                )
            ],
            get_method=None,
            item_class_name=ModelRecipe.__name__,
        )


class RecipeJob(_commons.ServerJob):
    """Monitor the creation of a custom recipe in the Driverless AI server."""

    def __init__(self, client: "_core.Client", key: str) -> None:
        super().__init__(client=client, key=key)

    def _update(self) -> None:
        self._set_raw_info(self._client._backend.get_custom_recipe_job(key=self.key))

    def result(self, silent: bool = False) -> Union["Recipe", None]:
        """
        Awaits the job's completion before returning the created custom recipe.

        Args:
            silent: Whether to display status updates or not.

        Returns:
            Created custom recipe by the job.

        Raises:
            NotImplementedError: If the recipe type is not implemented.
        """
        self._wait(silent)
        entity = self._get_raw_info().entity
        recipe_mapping = OrderedDict(
            {
                "datas": DataRecipe,
                "explainers": ExplainerRecipe,
                "individuals": IndividualRecipe,
                "models": ModelRecipe,
                "pretransformers": PreTransformerRecipe,
                "scorers": ScorerRecipe,
                "transformers": TransformerRecipe,
            }
        )
        for attr, recipe_class in recipe_mapping.items():
            info = getattr(entity, attr, None)
            if info:
                return recipe_class(self._client, info[0])

        raise NotImplementedError("Not implemented for the given recipe type")

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
        if verbose == 1:
            return f"{status.message} {self._get_raw_info().progress:.2%}"
        if verbose == 2:
            if status == _enums.JobStatus.FAILED:
                message = " - " + self._get_raw_info().error
            else:
                message = ""  # message for recipes is partially nonsense atm
            return f"{status.message} {self._get_raw_info().progress:.2%}{message}"
        return status.message


class Recipes:
    """
    Interact with
    [recipes](https://docs.h2o.ai/driverless-ai/1-10-lts/docs/userguide/custom_recipes.html)
    in the Driverless AI server.
    """

    def __init__(self, client: "_core.Client") -> None:
        self._client = client
        self._data = DataRecipes(client)
        self._explainers = ExplainerRecipes(client)
        self._individuals = IndividualRecipes(client)
        self._models = ModelRecipes(client)
        self._scorers = ScorerRecipes(client)
        self._transformers = TransformerRecipes(client)
        self._pre_transformers = PreTransformerRecipes(client)

    @property
    def data(self) -> "DataRecipes":
        """Interact with data recipes in the Driverless AI server."""
        return self._data

    @property
    def explainers(self) -> "ExplainerRecipes":
        """Interact with explainer recipes in the Driverless AI server."""
        return self._explainers

    @property
    @_utils.min_supported_dai_version("1.10.2")
    def individuals(self) -> "IndividualRecipes":
        """Interact with individual recipes in the Driverless AI server."""
        return self._individuals

    @property
    def models(self) -> "ModelRecipes":
        """Interact with model recipes in the Driverless AI server."""
        return self._models

    @property
    def scorers(self) -> "ScorerRecipes":
        """Interact with scorer recipes in the Driverless AI server."""
        return self._scorers

    @property
    def transformers(self) -> "TransformerRecipes":
        """Interact with transformer recipes in the Driverless AI server."""
        return self._transformers

    @property
    def pre_transformers(self) -> "PreTransformerRecipes":
        """Interact with pre-transformer recipes in the Driverless AI server."""
        return self._pre_transformers

    def create(
        self,
        recipe: str,
        username: str = None,
        password: str = None,
    ) -> "Recipe":
        """
        Creates a custom recipe in the Driverless AI server.

        Args:
            recipe: The path or URL to the recipe.
            username: Username to use when connecting to BitBucket.
            password: Password to use when connecting to BitBucket.

        Returns:
            Created custom recipe.

        ??? Example
            ```py
            recipe = client.recipes.create(
                recipe="https://github.com/h2oai/driverlessai-recipes/blob/master/scorers/regression/explained_variance.py"
            )
            ```
        """
        return self.create_async(
            recipe=recipe, username=username, password=password
        ).result()

    def create_async(
        self,
        recipe: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ) -> RecipeJob:
        """
        Launches the creation of a custom recipe in the Driverless AI server.

        Args:
            recipe: The path or URL to the recipe.
            username: Username to use when connecting to BitBucket.
            password: Password to use when connecting to BitBucket.

        Returns:
            The custom recipe job.

        ??? Example
            ```py
            recipe_job = client.recipes.create_async(
                recipe="https://github.com/h2oai/driverlessai-recipes/blob/master/scorers/regression/explained_variance.py"
            )
            ```
        """
        if re.match("^http[s]?://", recipe):
            if username is not None and password is not None:
                _utils.check_server_support(
                    client=self._client,
                    minimum_server_version="1.10.2",
                    parameter="create_custom_recipe_from_bitbucket",
                )
                _logging.logger.info("Calling bitbucket recipe upload function")
                key = self._client._backend.create_custom_recipe_from_bitbucket(
                    resource_link=recipe, username=username, password=password
                )
            else:
                key = self._client._backend.create_custom_recipe_from_url(url=recipe)
        else:
            key = self._client._backend._perform_recipe_upload(file_path=recipe)
        return RecipeJob(self._client, key)


class ScorerRecipe(Recipe):
    """A scorer recipe in the Driverless AI server."""

    def __init__(self, client: "_core.Client", info: Any) -> None:
        super().__init__(client=client, info=info)
        self._set_is_custom(info.is_custom)

    @property
    def description(self) -> str:
        """Description of the recipe."""
        return self._get_raw_info().description

    @property
    def for_binomial(self) -> bool:
        """`True` if scorer works for binomial models."""
        return self._get_raw_info().for_binomial

    @property
    def for_multiclass(self) -> bool:
        """`True` if scorer works for multiclass models."""
        return self._get_raw_info().for_multiclass

    @property
    def for_regression(self) -> bool:
        """`True` if scorer works for regression models."""
        return self._get_raw_info().for_regression


class ScorerRecipes:
    """Interact with scorer recipes in the Driverless AI server."""

    def __init__(self, client: "_core.Client") -> None:
        self._client = client

    def list(self) -> Sequence["ScorerRecipe"]:
        """
        Retrieves scorer recipes in the Driverless AI server.

        Returns:
            Scorer recipes.

        ??? Example
            ```py
            # Get all binomial scorer recipes.
            binomial_scorers = [
                r for r in client.recipes.scorers.list() if r.for_binomial
            ]

            # Get all multiclass scorer recipes.
            multiclass_scorers = [
                r for r in client.recipes.scorers.list() if r.for_multiclass
            ]

            # Get all regression scorer recipes.
            regression_scorers = [
                r for r in client.recipes.scorers.list() if r.for_regression
            ]

            # Get all custom scorer recipes.
            custom_scorers = [r for r in client.recipes.scorers.list() if r.is_custom]
            ```
        """
        return _commons.ServerObjectList(
            data=[
                ScorerRecipe(self._client, s)
                for s in self._client._backend.list_scorers(config_overrides="")
            ],
            get_method=None,
            item_class_name=ScorerRecipe.__name__,
        )


class TransformerRecipe(Recipe):
    """A transformer recipe in the Driverless AI server."""

    def __init__(self, client: "_core.Client", info: Any) -> None:
        super().__init__(client=client, info=info)
        self._set_is_custom(info.is_custom)


class TransformerRecipes:
    """Interact with transformer recipes in the Driverless AI server."""

    def __init__(self, client: "_core.Client") -> None:
        self._client = client

    def list(self) -> Sequence["TransformerRecipe"]:
        """
        Retrieves transformer recipes in the Driverless AI server.

        Returns:
            Transformer recipes.

        ??? Example
            ```py
            # Get names of all transformers.
            transformers = [r.name for r in client.recipes.transformers.list()]

            # Get custom transformers.
            custom_transformers = [
                r for r in client.recipes.transformers.list() if r.is_custom
            ]
        ```
        """
        return _commons.ServerObjectList(
            data=[
                TransformerRecipe(self._client, t)
                for t in self._client._backend.list_transformers(
                    config_overrides="",
                )
            ],
            get_method=None,
            item_class_name=TransformerRecipe.__name__,
        )


class PreTransformerRecipe(Recipe):
    """A pre-transformer recipe in the Driverless AI server."""

    def __init__(self, client: "_core.Client", info: Any) -> None:
        super().__init__(client=client, info=info)
        self._set_is_custom(info.is_custom)


class PreTransformerRecipes:
    """Interact with pre-transformer recipes in the Driverless AI server."""

    def __init__(self, client: "_core.Client") -> None:
        self._client = client

    def list(self) -> Sequence["PreTransformerRecipe"]:
        """
        Retrieves pre-transformer recipes in the Driverless AI server.

        Returns:
            Pre-transformer recipes.

        ??? Example
            ```py
            # Get names of all pre-transformers.
            pre_transformers = [r.name for r in client.recipes.pre_transformers.list()]

            # Get custom pre-transformers.
            custom_pre_transformers = [
                r for r in client.recipes.pre_transformers.list() if r.is_custom
            ]
        ```
        """
        return _commons.ServerObjectList(
            data=[
                PreTransformerRecipe(self._client, t)
                for t in self._client._backend.list_pretransformers(
                    config_overrides="",
                )
            ],
            get_method=None,
            item_class_name=PreTransformerRecipe.__name__,
        )
