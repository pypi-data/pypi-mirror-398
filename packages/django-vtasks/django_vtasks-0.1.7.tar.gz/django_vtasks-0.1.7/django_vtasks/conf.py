"""
Settings for django-vtasks.

Settings are configured in Django's `settings.py` and accessed via the
`vtasks_settings` object.

Example:
```
# settings.py
VTASKS_QUEUES = ["high", "default", "low"]

# your_app/tasks.py
from django_vtasks.conf import vtasks_settings

print(vtasks_settings.VTASKS_QUEUES)
```
"""

from django.conf import settings as django_settings
from django.core.signals import setting_changed
from django.dispatch import receiver

DEFAULTS = {
    "VTASKS_QUEUES": ["default"],
    "VTASKS_CONCURRENCY": 50,
    "VTASKS_BATCH_QUEUES": {},
    "VTASKS_RUN_SCHEDULER": True,
    "VTASKS_SCHEDULE": {},
    "VTASKS_COMPRESS_THRESHOLD": 1024,
    "VTASKS_DLQ_CAP": 1000,
    "VTASKS_VALKEY_PREFIX": "vt",
}


class VtasksSettings:
    """
    A lazy settings object that gets settings from Django's settings.py.
    """

    def __init__(self, defaults):
        self._defaults = defaults
        # Track which attributes we have cached so we can clear them later
        self._cached_attrs = set()

    def __getattr__(self, name):
        if not name.startswith("VTASKS_"):
            raise AttributeError(f"Invalid vtasks setting: {name}")

        default_val = self._defaults.get(name)
        val = getattr(django_settings, name, default_val)

        # Special handling for VALKEY_PREFIX to ensure it ends with a colon
        if name == "VTASKS_VALKEY_PREFIX":
            if val and not val.endswith(":"):
                val += ":"

        # Cache the value on the instance.
        # This prevents __getattr__ from running on subsequent access.
        self._cached_attrs.add(name)
        setattr(self, name, val)
        return val

    def reload(self):
        """
        Wipe the instance attributes so __getattr__ runs again on next access.
        """
        for attr in self._cached_attrs:
            delattr(self, attr)
        self._cached_attrs.clear()


settings = VtasksSettings(DEFAULTS)


@receiver(setting_changed)
def reload_vtasks_settings(*args, **kwargs):
    """
    Listen for the 'setting_changed' signal, which is sent by override_settings
    (and other Django internals) whenever settings are modified.
    """
    setting = kwargs.get("setting")

    # Only reload if the changed setting belongs to our package
    if setting and setting.startswith("VTASKS_"):
        settings.reload()
