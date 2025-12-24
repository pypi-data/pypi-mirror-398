from django.conf import settings
from rest_framework.views import APIView
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated


class BaseAuthenticatedAPIView(APIView):
    """
    Base API view with configurable authentication for WhatsApp API endpoints.
    
    Authentication and permission classes can be configured via Django settings:
    
    WHATSAPP_API_AUTHENTICATION_CLASSES = [
        'rest_framework.authentication.TokenAuthentication',
        # or 'rest_framework_simplejwt.authentication.JWTAuthentication',
        # or 'django_whatsapp_api_wrapper.authentication.APIKeyAuthentication',
    ]
    
    WHATSAPP_API_PERMISSION_CLASSES = [
        'rest_framework.permissions.IsAuthenticated',
    ]
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Get authentication classes from settings
        auth_classes_setting = getattr(settings, 'WHATSAPP_API_AUTHENTICATION_CLASSES', None)
        if auth_classes_setting:
            self.authentication_classes = self._import_classes(auth_classes_setting)
        else:
            # Default to TokenAuthentication if no setting is provided
            self.authentication_classes = [TokenAuthentication]
        
        # Get permission classes from settings
        perm_classes_setting = getattr(settings, 'WHATSAPP_API_PERMISSION_CLASSES', None)
        if perm_classes_setting:
            self.permission_classes = self._import_classes(perm_classes_setting)
        else:
            # Default to IsAuthenticated if no setting is provided
            self.permission_classes = [IsAuthenticated]
    
    def _import_classes(self, class_paths):
        """Import classes from string paths."""
        classes = []
        for class_path in class_paths:
            try:
                module_path, class_name = class_path.rsplit('.', 1)
                module = __import__(module_path, fromlist=[class_name])
                cls = getattr(module, class_name)
                classes.append(cls)
            except (ImportError, AttributeError, ValueError) as e:
                raise ImportError(f"Could not import '{class_path}': {e}")
        return classes
