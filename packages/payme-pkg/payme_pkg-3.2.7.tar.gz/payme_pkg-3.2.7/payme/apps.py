from django.apps import AppConfig

from payme.licensing import validate_api_key


class PaymeConfig(AppConfig):
    """Payme app config."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'payme'

    def ready(self):
        validate_api_key()
