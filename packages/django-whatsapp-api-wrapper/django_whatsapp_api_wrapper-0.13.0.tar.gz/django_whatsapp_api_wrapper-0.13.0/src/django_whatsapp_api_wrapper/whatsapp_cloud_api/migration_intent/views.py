"""
DRF Views for Migration Intent API operations.

All views use TenantMixin for multi-tenancy support and BaseAuthenticatedAPIView
for consistent authentication handling.
"""

import logging
from rest_framework.response import Response
from rest_framework import status

from ...authentication.base import BaseAuthenticatedAPIView
from ...decorators import require_tenant
from ...mixins import TenantMixin
from .client import MigrationIntentAPI
from .serializers import (
    CreateMigrationIntentSerializer,
    SetSolutionMigrationIntentSerializer,
    GetMigrationIntentQuerySerializer,
)

logger = logging.getLogger(__name__)


class MigrationIntentMixin(TenantMixin):
    """
    Extended TenantMixin for Migration Intent API.

    Provides helper method to get MigrationIntentAPI instance
    configured with tenant credentials.
    """

    def get_migration_intent_api(self, request) -> MigrationIntentAPI:
        """
        Get MigrationIntentAPI instance configured for tenant.

        Args:
            request: DRF request object

        Returns:
            MigrationIntentAPI instance configured with tenant credentials
        """
        token, waba_id, api_version = self.get_tenant_credentials(request)
        return MigrationIntentAPI(token=token, api_version=api_version)


