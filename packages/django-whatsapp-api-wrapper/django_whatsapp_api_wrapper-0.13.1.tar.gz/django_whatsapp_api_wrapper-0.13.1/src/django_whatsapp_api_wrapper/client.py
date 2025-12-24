import logging
import requests
from django.conf import settings
from .whatsapp_cloud_api.messages import Message
from .models import WhatsAppCloudApiBusiness


class WhatsApp:
    def __init__(self, sender_phone_number: str):
        """
        Initialize the WhatsApp Object

        Args:
            sender_phone_number[str]: The sender phone number
        """
        
        self.PACKAGE_VERSION = settings.WHATSAPP_CLOUD_API_PACKAGE_VERSION  # package version

        whatsapp_cloud_api_business = WhatsAppCloudApiBusiness.objects.get(phone_number = sender_phone_number)

        if whatsapp_cloud_api_business.token == "":
            logging.error("Token not provided")
            raise ValueError("Token not provided but required")
        if whatsapp_cloud_api_business.phone_number_id == "":   
            logging.error("Phone number ID not provided")
            raise ValueError("Phone number ID not provided but required")

        self.API_VERSION = whatsapp_cloud_api_business.api_version  # api version

        self.token = whatsapp_cloud_api_business.token
        self.phone_number_id = whatsapp_cloud_api_business.phone_number_id
        self.base_url = f"https://graph.facebook.com/{self.API_VERSION}"
        self.url = f"{self.base_url}/{self.phone_number_id}/messages"
        
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}",
        }

    def build_message(self, **kwargs) -> Message:
        """
        Build a message object

        Args:
            data[dict]: The message data
            content[str]: The message content
            to[str]: The recipient
            rec_type[str]: The recipient type (individual/group)
        """
        return Message(**kwargs, instance=self)
