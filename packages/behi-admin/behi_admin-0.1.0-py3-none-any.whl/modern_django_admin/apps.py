from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ModernDjangoAdminConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "modern_django_admin"
    verbose_name = _("Modern Django Admin")

    def ready(self):
        try:
            from django.contrib.admin.sites import site
            from modern_django_admin.admin import modern_admin_site
            
            for model, model_admin in site._registry.items():
                if model not in modern_admin_site._registry:
                    try:
                        admin_class = type(model_admin)
                        modern_admin_site.register(model, admin_class)
                    except Exception:
                        pass
        except ImportError:
            pass

