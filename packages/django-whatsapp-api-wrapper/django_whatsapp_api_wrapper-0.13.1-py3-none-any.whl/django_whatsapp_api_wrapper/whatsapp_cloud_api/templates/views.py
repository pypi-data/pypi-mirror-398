from rest_framework.response import Response
from rest_framework import status

from ...authentication.base import BaseAuthenticatedAPIView
from ...decorators import require_tenant
from ...mixins import TenantMixin
from .client import TemplateAPI
from .serializers import (
    TemplateCreateSerializer,
    TemplateEditSerializer,
    TemplateIdSerializer,
    TemplateNameSerializer,
    TemplateDeleteByIdSerializer,
    TemplateListQuerySerializer,
)


class TemplateByIdView(TenantMixin, BaseAuthenticatedAPIView):
    """
    Get or edit a template by ID.
    Requires multi-tenancy: tenant_id injected by TenantMiddleware.
    """

    @require_tenant
    def get(self, request, template_id: str):
        # Usa helper do TenantMixin - deixa claro de onde vem a API
        api = self.get_tenant_api(request)
        resp = api.get_template_by_id(template_id)
        return Response(resp.json(), status=resp.status_code)

    @require_tenant
    def post(self, request, template_id: str):
        # Validação primeiro
        serializer = TemplateEditSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Usa helper do TenantMixin
        api = self.get_tenant_api(request)
        resp = api.edit_template(template_id, serializer.validated_data)
        return Response(resp.json() if resp.content else None, status=resp.status_code)


class TemplateByNameView(TenantMixin, BaseAuthenticatedAPIView):
    """
    Get or delete a template by name.
    Requires multi-tenancy: tenant_id injected by TenantMiddleware.
    """

    @require_tenant
    def get(self, request):
        serializer = TemplateNameSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        api = self.get_tenant_api(request)
        resp = api.get_template_by_name(serializer.validated_data["name"])
        return Response(resp.json(), status=resp.status_code)

    @require_tenant
    def delete(self, request):
        serializer = TemplateNameSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        api = self.get_tenant_api(request)
        resp = api.delete_template_by_name(serializer.validated_data["name"])
        return Response(resp.json() if resp.content else None, status=resp.status_code)


class TemplateListCreateView(TenantMixin, BaseAuthenticatedAPIView):
    """
    List or create templates.
    Requires multi-tenancy: tenant_id injected by TenantMiddleware.
    """

    @require_tenant
    def get(self, request):
        serializer = TemplateListQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        api = self.get_tenant_api(request)
        resp = api.list_templates(**serializer.validated_data)
        return Response(resp.json(), status=resp.status_code)

    @require_tenant
    def post(self, request):
        serializer = TemplateCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        api = self.get_tenant_api(request)
        resp = api.create_template(serializer.validated_data)
        return Response(resp.json(), status=resp.status_code)


class TemplateNamespaceView(TenantMixin, BaseAuthenticatedAPIView):
    """
    Get template namespace.
    Requires multi-tenancy: tenant_id injected by TenantMiddleware.
    """

    @require_tenant
    def get(self, request):
        api = self.get_tenant_api(request)
        resp = api.get_namespace()
        return Response(resp.json(), status=resp.status_code)


class TemplateDeleteByIdView(TenantMixin, BaseAuthenticatedAPIView):
    """
    Delete a template by ID.
    Requires multi-tenancy: tenant_id injected by TenantMiddleware.
    """

    @require_tenant
    def delete(self, request):
        serializer = TemplateDeleteByIdSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        api = self.get_tenant_api(request)
        resp = api.delete_template_by_id(
            serializer.validated_data["hsm_id"], serializer.validated_data["name"]
        )
        return Response(resp.json() if resp.content else None, status=resp.status_code)


