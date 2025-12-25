"""Utilities for performing bulk operations on Django models.

This module centralizes helpers used by importers and maintenance
commands to create, update and delete large collections of model
instances efficiently. It provides batching, optional concurrent
execution, dependency-aware ordering and simulation helpers for
previewing cascade deletions.
"""

from collections import defaultdict
from collections.abc import Callable, Generator, Iterable
from functools import partial
from itertools import islice
from typing import TYPE_CHECKING, Any, Literal, cast, get_args, overload

from django.db import router, transaction
from django.db.models import (
    Field,
    Model,
    QuerySet,
)
from django.db.models.deletion import Collector
from winiutils.src.iterating.concurrent.multithreading import multithread_loop

from winidjango.src.db.models import (
    hash_model_instance,
    topological_sort_models,
)

if TYPE_CHECKING:
    from django.contrib.contenttypes.fields import GenericForeignKey
    from django.db.models.fields.related import ForeignObjectRel

import logging

logger = logging.getLogger(__name__)

MODE_TYPES = Literal["create", "update", "delete"]
MODES = get_args(MODE_TYPES)

MODE_CREATE = MODES[0]
MODE_UPDATE = MODES[1]
MODE_DELETE = MODES[2]

STANDARD_BULK_SIZE = 1000


def bulk_create_in_steps[TModel: Model](
    model: type[TModel],
    bulk: Iterable[TModel],
    step: int = STANDARD_BULK_SIZE,
) -> list[TModel]:
    """Create objects in batches and return created instances.

    Breaks ``bulk`` into chunks of size ``step`` and calls the project's
    batched bulk-create helper for each chunk. Execution is performed
    using the concurrent utility where configured for throughput.

    Args:
        model: Django model class to create instances for.
        bulk: Iterable of unsaved model instances.
        step: Number of instances to create per chunk.

    Returns:
        List of created model instances (flattened across chunks).
    """
    return cast(
        "list[TModel]",
        bulk_method_in_steps(model=model, bulk=bulk, step=step, mode=MODE_CREATE),
    )


def bulk_update_in_steps[TModel: Model](
    model: type[TModel],
    bulk: Iterable[TModel],
    update_fields: list[str],
    step: int = STANDARD_BULK_SIZE,
) -> int:
    """Update objects in batches and return total updated count.

    Args:
        model: Django model class.
        bulk: Iterable of model instances to update (must have PKs set).
        update_fields: Fields to update on each instance when calling
            ``bulk_update``.
        step: Chunk size for batched updates.

    Returns:
        Total number of rows updated across all chunks.
    """
    return cast(
        "int",
        bulk_method_in_steps(
            model=model, bulk=bulk, step=step, mode=MODE_UPDATE, fields=update_fields
        ),
    )


def bulk_delete_in_steps[TModel: Model](
    model: type[TModel], bulk: Iterable[TModel], step: int = STANDARD_BULK_SIZE
) -> tuple[int, dict[str, int]]:
    """Delete objects in batches and return deletion statistics.

    Each chunk is deleted using Django's QuerySet ``delete`` which
    returns a (count, per-model-counts) tuple. Results are aggregated
    across chunks and returned as a consolidated tuple.

    Args:
        model: Django model class.
        bulk: Iterable of model instances to delete.
        step: Chunk size for deletions.

    Returns:
        A tuple containing the total number of deleted objects and a
        mapping from model label to deleted count (including cascaded
        deletions).
    """
    return cast(
        "tuple[int, dict[str, int]]",
        bulk_method_in_steps(
            model=model,
            bulk=bulk,
            step=step,
            mode=MODE_DELETE,
        ),
    )


@overload
def bulk_method_in_steps[TModel: Model](
    model: type[TModel],
    bulk: Iterable[TModel],
    step: int,
    mode: Literal["create"],
    **kwargs: Any,
) -> list[TModel]: ...


@overload
def bulk_method_in_steps[TModel: Model](
    model: type[TModel],
    bulk: Iterable[TModel],
    step: int,
    mode: Literal["update"],
    **kwargs: Any,
) -> int: ...


