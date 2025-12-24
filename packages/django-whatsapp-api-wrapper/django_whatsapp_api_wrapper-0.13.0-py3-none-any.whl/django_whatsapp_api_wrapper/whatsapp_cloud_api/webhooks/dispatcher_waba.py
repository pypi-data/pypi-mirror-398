import datetime
from typing import Any, Dict

import hashlib
import json

from .models import (
    WebhookEvent,
    WhatsAppBusinessAccount,
    WabaAccountUpdate,
    WabaGenericEvent,
    WabaHistoryBatch,
    WabaHistoryItem,
    WabaHistoryThread,
    WabaHistoryMessage,
    WabaHistoryAssetMessage,
    WabaHistoryInbox,
    WabaSmbStateSyncItem,
    WabaSmbMessageEcho,
)


def _to_dt_from_seconds(seconds: int | None):
    if seconds is None:
        return None
    return datetime.datetime.fromtimestamp(int(seconds), tz=datetime.timezone.utc)


def handle_waba_change(entry: Dict[str, Any], change: Dict[str, Any], object_kind: str) -> None:
    waba_id = entry.get("id")
    entry_time = entry.get("time")
    ts = _to_dt_from_seconds(entry_time)
    if not waba_id:
        return

    waba, _ = WhatsAppBusinessAccount.objects.get_or_create(waba_id=waba_id)

    field = change.get("field")
    value = change.get("value") or {}

    meta = (value.get("metadata") or {})
    display_phone_number = meta.get("display_phone_number")
    phone_number_id = meta.get("phone_number_id")

    # Derive optional wamid/from_wa_id for certain WABA fields
    derived_wamid = None
    derived_from_wa_id = None
    if field == "smb_message_echoes":
        msgs = value.get("message_echoes") or []
        if len(msgs) == 1:
            derived_wamid = msgs[0].get("id")
            derived_from_wa_id = msgs[0].get("from")

    # Always create a fresh WebhookEvent for each WABA change (no upsert)
    event = WebhookEvent.objects.create(
        object=object_kind,
        entry_id=waba_id,
        field=field,
        waba=waba,
        phone_number_id=phone_number_id,
        display_phone_number=display_phone_number,
        event_kind=WebhookEvent.KIND_WABA,
        subtype=field,
        wamid=derived_wamid,
        from_wa_id=derived_from_wa_id,
        event_timestamp=ts,
        raw_payload=value,
    )

    if field == "account_update":
        WabaAccountUpdate.objects.update_or_create(
            event=event,
            defaults={
                "phone_number": value.get("phone_number"),
                "event_name": value.get("event"),
                "business_verification_status": value.get("business_verification_status"),
                "ban_info": value.get("ban_info"),
                "violation_info": value.get("violation_info"),
                "lock_info": value.get("lock_info"),
                "restriction_info": value.get("restriction_info"),
                "partner_client_certification_info": value.get("partner_client_certification_info"),
                "waba_info": value.get("waba_info"),
                "auth_international_rate_eligibility": value.get("auth_international_rate_eligibility"),
                "volume_tier_info": value.get("volume_tier_info"),
            },
        )
    elif field == "history":
        # Enfileirar para processamento assíncrono
        raw_value = value
        dedupe_source = {
            "field": field,
            "entry_id": waba_id,
            "value": raw_value,
        }
        dedupe_key = hashlib.sha256(json.dumps(dedupe_source, sort_keys=True).encode("utf-8")).hexdigest()

        WabaHistoryInbox.objects.update_or_create(
            dedupe_key=dedupe_key,
            defaults={
                "waba": waba,
                "entry_id": waba_id,
                "phone_number_id": phone_number_id,
                "display_phone_number": display_phone_number,
                "event_timestamp": ts,
                "payload": raw_value,
                "status": WabaHistoryInbox.STATUS_PENDING,
            },
        )
    else:
        # Keep generic capture of value for any other WABA field
        WabaGenericEvent.objects.create(event=event, value=value)

    # SMB app state sync
    if field == "smb_app_state_sync":
        for item in (value.get("state_sync") or []):
            contact = item.get("contact") or {}
            metadata = item.get("metadata") or {}
            WabaSmbStateSyncItem.objects.update_or_create(
                event=event,
                contact_phone_number=contact.get("phone_number", ""),
                action=item.get("action", ""),
                change_timestamp=_to_dt_from_seconds(
                    int(metadata.get("timestamp")) if metadata.get("timestamp") is not None else None
                ),
                defaults={
                    "item_type": item.get("type"),
                    "contact_full_name": contact.get("full_name"),
                    "contact_first_name": contact.get("first_name"),
                },
            )

    # SMB message echoes
    if field == "smb_message_echoes":
        for msg in (value.get("message_echoes") or []):
            m_type = msg.get("type")
            content = msg.get(m_type) if m_type else None
            WabaSmbMessageEcho.objects.update_or_create(
                event=event,
                wamid=msg.get("id"),
                defaults={
                    "from_number": msg.get("from"),
                    "to_number": msg.get("to"),
                    "webhook_timestamp": _to_dt_from_seconds(
                        int(msg.get("timestamp")) if msg.get("timestamp") is not None else None
                    ),
                    "msg_type": m_type or "unknown",
                    "content": content,
                },
            )


