import json
import logging
from importlib import import_module
from django.conf import settings
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .signals import webhook_event_received
from .whatsapp_cloud_api.webhooks.dispatcher import ingest_payload


@csrf_exempt
def whatsapp_webhook(request: HttpRequest) -> HttpResponse:
    """
    Webhook endpoint for WhatsApp Cloud API.

    - GET: Verification handshake using hub.mode, hub.challenge, hub.verify_token
    - POST: Receive event notifications (messages, status updates, etc.)
    """
    if request.method == "GET":
        mode = request.GET.get("hub.mode")
        token = request.GET.get("hub.verify_token")
        challenge = request.GET.get("hub.challenge")

        if mode == "subscribe" and token == getattr(settings, "WHATSAPP_CLOUD_API_VERIFY_TOKEN", getattr(settings, "WHATSAPP_VERIFY_TOKEN", None)):
            return HttpResponse(challenge or "", status=200)
        return HttpResponse(status=403)

    if request.method == "POST":
        try:
            payload = json.loads(request.body.decode("utf-8")) if request.body else {}
        except json.JSONDecodeError:
            return HttpResponse(status=400)

        # Emit signal so host projects can listen and act
        try:
            webhook_event_received.send(sender=None, payload=payload, request=request)
        except Exception:
            logging.getLogger(__name__).exception("Error while sending webhook_event_received signal")

        # Persist structured events using the internal dispatcher
        try:
            ingest_payload(payload)
        except Exception:
            logging.getLogger(__name__).exception("Error ingesting webhook payload in FBV handler")

        # Optional pluggable handler via settings.WHATSAPP_WEBHOOK_HANDLER = "path.to.callable"
        handler_path = getattr(settings, "WHATSAPP_WEBHOOK_HANDLER", None)
        if handler_path:
            try:
                module_path, func_name = handler_path.rsplit(".", 1)
                module = import_module(module_path)
                handler = getattr(module, func_name)
                response = handler(request=request, payload=payload)
                if isinstance(response, HttpResponse):
                    return response
            except Exception:
                logging.getLogger(__name__).exception("Error in WHATSAPP_WEBHOOK_HANDLER: %s", handler_path)

        return JsonResponse({"status": "received"}, status=200)

    return HttpResponse(status=405)


