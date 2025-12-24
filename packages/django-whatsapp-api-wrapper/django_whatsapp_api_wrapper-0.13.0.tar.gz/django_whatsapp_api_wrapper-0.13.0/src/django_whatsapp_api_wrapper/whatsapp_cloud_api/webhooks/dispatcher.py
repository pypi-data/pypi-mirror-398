import datetime
from typing import Any, Dict, Optional

from django.utils.dateparse import parse_datetime
from django.utils.timezone import make_aware

from .models import (
    WebhookEvent,
    WhatsAppContact,
    ConversationInfo,
    MessageText,
    MessageReaction,
    MessageMedia,
    MessageLocation,
    MessageContacts,
    MessageSystem,
    MessageOrder,
    MessageUnknown,
    StatusUpdate,
)
from .dispatcher_waba import handle_waba_change


def _to_dt(ts: Optional[str]) -> Optional[datetime.datetime]:
    if not ts:
        return None
    # WhatsApp sends unix epoch seconds as strings; try int first
    try:
        seconds = int(ts)
        return datetime.datetime.fromtimestamp(seconds, tz=datetime.timezone.utc)
    except (ValueError, TypeError):
        pass
    dt = parse_datetime(ts)
    return make_aware(dt) if dt and dt.tzinfo is None else dt


def _ensure_contact(contacts: Optional[list[dict]]) -> Optional[WhatsAppContact]:
    if not contacts:
        return None
    first = contacts[0]
    wa_id = first.get("wa_id")
    profile = first.get("profile") or {}
    if not wa_id:
        return None
    contact, _ = WhatsAppContact.objects.get_or_create(
        wa_id=wa_id, defaults={"profile_name": profile.get("name")}
    )
    # Update name if changed
    new_name = profile.get("name")
    if new_name and contact.profile_name != new_name:
        contact.profile_name = new_name
        contact.save(update_fields=["profile_name"])
    return contact


def _get_media_blob(msg: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
    for kind in ("image", "audio", "video", "document", "sticker"):
        if kind in msg:
            return kind, msg[kind]
    return "unknown", {}


def ingest_payload(payload: Dict[str, Any]) -> None:
    # Iterate entries and changes
    object_kind = payload.get("object")
    for entry in payload.get("entry", []) or []:
        entry_id = entry.get("id")
        for change in entry.get("changes", []) or []:
            value = change.get("value") or {}
            field = change.get("field")

            # WABA object: handle non-message/status fields via WABA dispatcher; 
            # keep messages/status here for proper KIND_MESSAGE/KIND_STATUS ingestion
            if object_kind == "whatsapp_business_account" and field not in {"messages", "statuses"}:
                handle_waba_change(entry, change, object_kind)
                continue

            metadata = value.get("metadata") or {}
            phone_number_id = metadata.get("phone_number_id")
            display_phone_number = metadata.get("display_phone_number")
            contacts = value.get("contacts") or []
            contact = _ensure_contact(contacts)

            # Messages
            for msg in value.get("messages", []) or []:
                msg_type = msg.get("type")
                wamid = msg.get("id")
                from_wa_id = msg.get("from")
                ts = _to_dt(msg.get("timestamp"))

                event, created = WebhookEvent.objects.update_or_create(
                    wamid=wamid,
                    event_kind=WebhookEvent.KIND_MESSAGE,
                    subtype=msg_type,
                    defaults={
                        "object": object_kind,
                        "entry_id": entry_id,
                        "field": field,
                        "phone_number_id": phone_number_id,
                        "display_phone_number": display_phone_number,
                        "from_wa_id": from_wa_id,
                        "event_timestamp": ts,
                        "raw_payload": msg,
                    },
                )

                if msg_type == "text":
                    body = (msg.get("text") or {}).get("body", "")
                    MessageText.objects.update_or_create(
                        event=event, defaults={"body": body}
                    )
                elif msg_type == "reaction":
                    reaction = msg.get("reaction") or {}
                    MessageReaction.objects.update_or_create(
                        event=event,
                        defaults={
                            "reacted_message_id": reaction.get("message_id", ""),
                            "emoji": reaction.get("emoji", ""),
                        },
                    )
                elif msg_type in {"image", "audio", "video", "document", "sticker"}:
                    media_type, blob = _get_media_blob(msg)
                    MessageMedia.objects.update_or_create(
                        event=event,
                        defaults={
                            "media_type": media_type,
                            "media_id": blob.get("id", ""),
                            "mime_type": blob.get("mime_type"),
                            "sha256": blob.get("sha256"),
                            "caption": blob.get("caption"),
                        },
                    )
                elif msg_type == "location":
                    loc = msg.get("location") or {}
                    MessageLocation.objects.update_or_create(
                        event=event,
                        defaults={
                            "latitude": loc.get("latitude", 0.0),
                            "longitude": loc.get("longitude", 0.0),
                            "name": loc.get("name"),
                            "address": loc.get("address"),
                        },
                    )
                elif msg_type == "contacts":
                    MessageContacts.objects.update_or_create(
                        event=event, defaults={"contacts": msg.get("contacts") or []}
                    )
                elif msg_type == "system":
                    system = msg.get("system") or {}
                    MessageSystem.objects.update_or_create(
                        event=event,
                        defaults={
                            "system_type": system.get("type", ""),
                            "body": system.get("body"),
                            "new_wa_id": system.get("new_wa_id"),
                        },
                    )
                elif msg_type == "order":
                    MessageOrder.objects.update_or_create(
                        event=event, defaults={"order": msg.get("order") or {}}
                    )
                else:
                    MessageUnknown.objects.update_or_create(
                        event=event, defaults={"errors": msg.get("errors")}
                    )

            # Status updates
            for st in value.get("statuses", []) or []:
                wamid = st.get("id")
                ts = _to_dt(st.get("timestamp"))
                event, created = WebhookEvent.objects.update_or_create(
                    wamid=wamid,
                    event_kind=WebhookEvent.KIND_STATUS,
                    subtype=st.get("status"),
                    defaults={
                        "object": object_kind,
                        "entry_id": entry_id,
                        "field": field,
                        "phone_number_id": phone_number_id,
                        "display_phone_number": display_phone_number,
                        "from_wa_id": st.get("recipient_id"),
                        "event_timestamp": ts,
                        "raw_payload": st,
                    },
                )

                conv_info = None
                conversation = st.get("conversation") or {}
                if conversation.get("id"):
                    conv_defaults = {
                        "origin_type": (conversation.get("origin") or {}).get("type"),
                        "category": (st.get("pricing") or {}).get("category"),
                        "pricing_model": (st.get("pricing") or {}).get("pricing_model"),
                        "billable": (st.get("pricing") or {}).get("billable"),
                    }
                    exp_ts = conversation.get("expiration_timestamp")
                    if exp_ts is not None:
                        conv_defaults["expiration_timestamp"] = _to_dt(str(exp_ts))
                    conv_info, _ = ConversationInfo.objects.update_or_create(
                        conversation_id=conversation.get("id"), defaults=conv_defaults
                    )

                error = None
                errors = st.get("errors") or []
                if errors:
                    error = errors[0]

                StatusUpdate.objects.update_or_create(
                    event=event,
                    defaults={
                        "status": st.get("status"),
                        "recipient_id": st.get("recipient_id"),
                        "error_code": error.get("code") if error else None,
                        "error_title": error.get("title") if error else None,
                        "error_message": error.get("message") if error else None,
                        "error_details": (error.get("error_data") if error else None),
                        "conversation": conv_info,
                    },
                )


