"""
MigrationIntentAPI client for WABA migrations between multi-partner solutions.

This client handles the Graph API calls for creating and managing migration
intents between WhatsApp Business Accounts in different solutions.
"""

import logging
from typing import Any, Dict, Optional

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class MigrationIntentAPI:
    """
    Client for Migration Intent operations via WhatsApp Graph API.

    Supports creating migration intents to move WABAs between multi-partner
    solutions, as well as querying migration status.

    Usage:
        ```python
        api = MigrationIntentAPI(token="your_token")

        # Create migration intent
        response = api.create_migration_intent(
            source_waba_id="123456789",
            destination_waba_id="987654321",
            solution_id="456789123"
        )

        # Get migration intent status
        intent_id = response.json().get('migration_intent_id')
        status = api.get_migration_intent(intent_id)
        ```
    """

    def __init__(
        self,
        token: Optional[str] = None,
        api_version: Optional[str] = None,
    ):
        """
        Initialize MigrationIntentAPI client.

        Args:
            token: Access token with whatsapp_business_management permission.
                   Falls back to settings.WHATSAPP_CLOUD_API_TOKEN
            api_version: Graph API version.
                        Falls back to settings.WHATSAPP_CLOUD_API_VERSION

        Raises:
            ValueError: If token is not provided and not in settings
        """
        self.token = token or getattr(settings, "WHATSAPP_CLOUD_API_TOKEN", None)
        self.api_version = api_version or getattr(
            settings, "WHATSAPP_CLOUD_API_VERSION", "v23.0"
        )

        if not self.token:
            raise ValueError("TOKEN is required for MigrationIntentAPI")

        self.base_url = f"https://graph.facebook.com/{self.api_version}"
        self.auth_headers = {
            "Authorization": f"Bearer {self.token}",
        }
        self.json_headers = {
            **self.auth_headers,
            "Content-Type": "application/json",
        }

    # =========================================================================
    # MIGRATION INTENT OPERATIONS
    # =========================================================================

    def create_migration_intent(
        self,
        source_waba_id: str,
        destination_waba_id: str,
        solution_id: str,
        migration_reason: Optional[str] = None,
        preserve_data: bool = True,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> requests.Response:
        """
        Create a migration intent for a WhatsApp Business Account.

        This initiates the migration process to move a WABA from one
        multi-partner solution to another.

        Args:
            source_waba_id: The WABA ID to migrate from
            destination_waba_id: The target WABA ID to migrate to
            solution_id: The destination multi-partner solution ID
            migration_reason: Optional reason for the migration
            preserve_data: Whether to preserve data during migration (default: True)
            metadata: Optional additional metadata for the migration

        Returns:
            requests.Response with JSON containing:
            - success: boolean
            - migration_intent_id: ID of the created intent
            - status: Initial status (typically PENDING)
            - estimated_completion_time: Estimated completion timestamp
            - approval_required: Whether business approval is needed
            - next_steps: List of next steps

        Example:
            >>> response = api.create_migration_intent(
            ...     source_waba_id="123456789",
            ...     destination_waba_id="987654321",
            ...     solution_id="456789123",
            ...     migration_reason="Migrating to new solution provider"
            ... )
            >>> intent_id = response.json()['migration_intent_id']
        """
        url = f"{self.base_url}/{source_waba_id}/migration_intent"

        payload: Dict[str, Any] = {
            "destination_waba_id": destination_waba_id,
            "solution_id": solution_id,
            "preserve_data": preserve_data,
        }

        if migration_reason:
            payload["migration_reason"] = migration_reason

        if metadata:
            payload["metadata"] = metadata

        logger.info(
            "Creating migration intent",
            extra={
                "source_waba_id": source_waba_id,
                "destination_waba_id": destination_waba_id,
                "solution_id": solution_id,
            },
        )

        return requests.post(url, headers=self.json_headers, json=payload)

    def get_migration_intent(
        self,
        migration_intent_id: str,
        fields: Optional[str] = None,
    ) -> requests.Response:
        """
        Get details for a specific Migration Intent.

        Retrieves comprehensive information about the migration intent,
        including current status, source and destination WABA details,
        solution information, and operation history.

        Args:
            migration_intent_id: The Migration Intent ID to query
            fields: Comma-separated list of fields to retrieve.
                   Default: id,waba,destination_waba,solution,status,created_time,updated_time

        Returns:
            requests.Response with JSON containing:
            - id: Migration intent ID
            - waba: Source WABA details
            - destination_waba: Destination WABA details
            - solution: Solution details
            - status: Current status (PENDING, APPROVED, IN_PROGRESS, COMPLETED, FAILED)
            - created_time: Creation timestamp
            - updated_time: Last update timestamp

        Example:
            >>> response = api.get_migration_intent("migration_123456789")
            >>> status = response.json()['status']
        """
        url = f"{self.base_url}/{migration_intent_id}"

        params: Dict[str, str] = {}
        if fields:
            params["fields"] = fields
        else:
            params["fields"] = (
                "id,waba,destination_waba,solution,status,created_time,updated_time"
            )

        logger.info(
            "Getting migration intent status",
            extra={"migration_intent_id": migration_intent_id},
        )

        return requests.get(url, headers=self.auth_headers, params=params)

    # =========================================================================
    # LEGACY ENDPOINT
    # =========================================================================

    def set_solution_migration_intent(
        self,
        waba_id: str,
        app_id: str,
    ) -> requests.Response:
        """
        Mark a WABA for migration using Embedded Signup flow.

        This endpoint is used when migrating customers from another
        solution provider to your Tech Provider account.

        Docs: https://developers.facebook.com/documentation/business-messaging/whatsapp/solution-providers/support/migrating-customers-off-solutions-via-embedded-signup

        Args:
            waba_id: The source WABA ID to mark for migration
            app_id: Your Meta App ID (the destination app)

        Returns:
            requests.Response with JSON containing:
            - id: Migration intent ID

        Example:
            >>> response = api.set_solution_migration_intent(
            ...     waba_id="123456789",
            ...     app_id="3271159996368927"
            ... )
            >>> intent_id = response.json()['id']
        """
        url = f"{self.base_url}/{waba_id}/set_solution_migration_intent"

        payload = {"app_id": app_id}

        logger.info(
            "Setting solution migration intent",
            extra={"waba_id": waba_id, "app_id": app_id},
        )

        return requests.post(url, headers=self.json_headers, json=payload)
