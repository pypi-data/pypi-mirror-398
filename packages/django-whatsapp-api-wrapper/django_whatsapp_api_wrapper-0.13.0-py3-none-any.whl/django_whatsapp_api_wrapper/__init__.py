# 1. Import Third Party Libraries
import logging
import requests

# 2. Lazy imports to avoid AppRegistryNotReady error
# This allows: from django_whatsapp_api_wrapper import WhatsApp, Message

def __getattr__(name):
    if name == 'WhatsApp':
        from .client import WhatsApp
        return WhatsApp
    elif name == 'Message':
        from .whatsapp_cloud_api.messages import Message
        return Message
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

__all__ = ["WhatsApp", "Message"]



