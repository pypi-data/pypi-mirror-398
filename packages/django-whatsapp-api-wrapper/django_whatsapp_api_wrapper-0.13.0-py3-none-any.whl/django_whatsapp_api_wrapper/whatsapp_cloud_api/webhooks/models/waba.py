from django.db import models

from .core import WebhookEvent


class WhatsAppBusinessAccount(models.Model):
    waba_id = models.CharField(max_length=64, unique=True, db_index=True)
    owner_business_id = models.CharField(max_length=64, null=True, blank=True)
    name = models.CharField(max_length=255, null=True, blank=True)
    meta = models.JSONField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "django_whatsapp_api_wrapper"
        verbose_name = "WABA"
        verbose_name_plural = "WABAs"

    def __str__(self) -> str:
        return self.waba_id


class WabaAccountUpdate(models.Model):
    event = models.OneToOneField(
        WebhookEvent, on_delete=models.CASCADE, related_name="waba_account_update"
    )
    phone_number = models.CharField(max_length=32, null=True, blank=True, db_index=True)
    event_name = models.CharField(max_length=64, null=True, blank=True, db_index=True)
    business_verification_status = models.CharField(max_length=64, null=True, blank=True)

    ban_info = models.JSONField(null=True, blank=True)
    violation_info = models.JSONField(null=True, blank=True)
    lock_info = models.JSONField(null=True, blank=True)
    restriction_info = models.JSONField(null=True, blank=True)
    partner_client_certification_info = models.JSONField(null=True, blank=True)
    waba_info = models.JSONField(null=True, blank=True)
    auth_international_rate_eligibility = models.JSONField(null=True, blank=True)
    volume_tier_info = models.JSONField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "django_whatsapp_api_wrapper"
        verbose_name = "WABA Account Update"
        verbose_name_plural = "WABA Account Updates"


class WabaGenericEvent(models.Model):
    event = models.OneToOneField(
        WebhookEvent, on_delete=models.CASCADE, related_name="waba_generic"
    )
    value = models.JSONField()

    class Meta:
        app_label = "django_whatsapp_api_wrapper"
        verbose_name = "WABA Generic Event"
        verbose_name_plural = "WABA Generic Events"


