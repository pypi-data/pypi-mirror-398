"""__init__ module."""

import logging
from pathlib import Path

import django
import django_stubs_ext
from django.conf import settings

import winidjango

logger = logging.getLogger(__name__)

django_stubs_ext.monkeypatch()
logger.info("Monkeypatched django-stubs")


logger = logging.getLogger(__name__)


# Configure Django settings for tests if not already configured
if not settings.configured:
    in_this_repo = Path(winidjango.__name__).exists()
    if in_this_repo:
        logger.info("Configuring minimal django settings for tests")
        installed_apps = ["tests"] if Path("tests").exists() else []
        settings.configure(
            DATABASES={
                "default": {
                    "ENGINE": "django.db.backends.sqlite3",
                    "NAME": ":memory:",
                }
            },
            INSTALLED_APPS=installed_apps,
            USE_TZ=True,
        )
        django.setup()
        logger.info("Django setup complete")
