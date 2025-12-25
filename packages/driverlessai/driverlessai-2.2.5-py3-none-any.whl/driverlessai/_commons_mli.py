import dataclasses
import functools
import inspect
from typing import Any
from typing import Callable
from typing import Dict
from typing import List
from typing import Optional
from typing import Union

from driverlessai import _core
from driverlessai import _enums
from driverlessai import _exceptions


class ConfigItem:
    _TYPE_MAP: Dict[str, type] = {
        "int": int,
        "float": float,
        "bool": bool,
        "list": list,
        "str": str,
        "dict": dict,
    }

    _DESCRIPTIVE_TYPE_MAP: Dict[str, str] = {
        "bool": "boolean",
        "str": "string",
        "int": "integer",
        "float": "floating-point",
        "list": "list",
        "dict": "dictionary",
    }

    def __init__(
        self,
        raw_name: str,
        comment: str,
        description: str,
        category: str,
        type_name: Optional[str],
        alias: Optional[str] = None,
        default: Optional[Union[int, float, str, bool, list, dict]] = None,
        min_val: Optional[Union[int, float]] = None,
        max_val: Optional[Union[int, float]] = None,
        valid_options: Optional[Union[List[int], List[float], List[str]]] = None,
    ):
        self.raw_name = raw_name
        self.comment = comment
        self.description = description
        self.category = category
        self.type_name = type_name
        self.alias = alias
        self.default = default
        self.min_val = min_val
        self.max_val = max_val
        self.valid_options = valid_options

        self._formatted_description: Optional[str] = None
        self._descriptive_type: Optional[str] = None
        self._formatted_valid_values: Optional[str] = None

    @property
    def descriptive_type(self) -> str:
        """A descriptive type name."""
        if self._descriptive_type is not None:
            return self._descriptive_type

        self._descriptive_type = self._DESCRIPTIVE_TYPE_MAP.get(
            self.type_name, self.type_name or ""
        )
        return self._descriptive_type

    @property
    def formatted_description(self) -> str:
        """Combined description and comment."""
        if self._formatted_description is not None:
            return self._formatted_description

        description = self.description.strip()
        comment = " ".join([s.strip() for s in self.comment.split("\n")]).strip()
        self._formatted_description = f"{description} {comment}"
        return self._formatted_description

    @property
    def formatted_valid_values(self) -> str:
        """Description of the valid values."""
        if self._formatted_valid_values is not None:
            return self._formatted_valid_values

        descriptive_type = self.descriptive_type
        self._formatted_valid_values = ""
        if descriptive_type:
            article = "An" if descriptive_type[0] in "aeiou" else "A"
            self._formatted_valid_values = f"{article} {descriptive_type} "

        if self.valid_options:
            self._formatted_valid_values = self._list_to_phrase(self.valid_options)
        elif self.type_name in ["int", "float"] and self.min_val != self.max_val:
            # Note: In explainer expert settings, self.max_val and self.min_val are
            # defaulted to 0.0 when not set
            if (
                self.min_val is not None
                and self.max_val is not None
                and self.min_val < self.max_val
            ):
                self._formatted_valid_values = (
                    f"{self._formatted_valid_values}value is within the range of "
                    f"{self._format_number(self.min_val)} to "
                    f"{self._format_number(self.max_val)}."
                ).capitalize()
            elif self.min_val is not None:
                self._formatted_valid_values = (
                    f"{self._formatted_valid_values}values greater than or equal to "
                    f"{self._format_number(self.min_val)}."
                ).capitalize()
            elif self.max_val is not None:
                self._formatted_valid_values = (
                    f"{self.formatted_valid_values}values "
                    f"less than or equal to {self._format_number(self.max_val)}."
                ).capitalize()

        return self._formatted_valid_values

    @property
    def name(self) -> str:
        """Alias if available or the raw name of this config item."""
        return self.alias or self.raw_name

    def _format_number(self, val: Union[int, float]) -> str:
        return f"{int(val) if self.type_name == 'int' else val}"

    @staticmethod
    def _list_to_phrase(items: Union[List[int], List[float], List[str]]) -> str:
        formatted_items: List[str]

        if items and isinstance(items[0], str):
            formatted_items = [f"'{i}'" for i in items]
        else:
            formatted_items = [f"{i}" for i in items]

        if len(formatted_items) == 1:
            return formatted_items[0]

        if len(formatted_items) > 1:
            formatted_items.insert(-1, "or")
            comma_separated = ", ".join(formatted_items)
            return comma_separated.replace(", or,", " or")

        return ""

    @staticmethod
    def create_from_dai_config_item(
        dai_config_item: Any, alias: Optional[str] = None
    ) -> "ConfigItem":
        """Create ConfigItem from Driverless AI ConfigItem object."""
        return ConfigItem(
            raw_name=dai_config_item.name,
            alias=alias,
            comment=dai_config_item.comment,
            description=dai_config_item.description,
            category=dai_config_item.category,
            default=dai_config_item.val,
            min_val=dai_config_item.min_,
            max_val=dai_config_item.max_,
            valid_options=dai_config_item.predefined,
            type_name=dai_config_item.type,
        )

    def matches_search_term(self, search_term: str) -> bool:
        """Checks if the search term matches either the raw_name, category, description
        or comment.

        Args:
            search_term: The search term to compare against.
        """
        return (
            search_term.lower()
            in " ".join(
                [self.raw_name, self.category, self.description, self.comment]
            ).lower()
        )

    def to_method_parameter(self) -> inspect.Parameter:
        """Returns a inspect.Parameter object representation of this instance."""
        return inspect.Parameter(
            name=self.name,
            kind=inspect.Parameter.KEYWORD_ONLY,
            default=self.default
            if self.default is not None
            else inspect.Parameter.empty,
            annotation=self._TYPE_MAP.get(self.type_name, self.type_name)
            if self.type_name
            else inspect.Parameter.empty,
        )

    def validate_value(self, val: Union[int, float, str, bool, list, dict]) -> None:
        """Validates a given value against the expected type and raises an expection
        if the value is deemed invalid.

        Args:
            val: The value to validate.
        """
        valid = True
        error_msg = ""

        expected_type = self._TYPE_MAP.get(self.type_name)
        alt_expected_type = int if expected_type is float else None
        value_type = type(val)

        def _descriptive_type_name(type_: type) -> str:
            return self._DESCRIPTIVE_TYPE_MAP.get(type_.__name__, f"'{type_.__name__}'")

        def _invalid_type_error_msg(alt_type: Optional[type] = None) -> str:
            desc_expected_type_name = _descriptive_type_name(expected_type)
            desc_alt_type_name = _descriptive_type_name(alt_type) if alt_type else ""
            desc_val_type_name = _descriptive_type_name(value_type)

            return (
                (
                    f"Invalid value type for '{self.name}'. "
                    f"Expected type {desc_expected_type_name}"
                )
                + (f" or {desc_alt_type_name}" if alt_type else "")
                + f", got {desc_val_type_name}"
            )

        if self.valid_options:
            valid = val in self.valid_options
            if not valid:
                error_msg = f"'{self.name}' must be of: {self.formatted_valid_values}"
        elif expected_type in [int, float, bool, list, dict, str] and not (
            (expected_type == value_type)
            or (alt_expected_type and alt_expected_type == value_type)
        ):
            valid = False
            error_msg = _invalid_type_error_msg(alt_expected_type)
        elif expected_type in [int, float] and self.min_val != self.max_val:

            # val is either int or float, the following assert is used to satisfy MyPy.
            assert isinstance(val, (int, float))

            if (
                self.min_val is not None
                and self.max_val is not None
                and self.min_val < self.max_val
            ):
                # Note: In explainer expert settings, self.max_val and self.min_val
                # are defaulted to 0.0 when not set
                valid = val >= self.min_val and val <= self.max_val
                error_msg = (
                    f"{self.name} must be within the range of "
                    f"{self._format_number(self.min_val)} to "
                    f"{self._format_number(self.max_val)}"
                )
            elif self.min_val is not None:
                valid = val >= self.min_val
                error_msg = (
                    f"{self.name} must be greater than or equal to "
                    f"{self._format_number(self.min_val)}"
                )
            elif self.max_val is not None:
                valid = val <= self.max_val
                error_msg = (
                    f"{self.name} must be less than or equal to "
                    f"{self._format_number(self.max_val)}"
                )
        if not valid:
            raise ValueError(error_msg)