class WabaHistoryBatch(models.Model):
    event = models.OneToOneField(
        WebhookEvent, on_delete=models.CASCADE, related_name="waba_history_batch"
    )
    # Copy of metadata for convenience (from value.metadata)
    display_phone_number = models.CharField(max_length=32, null=True, blank=True)
    phone_number_id = models.CharField(max_length=64, null=True, blank=True, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "django_whatsapp_api_wrapper"
        verbose_name = "WABA History Batch"
        verbose_name_plural = "WABA History Batches"


class WabaHistoryItem(models.Model):
    batch = models.ForeignKey(WabaHistoryBatch, on_delete=models.CASCADE, related_name="items")
    phase = models.IntegerField(null=True, blank=True)
    chunk_order = models.IntegerField(null=True, blank=True)
    progress = models.IntegerField(null=True, blank=True)
    errors = models.JSONField(null=True, blank=True)

    class Meta:
        app_label = "django_whatsapp_api_wrapper"
        verbose_name = "WABA History Item"
        verbose_name_plural = "WABA History Items"


class WabaHistoryThread(models.Model):
    item = models.ForeignKey(WabaHistoryItem, on_delete=models.CASCADE, related_name="threads")
    whatsapp_user_phone = models.CharField(max_length=32, db_index=True)

    class Meta:
        app_label = "django_whatsapp_api_wrapper"
        verbose_name = "WABA History Thread"
        verbose_name_plural = "WABA History Threads"


class WabaHistoryMessage(models.Model):
    thread = models.ForeignKey(WabaHistoryThread, on_delete=models.CASCADE, related_name="messages")
    from_number = models.CharField(max_length=32)
    to_number = models.CharField(max_length=32, null=True, blank=True)
    wamid = models.CharField(max_length=128, db_index=True)
    device_timestamp = models.DateTimeField(null=True, blank=True, db_index=True)
    msg_type = models.CharField(max_length=64)
    content = models.JSONField(null=True, blank=True)
    status = models.CharField(max_length=32, null=True, blank=True)

    class Meta:
        app_label = "django_whatsapp_api_wrapper"
        verbose_name = "WABA History Message"
        verbose_name_plural = "WABA History Messages"
        indexes = [
            models.Index(fields=["wamid"]),
            models.Index(fields=["device_timestamp"]),
        ]


class WabaHistoryAssetMessage(models.Model):
    event = models.ForeignKey(WebhookEvent, on_delete=models.CASCADE, related_name="waba_history_assets")
    from_number = models.CharField(max_length=32)
    wamid = models.CharField(max_length=128, db_index=True)
    device_timestamp = models.DateTimeField(null=True, blank=True, db_index=True)
    msg_type = models.CharField(max_length=64)
    content = models.JSONField(null=True, blank=True)

    class Meta:
        app_label = "django_whatsapp_api_wrapper"
        verbose_name = "WABA History Asset Message"
        verbose_name_plural = "WABA History Asset Messages"
        indexes = [
            models.Index(fields=["wamid"]),
            models.Index(fields=["device_timestamp"]),
        ]


class WabaHistoryInbox(models.Model):
    STATUS_PENDING = "PENDING"
    STATUS_PROCESSING = "PROCESSING"
    STATUS_DONE = "DONE"
    STATUS_FAILED = "FAILED"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_PROCESSING, "Processing"),
        (STATUS_DONE, "Done"),
        (STATUS_FAILED, "Failed"),
    ]

    waba = models.ForeignKey(
        "django_whatsapp_api_wrapper.WhatsAppBusinessAccount",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="history_inbox_items",
    )
    entry_id = models.CharField(max_length=128, db_index=True)
    phone_number_id = models.CharField(max_length=64, null=True, blank=True, db_index=True)
    display_phone_number = models.CharField(max_length=32, null=True, blank=True)
    event_timestamp = models.DateTimeField(null=True, blank=True, db_index=True)

    payload = models.JSONField()  # full change.value RAW

    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_PENDING, db_index=True)
    attempts = models.IntegerField(default=0)
    last_error = models.TextField(null=True, blank=True)

    dedupe_key = models.CharField(max_length=128, unique=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "django_whatsapp_api_wrapper"
        verbose_name = "WABA History Inbox"
        verbose_name_plural = "WABA History Inbox"
        indexes = [
            models.Index(fields=["status", "created_at"]),
        ]


class WabaSmbStateSyncItem(models.Model):
    event = models.ForeignKey(WebhookEvent, on_delete=models.CASCADE, related_name="waba_smb_state_sync_items")
    item_type = models.CharField(max_length=32, null=True, blank=True)
    contact_full_name = models.CharField(max_length=255, null=True, blank=True)
    contact_first_name = models.CharField(max_length=255, null=True, blank=True)
    contact_phone_number = models.CharField(max_length=32, db_index=True)
    action = models.CharField(max_length=16)
    change_timestamp = models.DateTimeField(null=True, blank=True, db_index=True)

    class Meta:
        app_label = "django_whatsapp_api_wrapper"
        verbose_name = "WABA SMB State Sync Item"
        verbose_name_plural = "WABA SMB State Sync Items"
        indexes = [
            models.Index(fields=["contact_phone_number"]),
            models.Index(fields=["change_timestamp"]),
        ]


class WabaSmbMessageEcho(models.Model):
    event = models.ForeignKey(WebhookEvent, on_delete=models.CASCADE, related_name="waba_smb_message_echoes")
    from_number = models.CharField(max_length=32)
    to_number = models.CharField(max_length=32)
    wamid = models.CharField(max_length=128, db_index=True)
    webhook_timestamp = models.DateTimeField(null=True, blank=True, db_index=True)
    msg_type = models.CharField(max_length=64)
    content = models.JSONField(null=True, blank=True)

    class Meta:
        app_label = "django_whatsapp_api_wrapper"
        verbose_name = "WABA SMB Message Echo"
        verbose_name_plural = "WABA SMB Message Echoes"
        indexes = [
            models.Index(fields=["wamid"]),
            models.Index(fields=["webhook_timestamp"]),
        ]


