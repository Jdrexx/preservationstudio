from django.apps import AppConfig


class StudioConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "studio"

    def ready(self):
        # Importing signals registers the post_save notification handlers;
        # checks registers the boot-time validation of the email config.
        from . import checks, signals  # noqa: F401
