"""
Mixins for django-whatsapp-api-wrapper views.

These mixins provide helper methods for multi-tenant views,
making it explicit where credentials come from.
"""
from typing import Tuple


class TenantMixin:
    """
    Mixin para views que precisam de tenant_id.

    Fornece métodos helper para acessar credenciais e APIs do tenant.
    O tenant_id deve estar presente em request (injetado por middleware).

    Usage:
        ```python
        from django_whatsapp_api_wrapper.mixins import TenantMixin
        from django_whatsapp_api_wrapper.decorators import require_tenant

        class MyView(TenantMixin, APIView):
            @require_tenant
            def get(self, request):
                # Usa helper methods do mixin
                api = self.get_tenant_api(request)
                templates = api.list_templates()
                # ...
        ```
    """

    def get_tenant_id(self, request) -> int:
        """
        Extrai tenant_id do request.

        O tenant_id é injetado pelo TenantMiddleware baseado no
        ClientCompany/Organization do usuário autenticado.

        Args:
            request: Django/DRF request object

        Returns:
            int: ID do tenant (empresa/organização)

        Raises:
            ValueError: Se tenant_id não encontrado no request
        """
        tenant_id = getattr(request, 'tenant_id', None)
        if not tenant_id:
            raise ValueError(
                "tenant_id not found in request. "
                "Ensure TenantMiddleware is configured and user is linked to a tenant."
            )
        return tenant_id

    def get_tenant_credentials(self, request) -> Tuple[str, str, str]:
        """
        Retorna credenciais WhatsApp Business do tenant.

        Busca as credenciais (token, waba_id, api_version) do banco de dados
        usando o tenant_id do request.

        Args:
            request: Django/DRF request object

        Returns:
            Tuple[str, str, str]: (token, waba_id, api_version)

        Raises:
            ValueError: Se credenciais não encontradas para o tenant

        Example:
            ```python
            token, waba_id, version = self.get_tenant_credentials(request)
            api = TemplateAPI(token=token, waba_id=waba_id, api_version=version)
            ```
        """
        from .utils import get_business_credentials_by_tenant
        tenant_id = self.get_tenant_id(request)
        return get_business_credentials_by_tenant(tenant_id)

    def get_tenant_api(self, request):
        """
        Retorna TemplateAPI configurado para o tenant.

        Helper que combina get_tenant_credentials + TemplateAPI
        para facilitar o uso nas views.

        Args:
            request: Django/DRF request object

        Returns:
            TemplateAPI: Instância configurada com credenciais do tenant

        Example:
            ```python
            @require_tenant
            def get(self, request):
                api = self.get_tenant_api(request)
                templates = api.list_templates()
                return Response(templates)
            ```
        """
        from .whatsapp_cloud_api.templates.client import TemplateAPI
        token, waba_id, api_version = self.get_tenant_credentials(request)
        return TemplateAPI(token=token, waba_id=waba_id, api_version=api_version)
