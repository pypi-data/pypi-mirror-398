from django.db import models

class MetaApp(models.Model):
    """
    Modelo para armazenar informações de um Aplicativo Meta
    """
    name = models.CharField(max_length=50)
    app_id = models.CharField(max_length=50)
    app_secret = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class WhatsAppCloudApiBusiness(models.Model):
    """
    Modelo para armazenar informações da conta WhatsApp Business API
    """
    type = models.CharField(
        max_length=20,
        verbose_name="Type",
        help_text="Tipo de conta WhatsApp Business",
        choices=[
            ('cloud_api', 'Cloud API'),
            ('coexistence', 'Coexistence')
        ],
        default='cloud_api'
    )
    
    token = models.TextField(
        verbose_name="Token",
        help_text="Token de acesso da API do WhatsApp Business"
    )
    api_version = models.CharField(
        max_length=20,
        verbose_name="API Version",
        help_text="Versão da API"
    )
    phone_number_id = models.CharField(
        max_length=50,
        verbose_name="Phone Number ID",
        help_text="ID do número de telefone da empresa no WhatsApp Business",
        null=True,
        blank=True
    )

    waba_id = models.CharField(
        max_length=50,
        verbose_name="WABA ID",
        help_text="ID da conta WhatsApp Business"
    )
    business_id = models.CharField(
        max_length=50,
        verbose_name="Business Portfolio ID",
        help_text="ID do portfólio de negócios"
    )
    phone_number = models.CharField(
        max_length=20,
        verbose_name="Número de Telefone",
        help_text="Número de telefone da empresa",
        null=True,
        blank=True
    )
    
    verify_token = models.CharField(
        max_length=100,
        verbose_name="Verify Token",
        help_text="Token de verificação do webhook",
        null=True,
        blank=True
    )
    
    code = models.TextField(
        verbose_name="Code",
        help_text="Código retornado pelo Business Callback",
        null=True,
        blank=True
    )
    
    auth_desired_pin = models.CharField(
        max_length=6,
        verbose_name="Auth Desired PIN",
        help_text="PIN de 6 dígitos para verificação em duas etapas do número de telefone da empresa",
        null=True,
        blank=True
    )

    # Multi-tenancy support
    tenant_id = models.IntegerField(
        verbose_name="Tenant ID",
        help_text="ID of the tenant/organization that owns this WhatsApp Business account",
        db_index=True,
        default=1  # Default tenant for single-tenant setups or migrations
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data de Criação"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Data de Atualização"
    )

    class Meta:
        verbose_name = "WhatsApp Business API"
        verbose_name_plural = "WhatsApp Business APIs"
        ordering = ['-created_at']
        unique_together = [('tenant_id', 'phone_number')]
        indexes = [
            models.Index(fields=['tenant_id', 'phone_number']),
        ]

    def __str__(self):
        return f"WhatsApp Business - {self.phone_number or self.waba_id}"


class MigrationIntent(models.Model):
    """
    Tracks migration intents for WABA migrations between multi-partner solutions.

    This model provides audit trail and status tracking for migrations,
    which can take time and may require multiple steps including business approval.
    """

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pendente"
        APPROVED = "APPROVED", "Aprovado"
        IN_PROGRESS = "IN_PROGRESS", "Em Progresso"
        COMPLETED = "COMPLETED", "Concluído"
        FAILED = "FAILED", "Falhou"
        CANCELLED = "CANCELLED", "Cancelado"

    # IDs from Meta
    migration_intent_id = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        verbose_name="Migration Intent ID",
        help_text="ID returned by Meta's API",
    )
    source_waba_id = models.CharField(
        max_length=50,
        db_index=True,
        verbose_name="Source WABA ID",
        help_text="WABA ID being migrated from",
    )
    destination_waba_id = models.CharField(
        max_length=50,
        verbose_name="Destination WABA ID",
        help_text="Target WABA ID (filled after Embedded Signup)",
        blank=True,
        default="",
    )
    solution_id = models.CharField(
        max_length=50,
        verbose_name="Solution ID",
        help_text="Not used for Tech Partners (only for MPS)",
        blank=True,
        default="",
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
        verbose_name="Status",
    )

    # Metadata
    migration_reason = models.TextField(
        blank=True,
        null=True,
        verbose_name="Migration Reason",
    )
    preserve_data = models.BooleanField(
        default=True,
        verbose_name="Preserve Data",
    )
    metadata = models.JSONField(
        blank=True,
        null=True,
        verbose_name="Metadata",
    )

    # API Response
    api_response = models.JSONField(
        blank=True,
        null=True,
        verbose_name="API Response",
        help_text="Complete response from Meta's API",
    )
    estimated_completion_time = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Estimated Completion Time",
    )
    approval_required = models.BooleanField(
        default=True,
        verbose_name="Approval Required",
    )

    # Multi-tenancy
    tenant_id = models.IntegerField(
        db_index=True,
        default=1,
        verbose_name="Tenant ID",
        help_text="ID of the tenant that initiated the migration",
    )

    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created At",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Updated At",
    )
    completed_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Completed At",
    )

    class Meta:
        verbose_name = "Migration Intent"
        verbose_name_plural = "Migration Intents"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["tenant_id", "status"], name="django_what_tenant__1a2b3c_idx"),
            models.Index(fields=["source_waba_id", "status"], name="django_what_source__4d5e6f_idx"),
        ]

    def __str__(self):
        return f"Migration {self.source_waba_id} → {self.destination_waba_id} ({self.status})"

    def mark_completed(self):
        """Mark migration as completed."""
        from django.utils import timezone

        self.status = self.Status.COMPLETED
        self.completed_at = timezone.now()
        self.save(update_fields=["status", "completed_at", "updated_at"])

    def mark_failed(self, error_response: dict = None):
        """Mark migration as failed with optional error details."""
        self.status = self.Status.FAILED
        if error_response:
            self.api_response = error_response
        self.save(update_fields=["status", "api_response", "updated_at"])

    def update_from_api(self, api_response: dict):
        """Update the record based on API response."""
        self.api_response = api_response

        if "status" in api_response:
            self.status = api_response["status"]

        if "estimated_completion_time" in api_response:
            from django.utils.dateparse import parse_datetime

            self.estimated_completion_time = parse_datetime(
                api_response["estimated_completion_time"]
            )

        self.save()
