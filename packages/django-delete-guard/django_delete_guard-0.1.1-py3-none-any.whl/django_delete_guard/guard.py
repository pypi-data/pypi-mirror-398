import os
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Optional, Set

from django.conf import settings

_OVERRIDE_TOKEN: ContextVar[Optional[str]] = ContextVar("delete_guard_override_token", default=None)


@dataclass(frozen=True)
class GuardConfig:
    env_var: str
    prod_values: Set[str]
    threshold: int


def get_config() -> GuardConfig:
    env_var = getattr(settings, "DELETE_GUARD_ENV_VAR", "APP_ENV")
    prod_values = set(v.lower() for v in getattr(settings, "DELETE_GUARD_PROD_VALUES", {"production", "prod"}))
    threshold = int(getattr(settings, "DELETE_GUARD_THRESHOLD", 100))
    return GuardConfig(env_var=env_var, prod_values=prod_values, threshold=threshold)


def is_production() -> bool:
    cfg = get_config()
    val = (os.getenv(cfg.env_var) or "").strip().lower()
    return val in cfg.prod_values


def get_override_token() -> Optional[str]:
    return _OVERRIDE_TOKEN.get()


@contextmanager
def allow_dangerous_delete(token: str):
    """
    Explicit override to permit bulk deletes in production.

    Usage:
        with allow_dangerous_delete("TICKET-123"):
            MyModel.objects.filter(...).delete()
    """
    if not isinstance(token, str) or not token.strip():
        raise ValueError("allow_dangerous_delete(token) requires a non-empty string token (e.g., 'JIRA-123').")

    reset = _OVERRIDE_TOKEN.set(token.strip())
    try:
        yield
    finally:
        _OVERRIDE_TOKEN.reset(reset)


def fail_fast_if_misconfigured():
    """
    Locked rule:
    - Guard enabled only if APP_ENV in {"production","prod"} (or configured values)
    - If prod is set but DEBUG=True, raise immediately.
    """
    if is_production() and getattr(settings, "DEBUG", False):
        cfg = get_config()
        raise RuntimeError(
            f"[django-delete-guard] Misconfiguration: {cfg.env_var}=production but settings.DEBUG=True. "
            "Refusing to start. Set DEBUG=False or change APP_ENV."
        )
