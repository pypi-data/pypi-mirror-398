"""
URL patterns for Migration Intent API endpoints.

All endpoints require authentication and tenant context.
"""

from django.urls import path

from .views import (
    CreateMigrationIntentView,
    GetMigrationIntentView,
    SetSolutionMigrationIntentView,
    ListMigrationIntentsView,
)


urlpatterns = [
    # New migration intent endpoints
    path(
        "intent/",
        CreateMigrationIntentView.as_view(),
        name="wa_migration_intent_create",
    ),
    path(
        "intent/<str:migration_intent_id>/",
        GetMigrationIntentView.as_view(),
        name="wa_migration_intent_get",
    ),
    path(
        "intents/",
        ListMigrationIntentsView.as_view(),
        name="wa_migration_intent_list",
    ),
    # Legacy endpoint
    path(
        "set-intent/",
        SetSolutionMigrationIntentView.as_view(),
        name="wa_migration_set_intent",
    ),
]
