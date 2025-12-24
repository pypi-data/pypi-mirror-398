from rest_framework import serializers


class WhatsAppCloudApiBusinessSerializer(serializers.Serializer):
    phone_number_id = serializers.CharField(required=False, allow_blank=True)
    waba_id = serializers.CharField(required=False, allow_blank=True)
    business_id = serializers.CharField(required=False, allow_blank=True)
    current_step = serializers.CharField(required=False, allow_blank=True)
    error_message = serializers.CharField(required=False, allow_blank=True)
    error_id = serializers.CharField(required=False, allow_blank=True)
    session_id = serializers.CharField(required=False, allow_blank=True)
    timestamp = serializers.CharField(required=False, allow_blank=True)
    phone_number = serializers.CharField(required=False, allow_blank=True)
    type = serializers.CharField(required=False, allow_blank=True)
    # Campos adicionais do payload real
    page_ids = serializers.ListField(child=serializers.CharField(), required=False, allow_empty=True)
    catalog_ids = serializers.ListField(child=serializers.CharField(), required=False, allow_empty=True)
    dataset_ids = serializers.ListField(child=serializers.CharField(), required=False, allow_empty=True)
    instagram_account_ids = serializers.ListField(child=serializers.CharField(), required=False, allow_empty=True)

class EmbeddedSignupEventSerializer(serializers.Serializer):
    data = WhatsAppCloudApiBusinessSerializer()
    type = serializers.ChoiceField(choices=["WA_EMBEDDED_SIGNUP"])  # fixed per docs
    event = serializers.CharField()  # FINISH, CANCEL, etc
    version = serializers.CharField(required=False, allow_blank=True)  # Campo adicional do payload


class BusinessCallbackDataSerializer(serializers.Serializer):
    waba_id = serializers.CharField(required=True)
    business_id = serializers.CharField(required=True)
    code = serializers.CharField(required=True)
    meta_app_id = serializers.CharField(required=True)
    phone_number_id = serializers.CharField(required=False, allow_blank=True)


class BusinessCallbackSerializer(serializers.Serializer):
    data = BusinessCallbackDataSerializer()
