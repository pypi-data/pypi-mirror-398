import logging
from typing import Tuple
from .models import WhatsAppCloudApiBusiness

logger = logging.getLogger(__name__)


def get_business_credentials_by_tenant(tenant_id: int) -> Tuple[str, str, str]:
    """
    Fetch WhatsApp Business credentials by tenant ID.

    Args:
        tenant_id: ID of the tenant/organization

    Returns:
        Tuple of (token, waba_id, api_version)

    Raises:
        ValueError: If no WhatsApp Business account found for tenant_id

    Example:
        >>> tenant_id = request.user.company_id
        >>> token, waba_id, version = get_business_credentials_by_tenant(tenant_id)
    """
    try:
        business = WhatsAppCloudApiBusiness.objects.get(tenant_id=tenant_id)
        return (business.token, business.waba_id, business.api_version)
    except WhatsAppCloudApiBusiness.DoesNotExist:
        raise ValueError(
            f"No WhatsApp Business account found for tenant_id={tenant_id}. "
            f"Please create one using: python manage.py setup_whatsapp --tenant-id {tenant_id}"
        )
    except WhatsAppCloudApiBusiness.MultipleObjectsReturned:
        logger.warning(f"Multiple WhatsApp accounts for tenant_id={tenant_id}, using most recent")
        business = WhatsAppCloudApiBusiness.objects.filter(
            tenant_id=tenant_id
        ).order_by('-created_at').first()
        return (business.token, business.waba_id, business.api_version)
