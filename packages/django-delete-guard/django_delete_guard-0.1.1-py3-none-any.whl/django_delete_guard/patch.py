from __future__ import annotations

from typing import Optional, Tuple

from django.db.models.query import QuerySet

from .exceptions import DangerousDeleteBlocked
from .guard import get_config, get_override_token, is_production

_PATCHED = False
_ORIGINAL_DELETE = None


def _safe_queryset_summary(qs: QuerySet) -> str:
    model_label = getattr(qs.model._meta, "label", qs.model.__name__)
    where = ""
    try:
        where = str(qs.query.where)
    except Exception:
        where = ""
    where = (where or "").strip()
    if where:
        where = where.replace("\n", " ")
        if len(where) > 200:
            where = where[:200] + "…"
        return f"{model_label}.objects.filter({where})"
    return f"{model_label}.objects.all()"


def _is_unfiltered_queryset(qs: QuerySet) -> bool:
    """
    Detect classic foot-gun: Model.objects.all().delete()
    and other deletes with no WHERE clause.
    """
    try:
        where = qs.query.where
        return not getattr(where, "children", None) or len(where.children) == 0
    except Exception:
        return False


def _estimate_rows_up_to(qs: QuerySet, limit: int) -> Tuple[Optional[int], bool]:
    """
    Returns (n, is_at_least_limit_plus_one?)
    We avoid full COUNT(); sample pk values up to (limit+1) using LIMIT.
    """
    try:
        if qs.query.is_sliced:
            low, high = qs.query.low_mark, qs.query.high_mark
            if high is not None:
                sliced_len = max(0, high - low)
                if sliced_len <= limit:
                    return sliced_len, False
    except Exception:
        pass

    try:
        sample = list(qs.order_by().values_list("pk", flat=True)[: limit + 1])
        n = len(sample)
        return n, (n >= limit + 1)
    except Exception:
        return None, True


def _blocked_message(qs: QuerySet, threshold: int, est: Optional[int], reason: str) -> str:
    summary = _safe_queryset_summary(qs)
    est_part = f"Estimated rows: {('unknown' if est is None else str(est))}"
    how = (
        "To proceed intentionally, wrap the delete call:\n"
        '  with allow_dangerous_delete("TICKET-123"):\n'
        "      qs.delete()\n"
        "Use a real ticket/approval ID."
    )
    return (
        f"[django-delete-guard] Blocked QuerySet.delete() in production.\n"
        f"Reason: {reason}\n"
        f"Query: {summary}\n"
        f"{est_part} (threshold={threshold})\n"
        f"{how}"
    )


def patch_queryset_delete():
    """
    Monkeypatch QuerySet.delete() once. Safe to call multiple times.
    """
    global _PATCHED, _ORIGINAL_DELETE
    if _PATCHED:
        return

    _ORIGINAL_DELETE = QuerySet.delete

    def guarded_delete(self: QuerySet, *args, **kwargs):
        if not is_production():
            return _ORIGINAL_DELETE(self, *args, **kwargs)

        cfg = get_config()
        token = get_override_token()
        if token:
            return _ORIGINAL_DELETE(self, *args, **kwargs)

        # Block unfiltered deletes immediately (classic foot-gun)
        if _is_unfiltered_queryset(self):
            est, _ = _estimate_rows_up_to(self, cfg.threshold)
            raise DangerousDeleteBlocked(
                _blocked_message(self, cfg.threshold, est, reason="Unfiltered delete (no WHERE clause)")
            )

        # Threshold-based block
        est, at_least = _estimate_rows_up_to(self, cfg.threshold)
        should_block = at_least or (est is None) or (est > cfg.threshold)

        if should_block:
            raise DangerousDeleteBlocked(
                _blocked_message(self, cfg.threshold, est, reason=f"Bulk delete exceeds threshold ({cfg.threshold})")
            )

        return _ORIGINAL_DELETE(self, *args, **kwargs)

    QuerySet.delete = guarded_delete  # type: ignore[assignment]
    _PATCHED = True
