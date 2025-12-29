from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

class DjangoFullKitConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "full_models"
    verbose_name = _("full models")
