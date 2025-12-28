from django.conf import settings

# Conditionally register Valkey admin
valkey_backend_path = "django_vtasks.backends.valkey.ValkeyTaskBackend"
is_valkey_configured = any(
    backend_config.get("BACKEND") == valkey_backend_path
    for backend_config in getattr(settings, "TASKS", {}).values()
)

if is_valkey_configured:
    from .admin_valkey import *  # noqa: F403, F401


# Conditionally register DB admin
if "django_vtasks.db" in settings.INSTALLED_APPS:
    from .db.admin import *  # noqa: F403, F401
