from django.contrib import admin

from .models import StatusUpdate


@admin.register(StatusUpdate)
class StatusUpdateAdmin(admin.ModelAdmin):
    list_display = ("status", "recipient_id", "error_code")
    list_filter = ("status",)
    search_fields = ("recipient_id",)


