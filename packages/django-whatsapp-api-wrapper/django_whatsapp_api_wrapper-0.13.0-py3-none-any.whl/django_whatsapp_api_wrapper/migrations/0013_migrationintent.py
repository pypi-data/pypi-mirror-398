# Created manually for MigrationIntent model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("django_whatsapp_api_wrapper", "0012_whatsappcloudapibusiness_tenant_id_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="MigrationIntent",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "migration_intent_id",
                    models.CharField(
                        db_index=True,
                        help_text="ID returned by Meta's API",
                        max_length=50,
                        unique=True,
                        verbose_name="Migration Intent ID",
                    ),
                ),
                (
                    "source_waba_id",
                    models.CharField(
                        db_index=True,
                        help_text="WABA ID being migrated from",
                        max_length=50,
                        verbose_name="Source WABA ID",
                    ),
                ),
                (
                    "destination_waba_id",
                    models.CharField(
                        help_text="Target WABA ID to migrate to",
                        max_length=50,
                        verbose_name="Destination WABA ID",
                    ),
                ),
                (
                    "solution_id",
                    models.CharField(
                        help_text="Destination multi-partner solution ID",
                        max_length=50,
                        verbose_name="Solution ID",
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("PENDING", "Pendente"),
                            ("APPROVED", "Aprovado"),
                            ("IN_PROGRESS", "Em Progresso"),
                            ("COMPLETED", "Concluído"),
                            ("FAILED", "Falhou"),
                            ("CANCELLED", "Cancelado"),
                        ],
                        db_index=True,
                        default="PENDING",
                        max_length=20,
                        verbose_name="Status",
                    ),
                ),
                (
                    "migration_reason",
                    models.TextField(
                        blank=True,
                        null=True,
                        verbose_name="Migration Reason",
                    ),
                ),
                (
                    "preserve_data",
                    models.BooleanField(
                        default=True,
                        verbose_name="Preserve Data",
                    ),
                ),
                (
                    "metadata",
                    models.JSONField(
                        blank=True,
                        null=True,
                        verbose_name="Metadata",
                    ),
                ),
                (
                    "api_response",
                    models.JSONField(
                        blank=True,
                        help_text="Complete response from Meta's API",
                        null=True,
                        verbose_name="API Response",
                    ),
                ),
                (
                    "estimated_completion_time",
                    models.DateTimeField(
                        blank=True,
                        null=True,
                        verbose_name="Estimated Completion Time",
                    ),
                ),
                (
                    "approval_required",
                    models.BooleanField(
                        default=True,
                        verbose_name="Approval Required",
                    ),
                ),
                (
                    "tenant_id",
                    models.IntegerField(
                        db_index=True,
                        default=1,
                        help_text="ID of the tenant that initiated the migration",
                        verbose_name="Tenant ID",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        verbose_name="Created At",
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True,
                        verbose_name="Updated At",
                    ),
                ),
                (
                    "completed_at",
                    models.DateTimeField(
                        blank=True,
                        null=True,
                        verbose_name="Completed At",
                    ),
                ),
            ],
            options={
                "verbose_name": "Migration Intent",
                "verbose_name_plural": "Migration Intents",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="migrationintent",
            index=models.Index(
                fields=["tenant_id", "status"],
                name="django_what_tenant__1a2b3c_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="migrationintent",
            index=models.Index(
                fields=["source_waba_id", "status"],
                name="django_what_source__4d5e6f_idx",
            ),
        ),
    ]