def error_if_interpretation_exists(client: "_core.Client", name: str) -> None:
    existing_names = [i.name for i in client.mli.iid.list()]

    if name in existing_names:
        raise _exceptions.InterpretationExists(
            f"Interpretation with name '{name}' already exists on the server. "
            "Use `force=True` to create another interpretation with the same name."
        )


def get_updated_signature(
    func: Callable, new_params: List[inspect.Parameter], delete_kwargs: bool = False
) -> inspect.Signature:
    """Gets an updated inspect.Signature object by combining the parameters from the
    original function with the provided list of new parameter. The new parameters are
    added before the variable keyword argument (**kwargs) or replaced if present.

     Args:
         func: the function to retrieve the original parameters from
         new_params: a list of new parameter to add before the variable keyword argument
         delete_kwargs: if True deletes the variable keyword argument (kwargs)
    Returns:
         inspect.Signature: the updated signature object
    """
    func_param = list(inspect.signature(func).parameters.values())

    # Find the first variable keyword argument
    kwarg_index = next(
        (
            index
            for index, param in enumerate(func_param)
            if param.kind == param.VAR_KEYWORD
        ),
        None,
    )

    if kwarg_index is None:
        # No variable keyword argument found, append new parameters at the end
        func_param.extend(new_params)
    else:
        # Variable keyword argument found
        before_kwargs = func_param[0:kwarg_index]
        kwarg = func_param[kwarg_index : len(func_param)]

        # Insert new parameters before it or replace it
        func_param = before_kwargs + new_params + (kwarg if not delete_kwargs else [])

    return inspect.Signature(func_param)


