from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
import logging
import requests
import random

from ..models import WhatsAppCloudApiBusiness, MetaApp
from .serializers import WhatsAppCloudApiBusinessSerializer, BusinessCallbackSerializer, EmbeddedSignupEventSerializer
from ..authentication.base import BaseAuthenticatedAPIView


logger = logging.getLogger(__name__)


class EmbeddedSignupCallbackView(BaseAuthenticatedAPIView):

    def post(self, request, *args, **kwargs):
        # Log dos dados recebidos para debugging
        logger.info(
            "EmbeddedSignup callback received - raw data",
            extra={
                'user_id': request.user.id,
                'user_email': getattr(request.user, 'email', None),
                'raw_data': request.data
            }
        )
        
        serializer = EmbeddedSignupEventSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        payload = serializer.validated_data
        data = payload.get('data', {})
        event = payload.get('event')
        
        # Log dos dados recebidos
        logger.info(
            "EmbeddedSignup callback received",
            extra={
                'user_id': user.id,
                'user_email': getattr(user, 'email', None),
                'event': event,
                'payload': payload
            }
        )
        
        # Salvar dados no modelo WhatsAppCloudApiBusiness apenas se for evento de sucesso
        if event in ['FINISH', 'FINISH_ONLY_WABA', 'FINISH_WHATSAPP_BUSINESS_APP_ONBOARDING']:
            waba_id = data.get('waba_id', '')
            
            if waba_id:
                try:
                    # Buscar WhatsAppCloudApiBusiness pelo waba_id
                    if event == 'FINISH_WHATSAPP_BUSINESS_APP_ONBOARDING':
                        type = 'coexistence'
                    else:
                        type = 'cloud_api'

                    # Resolve tenant_id from request (injected by backend via custom view or middleware)
                    # Falls back to 1 if not provided (for backwards compatibility)
                    tenant_id = getattr(request, '_tenant_id', 1)

                    logger.info(
                        "Creating/updating WhatsApp Business with tenant_id",
                        extra={
                            'user_id': user.id,
                            'waba_id': waba_id,
                            'tenant_id': tenant_id,
                            'tenant_source': 'request._tenant_id' if hasattr(request, '_tenant_id') else 'default'
                        }
                    )

                    business, created = WhatsAppCloudApiBusiness.objects.update_or_create(
                        waba_id=waba_id,
                        defaults={
                            'waba_id': data.get('waba_id', ''),
                            'business_id': data.get('business_id', ''),
                            'phone_number': data.get('phone_number', ''),
                            'phone_number_id': data.get('phone_number_id', ''),  # Fix: Add phone_number_id
                            'token': data.get('business_token', ''),  # Usando business_token como token
                            'api_version': 'v23.0',  # Versão padrão da API
                            'type': type,
                            'tenant_id': tenant_id,  # Fix: Add tenant_id resolution
                        }
                    )
                    
                    action = 'created' if created else 'updated'
                    
                    logger.info(
                        f"WhatsAppCloudApiBusiness {action} successfully",
                        extra={
                            'user_id': user.id,
                            'waba_id': waba_id,
                            'action': action
                        }
                    )
                except Exception as e:
                    logger.error(
                        "Failed to save WhatsAppCloudApiBusiness or WhatsAppEmbeddedSignUp data",
                        extra={
                            'user_id': user.id,
                            'waba_id': waba_id,
                            'error': str(e),
                            'payload': payload
                        },
                        exc_info=True
                    )
            else:
                logger.warning(
                    "waba_id not provided in callback data",
                    extra={
                        'user_id': user.id,
                        'event': event,
                        'data': data
                    }
                )
        else:
            logger.info(
                "Non-success event received, data not saved",
                extra={
                    'user_id': user.id,
                    'event': event,
                    'waba_id': data.get('waba_id', '')
                }
            )

        return Response({
            "status": "ok",
            "user_id": user.id,
            "event": event,
            "saved": event in ['FINISH', 'FINISH_ONLY_WABA', 'FINISH_WHATSAPP_BUSINESS_APP_ONBOARDING'],
            "received": payload,
        }, status=status.HTTP_200_OK)


