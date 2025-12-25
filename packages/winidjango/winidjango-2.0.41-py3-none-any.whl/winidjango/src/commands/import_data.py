"""Import command base class and utilities.

This module defines a reusable base command for importing tabular data
into Django models. Implementations should provide a concrete source
ingestion (for example, reading from CSV or an external API), a
cleaning/normalization step implemented by a `CleaningDF` subclass, and
mapping logic that groups cleaned data into model instances that can be
bulk-created.

The base command centralizes the typical flow:
1. Read raw data (``handle_import``)
2. Wrap and clean the data using a `CleaningDF` subclass
3. Convert the cleaned frame into per-model bulks
4. Persist bulks using the project's bulk create helpers

Using this base class ensures a consistent import lifecycle and
reduces duplicated boilerplate across different import implementations.
"""

import logging
from abc import abstractmethod
from collections.abc import Iterable

import polars as pl
from django.db.models import Model
from winiutils.src.data.dataframe.cleaning import CleaningDF

from winidjango.src.commands.base.base import ABCBaseCommand
from winidjango.src.db.bulk import bulk_create_bulks_in_steps

logger = logging.getLogger(__name__)


class ImportDataBaseCommand(ABCBaseCommand):
    """Abstract base for data-import Django management commands.

    Subclasses must implement the ingestion, cleaning-class selection,
    and mapping of cleaned rows to Django model instances. The base
    implementation wires these pieces together and calls the project's
    bulk creation helper to persist the data.

    Implementors typically only need to override the three abstract
    methods documented below.
    """

    @abstractmethod
    def handle_import(self) -> pl.DataFrame:
        """Read raw data from the import source.

        This method should read data from whatever source the concrete
        command targets (files, remote APIs, etc.) and return it as a
        ``polars.DataFrame``. No cleaning should be performed here;
        cleaning is handled by the cleaning `CleaningDF` returned from
        ``get_cleaning_df_cls``.

        Returns:
            pl.DataFrame: Raw (uncleaned) tabular data to be cleaned and
                mapped to model instances.
        """

    @abstractmethod
    def get_cleaning_df_cls(self) -> type[CleaningDF]:
        """Return the `CleaningDF` subclass used to normalize the data.

        The returned class will be instantiated with the raw DataFrame
        returned from :meth:`handle_import` and must provide the
        transformations required to prepare data for mapping into model
        instances.

        Returns:
            type[CleaningDF]: A subclass of ``CleaningDF`` that performs
                the necessary normalization and validation.
        """

    @abstractmethod
    def get_bulks_by_model(
        self, df: pl.DataFrame
    ) -> dict[type[Model], Iterable[Model]]:
        """Map the cleaned DataFrame to model-instance bulks.

        The implementation should inspect the cleaned DataFrame and
        return a mapping where keys are Django model classes and values
        are iterables of unsaved model instances (or dataclass-like
        objects accepted by the project's bulk-creation utility).

        Args:
            df (pl.DataFrame): The cleaned and normalized DataFrame.

        Returns:
            dict[type[Model], Iterable[Model]]: Mapping from model classes
                to iterables of instances that should be created.
        """

    def handle_command(self) -> None:
        """Execute the full import lifecycle.

        This template method reads raw data via :meth:`handle_import`,
        wraps it with the cleaning class returned by
        :meth:`get_cleaning_df_cls` and then persists the resulting
        model bulks returned by :meth:`get_bulks_by_model`.
        """
        data_df = self.handle_import()

        cleaning_df_cls = self.get_cleaning_df_cls()
        self.cleaning_df = cleaning_df_cls(data_df)

        self.import_to_db()

    def import_to_db(self) -> None:
        """Persist prepared model bulks to the database.

        Calls the project's `bulk_create_bulks_in_steps` helper with the
        mapping returned from :meth:`get_bulks_by_model`.
        """
        bulks_by_model = self.get_bulks_by_model(df=self.cleaning_df.df)

        bulk_create_bulks_in_steps(bulks_by_model)