def update_method_doc(
    obj: Any,
    method_to_update: str,
    updated_doc: Optional[str] = None,
    new_signature: Optional[inspect.Signature] = None,
    custom_doc_update_func: Optional[Callable[[str, str], str]] = None,
) -> None:
    """Updates a method's docstring and method signature dynamically

    Args:
        obj: The object where the method is located.
        method_to_update: The name of the method to update.
        updated_doc: The updated method docstring. If None or empty,
            the docstring is not updated.
        new_signature: The new method signature.
        custom_doc_update_func: A function to generate the updated docstring. This
            function should take two parameters (original docstring
            and updated docstring) and return the updated docstring.
            If not provided, the original docstring and updated
            docstring are concatenated with a newline character.

        ??? Example
        ```
        >>> class MyClass:
        ...     def __init__(self, method_doc):
        ...         _commons_mli.update_method_doc(
        ...             obj=self,
        ...             method_to_update="my_method",
        ...             updated_doc=method_doc,
        ...             new_signature=inspect.Signature(
        ...                 [
        ...                     inspect.Parameter(
        ...                         name="self",
        ...                         kind=inspect.Parameter.POSITIONAL_OR_KEYWORD),
        ...                     inspect.Parameter(
        ...                         name="name", kind=inspect.Parameter.KEYWORD_ONLY)
        ...                 ]
        ...             ),
        ...             custom_doc_update_func=lambda orig, updated: orig + updated
        ...         )
        ...
        ...     def my_method(self, **kwargs):
        ...         \"\"\"The original docstring.\"\"\"
        ...         print(kwargs)
        ...
        >>> obj = MyClass(" The updated docstring")
        >>> print(obj.my_method.__doc__)
        The original docstring. The updated docstring.
        >>> print(inspect.signature(obj.my_method))
        (self, *, name)
        ```
    """
    method: Callable = getattr(obj, method_to_update)

    @functools.wraps(method)
    def wrapper(_self: Any, *args: Any, **kwargs: Any) -> Any:
        return method(*args, **kwargs)

    if updated_doc:
        orig_doc = "\n".join([line.strip() for line in method.__doc__.splitlines()])
        wrapper.__doc__ = (
            custom_doc_update_func(orig_doc, updated_doc)
            if custom_doc_update_func
            else f"{orig_doc}\n\n{updated_doc}"
        )

    if new_signature is not None:
        setattr(wrapper, "__signature__", new_signature)
    setattr(obj, method_to_update, getattr(wrapper, "__get__")(obj, obj.__class__))


@dataclasses.dataclass
class _ExplainerInfo:
    key: str
    name: str
    id: str
    status: _enums.JobStatus

    @classmethod
    def get_all(
        cls, client: "_core.Client", mli_key: str
    ) -> Optional[List["_ExplainerInfo"]]:
        try:
            job_statuses = client._backend.get_explainer_job_statuses(
                mli_key=mli_key, explainer_job_keys=[]
            )
        except client._server_module.protocol.RemoteError:
            return None
        else:
            return [
                cls(
                    key=js.explainer_job_key,
                    name=js.explainer_job.entity.name,
                    id=js.explainer_job.entity.id,
                    status=_enums.JobStatus(js.explainer_job.status),
                )
                for js in job_statuses
            ]