@overload
def bulk_method_in_steps[TModel: Model](
    model: type[TModel],
    bulk: Iterable[TModel],
    step: int,
    mode: Literal["delete"],
    **kwargs: Any,
) -> tuple[int, dict[str, int]]: ...


def bulk_method_in_steps[TModel: Model](
    model: type[TModel],
    bulk: Iterable[TModel],
    step: int,
    mode: MODE_TYPES,
    **kwargs: Any,
) -> int | tuple[int, dict[str, int]] | list[TModel]:
    """Run a batched bulk operation (create/update/delete) on ``bulk``.

    This wrapper warns if called from within an existing transaction and
    delegates actual work to :func:`bulk_method_in_steps_atomic` which is
    executed inside an atomic transaction. The return type depends on
    ``mode`` (see :mod:`winidjango.src.db.bulk` constants).

    Args:
        model: Django model class to operate on.
        bulk: Iterable of model instances.
        step: Chunk size for processing.
        mode: One of ``'create'``, ``'update'`` or ``'delete'``.
        **kwargs: Additional keyword arguments forwarded to the underlying
            bulk methods (for example ``update_fields`` for updates).

    Returns:
        For ``create``: list of created instances.
        For ``update``: integer number of updated rows.
        For ``delete``: tuple(total_deleted, per_model_counts).
    """
    # check if we are inside a transaction.atomic block
    _in_atomic_block = transaction.get_connection().in_atomic_block
    if _in_atomic_block:
        logger.info(
            "BE CAREFUL USING BULK OPERATIONS INSIDE A BROADER TRANSACTION BLOCK. "
            "BULKING WITH BULKS THAT DEPEND ON EACH OTHER CAN CAUSE "
            "INTEGRITY ERRORS OR POTENTIAL OTHER ISSUES."
        )
    return bulk_method_in_steps_atomic(
        model=model, bulk=bulk, step=step, mode=mode, **kwargs
    )


# Overloads for bulk_method_in_steps_atomic
@overload
@transaction.atomic
def bulk_method_in_steps_atomic[TModel: Model](
    model: type[TModel],
    bulk: Iterable[TModel],
    step: int,
    mode: Literal["create"],
    **kwargs: Any,
) -> list[TModel]: ...


@overload
@transaction.atomic
def bulk_method_in_steps_atomic[TModel: Model](
    model: type[TModel],
    bulk: Iterable[TModel],
    step: int,
    mode: Literal["update"],
    **kwargs: Any,
) -> int: ...


@overload
@transaction.atomic
def bulk_method_in_steps_atomic[TModel: Model](
    model: type[TModel],
    bulk: Iterable[TModel],
    step: int,
    mode: Literal["delete"],
    **kwargs: Any,
) -> tuple[int, dict[str, int]]: ...


@transaction.atomic
def bulk_method_in_steps_atomic[TModel: Model](
    model: type[TModel],
    bulk: Iterable[TModel],
    step: int,
    mode: MODE_TYPES,
    **kwargs: Any,
) -> int | tuple[int, dict[str, int]] | list[TModel]:
    """Atomic implementation of the batched bulk operation.

    This function is decorated with ``transaction.atomic`` so each call
    to this function runs in a database transaction. Note that nesting
    additional, outer atomic blocks that also include dependent bulk
    operations can cause integrity issues for operations that depend on
    each other's side-effects; callers should be careful about atomic
    decorator placement in higher-level code.

    Args:
        model: Django model class.
        bulk: Iterable of model instances.
        step: Chunk size for processing.
        mode: One of ``'create'``, ``'update'`` or ``'delete'``.
        **kwargs: Forwarded to the underlying bulk method.

    Returns:
        See :func:`bulk_method_in_steps` for return value semantics.
    """
    bulk_method = get_bulk_method(model=model, mode=mode, **kwargs)

    chunks = get_step_chunks(bulk=bulk, step=step)

    # multithreading significantly increases speed
    result = multithread_loop(
        process_function=bulk_method,
        process_args=chunks,
    )

    return flatten_bulk_in_steps_result(result=result, mode=mode)


