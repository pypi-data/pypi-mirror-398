from django.db import models


class WhatsAppContact(models.Model):
    wa_id = models.CharField(max_length=32, unique=True, db_index=True)
    profile_name = models.CharField(max_length=255, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "django_whatsapp_api_wrapper"
        verbose_name = "WhatsApp Contact"
        verbose_name_plural = "WhatsApp Contacts"

    def __str__(self) -> str:
        return f"{self.profile_name or ''} ({self.wa_id})".strip()


class ConversationInfo(models.Model):
    conversation_id = models.CharField(max_length=64, unique=True, db_index=True)
    origin_type = models.CharField(max_length=64, null=True, blank=True)
    expiration_timestamp = models.DateTimeField(null=True, blank=True)
    pricing_model = models.CharField(max_length=32, null=True, blank=True)
    category = models.CharField(max_length=64, null=True, blank=True)
    billable = models.BooleanField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "django_whatsapp_api_wrapper"
        verbose_name = "Conversation Info"
        verbose_name_plural = "Conversation Infos"

    def __str__(self) -> str:
        return self.conversation_id


class WebhookEvent(models.Model):
    KIND_MESSAGE = "message"
    KIND_STATUS = "status"
    KIND_WABA = "waba"
    KIND_ACCOUNT_UPDATE = "account_update"
    KIND_UNKNOWN = "unknown"
    KIND_CHOICES = [
        (KIND_MESSAGE, "Message"),
        (KIND_STATUS, "Status"),
        (KIND_WABA, "WABA"),
        (KIND_ACCOUNT_UPDATE, "Account Update"),
        (KIND_UNKNOWN, "Unknown"),
    ]

    # Common envelope fields
    object = models.CharField(max_length=64, null=True, blank=True)
    entry_id = models.CharField(max_length=128, null=True, blank=True)
    field = models.CharField(max_length=64, null=True, blank=True)

    phone_number_id = models.CharField(max_length=64, null=True, blank=True, db_index=True)
    display_phone_number = models.CharField(max_length=32, null=True, blank=True)

    # Event identifiers
    event_kind = models.CharField(max_length=16, choices=KIND_CHOICES, db_index=True)
    subtype = models.CharField(max_length=32, null=True, blank=True, db_index=True)
    wamid = models.CharField(max_length=128, null=True, blank=True, db_index=True)
    from_wa_id = models.CharField(max_length=32, null=True, blank=True, db_index=True)

    # Link to owning WABA when applicable (WABA webhooks)
    waba = models.ForeignKey(
        "django_whatsapp_api_wrapper.WhatsAppBusinessAccount",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="events",
        db_index=True,
    )

    event_timestamp = models.DateTimeField(null=True, blank=True, db_index=True)
    webhook_received_at = models.DateTimeField(auto_now_add=True)

    raw_payload = models.JSONField()

    class Meta:
        app_label = "django_whatsapp_api_wrapper"
        verbose_name = "Webhook Event"
        verbose_name_plural = "Webhook Events"
        indexes = [
            models.Index(fields=["wamid"]),
            models.Index(fields=["event_kind", "subtype"]),
            models.Index(fields=["event_timestamp"]),
            models.Index(fields=["phone_number_id"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["wamid", "event_kind", "subtype"],
                name="uniq_event_wamid_kind_subtype",
                deferrable=models.Deferrable.DEFERRED,
            )
        ]

    def __str__(self) -> str:
        return f"{self.event_kind}:{self.subtype or '-'}:{self.wamid or '-'}"


