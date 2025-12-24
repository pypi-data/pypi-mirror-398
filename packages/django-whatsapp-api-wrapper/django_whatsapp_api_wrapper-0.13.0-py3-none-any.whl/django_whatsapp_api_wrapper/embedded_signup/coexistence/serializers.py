from rest_framework import serializers


class SyncContactsSerializer(serializers.Serializer):
    """
    Serializer para sincronização de contatos do WhatsApp Business app
    """
    phone_number_id = serializers.CharField(
        required=True,
        help_text="ID do número de telefone do WhatsApp Business"
    )


class SyncHistorySerializer(serializers.Serializer):
    """
    Serializer para sincronização do histórico de mensagens do WhatsApp Business app
    """
    phone_number_id = serializers.CharField(
        required=True,
        help_text="ID do número de telefone do WhatsApp Business"
    )


class SyncResponseSerializer(serializers.Serializer):
    """
    Serializer para resposta de sincronização
    """
    status = serializers.CharField()
    messaging_product = serializers.CharField(required=False)
    request_id = serializers.CharField(required=False)
    message = serializers.CharField(required=False)

