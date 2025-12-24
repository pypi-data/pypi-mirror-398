from rest_framework import serializers


class MetadataSerializer(serializers.Serializer):
    display_phone_number = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    phone_number_id = serializers.CharField(required=False, allow_null=True, allow_blank=True)


class ContactProfileSerializer(serializers.Serializer):
    name = serializers.CharField(required=False, allow_null=True, allow_blank=True)


class ContactSerializer(serializers.Serializer):
    wa_id = serializers.CharField()
    profile = ContactProfileSerializer(required=False)


class TextMessageSerializer(serializers.Serializer):
    id = serializers.CharField()
    from_ = serializers.CharField(source="from")
    timestamp = serializers.CharField()
    text = serializers.DictField()
    type = serializers.ChoiceField(choices=["text"])  # noqa: RUF001


class ReactionMessageSerializer(serializers.Serializer):
    id = serializers.CharField()
    from_ = serializers.CharField(source="from")
    timestamp = serializers.CharField()
    reaction = serializers.DictField()
    type = serializers.ChoiceField(choices=["reaction"])  # noqa: RUF001


class MediaMessageSerializer(serializers.Serializer):
    id = serializers.CharField()
    from_ = serializers.CharField(source="from")
    timestamp = serializers.CharField()
    type = serializers.ChoiceField(choices=["image", "audio", "video", "document", "sticker"])  # noqa: RUF001
    image = serializers.DictField(required=False)
    audio = serializers.DictField(required=False)
    video = serializers.DictField(required=False)
    document = serializers.DictField(required=False)
    sticker = serializers.DictField(required=False)


class LocationMessageSerializer(serializers.Serializer):
    id = serializers.CharField()
    from_ = serializers.CharField(source="from")
    timestamp = serializers.CharField()
    type = serializers.ChoiceField(choices=["location"])  # noqa: RUF001
    location = serializers.DictField()


class ContactsMessageSerializer(serializers.Serializer):
    id = serializers.CharField()
    from_ = serializers.CharField(source="from")
    timestamp = serializers.CharField()
    type = serializers.ChoiceField(choices=["contacts"])  # noqa: RUF001
    contacts = serializers.ListField(child=serializers.DictField())


class SystemMessageSerializer(serializers.Serializer):
    id = serializers.CharField()
    from_ = serializers.CharField(source="from")
    timestamp = serializers.CharField()
    type = serializers.ChoiceField(choices=["system"])  # noqa: RUF001
    system = serializers.DictField()


class OrderMessageSerializer(serializers.Serializer):
    id = serializers.CharField()
    from_ = serializers.CharField(source="from")
    timestamp = serializers.CharField()
    type = serializers.ChoiceField(choices=["order"])  # noqa: RUF001
    order = serializers.DictField()


class UnknownMessageSerializer(serializers.Serializer):
    id = serializers.CharField()
    from_ = serializers.CharField(source="from")
    timestamp = serializers.CharField()
    type = serializers.CharField()
    errors = serializers.ListField(child=serializers.DictField(), required=False)


class StatusSerializer(serializers.Serializer):
    id = serializers.CharField()
    status = serializers.ChoiceField(choices=["sent", "delivered", "read", "failed"])  # noqa: RUF001
    timestamp = serializers.CharField()
    recipient_id = serializers.CharField(required=False, allow_blank=True)
    conversation = serializers.DictField(required=False)
    pricing = serializers.DictField(required=False)
    errors = serializers.ListField(child=serializers.DictField(), required=False)


class ValueSerializer(serializers.Serializer):
    messaging_product = serializers.ChoiceField(choices=["whatsapp"])  # noqa: RUF001
    metadata = MetadataSerializer(required=False)
    contacts = serializers.ListField(child=ContactSerializer(), required=False)
    messages = serializers.ListField(child=serializers.DictField(), required=False)
    statuses = serializers.ListField(child=serializers.DictField(), required=False)


class ChangeSerializer(serializers.Serializer):
    value = ValueSerializer()
    field = serializers.CharField()


class EntrySerializer(serializers.Serializer):
    id = serializers.CharField()
    changes = serializers.ListField(child=ChangeSerializer())


class WebhookEnvelopeSerializer(serializers.Serializer):
    object = serializers.CharField()
    entry = serializers.ListField(child=EntrySerializer())


