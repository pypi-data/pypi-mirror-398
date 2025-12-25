# ───────────────────────────────────────────────────── imports ────────────────────────────────────────────────────── #
from pydantic import BaseModel, ConfigDict
from typing_extensions import TypeAlias

from core_common_data_types.base_data_types_tos import CamelCaseBaseModelWithExtra

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #
#                           specifies all modules that shall be loaded and imported into the                           #
#                                current namespace when we use 'from package import *'                                 #
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #

__all__ = ["CamelCaseModelWithExtra"]

from core_common_data_types.utils_data_types_tos import to_lower_camel

# DEPRECATED => Keep until we are sure to replace all its references
CamelCaseModelWithExtra: TypeAlias = CamelCaseBaseModelWithExtra


class BaseModelWithAlias(BaseModel):
    """
    Base Model with enabled alias.
    Whether an aliased field may be populated by its name as given by the model attribute, as well as the alias
    """

    def dict(self, *args, **kwargs):
        if kwargs and kwargs.get("exclude_none") is not None:
            kwargs["exclude_none"] = True
        return super().model_dump(*args, **kwargs)

    def dict_alias(self, *args, **kwargs):
        """Generate a dictionary representation of the model with field alias as keys"""
        return self.dict(by_alias=True, *args, **kwargs)

    model_config = ConfigDict(
        alias_generator=to_lower_camel,
        # Convert snake_case to camelCase for JSON serialization
        populate_by_name=True,
        # Allows setting values by both the original name and the alias
        arbitrary_types_allowed=True,  # Allows arbitrary (non-Pydantic) types
        protected_namespaces=(),
    )
