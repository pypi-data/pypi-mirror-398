# pylint: disable=useless-parent-delegation,bad-classmethod-argument,too-many-function-args,invalid-metaclass
# ───────────────────────────────────────────────────── imports ────────────────────────────────────────────────────── #
from typing import Any, Dict, List, Optional, TypeVar

from pydantic import BaseModel
from pydantic.main import IncEx

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #
#                           specifies all modules that shall be loaded and imported into the                           #
#                                current namespace when we use 'from package import *'                                 #
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #

__all__ = [
    "PropertyBaseModel",
    "ExcludeUnsetBaseModel",
    "OptionalBaseModel",
    "UpdateBaseModel",
    "ExcludeUnsetBaseModelT",
    "PropertyBaseModelT",
    "OptionalBaseModelT",
    "UpdateBaseModelT",
]


class PropertyBaseModel(BaseModel):
    """
    Base Model that overrides the dict function to include the object properties.
    """

    @classmethod
    def get_properties(cls) -> List:
        return [prop for prop, value in cls.__dict__.items() if isinstance(value, property)]

    @classmethod
    def is_prop_base(cls, base) -> bool:
        if PropertyBaseModel in base.__bases__ or isinstance(base, PropertyBaseModel):
            return True
        return any((cls.is_prop_base(base=sub_base) for sub_base in base.__bases__))

    def dict_prop(self, **kwargs) -> Dict[str, Any]:
        return self.dict(show_prop=True, **kwargs)

    def dict(
        self,
        *,
        include: Optional[IncEx] = None,
        exclude: Optional[IncEx] = None,
        show_prop: bool = False,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Override the dict function to include our properties.
        """

        attributes = super().model_dump(include=include, exclude=exclude, **kwargs)

        if not show_prop:
            return attributes

        props = self.get_properties()
        self._add_bases_properties(
            base=self.__class__,
            attributes=attributes,
            props=props,
            dict_args={"include": include, "exclude": exclude, **kwargs},
        )

        # Include and exclude properties
        if include:
            props = [prop for prop in props if prop in include]
        if exclude:
            props = [prop for prop in props if prop not in exclude]

        # Update the attribute dict with the properties
        if props:
            attributes.update({prop: getattr(self, prop) for prop in props})

        return attributes

    def _add_bases_properties(self, base, attributes: Dict, props: List, dict_args: Dict) -> None:
        is_prop_base = False
        for sub_base in base.__bases__:
            if self.is_prop_base(base=sub_base):
                is_prop_base = True
                attributes.update(sub_base(**attributes).dict_prop(**dict_args))
            self._add_bases_properties(base=sub_base, attributes=attributes, props=props, dict_args=dict_args)
        if is_prop_base:
            props.extend(base.get_properties())

    class Config:
        """
        Class with base attributes for configuration.
        """

        validate_assignment = True


class ExcludeUnsetBaseModel(BaseModel):
    """
    Base model to return only the data that has been set.
    """

    def model_dump(self, *args, exclude_unset: bool = True, **kwargs) -> Dict:
        """Generate a dictionary representation of the model, whose keys will be in camelCase format.

        The parameter `exclude_unset` is set as True by default in order to update only those fields that
        have been set by the user.
        In this way, it is easy to distinguish the fields that the user has indicated as null from those that
        the user has not set and are null because they are optional.

        """
        return super().model_dump(exclude_unset=exclude_unset, *args, **kwargs)


class OptionalBaseModel(BaseModel):
    """A Pydantic base model that makes all fields optional by default."""

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs: Any) -> None:
        super().__pydantic_init_subclass__(**kwargs)

        for k, v in cls.model_fields.items():
            if v.is_required():
                v.default = None

        cls.model_rebuild(force=True)


class UpdateBaseModel(ExcludeUnsetBaseModel, OptionalBaseModel):  # type:ignore
    """Base model for updating DTOs data.

    By making information update data models extend from this data model, it makes it easier to distinguish the
    fields that the user has actually modified (`exclude_unset`=True) from those that the user has not indicated.

    """


# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #
#                                                    Generic Types                                                     #
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #

ExcludeUnsetBaseModelT = TypeVar("ExcludeUnsetBaseModelT", bound=ExcludeUnsetBaseModel)
PropertyBaseModelT = TypeVar("PropertyBaseModelT", bound=PropertyBaseModel)
OptionalBaseModelT = TypeVar("OptionalBaseModelT", bound=OptionalBaseModel)
UpdateBaseModelT = TypeVar("UpdateBaseModelT", bound=UpdateBaseModel)
