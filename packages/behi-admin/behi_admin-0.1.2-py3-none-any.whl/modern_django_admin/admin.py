from django.apps import apps
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.db.models import Q
from django.http import JsonResponse
from django.urls import path, reverse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods


class ModernAdminSite(admin.AdminSite):
    site_header = getattr(settings, "MODERN_ADMIN_SITE_HEADER", _("Modern Django Administration"))
    site_title = getattr(settings, "MODERN_ADMIN_SITE_TITLE", _("Django Admin"))
    index_title = getattr(settings, "MODERN_ADMIN_INDEX_TITLE", _("Welcome to Modern Django Admin"))

    def __init__(self, name="modern_admin"):
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
            path("global-search/", self.admin_view(self.global_search_view), name="global_search"),
            path("dashboard-data/", self.admin_view(self.dashboard_data_view), name="dashboard_data"),
        ]
        return custom_urls + urls

    @require_http_methods(["GET"])
    def global_search_view(self, request):
        if not getattr(settings, "MODERN_ADMIN_GLOBAL_SEARCH_ENABLED", True):
            return JsonResponse({"error": "Global search is disabled"}, status=403)

        query = request.GET.get("q", "").strip()
        min_query_len = getattr(settings, "MODERN_ADMIN_GLOBAL_SEARCH_MIN_QUERY_LEN", 2)
        max_results_per_model = getattr(settings, "MODERN_ADMIN_GLOBAL_SEARCH_MAX_RESULTS_PER_MODEL", 10)

        if not query or len(query) < min_query_len:
            return JsonResponse({"results": []})

        results = []
        whitelist = getattr(settings, "MODERN_ADMIN_GLOBAL_SEARCH_MODELS_WHITELIST", None)
        blacklist = getattr(settings, "MODERN_ADMIN_GLOBAL_SEARCH_MODELS_BLACKLIST", None)

        for model in apps.get_models():
            app_label = model._meta.app_label
            model_name = model._meta.model_name
            model_key = f"{app_label}.{model_name}"

            if whitelist and model_key not in whitelist:
                continue

            if blacklist and model_key in blacklist:
                continue

            if model not in self._registry:
                continue

            model_admin = self._registry[model]
            if not model_admin.has_view_permission(request):
                continue
            search_fields = getattr(model_admin, "search_fields", [])

            if not search_fields:
                continue

            q_objects = Q()
            for field in search_fields:
                q_objects |= Q(**{f"{field}__icontains": query})

            try:
                queryset = model_admin.get_queryset(request).filter(q_objects)[:max_results_per_model]
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

    @require_http_methods(["GET"])
    def dashboard_data_view(self, request):
        from modern_django_admin.widgets import RecentActionsWidget, WidgetRegistry

        widgets_config = getattr(settings, "MODERN_ADMIN_DASHBOARD_WIDGETS", [])
        data = {
            "widgets": [],
            "recent_actions": [],
        }

        for widget_config in widgets_config:
            widget_type = widget_config.get("type", "count")
            widget_class = WidgetRegistry.get_widget_class(widget_type)

            if widget_class:
                try:
                    widget = widget_class(widget_config)
                    widget_data = widget.render(request, self)
                    if widget_data:
                        data["widgets"].append(widget_data)
                except Exception:
                    continue
            else:
                if widget_type == "count":
                    app_label = widget_config.get("app_label")
                    model_name = widget_config.get("model_name")
                    if app_label and model_name:
                        try:
                            model = apps.get_model(app_label, model_name)
                            if model and model in self._registry:
                                model_admin = self._registry[model]
                                if model_admin.has_view_permission(request):
                                    count = model.objects.count()
                                    data["widgets"].append({
                                        "type": "count",
                                        "title": widget_config.get("title", model._meta.verbose_name_plural),
                                        "data": {
                                            "count": count,
                                            "url": f"/admin/{app_label}/{model_name}/",
                                        },
                                    })
                        except (LookupError, AttributeError):
                            pass

        try:
            recent_actions_widget = RecentActionsWidget()
            recent_actions_data = recent_actions_widget.render(request, self)
            if recent_actions_data and recent_actions_data.get("data"):
                data["recent_actions"] = recent_actions_data["data"]
        except Exception:
            pass

        return JsonResponse(data)


modern_admin_site = ModernAdminSite(name="modern_admin")

