# pylint: disable=useless-parent-delegation,bad-classmethod-argument
# ───────────────────────────────────────────────────── imports ────────────────────────────────────────────────────── #
from typing import Any, Dict, Optional, TypeVar

from pydantic import BaseModel, ConfigDict
from pydantic.fields import FieldInfo

from core_common_data_types.base_data_types_dtos import ExcludeUnsetBaseModel, UpdateBaseModel
from core_common_data_types.utils_data_types_tos import to_lower_camel

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #
#                           specifies all modules that shall be loaded and imported into the                           #
#                                current namespace when we use 'from package import *'                                 #
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #

__all__ = [
    "CamelCaseBaseModel",
    "CamelCaseBaseModelWithExtra",
    "CamelCaseExcludeUnsetBaseModel",
    "CamelCaseUpdateBaseModel",
    "CamelCaseBaseModelT",
    "CamelCaseBaseModelWithExtraT",
    "CamelCaseExcludeUnsetBaseModelT",
    "CamelCaseUpdateBaseModelT",
]


class CamelCaseBaseModel(BaseModel):
    """Base Model with enabled alias.

    Whether an aliased field may be populated by its name as given by the model attribute, as well as the alias.

    """

    model_config = ConfigDict(alias_generator=to_lower_camel, populate_by_name=True, extra="ignore")

    def dict(self, *args, by_alias: bool = True, **kwargs) -> Dict:
        """
        Generate a dictionary representation of the model, whose keys follow the JSON convention, optionally specifying
        which fields to include or exclude.
        """
        return super().model_dump(**kwargs, by_alias=by_alias)

    def dict_py(self, *args, **kwargs):
        """Gets the dictionary whose keys follow the Python convention.

        It is the same behavior as the dict() method but with a more descriptive name.     {         "snake_case_key":
        value     }

        """
        if kwargs and "by_alias" in kwargs:
            kwargs.pop("by_alias", None)
        return super().model_dump(by_alias=False, *args, **kwargs)

    def dict_json(self, *args, **kwargs):
        """Gets the dictionary whose keys follow the JSON convention by ensuring that 'aliases' are used as keys:
        {
            "camelCaseKey": value
        }
        """
        if kwargs and "by_alias" in kwargs:
            kwargs.pop("by_alias", None)
        return super().model_dump(by_alias=True, *args, **kwargs)

    def update(self, data: Dict[str, object]) -> None:
        # Data update
        for key, field in self.model_fields.items():
            if field.title in data or field.alias in data:
                if field.title is not None:
                    name = field.title
                else:
                    raise Exception("Field without a title, shouldn't happen")
                alias_value: Optional[Any] = None
                if field.alias is not None:
                    alias_value = data.get(field.alias)
                setattr(self, name, data.get(name, alias_value))
        # Data Validation
        self.__class__(**self.dict())

    @classmethod
    def get_field(cls, field_name: str, values: Dict) -> Any:
        """Retrieve the value of the field from the given dictionary searching by the field name and its alias.

        If exist a value for the field name and the alias, it will return the field name value

        """
        field: FieldInfo = cls.model_fields[field_name]
        return values.get(field.title, values.get(field.alias))


class CamelCaseBaseModelWithExtra(CamelCaseBaseModel, extra="allow"):
    """Base Model with enabled alias for extra fields.

    Whether an aliased field may be populated by its name as given by the model attribute, as well as the alias.

    """

    model_config = ConfigDict(extra="allow")

    def model_dump(self, *args, by_alias: bool = True, **kwargs) -> Dict:
        data = super().model_dump(by_alias=by_alias, **kwargs)
        # Take into consideration the extra fields for the camel_case serialization since them are not considered by
        # model_dump implementation (they're not fields, and hence can't store alias information).
        if self.model_extra is not None:
            if not by_alias:
                data.update(self.model_extra)
            else:
                for k, v in self.model_extra.items():
                    data.pop(k)
                    data.update({to_lower_camel(k): v})
        return data

    def dict(self, *args, by_alias: bool = True, **kwargs) -> Dict:
        return self.model_dump(by_alias=by_alias, **kwargs)


class CamelCaseExcludeUnsetBaseModel(CamelCaseBaseModel, ExcludeUnsetBaseModel):
    """
    Base model for TOs to return only the data that has been set.
    """


class CamelCaseUpdateBaseModel(CamelCaseBaseModel, UpdateBaseModel):  # type:ignore[misc]
    """Base model for updating TOs data.

    By making information update data models extend from this data model, it makes it easier to distinguish the
    fields that the user has actually modified (`exclude_unset`=True) from those that the user has not indicated.

    """


# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #
#                                                    Generic Types                                                     #
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #

CamelCaseBaseModelT = TypeVar("CamelCaseBaseModelT", bound=CamelCaseBaseModel)
CamelCaseBaseModelWithExtraT = TypeVar("CamelCaseBaseModelWithExtraT", bound=CamelCaseBaseModelWithExtra)
CamelCaseExcludeUnsetBaseModelT = TypeVar("CamelCaseExcludeUnsetBaseModelT", bound=CamelCaseExcludeUnsetBaseModel)
CamelCaseUpdateBaseModelT = TypeVar("CamelCaseUpdateBaseModelT", bound=CamelCaseUpdateBaseModel)
