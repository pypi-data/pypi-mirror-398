from contextlib import suppress

from django.conf import settings
from django.utils.module_loading import import_string
from dynamic_preferences.exceptions import NotFoundInRegistry
from dynamic_preferences.registries import global_preferences_registry


def get_backend():
    from wbcrm.synchronization.activity.controller import ActivityController

    if not settings.DEBUG:
        with suppress(NotFoundInRegistry):
            if backend := global_preferences_registry.manager()["wbactivity_sync__sync_backend_calendar"]:
                backend = import_string(backend)
                return ActivityController(backend=backend)
