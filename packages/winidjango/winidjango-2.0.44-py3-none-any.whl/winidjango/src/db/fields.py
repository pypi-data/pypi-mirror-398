"""Utilities for inspecting Django model fields.

This module provides small helpers that make it easier to introspect
Django model fields and metadata in a type-friendly way. The helpers are
used across the project's database utilities to implement operations like
topological sorting and deterministic hashing of model instances.
"""

from typing import TYPE_CHECKING, Any

from django.db.models import Field, Model

if TYPE_CHECKING:
    from django.contrib.contenttypes.fields import GenericForeignKey
    from django.db.models.fields.related import ForeignObjectRel
    from django.db.models.options import Options


def get_field_names(
    fields: "list[Field[Any, Any] | ForeignObjectRel | GenericForeignKey]",
) -> list[str]:
    """Return the ``name`` attribute for a list of Django field objects.

    Args:
        fields (list[Field | ForeignObjectRel | GenericForeignKey]):
            Field objects obtained from a model's ``_meta.get_fields()``.

    Returns:
        list[str]: List of field names in the same order as ``fields``.
    """
    return [field.name for field in fields]


def get_model_meta(model: type[Model]) -> "Options[Model]":
    """Return a model class' ``_meta`` options object.

    This small wrapper exists to make typing clearer at call sites where
    the code needs the model Options object.

    Args:
        model (type[Model]): Django model class.

    Returns:
        Options: The model's ``_meta`` options object.
    """
    return model._meta  # noqa: SLF001


def get_fields[TModel: Model](
    model: type[TModel],
) -> "list[Field[Any, Any] | ForeignObjectRel | GenericForeignKey]":
    """Return all field objects for a Django model.

    This wraps ``model._meta.get_fields()`` and is typed to include
    relationship fields so callers can handle both regular and related
    fields uniformly.

    Args:
        model (type[Model]): Django model class.

    Returns:
        list[Field | ForeignObjectRel | GenericForeignKey]: All field
            objects associated with the model.
    """
    return get_model_meta(model).get_fields()
