import json
import logging
from importlib import import_module

from django.conf import settings
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from rest_framework.views import APIView

from .dispatcher import ingest_payload


@method_decorator(csrf_exempt, name="dispatch")
class WhatsappWebhookView(APIView):
    def get(self, request: HttpRequest) -> HttpResponse:
        mode = request.GET.get("hub.mode")
        token = request.GET.get("hub.verify_token")
        challenge = request.GET.get("hub.challenge")

        if mode == "subscribe" and token == getattr(settings, "WHATSAPP_CLOUD_API_VERIFY_TOKEN", getattr(settings, "WHATSAPP_VERIFY_TOKEN", None)):
            return HttpResponse(challenge or "", status=200)
        return HttpResponse(status=403)

    def post(self, request: HttpRequest) -> HttpResponse:
        try:
            payload = json.loads(request.body.decode("utf-8")) if request.body else {}
        except json.JSONDecodeError:
            return HttpResponse(status=400)

        try:
            ingest_payload(payload)
        except Exception:
            logging.getLogger(__name__).exception("Error ingesting webhook payload")

        # Optional handler for backward compatibility
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


