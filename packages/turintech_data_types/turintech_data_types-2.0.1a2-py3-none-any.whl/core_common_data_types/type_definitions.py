# ───────────────────────────────────────────────────── imports ────────────────────────────────────────────────────── #
from enum import Enum
from pathlib import Path
from typing import Literal, Mapping, Sequence, TypeVar, Union

from pydantic import BaseModel
from pydantic_settings import BaseSettings
from typing_extensions import TypeAlias

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #
#                           specifies all modules that shall be loaded and imported into the                           #
#                                current namespace when we use 'from package import *'                                 #
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #

__all__ = [
    "PathType",
    "DataModelType",
    "JsonType",
    "DictType",
    "GenericT",
    "EnumT",
    "DataModelT",
    "JsonT",
    "DictT",
    "BaseModelT",
    "BaseSettingsT",
    "PositionType",
]

from core_common_data_types import PropertyBaseModel
from core_common_data_types.base_data_types import BaseModelWithAlias

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #
#                                                      Data types                                                      #
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #

PathType: TypeAlias = Union[str, Path]

DataModelType: TypeAlias = Union[BaseModel, Sequence[BaseModel], BaseModelWithAlias, Sequence[BaseModelWithAlias]]
JsonType: TypeAlias = Union[Mapping, Sequence[Mapping]]
DictType: TypeAlias = Union[Mapping, BaseModel, BaseSettings, PropertyBaseModel, BaseModelWithAlias]

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #
#                                                    Generic Types                                                     #
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #

GenericT = TypeVar("GenericT")
EnumT = TypeVar("EnumT", bound=Enum)

DataModelT = TypeVar("DataModelT", bound=DataModelType)
JsonT = TypeVar("JsonT", bound=JsonType)
DictT = TypeVar("DictT", bound=DictType)

BaseModelT = TypeVar("BaseModelT", bound=BaseModel)
BaseSettingsT = TypeVar("BaseSettingsT", bound=BaseSettings)

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #
#                                                     Filter types                                                     #
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #

PositionType: TypeAlias = Literal["oldest", "latest"]
