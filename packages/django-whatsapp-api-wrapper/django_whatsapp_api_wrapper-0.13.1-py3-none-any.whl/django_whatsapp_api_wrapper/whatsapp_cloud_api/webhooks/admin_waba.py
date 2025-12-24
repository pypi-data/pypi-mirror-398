from django.contrib import admin

from .models import (
    WhatsAppBusinessAccount,
    WabaAccountUpdate,
    WabaGenericEvent,
    WabaHistoryBatch,
    WabaHistoryItem,
    WabaHistoryThread,
    WabaHistoryMessage,
    WabaHistoryAssetMessage,
    WabaHistoryInbox,
    WabaSmbStateSyncItem,
    WabaSmbMessageEcho,
)


@admin.register(WhatsAppBusinessAccount)
class WhatsAppBusinessAccountAdmin(admin.ModelAdmin):
    list_display = ("waba_id", "owner_business_id", "name", "created_at")
    search_fields = ("waba_id", "owner_business_id", "name")


@admin.register(WabaAccountUpdate)
class WabaAccountUpdateAdmin(admin.ModelAdmin):
    list_display = (
        "get_subtype",
        "get_waba_id",
        "phone_number",
        "event_name",
        "get_event_timestamp",
    )
    list_filter = ("event_name",)
    search_fields = ("phone_number", "event__entry_id")

    def get_subtype(self, obj):
        return obj.event.subtype

    def get_waba_id(self, obj):
        return obj.event.entry_id

    def get_event_timestamp(self, obj):
        return obj.event.event_timestamp

    get_subtype.short_description = "Subtype"
    get_waba_id.short_description = "WABA ID"
    get_event_timestamp.short_description = "Timestamp"


@admin.register(WabaGenericEvent)
class WabaGenericEventAdmin(admin.ModelAdmin):
    list_display = ("get_subtype", "get_waba_id", "get_event_timestamp")
    search_fields = ("event__entry_id",)

    def get_subtype(self, obj):
        return obj.event.subtype

    def get_waba_id(self, obj):
        return obj.event.entry_id

    def get_event_timestamp(self, obj):
        return obj.event.event_timestamp

    get_subtype.short_description = "Subtype"
    get_waba_id.short_description = "WABA ID"
    get_event_timestamp.short_description = "Timestamp"


@admin.register(WabaHistoryBatch)
class WabaHistoryBatchAdmin(admin.ModelAdmin):
    list_display = ("get_waba_id", "display_phone_number", "phone_number_id", "get_event_timestamp")
    search_fields = ("event__entry_id", "phone_number_id", "display_phone_number")

    def get_waba_id(self, obj):
        return obj.event.entry_id

    def get_event_timestamp(self, obj):
        return obj.event.event_timestamp

    get_waba_id.short_description = "WABA ID"
    get_event_timestamp.short_description = "Timestamp"


@admin.register(WabaHistoryItem)
class WabaHistoryItemAdmin(admin.ModelAdmin):
    list_display = ("batch", "phase", "chunk_order", "progress")
    list_filter = ("phase",)


@admin.register(WabaHistoryThread)
class WabaHistoryThreadAdmin(admin.ModelAdmin):
    list_display = ("item", "whatsapp_user_phone")
    search_fields = ("whatsapp_user_phone",)


@admin.register(WabaHistoryMessage)
class WabaHistoryMessageAdmin(admin.ModelAdmin):
    list_display = ("thread", "wamid", "msg_type", "status", "device_timestamp")
    list_filter = ("msg_type", "status")
    search_fields = ("wamid",)


@admin.register(WabaHistoryAssetMessage)
class WabaHistoryAssetMessageAdmin(admin.ModelAdmin):
    list_display = ("event", "wamid", "msg_type", "device_timestamp")
    list_filter = ("msg_type",)
    search_fields = ("wamid",)


@admin.register(WabaHistoryInbox)
class WabaHistoryInboxAdmin(admin.ModelAdmin):
    list_display = (
        "entry_id",
        "phone_number_id",
        "status",
        "attempts",
        "event_timestamp",
        "created_at",
    )
    list_filter = ("status",)
    search_fields = ("entry_id", "phone_number_id")


@admin.register(WabaSmbStateSyncItem)
class WabaSmbStateSyncItemAdmin(admin.ModelAdmin):
    list_display = (
        "event",
        "item_type",
        "contact_phone_number",
        "action",
        "change_timestamp",
    )
    list_filter = ("action", "item_type")
    search_fields = ("contact_phone_number",)


@admin.register(WabaSmbMessageEcho)
class WabaSmbMessageEchoAdmin(admin.ModelAdmin):
    list_display = ("event", "wamid", "from_number", "to_number", "msg_type", "webhook_timestamp")
    list_filter = ("msg_type",)
    search_fields = ("wamid", "from_number", "to_number")