def get_step_chunks(
    bulk: Iterable[Model], step: int
) -> Generator[tuple[list[Model]], None, None]:
    """Yield consecutive chunks of at most ``step`` items from ``bulk``.

    The function yields a single-tuple containing the chunk (a list of
    model instances) because the concurrent execution helper expects a
    tuple of positional arguments for the target function.

    Args:
        bulk: Iterable of model instances.
        step: Maximum number of instances per yielded chunk.

    Yields:
        Tuples where the first element is a list of model instances.
    """
    bulk = iter(bulk)
    while True:
        chunk = list(islice(bulk, step))
        if not chunk:
            break
        yield (chunk,)  # bc concurrent_loop expects a tuple of args


# Overloads for get_bulk_method
@overload
def get_bulk_method(
    model: type[Model], mode: Literal["create"], **kwargs: Any
) -> Callable[[list[Model]], list[Model]]: ...


@overload
def get_bulk_method(
    model: type[Model], mode: Literal["update"], **kwargs: Any
) -> Callable[[list[Model]], int]: ...


@overload
def get_bulk_method(
    model: type[Model], mode: Literal["delete"], **kwargs: Any
) -> Callable[[list[Model]], tuple[int, dict[str, int]]]: ...


def get_bulk_method(
    model: type[Model], mode: MODE_TYPES, **kwargs: Any
) -> Callable[[list[Model]], list[Model] | int | tuple[int, dict[str, int]]]:
    """Return a callable that performs the requested bulk operation on a chunk.

    The returned function accepts a single argument (a list of model
    instances) and returns the per-chunk result for the chosen mode.

    Args:
        model: Django model class.
        mode: One of ``'create'``, ``'update'`` or ``'delete'``.
        **kwargs: Forwarded to the underlying ORM bulk methods.

    Raises:
        ValueError: If ``mode`` is invalid.

    Returns:
        Callable that accepts a list of model instances and returns the
        result for that chunk.
    """
    bulk_method: Callable[[list[Model]], list[Model] | int | tuple[int, dict[str, int]]]
    if mode == MODE_CREATE:

        def bulk_create_chunk(chunk: list[Model]) -> list[Model]:
            return model.objects.bulk_create(objs=chunk, **kwargs)

        bulk_method = bulk_create_chunk
    elif mode == MODE_UPDATE:

        def bulk_update_chunk(chunk: list[Model]) -> int:
            return model.objects.bulk_update(objs=chunk, **kwargs)

        bulk_method = bulk_update_chunk
    elif mode == MODE_DELETE:

        def bulk_delete_chunk(chunk: list[Model]) -> tuple[int, dict[str, int]]:
            return bulk_delete(model=model, objs=chunk, **kwargs)

        bulk_method = bulk_delete_chunk
    else:
        msg = f"Invalid method. Must be one of {MODES}"
        raise ValueError(msg)

    return bulk_method


# Overloads for flatten_bulk_in_steps_result
@overload
def flatten_bulk_in_steps_result[TModel: Model](
    result: list[list[TModel]], mode: Literal["create"]
) -> list[TModel]: ...


@overload
def flatten_bulk_in_steps_result[TModel: Model](
    result: list[int], mode: Literal["update"]
) -> int: ...


@overload
def flatten_bulk_in_steps_result[TModel: Model](
    result: list[tuple[int, dict[str, int]]], mode: Literal["delete"]
) -> tuple[int, dict[str, int]]: ...


