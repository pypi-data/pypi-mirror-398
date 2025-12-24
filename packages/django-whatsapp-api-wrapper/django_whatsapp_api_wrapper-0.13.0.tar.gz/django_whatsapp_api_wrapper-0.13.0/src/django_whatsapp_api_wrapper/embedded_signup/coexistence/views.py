from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
import logging
import requests

from ...models import WhatsAppCloudApiBusiness
from .serializers import SyncContactsSerializer, SyncHistorySerializer
from ...authentication.base import BaseAuthenticatedAPIView


logger = logging.getLogger(__name__)


class SyncContactsView(BaseAuthenticatedAPIView):
    """
    Endpoint para iniciar a sincronização de contatos do WhatsApp Business app.
    
    Após o onboarding do cliente, você tem 24 horas para sincronizar seus contatos
    e histórico de mensagens, caso contrário eles devem ser offboarded e completar
    o fluxo novamente.
    
    Nota: Este endpoint só pode ser executado uma vez. Se precisar executá-lo novamente,
    o cliente deve primeiro fazer offboard e completar o fluxo de Embedded Signup novamente.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        """
        Inicia a sincronização de contatos.
        
        Se bem-sucedido, um conjunto de webhooks smb_app_state_sync será disparado
        descrevendo os contatos do WhatsApp no WhatsApp Business app do cliente.
        
        Body:
            {
                "phone_number_id": "123456789"
            }
            
        Returns:
            {
                "status": "success",
                "messaging_product": "whatsapp",
                "request_id": "<REQUEST_ID>"
            }
        """
        serializer = SyncContactsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        phone_number_id = serializer.validated_data.get('phone_number_id')
        
        logger.info(
            "Initiating contacts synchronization",
            extra={
                'user_id': user.id,
                'phone_number_id': phone_number_id
            }
        )
        
        try:
            # Buscar WhatsAppCloudApiBusiness pelo phone_number_id
            business = WhatsAppCloudApiBusiness.objects.get(phone_number_id=phone_number_id)
            
            # Verificar se é do tipo coexistence
            if business.type != 'coexistence':
                logger.warning(
                    "Attempted to sync contacts for non-coexistence business",
                    extra={
                        'user_id': user.id,
                        'phone_number_id': phone_number_id,
                        'business_type': business.type
                    }
                )
                return Response({
                    "status": "error",
                    "message": "This endpoint is only available for coexistence type businesses"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Fazer requisição à API do Facebook
            url = f"https://graph.facebook.com/{business.api_version}/{phone_number_id}/smb_app_data"
            headers = {
                'Authorization': f'Bearer {business.token}',
                'Content-Type': 'application/json'
            }
            data = {
                'messaging_product': 'whatsapp',
                'sync_type': 'smb_app_state_sync'
            }
            
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            
            result = response.json()
            request_id = result.get('request_id')
            
            logger.info(
                "Contacts synchronization initiated successfully",
                extra={
                    'user_id': user.id,
                    'phone_number_id': phone_number_id,
                    'request_id': request_id
                }
            )
            
            return Response({
                "status": "success",
                "messaging_product": result.get('messaging_product'),
                "request_id": request_id,
                "message": "Contacts synchronization initiated. Webhooks will be triggered with contact data."
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
                "Failed to initiate contacts synchronization",
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
                "message": "Failed to initiate contacts synchronization",
                "details": e.response.json() if hasattr(e, 'response') else str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        except Exception as e:
            logger.error(
                "Unexpected error initiating contacts synchronization",
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


class SyncHistoryView(BaseAuthenticatedAPIView):
    """
    Endpoint para iniciar a sincronização do histórico de mensagens do WhatsApp Business app.
    
    Após o onboarding do cliente, você tem 24 horas para sincronizar seus contatos
    e histórico de mensagens, caso contrário eles devem ser offboarded e completar
    o fluxo novamente.
    
    Nota: Este endpoint só pode ser executado uma vez. Se precisar executá-lo novamente,
    o cliente deve primeiro fazer offboard e completar o fluxo de Embedded Signup novamente.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        """
        Inicia a sincronização do histórico de mensagens.
        
        Se o cliente escolheu compartilhar seu histórico de mensagens, uma série de
        webhooks 'history' será disparada, descrevendo cada mensagem enviada ou recebida.
        
        Se o cliente escolheu NÃO compartilhar, um webhook 'history' com error code 2593109
        será disparado.
        
        Body:
            {
                "phone_number_id": "123456789"
            }
            
        Returns:
            {
                "status": "success",
                "messaging_product": "whatsapp",
                "request_id": "<REQUEST_ID>"
            }
        """
        serializer = SyncHistorySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        phone_number_id = serializer.validated_data.get('phone_number_id')
        
        logger.info(
            "Initiating message history synchronization",
            extra={
                'user_id': user.id,
                'phone_number_id': phone_number_id
            }
        )
        
        try:
            # Buscar WhatsAppCloudApiBusiness pelo phone_number_id
            business = WhatsAppCloudApiBusiness.objects.get(phone_number_id=phone_number_id)
            
            # Verificar se é do tipo coexistence
            if business.type != 'coexistence':
                logger.warning(
                    "Attempted to sync history for non-coexistence business",
                    extra={
                        'user_id': user.id,
                        'phone_number_id': phone_number_id,
                        'business_type': business.type
                    }
                )
                return Response({
                    "status": "error",
                    "message": "This endpoint is only available for coexistence type businesses"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Fazer requisição à API do Facebook
            url = f"https://graph.facebook.com/{business.api_version}/{phone_number_id}/smb_app_data"
            headers = {
                'Authorization': f'Bearer {business.token}',
                'Content-Type': 'application/json'
            }
            data = {
                'messaging_product': 'whatsapp',
                'sync_type': 'history'
            }
            
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            
            result = response.json()
            request_id = result.get('request_id')
            
            logger.info(
                "Message history synchronization initiated successfully",
                extra={
                    'user_id': user.id,
                    'phone_number_id': phone_number_id,
                    'request_id': request_id
                }
            )
            
            return Response({
                "status": "success",
                "messaging_product": result.get('messaging_product'),
                "request_id": request_id,
                "message": "Message history synchronization initiated. Webhooks will be triggered with message data."
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
                "Failed to initiate message history synchronization",
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
                "message": "Failed to initiate message history synchronization",
                "details": e.response.json() if hasattr(e, 'response') else str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        except Exception as e:
            logger.error(
                "Unexpected error initiating message history synchronization",
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

