"""src package.

This package exposes the project's internal modules used by the
command-line utilities and database helpers. It exists primarily so
that code under `winidjango/src` can be imported using the
`winidjango.src` package path in other modules and tests.

The package itself contains the following subpackages:
- `commands` - management command helpers and base classes
- `db` - database utilities and model helpers

Consumers should import the specific submodules they need rather than
relying on side effects from this package's import-time execution.
"""
