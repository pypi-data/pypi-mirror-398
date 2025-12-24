from django.urls import path

from .views import (
    TemplateByIdView,
    TemplateByNameView,
    TemplateListCreateView,
    TemplateNamespaceView,
    TemplateDeleteByIdView,
)


urlpatterns = [
    path("templates/", TemplateListCreateView.as_view(), name="wa_templates_list_create"),
    path("templates/namespace/", TemplateNamespaceView.as_view(), name="wa_templates_namespace"),
    path("templates/by-name/", TemplateByNameView.as_view(), name="wa_templates_by_name"),
    path("templates/delete-by-id/", TemplateDeleteByIdView.as_view(), name="wa_templates_delete_by_id"),
    path("templates/<str:template_id>/", TemplateByIdView.as_view(), name="wa_template_by_id"),
]


