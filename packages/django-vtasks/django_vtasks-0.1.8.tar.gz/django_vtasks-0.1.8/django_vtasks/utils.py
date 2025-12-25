UNNEEDED_APPS = [
    "django.contrib.admin",
    "django.contrib.staticfiles",
    "django.contrib.sessions",
    "django.contrib.messages",
    "debug_toolbar",
]


def prune_installed_apps(installed_apps: list[str]) -> list[str]:
    """Reduce worker memory usage by removing some apps"""
    return [app for app in installed_apps if app not in UNNEEDED_APPS]
