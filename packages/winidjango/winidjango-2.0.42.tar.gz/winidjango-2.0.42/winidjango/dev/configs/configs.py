"""Configs for pyrig.

All subclasses of ConfigFile in the configs package are automatically called.
"""

from pyrig.dev.configs.pyproject import PyprojectConfigFile as PyrigPyprojectConfigFile


class PyprojectConfigFile(PyrigPyprojectConfigFile):
    """Pyproject.toml config file."""

    @classmethod
    def get_standard_dev_dependencies(cls) -> list[str]:
        """Get the standard dev dependencies."""
        dev_dependencies = super().get_standard_dev_dependencies()
        dev_dependencies.extend(["django-stubs", "pytest-django"])

        return sorted(dev_dependencies)
