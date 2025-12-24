from django.contrib.auth.models import AnonymousUser
from django.conf import settings
from rest_framework import authentication
from rest_framework import exceptions


class APIKeyAuthentication(authentication.BaseAuthentication):
    """
    Simple API key authentication for WhatsApp API endpoints.
    
    Clients should authenticate by passing the API key in the "X-WhatsApp-API-Key" header.
    For example:
        X-WhatsApp-API-Key: your_api_key_here
    """
    
    def authenticate(self, request):
        api_key = request.META.get('HTTP_X_WHATSAPP_API_KEY')
        if not api_key:
            return None
        
        expected_api_key = getattr(settings, 'WHATSAPP_API_KEY', None)
        if not expected_api_key:
            raise exceptions.AuthenticationFailed('WHATSAPP_API_KEY not configured in settings')
        
        if api_key != expected_api_key:
            raise exceptions.AuthenticationFailed('Invalid API key')
        
        # Return a tuple of (user, auth) where user can be AnonymousUser for API key auth
        return (AnonymousUser(), api_key)

    def authenticate_header(self, request):
        return 'X-WhatsApp-API-Key'
