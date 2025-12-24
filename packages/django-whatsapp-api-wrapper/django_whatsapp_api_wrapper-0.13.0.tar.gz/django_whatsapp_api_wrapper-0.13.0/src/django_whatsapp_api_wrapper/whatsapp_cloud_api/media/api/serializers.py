from rest_framework import serializers


class MediaUploadSerializer(serializers.Serializer):
    sender_phone_number = serializers.CharField()
    file = serializers.FileField()
    type = serializers.ChoiceField(
        choices=[
            ("audio", "audio"),
            ("document", "document"),
            ("image", "image"),
            ("sticker", "sticker"),
            ("video", "video"),
        ]
    )


class MediaIdSerializer(serializers.Serializer):
    sender_phone_number = serializers.CharField()
    media_id = serializers.CharField()


class MediaUrlDownloadSerializer(serializers.Serializer):
    sender_phone_number = serializers.CharField()
    url = serializers.URLField()

