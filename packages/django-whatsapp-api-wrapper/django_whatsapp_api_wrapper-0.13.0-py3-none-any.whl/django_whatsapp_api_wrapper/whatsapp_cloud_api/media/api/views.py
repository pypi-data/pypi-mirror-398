from typing import Dict

import requests
from django.core.files.uploadedfile import InMemoryUploadedFile, TemporaryUploadedFile
from django.http import HttpResponse
from django.conf import settings
from rest_framework.response import Response
from rest_framework import status

from ....authentication.base import BaseAuthenticatedAPIView
from .serializers import MediaUploadSerializer, MediaIdSerializer, MediaUrlDownloadSerializer
from ....models import WhatsAppCloudApiBusiness


def _build_media_upload_url(api_version: str, phone_number_id: str) -> str:
    return f"https://graph.facebook.com/{api_version}/{phone_number_id}/media"


def _build_media_id_url(api_version: str, media_id: str, phone_number_id: str | None = None) -> str:
    base = f"https://graph.facebook.com/{api_version}/{media_id}"
    if phone_number_id:
        return f"{base}?phone_number_id={phone_number_id}"
    return base


def _auth_headers(token: str) -> Dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


class MediaUploadView(BaseAuthenticatedAPIView):
    def post(self, request):
        serializer = MediaUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        v = serializer.validated_data

        # Resolve business credentials by sender phone number
        business = WhatsAppCloudApiBusiness.objects.get(phone_number=v["sender_phone_number"])
        url = _build_media_upload_url(business.api_version, business.phone_number_id)

        uploaded: InMemoryUploadedFile | TemporaryUploadedFile = v["file"]

        files = {
            # 'file' must include the filename and content-type for correct MIME handling
            "file": (uploaded.name, uploaded.file, uploaded.content_type or "application/octet-stream"),
        }
        data = {"messaging_product": "whatsapp"}

        resp = requests.post(url, headers=_auth_headers(business.token), files=files, data=data)
        body = resp.json() if resp.content else None
        return Response(body, status=resp.status_code)


class MediaGetUrlView(BaseAuthenticatedAPIView):
    def get(self, request, media_id: str):
        serializer = MediaIdSerializer(data={
            "sender_phone_number": request.query_params.get("sender_phone_number"),
            "media_id": media_id,
        })
        serializer.is_valid(raise_exception=True)
        v = serializer.validated_data

        business = WhatsAppCloudApiBusiness.objects.get(phone_number=v["sender_phone_number"])
        url = _build_media_id_url(business.api_version, v["media_id"], business.phone_number_id)
        resp = requests.get(url, headers=_auth_headers(business.token))
        body = resp.json() if resp.content else None
        return Response(body, status=resp.status_code)


class MediaDeleteView(BaseAuthenticatedAPIView):
    def delete(self, request, media_id: str):
        serializer = MediaIdSerializer(data={
            "sender_phone_number": request.query_params.get("sender_phone_number"),
            "media_id": media_id,
        })
        serializer.is_valid(raise_exception=True)
        v = serializer.validated_data

        business = WhatsAppCloudApiBusiness.objects.get(phone_number=v["sender_phone_number"])
        url = _build_media_id_url(business.api_version, v["media_id"], business.phone_number_id)
        resp = requests.delete(url, headers=_auth_headers(business.token))
        body = resp.json() if resp.content else None
        return Response(body, status=resp.status_code)


class MediaDownloadView(BaseAuthenticatedAPIView):
    def get(self, request):
        serializer = MediaUrlDownloadSerializer(data={
            "sender_phone_number": request.query_params.get("sender_phone_number"),
            "url": request.query_params.get("url"),
        })
        serializer.is_valid(raise_exception=True)
        v = serializer.validated_data

        business = WhatsAppCloudApiBusiness.objects.get(phone_number=v["sender_phone_number"])

        # media URLs expire after 5 minutes; simply forward the GET with auth header
        resp = requests.get(v["url"], headers=_auth_headers(business.token), stream=True)

        # On success, proxy back binary with content-type
        content = resp.content
        status_code = resp.status_code
        content_type = resp.headers.get("Content-Type", "application/octet-stream")
        disposition = resp.headers.get("Content-Disposition")

        django_resp = HttpResponse(content=content, status=status_code, content_type=content_type)
        if disposition:
            django_resp["Content-Disposition"] = disposition
        return django_resp


