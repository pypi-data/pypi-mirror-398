from django.db import models

from .core import WebhookEvent, ConversationInfo


class StatusUpdate(models.Model):
    STATUS_SENT = "sent"
    STATUS_DELIVERED = "delivered"
    STATUS_READ = "read"
    STATUS_FAILED = "failed"
    STATUS_CHOICES = [
        (STATUS_SENT, "Sent"),
        (STATUS_DELIVERED, "Delivered"),
        (STATUS_READ, "Read"),
        (STATUS_FAILED, "Failed"),
    ]

    event = models.OneToOneField(WebhookEvent, on_delete=models.CASCADE, related_name="status_update")
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, db_index=True)
    recipient_id = models.CharField(max_length=32, null=True, blank=True, db_index=True)

    # Error details for failed statuses
    error_code = models.IntegerField(null=True, blank=True)
    error_title = models.CharField(max_length=255, null=True, blank=True)
    error_message = models.CharField(max_length=512, null=True, blank=True)
    error_details = models.JSONField(null=True, blank=True)

    # Conversation / pricing info
    conversation = models.ForeignKey(ConversationInfo, on_delete=models.SET_NULL, null=True, blank=True, related_name="status_updates")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "django_whatsapp_api_wrapper"
        verbose_name = "Status Update"
        verbose_name_plural = "Status Updates"


