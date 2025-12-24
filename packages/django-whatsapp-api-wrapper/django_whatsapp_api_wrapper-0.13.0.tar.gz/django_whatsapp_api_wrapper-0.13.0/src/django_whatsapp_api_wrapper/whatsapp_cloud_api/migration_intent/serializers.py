"""
Serializers for Migration Intent API endpoints.
"""

from rest_framework import serializers


# =============================================================================
# REQUEST SERIALIZERS
# =============================================================================


class CreateMigrationIntentSerializer(serializers.Serializer):
    """
    Serializer for creating a migration intent.

    Example request:
        {
            "source_waba_id": "123456789",
            "destination_waba_id": "987654321",
            "solution_id": "456789123",
            "migration_reason": "Migrating to new solution provider",
            "preserve_data": true,
            "metadata": {"business_approval_id": "approval_123"}
        }
    """

    source_waba_id = serializers.CharField(
        help_text="The WABA ID to migrate from"
    )
    destination_waba_id = serializers.CharField(
        help_text="The target WABA ID to migrate to"
    )
    solution_id = serializers.CharField(
        help_text="The destination multi-partner solution ID"
    )
    migration_reason = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Optional reason for the migration",
    )
    preserve_data = serializers.BooleanField(
        default=True,
        help_text="Whether to preserve data during migration",
    )
    metadata = serializers.DictField(
        required=False,
        allow_null=True,
        help_text="Optional additional metadata for the migration",
    )


class SetSolutionMigrationIntentSerializer(serializers.Serializer):
    """
    Serializer for the legacy set_solution_migration_intent endpoint.

    Example request:
        {
            "waba_id": "123456789",
            "solution_id": "456789123"
        }
    """

    waba_id = serializers.CharField(
        help_text="The WABA ID to mark for migration"
    )
    solution_id = serializers.CharField(
        help_text="The destination multi-partner solution ID"
    )


class GetMigrationIntentQuerySerializer(serializers.Serializer):
    """
    Serializer for query parameters when getting migration intent.
    """

    fields = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Comma-separated list of fields to retrieve",
    )


# =============================================================================
# RESPONSE SERIALIZERS
# =============================================================================


class WabaInfoSerializer(serializers.Serializer):
    """Serializer for WABA information in migration intent responses."""

    id = serializers.CharField()
    name = serializers.CharField(required=False)
    status = serializers.CharField(required=False)
    timezone_id = serializers.CharField(required=False)
    message_template_namespace = serializers.CharField(required=False)


class SolutionInfoSerializer(serializers.Serializer):
    """Serializer for solution information in migration intent responses."""

    id = serializers.CharField()
    name = serializers.CharField(required=False)
    partner_id = serializers.CharField(required=False)
    status = serializers.CharField(required=False)


class MigrationIntentResponseSerializer(serializers.Serializer):
    """
    Response serializer for create migration intent.

    Example response:
        {
            "success": true,
            "migration_intent_id": "migration_123456789",
            "status": "PENDING",
            "estimated_completion_time": "2024-12-01T12:00:00Z",
            "approval_required": true,
            "next_steps": [
                "Await business approval",
                "Confirm migration settings",
                "Schedule data transfer"
            ]
        }
    """

    success = serializers.BooleanField()
    migration_intent_id = serializers.CharField()
    status = serializers.CharField(
        help_text="Status: PENDING, APPROVED, IN_PROGRESS, COMPLETED, FAILED"
    )
    estimated_completion_time = serializers.DateTimeField(required=False)
    approval_required = serializers.BooleanField(required=False)
    next_steps = serializers.ListField(
        child=serializers.CharField(),
        required=False,
    )


class MigrationIntentStatusSerializer(serializers.Serializer):
    """
    Response serializer for get migration intent status.

    Example response:
        {
            "id": "1234567890123456",
            "waba": {
                "id": "1234567890123456",
                "name": "Source Business Account",
                "status": "ACTIVE"
            },
            "destination_waba": {
                "id": "2345678901234567",
                "name": "Destination Business Account",
                "status": "ACTIVE"
            },
            "solution": {
                "id": "3456789012345678",
                "name": "My Business Solution",
                "status": "ACTIVE"
            },
            "status": "PENDING",
            "created_time": "2024-01-15T10:30:00Z",
            "updated_time": "2024-01-15T14:45:00Z"
        }
    """

    id = serializers.CharField()
    waba = WabaInfoSerializer(required=False)
    destination_waba = WabaInfoSerializer(required=False)
    solution = SolutionInfoSerializer(required=False)
    status = serializers.CharField(
        help_text="Status: PENDING, APPROVED, IN_PROGRESS, COMPLETED, FAILED"
    )
    created_time = serializers.DateTimeField(required=False)
    updated_time = serializers.DateTimeField(required=False)


class LegacyMigrationIntentResponseSerializer(serializers.Serializer):
    """
    Response serializer for legacy set_solution_migration_intent endpoint.

    Example response:
        {
            "id": "migration_123456789"
        }
    """

    id = serializers.CharField()
