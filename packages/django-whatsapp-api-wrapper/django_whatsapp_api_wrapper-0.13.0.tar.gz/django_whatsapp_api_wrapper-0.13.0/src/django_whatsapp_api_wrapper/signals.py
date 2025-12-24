from django.dispatch import Signal


# Emitted for every POST received on the webhook endpoint.
# Receivers will get keyword arguments: payload (dict) and request (HttpRequest)
webhook_event_received = Signal()


