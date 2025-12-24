"""
Decorators for django-whatsapp-api-wrapper.

These decorators make multi-tenancy requirements explicit in the code.
"""
from functools import wraps
from rest_framework.response import Response


def require_tenant(view_func):
    """
    Decorator que extrai e valida o tenant_id diretamente do usuário autenticado.

    Este decorator torna a multi-tenancy EXPLÍCITA e VISÍVEL no código.
    Não depende de middleware - extrai o tenant_id diretamente do Employee do usuário.

    Fluxo EXPLÍCITO:
    1. Pega request.user (já autenticado pela view)
    2. Busca Employee.objects.get(user=request.user)
    3. Pega employee.client_company.id como tenant_id
    4. Injeta request.tenant_id para uso na view

    Usage:
        ```python
        from django_whatsapp_api_wrapper.decorators import require_tenant

        class MyView(BaseAuthenticatedAPIView):
            @require_tenant  # ← VISÍVEL que esta view precisa de tenant
            def get(self, request):
                # tenant_id está garantido aqui
                tenant_id = request.tenant_id
                # ...
        ```

    Requirements:
        - Usuário deve estar autenticado (BaseAuthenticatedAPIView garante isso)
        - Usuário deve ter um Employee no banco
        - Employee deve ter um client_company associado

    Returns:
        400 response se usuário não tiver Employee ou ClientCompany
    """
    @wraps(view_func)
    def wrapper(self, request, *args, **kwargs):
        # 1. Verifica se usuário está autenticado
        if not request.user or not request.user.is_authenticated:
            return Response(
                {
                    "error": "Authentication required",
                    "detail": "User must be authenticated to access this endpoint."
                },
                status=401
            )

        # 2. Busca Employee do usuário (EXPLÍCITO - você VÊ isso acontecendo)
        try:
            from chico.models import Employee
            employee = Employee.objects.select_related('client_company').get(
                user=request.user
            )
        except Employee.DoesNotExist:
            return Response(
                {
                    "error": "No Employee profile found",
                    "detail": f"User {request.user.email} does not have an Employee profile. "
                             "Contact administrator to set up your company association."
                },
                status=400
            )

        # 3. Valida que Employee tem ClientCompany (EXPLÍCITO)
        if not employee.client_company:
            return Response(
                {
                    "error": "No company associated",
                    "detail": f"Employee profile exists but is not associated with any company. "
                             "Contact administrator to complete your setup."
                },
                status=400
            )

        # 4. Injeta tenant_id no request (EXPLÍCITO - fica claro de onde vem)
        request.tenant_id = employee.client_company.id

        # 5. Chama a view original
        return view_func(self, request, *args, **kwargs)

    return wrapper
