from django.dispatch import receiver
from django.contrib.admin.sites import site
from django.contrib.admin import ModelAdmin
from modern_django_admin.admin import modern_admin_site


@receiver(site._registry_changed, dispatch_uid="sync_modern_admin")
def sync_to_modern_admin(sender, **kwargs):
    for model, model_admin in site._registry.items():
        if model not in modern_admin_site._registry:
            if isinstance(model_admin, ModelAdmin):
                admin_class = model_admin.__class__
                modern_admin_site.register(model, admin_class)
            else:
                modern_admin_site.register(model, model_admin)

