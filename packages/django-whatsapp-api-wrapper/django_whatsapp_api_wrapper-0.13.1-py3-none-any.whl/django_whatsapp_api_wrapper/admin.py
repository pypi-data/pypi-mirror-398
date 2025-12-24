import logging

from django.contrib import admin
from .models import WhatsAppCloudApiBusiness, MetaApp, MigrationIntent


# Register your models here.
admin.site.register(WhatsAppCloudApiBusiness)
admin.site.register(MetaApp)


@admin.register(MigrationIntent)
class MigrationIntentAdmin(admin.ModelAdmin):
    list_display = [
        "migration_intent_id",
        "source_waba_id",
        "destination_waba_id",
        "status",
        "tenant_id",
        "created_at",
    ]
    list_filter = ["status", "tenant_id", "created_at"]
    search_fields = [
        "migration_intent_id",
        "source_waba_id",
        "destination_waba_id",
        "solution_id",
    ]
    readonly_fields = ["created_at", "updated_at", "completed_at"]
    ordering = ["-created_at"]

# Import webhooks admin registrations so they are discovered
try:
    from .whatsapp_cloud_api.webhooks import admin as webhooks_admin  # noqa: F401
except Exception:
    logging.getLogger(__name__).exception("Failed to import webhooks admin")


    

    
