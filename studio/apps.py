from django.apps import AppConfig


class StudioConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "studio"

    def ready(self):
        # Importing signals registers the post_save notification handlers.
        from . import signals  # noqa: F401
