from typing import Any, Dict

import requests
from rest_framework import status
from rest_framework.response import Response

from django.conf import settings

from ....authentication.base import BaseAuthenticatedAPIView

from .serializers import (
    MessageGenericSerializer,
    MessageTextSerializer,
    MessageTextReplySerializer,
    MessageTemplateSerializer,
)


def build_url() -> str:
    api_version = getattr(settings, "WHATSAPP_CLOUD_API_VERSION")
    phone_number_id = getattr(settings, "WHATSAPP_CLOUD_API_PHONE_NUMBER_ID")
    base_url = f"https://graph.facebook.com/{api_version}/{phone_number_id}/messages"
    return base_url


def auth_headers() -> Dict[str, str]:
    token = getattr(settings, "WHATSAPP_CLOUD_API_TOKEN")
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


class MessageSendView(BaseAuthenticatedAPIView):
    def post(self, request):
        serializer = MessageGenericSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        payload: Dict[str, Any] = {
            "messaging_product": "whatsapp",
            "recipient_type": data.get("recipient_type", "individual"),
            "to": data["to"],
            "type": data["type"],
        }
        if "context" in data:
            payload["context"] = data["context"]

        # Include the type-specific object
        payload[data["type"]] = data[data["type"]]

        resp = requests.post(build_url(), headers=auth_headers(), json=payload)
        body = resp.json() if resp.content else None
        return Response(body, status=resp.status_code)


class MessageTextView(BaseAuthenticatedAPIView):
    def post(self, request):
        serializer = MessageTextSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        v = serializer.validated_data

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": v["to"],
            "type": "text",
            "text": {"preview_url": v.get("preview_url", False), "body": v["body"]},
        }
        resp = requests.post(build_url(), headers=auth_headers(), json=payload)
        return Response(resp.json() if resp.content else None, status=resp.status_code)


class MessageTextReplyView(BaseAuthenticatedAPIView):
    def post(self, request):
        serializer = MessageTextReplySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        v = serializer.validated_data

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": v["to"],
            "context": {"message_id": v["reply_to"]},
            "type": "text",
            "text": {"preview_url": v.get("preview_url", False), "body": v["body"]},
        }
        resp = requests.post(build_url(), headers=auth_headers(), json=payload)
        return Response(resp.json() if resp.content else None, status=resp.status_code)


class MessageTemplateView(BaseAuthenticatedAPIView):
    def post(self, request):
        serializer = MessageTemplateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        v = serializer.validated_data

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": v["to"],
            "type": "template",
            "template": {
                "name": v["name"],
                "language": v["language"],
            },
        }
        if v.get("components"):
            payload["template"]["components"] = v["components"]

        resp = requests.post(build_url(), headers=auth_headers(), json=payload)
        return Response(resp.json() if resp.content else None, status=resp.status_code)