class CreateMigrationIntentView(MigrationIntentMixin, BaseAuthenticatedAPIView):
    """
    POST: Create a migration intent for WABA migration.

    Creates a new migration intent to initiate the process of migrating
    a WhatsApp Business Account from one multi-partner solution to another.

    Request body:
        {
            "source_waba_id": "123456789",
            "destination_waba_id": "987654321",
            "solution_id": "456789123",
            "migration_reason": "Migrating to new provider",
            "preserve_data": true,
            "metadata": {}
        }

    Response:
        {
            "success": true,
            "migration_intent_id": "migration_123456789",
            "status": "PENDING",
            "approval_required": true,
            "next_steps": [...]
        }
    """

    @require_tenant
    def post(self, request):
        serializer = CreateMigrationIntentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        try:
            api = self.get_migration_intent_api(request)
            response = api.create_migration_intent(
                source_waba_id=data["source_waba_id"],
                destination_waba_id=data["destination_waba_id"],
                solution_id=data["solution_id"],
                migration_reason=data.get("migration_reason"),
                preserve_data=data.get("preserve_data", True),
                metadata=data.get("metadata"),
            )

            result = response.json()

            if response.ok:
                logger.info(
                    "Migration intent created successfully",
                    extra={
                        "tenant_id": request.tenant_id,
                        "source_waba_id": data["source_waba_id"],
                        "destination_waba_id": data["destination_waba_id"],
                        "migration_intent_id": result.get("migration_intent_id"),
                    },
                )

                # Persist to database
                self._save_migration_intent(request, data, result)

            return Response(result, status=response.status_code)

        except Exception as e:
            logger.exception("Failed to create migration intent")
            return Response(
                {"success": False, "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def _save_migration_intent(self, request, data: dict, result: dict):
        """Save migration intent to database for tracking."""
        try:
            from ...models import MigrationIntent

            MigrationIntent.objects.create(
                migration_intent_id=result.get("migration_intent_id", result.get("id")),
                source_waba_id=data["source_waba_id"],
                destination_waba_id=data["destination_waba_id"],
                solution_id=data["solution_id"],
                migration_reason=data.get("migration_reason"),
                preserve_data=data.get("preserve_data", True),
                metadata=data.get("metadata"),
                api_response=result,
                status=result.get("status", "PENDING"),
                approval_required=result.get("approval_required", True),
                tenant_id=request.tenant_id,
            )
        except Exception as e:
            logger.warning(
                f"Failed to save migration intent to database: {e}",
                extra={"tenant_id": request.tenant_id},
            )


class GetMigrationIntentView(MigrationIntentMixin, BaseAuthenticatedAPIView):
    """
    GET: Get migration intent status and details.

    Retrieves comprehensive information about a migration intent,
    including current status, source and destination WABA details,
    solution information, and operation history.

    URL params:
        migration_intent_id: The ID of the migration intent

    Query params:
        fields: Optional comma-separated list of fields to retrieve

    Response:
        {
            "id": "migration_123456789",
            "waba": {...},
            "destination_waba": {...},
            "solution": {...},
            "status": "PENDING",
            "created_time": "...",
            "updated_time": "..."
        }
    """

    @require_tenant
    def get(self, request, migration_intent_id: str):
        serializer = GetMigrationIntentQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        fields = serializer.validated_data.get("fields")

        try:
            api = self.get_migration_intent_api(request)
            response = api.get_migration_intent(migration_intent_id, fields)

            result = response.json()

            if response.ok:
                # Update local database record
                self._update_migration_intent(migration_intent_id, result)

            return Response(result, status=response.status_code)

        except Exception as e:
            logger.exception("Failed to get migration intent")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def _update_migration_intent(self, migration_intent_id: str, result: dict):
        """Update local database record with latest status."""
        try:
            from ...models import MigrationIntent

            intent = MigrationIntent.objects.filter(
                migration_intent_id=migration_intent_id
            ).first()

            if intent:
                intent.update_from_api(result)
        except Exception as e:
            logger.warning(
                f"Failed to update migration intent in database: {e}",
                extra={"migration_intent_id": migration_intent_id},
            )


class SetSolutionMigrationIntentView(MigrationIntentMixin, BaseAuthenticatedAPIView):
    """
    POST: Mark WABA for migration (legacy endpoint).

    This is the older endpoint for marking a WABA for migration.
    Use CreateMigrationIntentView for the newer API.

    Request body:
        {
            "waba_id": "123456789",
            "solution_id": "456789123"
        }

    Response:
        {
            "id": "migration_123456789"
        }
    """

    @require_tenant
    def post(self, request):
        serializer = SetSolutionMigrationIntentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        try:
            api = self.get_migration_intent_api(request)
            response = api.set_solution_migration_intent(
                waba_id=data["waba_id"],
                solution_id=data["solution_id"],
            )

            result = response.json()

            if response.ok:
                logger.info(
                    "Solution migration intent set successfully (legacy)",
                    extra={
                        "tenant_id": request.tenant_id,
                        "waba_id": data["waba_id"],
                        "migration_intent_id": result.get("id"),
                    },
                )

            return Response(result, status=response.status_code)

        except Exception as e:
            logger.exception("Failed to set solution migration intent")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ListMigrationIntentsView(MigrationIntentMixin, BaseAuthenticatedAPIView):
    """
    GET: List all migration intents for the tenant.

    Returns a list of migration intents from the local database,
    filtered by tenant_id.

    Query params:
        status: Optional filter by status (PENDING, APPROVED, COMPLETED, etc.)

    Response:
        [
            {
                "id": 1,
                "migration_intent_id": "migration_123456789",
                "source_waba_id": "123456789",
                "destination_waba_id": "987654321",
                "status": "PENDING",
                "created_at": "...",
                ...
            },
            ...
        ]
    """

    @require_tenant
    def get(self, request):
        try:
            from ...models import MigrationIntent

            queryset = MigrationIntent.objects.filter(tenant_id=request.tenant_id)

            # Optional status filter
            status_filter = request.query_params.get("status")
            if status_filter:
                queryset = queryset.filter(status=status_filter.upper())

            intents = queryset.order_by("-created_at").values(
                "id",
                "migration_intent_id",
                "source_waba_id",
                "destination_waba_id",
                "solution_id",
                "status",
                "migration_reason",
                "approval_required",
                "created_at",
                "updated_at",
                "completed_at",
            )

            return Response(list(intents), status=status.HTTP_200_OK)

        except Exception as e:
            logger.exception("Failed to list migration intents")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
