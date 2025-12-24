import logging
from typing import Any, Dict, Optional

import requests
from django.conf import settings


class TemplateAPI:
    """
    Minimal client focused on Template management endpoints of WhatsApp Graph API.
    Uses settings.WHATSAPP_CLOUD_API_TOKEN, settings.WHATSAPP_CLOUD_API_VERSION and settings.WHATSAPP_CLOUD_API_WABA_ID.
    """

    def __init__(self, token: Optional[str] = None, waba_id: Optional[str] = None, api_version: Optional[str] = None):
        self.token = token or getattr(settings, "WHATSAPP_CLOUD_API_TOKEN", None)
        self.waba_id = waba_id or getattr(settings, "WHATSAPP_CLOUD_API_WABA_ID", None)
        self.api_version = api_version or getattr(settings, "WHATSAPP_CLOUD_API_VERSION", "v18.0")

        if not self.token:
            raise ValueError("TOKEN setting is required for TemplateAPI")
        if not self.waba_id:
            raise ValueError("WABA_ID setting is required for TemplateAPI")

        self.base_url = f"https://graph.facebook.com/{self.api_version}"
        self.auth_headers = {
            "Authorization": f"Bearer {self.token}",
        }

    def get_template_by_id(self, template_id: str) -> requests.Response:
        url = f"{self.base_url}/{template_id}"
        return requests.get(url, headers=self.auth_headers)

    def get_template_by_name(self, name: str) -> requests.Response:
        url = f"{self.base_url}/{self.waba_id}/message_templates"
        return requests.get(url, headers=self.auth_headers, params={"name": name})

    def list_templates(self, **params: Any) -> requests.Response:
        url = f"{self.base_url}/{self.waba_id}/message_templates"
        return requests.get(url, headers=self.auth_headers, params=params)

    def get_namespace(self) -> requests.Response:
        url = f"{self.base_url}/{self.waba_id}"
        return requests.get(url, headers=self.auth_headers, params={"fields": "message_template_namespace"})

    def create_template(self, payload: Dict[str, Any]) -> requests.Response:
        url = f"{self.base_url}/{self.waba_id}/message_templates"
        headers = {**self.auth_headers, "Content-Type": "application/json"}
        return requests.post(url, headers=headers, json=payload)

    def edit_template(self, template_id: str, payload: Dict[str, Any]) -> requests.Response:
        url = f"{self.base_url}/{template_id}"
        headers = {**self.auth_headers, "Content-Type": "application/json"}
        return requests.post(url, headers=headers, json=payload)

    def delete_template_by_name(self, name: str) -> requests.Response:
        url = f"{self.base_url}/{self.waba_id}/message_templates"
        return requests.delete(url, headers=self.auth_headers, params={"name": name})

    def delete_template_by_id(self, hsm_id: str, name: str) -> requests.Response:
        url = f"{self.base_url}/{self.waba_id}/message_templates"
        return requests.delete(url, headers=self.auth_headers, params={"hsm_id": hsm_id, "name": name})


