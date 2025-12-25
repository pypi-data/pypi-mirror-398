"""Utilities and an abstract base class for Django management commands.

This module defines :class:`ABCBaseCommand`, a reusable abstract base
that combines Django's ``BaseCommand`` with the project's logging
mixins and standard argument handling. The base class implements a
template method pattern so concrete commands only need to implement the
abstract extension points for providing command-specific arguments and
business logic.
"""

import logging
from abc import abstractmethod
from argparse import ArgumentParser
from typing import Any

from django.core.management import BaseCommand
from winiutils.src.oop.mixins.mixin import ABCLoggingMixin

logger = logging.getLogger(__name__)


class ABCBaseCommand(ABCLoggingMixin, BaseCommand):
    """Abstract base class for management commands with logging and standard options.

    The class wires common behavior such as base arguments (dry-run,
    batching, timeouts) and provides extension points that concrete
    commands must implement: :meth:`add_command_arguments` and
    :meth:`handle_command`.

    Notes:
        - Inheritance order matters: the logging mixin must precede
          ``BaseCommand`` so mixin initialization occurs as expected.
        - The base class follows the template method pattern; concrete
          commands should not override :meth:`add_arguments` or
          :meth:`handle` but implement the abstract hooks instead.
    """

    class Options:
        """Just a container class for hard coding the option keys."""

        DRY_RUN = "dry_run"
        FORCE = "force"
        DELETE = "delete"
        YES = "yes"
        TIMEOUT = "timeout"
        BATCH_SIZE = "batch_size"
        THREADS = "threads"
        PROCESSES = "processes"

    def add_arguments(self, parser: ArgumentParser) -> None:
        """Configure command-line arguments for the command.

        Adds common base arguments (dry-run, force, delete, timeout,
        batching and concurrency options) and then delegates to
        :meth:`add_command_arguments` for command-specific options.

        Args:
            parser (ArgumentParser): The argument parser passed by Django.
        """
        # add base args that are used in most commands
        self.base_add_arguments(parser)

        # add additional args that are specific to the command
        self.add_command_arguments(parser)

    def base_add_arguments(self, parser: ArgumentParser) -> None:
        """Add the project's standard command-line arguments to ``parser``.

        Args:
            parser (ArgumentParser): The argument parser passed by Django.
        """
        parser.add_argument(
            f"--{self.Options.DRY_RUN}",
            action="store_true",
            help="Show what would be done without actually executing the changes",
        )

        parser.add_argument(
            f"--{self.Options.FORCE}",
            action="store_true",
            help="Force an action in a command",
        )

        parser.add_argument(
            f"--{self.Options.DELETE}",
            action="store_true",
            help="Deleting smth in a command",
        )

        parser.add_argument(
            f"--{self.Options.YES}",
            action="store_true",
            help="Answer yes to all prompts",
            default=False,
        )

        parser.add_argument(
            f"--{self.Options.TIMEOUT}",
            type=int,
            help="Timeout for a command",
            default=None,
        )

        parser.add_argument(
            f"--{self.Options.BATCH_SIZE}",
            type=int,
            default=None,
            help="Number of items to process in each batch",
        )

        parser.add_argument(
            f"--{self.Options.THREADS}",
            type=int,
            default=None,
            help="Number of threads to use for processing",
        )

        parser.add_argument(
            f"--{self.Options.PROCESSES}",
            type=int,
            default=None,
            help="Number of processes to use for processing",
        )

    @abstractmethod
    def add_command_arguments(self, parser: ArgumentParser) -> None:
        """Define command-specific arguments.

        Implement this hook to add options and positional arguments that are
        specific to the concrete management command.

        Args:
            parser (ArgumentParser): The argument parser passed by Django.
        """

    def handle(self, *args: Any, **options: Any) -> None:
        """Orchestrate command execution.

        Performs shared pre-processing by calling :meth:`base_handle` and
        then delegates to :meth:`handle_command` which must be implemented
        by subclasses.

        Args:
            *args: Positional arguments forwarded from Django.
            **options: Parsed command-line options.
        """
        self.base_handle(*args, **options)
        self.handle_command()

    def base_handle(self, *args: Any, **options: Any) -> None:
        """Perform common pre-processing for commands.

        Stores the incoming arguments and options on the instance for use
        by :meth:`handle_command` and subclasses.

        Args:
            *args: Positional arguments forwarded from Django.
            **options: Parsed command-line options.
        """
        self.args = args
        self.options = options

    @abstractmethod
    def handle_command(self) -> None:
        """Run the command-specific behavior.

        This abstract hook should be implemented by concrete commands to
        perform the command's main work. Implementations should read
        ``self.args`` and ``self.options`` which were set in
        :meth:`base_handle`.
        """

    def get_option(self, option: str) -> Any:
        """Retrieve a parsed command option by key.

        Args:
            option (str): The option key to retrieve from ``self.options``.

        Returns:
            Any: The value for the requested option. If the option is not
                present a ``KeyError`` will be raised (matching how Django
                exposes options in management commands).
        """
        return self.options[option]
