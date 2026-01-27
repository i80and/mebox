from django.apps import AppConfig


class WikiConfig(AppConfig):
    name = "wiki"

    def ready(self):
        # Import signals when the app is ready
        pass
