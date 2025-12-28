from django.apps import AppConfig

from .guard import fail_fast_if_misconfigured
from .patch import patch_queryset_delete


class DeleteGuardConfig(AppConfig):
    name = "django_delete_guard"
    verbose_name = "Django Delete Guard"

    def ready(self):
        fail_fast_if_misconfigured()
        patch_queryset_delete()
