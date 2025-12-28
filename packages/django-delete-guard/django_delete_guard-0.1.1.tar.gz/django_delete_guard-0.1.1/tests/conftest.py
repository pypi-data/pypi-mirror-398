import os

import django
import pytest
from django.conf import settings


@pytest.fixture(scope="session", autouse=True)
def _django_setup():
    """
    Minimal Django settings for tests. We do NOT rely on migrations.
    We'll create tables with schema_editor in the tests themselves.
    """
    if not settings.configured:
        settings.configure(
            DEBUG=False,
            SECRET_KEY="test",
            INSTALLED_APPS=[
                "django.contrib.contenttypes",
                "django_delete_guard",
            ],
            DATABASES={
                "default": {
                    "ENGINE": "django.db.backends.sqlite3",
                    "NAME": ":memory:",
                }
            },
            DEFAULT_AUTO_FIELD="django.db.models.AutoField",
        )
    django.setup()


@pytest.fixture
def prod_env(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    yield
    monkeypatch.delenv("APP_ENV", raising=False)


@pytest.fixture
def nonprod_env(monkeypatch):
    monkeypatch.setenv("APP_ENV", "staging")
    yield
    monkeypatch.delenv("APP_ENV", raising=False)