def flatten_bulk_in_steps_result[TModel: Model](
    result: list[int] | list[tuple[int, dict[str, int]]] | list[list[TModel]], mode: str
) -> int | tuple[int, dict[str, int]] | list[TModel]:
    """Aggregate per-chunk results returned by concurrent bulk execution.

    Depending on ``mode`` the function reduces a list of per-chunk
    results into a single consolidated return value:

    - ``create``: flattens a list of lists into a single list of objects
    - ``update``: sums integer counts returned per chunk
    - ``delete``: aggregates (count, per-model-dict) tuples into a single
      total and combined per-model counts

    Args:
        result: List of per-chunk results returned by the chunk function.
        mode: One of the supported modes.

    Returns:
        Aggregated result corresponding to ``mode``.
    """
    if mode == MODE_UPDATE:
        # formated as [1000, 1000, ...]
        # since django 4.2 bulk_update returns the count of updated objects
        result = cast("list[int]", result)
        return int(sum(result))
    if mode == MODE_DELETE:
        # formated as [(count, {model_name: count, model_cascade_name: count}), ...]
        # join the results to get the total count of deleted objects
        result = cast("list[tuple[int, dict[str, int]]]", result)
        total_count = 0
        count_sum_by_model: defaultdict[str, int] = defaultdict(int)
        for count_sum, count_by_model in result:
            total_count += count_sum
            for model_name, count in count_by_model.items():
                count_sum_by_model[model_name] += count
        return (total_count, dict(count_sum_by_model))
    if mode == MODE_CREATE:
        # formated as [[obj1, obj2, ...], [obj1, obj2, ...], ...]
        result = cast("list[list[TModel]]", result)
        return [item for sublist in result for item in sublist]

    msg = f"Invalid method. Must be one of {MODES}"
    raise ValueError(msg)


def bulk_delete(
    model: type[Model], objs: Iterable[Model], **_: Any
) -> tuple[int, dict[str, int]]:
    """Delete the provided objects and return Django's delete summary.

    Accepts either a QuerySet or an iterable of model instances. When an
    iterable of instances is provided it is converted to a QuerySet by
    filtering on primary keys before calling ``QuerySet.delete()``.

    Args:
        model: Django model class.
        objs: Iterable of model instances or a QuerySet.

    Returns:
        Tuple(total_deleted, per_model_counts) as returned by ``delete()``.
    """
    query_set = objs
    if not isinstance(query_set, QuerySet):
        query_set = list(query_set)
        pks = [obj.pk for obj in query_set]
        query_set = model.objects.filter(pk__in=pks)

    return query_set.delete()


def bulk_create_bulks_in_steps[TModel: Model](
    bulk_by_class: dict[type[TModel], Iterable[TModel]],
    step: int = STANDARD_BULK_SIZE,
) -> dict[type[TModel], list[TModel]]:
    """Create multiple model-type bulks in dependency order.

    The function topologically sorts the provided model classes so that
    models referenced by foreign keys are created before models that
    reference them. Each class' instances are created in batches using
    :func:`bulk_create_in_steps`.

    Args:
        bulk_by_class: Mapping from model class to iterable of instances to create.
        step: Chunk size for each model's batched creation.

    Returns:
        Mapping from model class to list of created instances.
    """
    # order the bulks in order of creation depending how they depend on each other
    models_ = list(bulk_by_class.keys())
    ordered_models = topological_sort_models(models=models_)

    results: dict[type[TModel], list[TModel]] = {}
    for model_ in ordered_models:
        bulk = bulk_by_class[model_]
        result = bulk_create_in_steps(model=model_, bulk=bulk, step=step)
        results[model_] = result

    return results


