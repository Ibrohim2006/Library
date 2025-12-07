from django.apps import AppConfig


class LibraryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'library'
    verbose_name = 'Library Management'

    def ready(self):
        """
        Import signals when app is ready.
        This ensures automatic counter updates work.
        """
        import library.signals  # noqa