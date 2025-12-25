"""Database utilities and lightweight model helpers.

This module provides helpers used across the project when manipulating
Django models: ordering models by foreign-key dependencies, creating a
deterministic hash for unsaved instances, and a project-wide
``BaseModel`` that exposes common timestamp fields.
"""

from datetime import datetime
from graphlib import TopologicalSorter
from typing import TYPE_CHECKING, Any, Self, cast

from django.db.models import DateTimeField, Field, Model
from django.db.models.fields.related import ForeignKey, ForeignObjectRel
from django.forms.models import model_to_dict

from winidjango.src.db.fields import get_field_names, get_fields

if TYPE_CHECKING:
    from django.contrib.contenttypes.fields import GenericForeignKey
    from django.db.models.options import Options

import logging

logger = logging.getLogger(__name__)


def topological_sort_models[TModel: Model](
    models: list[type[TModel]],
) -> list[type[TModel]]:
    """Sort Django models in dependency order using topological sorting.

    Analyzes foreign key relationships between Django models and returns them
    in an order where dependencies come before dependents. This ensures that
    when performing operations like bulk creation or deletion, models are
    processed in the correct order to avoid foreign key constraint violations.

    The function uses Python's graphlib.TopologicalSorter to perform the sorting
    based on ForeignKey relationships between the provided models. Only
    relationships between models in the input list are considered.

    Args:
        models (list[type[Model]]): A list of Django model classes to sort
            based on their foreign key dependencies.

    Returns:
        list[type[Model]]: The input models sorted in dependency order, where
            models that are referenced by foreign keys appear before models
            that reference them. Self-referential relationships are ignored.

    Raises:
        graphlib.CycleError: If there are circular dependencies between models
            that cannot be resolved.

    Example:
        >>> # Assuming Author model has no dependencies
        >>> # and Book model has ForeignKey to Author
        >>> models = [Book, Author]
        >>> sorted_models = topological_sort_models(models)
        >>> sorted_models
        [<class 'Author'>, <class 'Book'>]

    Note:
        - Only considers ForeignKey relationships, not other field types
        - Self-referential foreign keys are ignored to avoid self-loops
        - Only relationships between models in the input list are considered
    """
    ts: TopologicalSorter[type[TModel]] = TopologicalSorter()

    for model in models:
        deps = {
            cast("type[TModel]", field.related_model)
            for field in get_fields(model)
            if isinstance(field, ForeignKey)
            and isinstance(field.related_model, type)
            and field.related_model in models
            and field.related_model is not model
        }
        ts.add(model, *deps)

    return list(ts.static_order())


def hash_model_instance(
    instance: Model,
    fields: "list[Field[Any, Any] | ForeignObjectRel | GenericForeignKey]",
) -> int:
    """Compute a deterministic hash for a model instance.

    The function returns a hash suitable for comparing unsaved model
    instances by their field values. If the instance has a primary key
    (``instance.pk``) that key is hashed and returned immediately; this
    keeps comparisons cheap for persisted objects.

    Args:
        instance (Model): The Django model instance to hash.
        fields (list[Field | ForeignObjectRel | GenericForeignKey]):
            Field objects that should be included when computing the hash.

    Returns:
        int: Deterministic integer hash of the instance. For persisted
            instances this is ``hash(instance.pk)``.

    Notes:
        - The returned hash is intended for heuristic comparisons (e.g.
          deduplication in import pipelines) and is not cryptographically
          secure. Use with care when relying on absolute uniqueness.
    """
    if instance.pk:
        return hash(instance.pk)

    field_names = get_field_names(fields)
    model_dict = model_to_dict(instance, fields=field_names)
    sorted_dict = dict(sorted(model_dict.items()))
    values = (type(instance), tuple(sorted_dict.items()))
    return hash(values)


class BaseModel(Model):
    """Abstract base model containing common fields and helpers.

    Concrete models can inherit from this class to get consistent
    ``created_at`` and ``updated_at`` timestamp fields and convenient
    string representations.
    """

    created_at: DateTimeField[datetime, datetime] = DateTimeField(auto_now_add=True)
    updated_at: DateTimeField[datetime, datetime] = DateTimeField(auto_now=True)

    class Meta:
        """Mark the model as abstract."""

        # abstract does not inherit in children
        abstract = True

    def __str__(self) -> str:
        """Return a concise human-readable representation.

        The default shows the model class name and primary key which is
        useful for logging and interactive debugging.

        Returns:
            str: Short representation, e.g. ``MyModel(123)``.
        """
        return f"{self.__class__.__name__}({self.pk})"

    def __repr__(self) -> str:
        """Base representation of a model."""
        return str(self)

    @property
    def meta(self) -> "Options[Self]":
        """Return the model's ``_meta`` options object.

        This property is a small convenience wrapper used to make access
        sites slightly more explicit in code and improve typing in callers.
        """
        return self._meta
