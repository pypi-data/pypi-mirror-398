from django.urls import path

from .views import WhatsappWebhookView


urlpatterns = [
    path("", WhatsappWebhookView.as_view(), name="whatsapp_webhook_api"),
]


