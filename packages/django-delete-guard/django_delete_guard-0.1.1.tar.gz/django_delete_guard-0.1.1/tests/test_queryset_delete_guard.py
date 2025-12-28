import pytest
from django.db import connection, models

from django_delete_guard.exceptions import DangerousDeleteBlocked
from django_delete_guard.guard import allow_dangerous_delete, fail_fast_if_misconfigured


class Thing(models.Model):
    name = models.CharField(max_length=64)

    class Meta:
        app_label = "tests_app"


@pytest.fixture
def thing_table():
    with connection.schema_editor() as schema_editor:
        schema_editor.create_model(Thing)
    try:
        yield
    finally:
        with connection.schema_editor() as schema_editor:
            schema_editor.delete_model(Thing)


def test_nonprod_does_not_block_unfiltered_delete(nonprod_env, thing_table):
    Thing.objects.bulk_create([Thing(name=f"t{i}") for i in range(300)])
    # Should not block in non-prod
    deleted_count, _ = Thing.objects.all().delete()
    assert deleted_count == 300


def test_prod_blocks_unfiltered_delete(prod_env, thing_table):
    Thing.objects.bulk_create([Thing(name=f"t{i}") for i in range(10)])
    with pytest.raises(DangerousDeleteBlocked) as e:
        Thing.objects.all().delete()
    assert "Unfiltered delete" in str(e.value)


def test_prod_blocks_bulk_delete_over_threshold(prod_env, thing_table):
    Thing.objects.bulk_create([Thing(name=f"t{i}") for i in range(150)])
    with pytest.raises(DangerousDeleteBlocked) as e:
        Thing.objects.filter(name__startswith="t").delete()
    assert "exceeds threshold" in str(e.value)


def test_prod_allows_delete_under_threshold(prod_env, thing_table):
    Thing.objects.bulk_create([Thing(name=f"t{i}") for i in range(50)])
    deleted_count, _ = Thing.objects.filter(name__startswith="t").delete()
    assert deleted_count == 50


def test_prod_allows_with_override_even_unfiltered(prod_env, thing_table):
    Thing.objects.bulk_create([Thing(name=f"t{i}") for i in range(250)])
    with allow_dangerous_delete("JIRA-123"):
        deleted_count, _ = Thing.objects.all().delete()
    assert deleted_count == 250


def test_fail_fast_when_prod_but_debug_true(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    # Simulate DEBUG=True without needing app startup
    from django.conf import settings
    old_debug = settings.DEBUG
    settings.DEBUG = True
    try:
        with pytest.raises(RuntimeError) as e:
            fail_fast_if_misconfigured()
        assert "Misconfiguration" in str(e.value)
    finally:
        settings.DEBUG = old_debug
        monkeypatch.delenv("APP_ENV", raising=False)
