from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.urls import path, reverse
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.apps import apps


class ModernAdminSite(admin.AdminSite):
    site_header = getattr(settings, "MODERN_ADMIN_SITE_HEADER", _("Modern Django Administration"))
    site_title = getattr(settings, "MODERN_ADMIN_SITE_TITLE", _("Django Admin"))
    index_title = getattr(settings, "MODERN_ADMIN_INDEX_TITLE", _("Welcome to Modern Django Admin"))

    def __init__(self, name="admin"):
        super().__init__(name)
        self._sync_registry()

    def _sync_registry(self):
        try:
            for model, model_admin in admin.site._registry.items():
                if model not in self._registry:
                    try:
                        admin_class = type(model_admin)
                        if admin_class != admin.ModelAdmin:
                            self.register(model, admin_class)
                    except (TypeError, ValueError, AttributeError):
                        pass
        except (AttributeError, RuntimeError):
            pass

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path("global-search/", self.global_search_view, name="global_search"),
            path("dashboard-data/", self.dashboard_data_view, name="dashboard_data"),
        ]
        return custom_urls + urls

    @login_required
    @require_http_methods(["GET"])
    def global_search_view(self, request):
        if not getattr(settings, "MODERN_ADMIN_GLOBAL_SEARCH_ENABLED", True):
            return JsonResponse({"error": "Global search is disabled"}, status=403)

        query = request.GET.get("q", "").strip()
        if not query or len(query) < 2:
            return JsonResponse({"results": []})

        results = []
        whitelist = getattr(settings, "MODERN_ADMIN_GLOBAL_SEARCH_MODELS_WHITELIST", None)

        for model in apps.get_models():
            app_label = model._meta.app_label
            model_name = model._meta.model_name

            if whitelist and f"{app_label}.{model_name}" not in whitelist:
                continue

            if not self.has_view_permission(request, model):
                continue

            if model not in self._registry:
                continue

            model_admin = self._registry[model]
            search_fields = getattr(model_admin, "search_fields", [])

            if not search_fields:
                continue

            q_objects = Q()
            for field in search_fields:
                q_objects |= Q(**{f"{field}__icontains": query})

            try:
                queryset = model_admin.get_queryset(request).filter(q_objects)[:10]
                for obj in queryset:
                    try:
                        change_url = reverse(f"{self.name}:{app_label}_{model_name}_change", args=[obj.pk])
                    except Exception:
                        change_url = f"/admin/{app_label}/{model_name}/{obj.pk}/change/"
                    results.append({
                        "app": app_label,
                        "model": model_name,
                        "model_verbose": model._meta.verbose_name,
                        "object_id": str(obj.pk),
                        "object_str": str(obj),
                        "url": change_url,
                    })
            except (AttributeError, ValueError, TypeError):
                continue

        return JsonResponse({"results": results})

    @login_required
    @require_http_methods(["GET"])
    def dashboard_data_view(self, request):
        widgets_config = getattr(settings, "MODERN_ADMIN_DASHBOARD_WIDGETS", [])
        data = {
            "widgets": [],
            "recent_actions": [],
        }

        from django.contrib.admin.models import LogEntry
        recent_actions = LogEntry.objects.select_related("user", "content_type").order_by("-action_time")[:10]
        for action in recent_actions:
            data["recent_actions"].append({
                "action_time": action.action_time.isoformat(),
                "user": action.user.get_full_name() or action.user.username,
                "content_type": action.content_type.model,
                "object_repr": action.object_repr,
                "action_flag": action.get_action_flag_display(),
                "change_message": action.change_message,
            })

        for widget_config in widgets_config:
            widget_type = widget_config.get("type", "count")
            if widget_type == "count":
                app_label = widget_config.get("app_label")
                model_name = widget_config.get("model_name")
                if app_label and model_name:
                    try:
                        model = apps.get_model(app_label, model_name)
                        if self.has_view_permission(request, model):
                            count = model.objects.count()
                            data["widgets"].append({
                                "type": "count",
                                "title": widget_config.get("title", model._meta.verbose_name_plural),
                                "count": count,
                                "url": f"/admin/{app_label}/{model_name}/",
                            })
                    except (LookupError, AttributeError):
                        pass

        return JsonResponse(data)


modern_admin_site = ModernAdminSite(name="modern_admin")