def get_differences_between_bulks(
    bulk1: list[Model],
    bulk2: list[Model],
    fields: "list[Field[Any, Any] | ForeignObjectRel | GenericForeignKey]",
) -> tuple[list[Model], list[Model], list[Model], list[Model]]:
    """Return differences and intersections between two bulks of the same model.

    Instances are compared using :func:`hash_model_instance` over the
    provided ``fields``. The function maintains the original ordering
    for returned lists so that callers can preserve deterministic
    ordering when applying diffs.

    Args:
        bulk1: First list of model instances.
        bulk2: Second list of model instances.
        fields: Fields to include when hashing instances.

    Raises:
        ValueError: If bulks are empty or contain different model types.

    Returns:
        Four lists in the order:
            (in_1_not_2, in_2_not_1, in_both_from_1, in_both_from_2).
    """
    if not bulk1 or not bulk2:
        return bulk1, bulk2, [], []

    if type(bulk1[0]) is not type(bulk2[0]):
        msg = "Both bulks must be of the same model type."
        raise ValueError(msg)

    hash_model_instance_with_fields = partial(
        hash_model_instance,
        fields=fields,
    )
    # Precompute hashes and map them directly to models in a single pass for both bulks
    hashes1 = list(map(hash_model_instance_with_fields, bulk1))
    hashes2 = list(map(hash_model_instance_with_fields, bulk2))

    # Convert keys to sets for difference operations
    set1, set2 = set(hashes1), set(hashes2)

    # Calculate differences between sets
    # Find differences and intersection with original order preserved
    # Important, we need to return the original objects that are the same in memory,
    # so in_1_not_2 and in_2_not_1
    in_1_not_2 = set1 - set2
    in_1_not_2_list = [
        model
        for model, hash_ in zip(bulk1, hashes1, strict=False)
        if hash_ in in_1_not_2
    ]

    in_2_not_1 = set2 - set1
    in_2_not_1_list = [
        model
        for model, hash_ in zip(bulk2, hashes2, strict=False)
        if hash_ in in_2_not_1
    ]

    in_1_and_2 = set1 & set2
    in_1_and_2_from_1 = [
        model
        for model, hash_ in zip(bulk1, hashes1, strict=False)
        if hash_ in in_1_and_2
    ]
    in_1_and_2_from_2 = [
        model
        for model, hash_ in zip(bulk2, hashes2, strict=False)
        if hash_ in in_1_and_2
    ]

    return in_1_not_2_list, in_2_not_1_list, in_1_and_2_from_1, in_1_and_2_from_2


def simulate_bulk_deletion(
    model_class: type[Model], entries: list[Model]
) -> dict[type[Model], set[Model]]:
    """Simulate Django's delete cascade and return affected objects.

    Uses :class:`django.db.models.deletion.Collector` to determine which
    objects (including cascaded related objects) would be removed if the
    provided entries were deleted. No database writes are performed.

    Args:
        model_class: Model class of the provided entries.
        entries: Instances to simulate deletion for.

    Returns:
        Mapping from model class to set of instances that would be deleted.
    """
    if not entries:
        return {}

    # Initialize the Collector
    using = router.db_for_write(model_class)
    collector = Collector(using)

    # Collect deletion cascade for all entries
    collector.collect(entries)  # ty:ignore[invalid-argument-type]

    # Prepare the result dictionary
    deletion_summary: defaultdict[type[Model], set[Model]] = defaultdict(set)

    # Add normal deletes
    for model, objects in collector.data.items():
        deletion_summary[model].update(objects)  # objects is already iterable

    # Add fast deletes (explicitly expand querysets)
    for queryset in collector.fast_deletes:
        deletion_summary[queryset.model].update(list(queryset))

    return deletion_summary


def multi_simulate_bulk_deletion(
    entries: dict[type[Model], list[Model]],
) -> dict[type[Model], set[Model]]:
    """Simulate deletions for multiple model classes and merge results.

    Runs :func:`simulate_bulk_deletion` for each provided model and
    returns a unified mapping of all models that would be deleted.

    Args:
        entries: Mapping from model class to list of instances to simulate.

    Returns:
        Mapping from model class to set of instances that would be deleted.
    """
    deletion_summaries = [
        simulate_bulk_deletion(model, entry) for model, entry in entries.items()
    ]
    # join the dicts to get the total count of deleted objects
    joined_deletion_summary: defaultdict[type[Model], set[Model]] = defaultdict(set)
    for deletion_summary in deletion_summaries:
        for model, objects in deletion_summary.items():
            joined_deletion_summary[model].update(objects)

    return dict(joined_deletion_summary)
