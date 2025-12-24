from typing import Any, Dict, List

from rest_framework import serializers


class TemplateCreateSerializer(serializers.Serializer):
    name = serializers.CharField()
    language = serializers.CharField()
    category = serializers.CharField()
    components = serializers.ListField(child=serializers.DictField(), allow_empty=False)


class TemplateEditSerializer(serializers.Serializer):
    name = serializers.CharField()
    language = serializers.CharField()
    category = serializers.CharField()
    components = serializers.ListField(child=serializers.DictField(), allow_empty=False)


class TemplateIdSerializer(serializers.Serializer):
    template_id = serializers.CharField()


class TemplateNameSerializer(serializers.Serializer):
    name = serializers.CharField()


class TemplateDeleteByIdSerializer(serializers.Serializer):
    hsm_id = serializers.CharField()
    name = serializers.CharField()


class TemplateListQuerySerializer(serializers.Serializer):
    limit = serializers.IntegerField(required=False, min_value=1, max_value=1000)
    after = serializers.CharField(required=False)
    before = serializers.CharField(required=False)