class BusinessCallbackView(BaseAuthenticatedAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = BusinessCallbackSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        data = serializer.validated_data.get('data', {})
        
        phone_number_id = data.get('phone_number_id')
        waba_id = data.get('waba_id')
        business_id = data.get('business_id')
        code = data.get('code')
        meta_app_id = data.get('meta_app_id')
        
        logger.info(
            "Business callback received - raw data",
            extra={
                'user_id': request.user.id,
                'user_email': getattr(request.user, 'email', None),
                'raw_data': request.data,
                'data': data,
                'phone_number_id': phone_number_id,
                'waba_id': waba_id,
                'business_id': business_id,
                'meta_app_id': meta_app_id,
                'code': code
            }
        )
        
        try:
            # Buscar WhatsAppCloudApiBusiness pelo phone_number_id
            business = WhatsAppCloudApiBusiness.objects.get(waba_id=waba_id)
            
            # Atualizar WhatsAppCloudApiBusiness
            business.code = code
            business.save()
            
            # Buscar MetaApp
            meta_app = MetaApp.objects.get(app_id=meta_app_id)
            
            # ETAPA 1: Trocar código por business token
            business_token = self._exchange_code_for_token(code, meta_app, business.api_version)
            if business_token:
                business.token = business_token
                business.save()
                
                # ETAPA 2: Assinar webhooks na WABA
                webhook_success = self._subscribe_to_webhooks(business_token, business.waba_id, business.api_version)
                
                if webhook_success:
                    # Se o tipo for coexistence, pular a etapa 3 de cadastro de telefone
                    if getattr(business, 'type', None) == 'coexistence':
                        logger.info(
                            "Coexistence type detected, skipping phone registration",
                            extra={
                                'user_id': user.id,
                                'business_id': business.id,
                                'webhook_subscribed': webhook_success,
                                'phone_registered': False
                            }
                        )
                        return Response({
                            "status": "success",
                            "message": "Business callback processed successfully (phone registration skipped for coexistence)",
                            "business_id": business.id,
                            "webhook_subscribed": webhook_success,
                            "phone_registered": False
                        }, status=status.HTTP_200_OK)
                    
                    # ETAPA 3: Cadastrar número de telefone
                    auth_desired_pin = self._register_phone_number(business_token, business.phone_number_id, business.api_version)
                    
                    if auth_desired_pin:
                        # Salvar o PIN no modelo WhatsAppCloudApiBusiness
                        business.auth_desired_pin = auth_desired_pin
                        business.save()
                        
                        logger.info(
                            "Business callback processed successfully",
                            extra={
                                'user_id': user.id,
                                'business_id': business.id,
                                'auth_desired_pin': auth_desired_pin,
                                'webhook_subscribed': webhook_success,
                                'phone_registered': True
                            }
                        )
                        
                        return Response({
                            "status": "success",
                            "message": "Business callback processed successfully",
                            "business_id": business.id,
                            "webhook_subscribed": webhook_success,
                            "phone_registered": True
                        }, status=status.HTTP_200_OK)
                    else:
                        logger.error("Failed to register phone number")
                        return Response({
                            "status": "error",
                            "message": "Failed to register phone number"
                        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                else:
                    logger.error("Failed to subscribe to webhooks")
                    return Response({
                        "status": "error",
                        "message": "Failed to subscribe to webhooks"
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                logger.error("Failed to exchange code for business token")
                return Response({
                    "status": "error",
                    "message": "Failed to exchange code for business token"
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except WhatsAppCloudApiBusiness.DoesNotExist:
            logger.error("WhatsAppCloudApiBusiness not found", extra={'phone_number_id': phone_number_id})
            return Response({
                "status": "error",
                "message": "WhatsApp Business not found"
            }, status=status.HTTP_404_NOT_FOUND)
        except MetaApp.DoesNotExist:
            logger.error("MetaApp not found", extra={'meta_app_id': meta_app_id})
            return Response({
                "status": "error",
                "message": "Meta App not found"
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(
                "Business callback processing failed",
                extra={
                    'user_id': user.id,
                    'error': str(e),
                    'data': data
                },
                exc_info=True
            )
            return Response({
                "status": "error",
                "message": "Internal server error"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _exchange_code_for_token(self, code, meta_app, api_version):
        """ETAPA 1: Trocar código por business token"""
        try:
            url = f"https://graph.facebook.com/{api_version}/oauth/access_token"
            params = {
                'client_id': meta_app.app_id,
                'client_secret': meta_app.app_secret,
                'code': code
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            business_token = data.get('access_token')
            
            logger.info("Code exchanged for business token successfully", extra={'data': data})
            return business_token
            
        except Exception as e:
            logger.error(f"Failed to exchange code for token: {str(e)}")
            return None

    def _subscribe_to_webhooks(self, business_token, waba_id, api_version):
        """ETAPA 2: Assinar webhooks na WABA"""
        try:
            url = f"https://graph.facebook.com/{api_version}/{waba_id}/subscribed_apps"
            headers = {
                'Authorization': f'Bearer {business_token}'
            }
            
            response = requests.post(url, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            success = data.get('success', False)
            
            logger.info("Webhooks subscription result", extra={'data': data})
                
            return success
            
        except Exception as e:
            logger.error(f"Failed to subscribe to webhooks: {str(e)}")
            return False

    def _register_phone_number(self, business_token, phone_number_id, api_version):
        """ETAPA 3: Cadastrar número de telefone"""

        # Gerar PIN aleatório de 6 dígitos
        auth_desired_pin = str(random.randint(100000, 999999))

        url = f"https://graph.facebook.com/{api_version}/{phone_number_id}/register"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {business_token}'
        }

        data = {
            'messaging_product': 'whatsapp',
            'pin': auth_desired_pin
        }

        logger.info("Register phone number data", extra={'url': url, 'headers': headers, 'data': data})

        try:
            response = requests.post(url, headers=headers, json=data)
            logger.info("Register phone number response", extra={'response': response.text})
            result = response.json()

            logger.info("Register phone number result", extra={'result': result})

            response.raise_for_status()
            success = result.get('success', False)

            if success:
                logger.info("Phone number registered successfully")
                return auth_desired_pin
            else:
                logger.error("Failed to register phone number")
                return None

        except requests.exceptions.HTTPError as e:
            # Check if error is due to 2FA being enabled (error 2388001)
            if e.response.status_code == 400:
                try:
                    error_data = e.response.json().get('error', {})
                    error_subcode = error_data.get('error_subcode')

                    # Error 2388001: Two-factor authentication enabled
                    # This is a valid state - phone is still usable, just can't set PIN
                    if error_subcode == 2388001:
                        logger.warning(
                            "Phone number has 2FA enabled, skipping PIN registration",
                            extra={
                                'phone_number_id': phone_number_id,
                                'error_subcode': error_subcode,
                                'error_message': error_data.get('message'),
                                'error_user_msg': error_data.get('error_user_msg')
                            }
                        )
                        # Return None to indicate no PIN was set (phone is still usable)
                        return None
                except Exception:
                    pass

            # Log the full error for other cases
            logger.error(
                "Phone registration failed",
                extra={
                    'status_code': e.response.status_code,
                    'error_response': e.response.json() if e.response.content else None
                },
                exc_info=True
            )
            return None


class OnboardingStatusView(BaseAuthenticatedAPIView):
    """
    Endpoint para verificar o status do onboarding de um número de telefone.
    Retorna se o número está registrado para uso com Cloud API e WhatsApp Business app.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, phone_number_id, *args, **kwargs):
        """
        Verifica o status do onboarding do número de telefone.
        
        Args:
            phone_number_id: ID do número de telefone no WhatsApp Business
            
        Returns:
            {
                "is_on_biz_app": true/false,
                "platform_type": "CLOUD_API" ou outro,
                "id": "phone_number_id"
            }
        """
        user = request.user
        
        logger.info(
            "Checking onboarding status",
            extra={
                'user_id': user.id,
                'phone_number_id': phone_number_id
            }
        )
        
        try:
            # Buscar WhatsAppCloudApiBusiness pelo phone_number_id
            business = WhatsAppCloudApiBusiness.objects.get(phone_number_id=phone_number_id)
            
            # Fazer requisição à API do Facebook
            url = f"https://graph.facebook.com/{business.api_version}/{phone_number_id}"
            params = {
                'fields': 'is_on_biz_app,platform_type'
            }
            headers = {
                'Authorization': f'Bearer {business.token}'
            }
            
            response = requests.get(url, params=params, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            
            logger.info(
                "Onboarding status retrieved successfully",
                extra={
                    'user_id': user.id,
                    'phone_number_id': phone_number_id,
                    'status': data
                }
            )
            
            return Response({
                "status": "success",
                "data": data
            }, status=status.HTTP_200_OK)
            
        except WhatsAppCloudApiBusiness.DoesNotExist:
            logger.error(
                "WhatsAppCloudApiBusiness not found",
                extra={
                    'user_id': user.id,
                    'phone_number_id': phone_number_id
                }
            )
            return Response({
                "status": "error",
                "message": "WhatsApp Business not found"
            }, status=status.HTTP_404_NOT_FOUND)
            
        except requests.exceptions.HTTPError as e:
            logger.error(
                "Failed to retrieve onboarding status from Facebook API",
                extra={
                    'user_id': user.id,
                    'phone_number_id': phone_number_id,
                    'error': str(e),
                    'response': e.response.text if hasattr(e, 'response') else None
                },
                exc_info=True
            )
            return Response({
                "status": "error",
                "message": "Failed to retrieve onboarding status",
                "details": e.response.json() if hasattr(e, 'response') else str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        except Exception as e:
            logger.error(
                "Unexpected error checking onboarding status",
                extra={
                    'user_id': user.id,
                    'phone_number_id': phone_number_id,
                    'error': str(e)
                },
                exc_info=True
            )
            return Response({
                "status": "error",
                "message": "Internal server error"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

