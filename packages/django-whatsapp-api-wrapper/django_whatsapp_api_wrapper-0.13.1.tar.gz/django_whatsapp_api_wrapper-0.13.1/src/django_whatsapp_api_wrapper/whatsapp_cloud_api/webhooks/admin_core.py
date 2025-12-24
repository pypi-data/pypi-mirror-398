from django.contrib import admin

from .models import WebhookEvent, WhatsAppContact, ConversationInfo


@admin.register(WebhookEvent)
class WebhookEventAdmin(admin.ModelAdmin):
    list_display = ("event_kind", "subtype", "wamid", "from_wa_id", "phone_number_id", "event_timestamp")
    list_filter = ("event_kind", "subtype", "phone_number_id")
    search_fields = ("wamid", "from_wa_id")
    readonly_fields = ("raw_payload",)


admin.site.register(WhatsAppContact)
admin.site.register(ConversationInfo)


