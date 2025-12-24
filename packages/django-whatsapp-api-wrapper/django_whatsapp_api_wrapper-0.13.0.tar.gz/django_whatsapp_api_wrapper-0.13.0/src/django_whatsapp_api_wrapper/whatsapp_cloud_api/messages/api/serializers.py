from typing import Any, Dict, Optional

from rest_framework import serializers


class MessageGenericSerializer(serializers.Serializer):
    to = serializers.CharField()
    recipient_type = serializers.ChoiceField(choices=[("individual", "individual")], required=False)
    type = serializers.ChoiceField(
        choices=[
            ("text", "text"),
            ("template", "template"),
            ("image", "image"),
            ("audio", "audio"),
            ("document", "document"),
            ("video", "video"),
            ("sticker", "sticker"),
            ("location", "location"),
            ("contacts", "contacts"),
            ("reaction", "reaction"),
            ("interactive", "interactive"),
        ]
    )

    # Optional common fields
    context = serializers.DictField(required=False)

    # Payloads per type (passed through to the Graph API)
    text = serializers.DictField(required=False)
    template = serializers.DictField(required=False)
    image = serializers.DictField(required=False)
    audio = serializers.DictField(required=False)
    document = serializers.DictField(required=False)
    video = serializers.DictField(required=False)
    sticker = serializers.DictField(required=False)
    location = serializers.DictField(required=False)
    contacts = serializers.DictField(required=False)
    reaction = serializers.DictField(required=False)
    interactive = serializers.DictField(required=False)

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        message_type: str = attrs.get("type")
        payload = attrs.get(message_type)
        if payload is None:
            raise serializers.ValidationError({message_type: "is required for this message type"})
        return attrs


class MessageTextSerializer(serializers.Serializer):
    to = serializers.CharField()
    body = serializers.CharField()
    preview_url = serializers.BooleanField(required=False, default=False)


class MessageTextReplySerializer(serializers.Serializer):
    to = serializers.CharField()
    reply_to = serializers.CharField()
    body = serializers.CharField()
    preview_url = serializers.BooleanField(required=False, default=False)


class MessageTemplateSerializer(serializers.Serializer):
    to = serializers.CharField()
    name = serializers.CharField()
    language = serializers.DictField()
    components = serializers.ListField(child=serializers.DictField(), required=False)


