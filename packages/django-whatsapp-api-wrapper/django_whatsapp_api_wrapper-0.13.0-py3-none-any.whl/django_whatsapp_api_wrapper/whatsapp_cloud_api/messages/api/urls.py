from django.urls import path

from .views import (
    MessageSendView,
    MessageTextReplyView,
    MessageTextView,
    MessageTemplateView,
)


urlpatterns = [
    path("send/", MessageSendView.as_view(), name="wa_messages_send"),
    path("text/", MessageTextView.as_view(), name="wa_messages_text"),
    path("text/reply/", MessageTextReplyView.as_view(), name="wa_messages_text_reply"),
    path("template/", MessageTemplateView.as_view(), name="wa_messages_template"),
]


