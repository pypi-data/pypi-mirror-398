class DangerousDeleteBlocked(RuntimeError):
    """Raised when a bulk QuerySet.delete() is blocked by the guard."""
