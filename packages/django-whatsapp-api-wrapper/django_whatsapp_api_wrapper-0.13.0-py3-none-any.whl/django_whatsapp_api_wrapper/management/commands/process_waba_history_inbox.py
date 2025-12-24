from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from ...whatsapp_cloud_api.webhooks.models import (
    WebhookEvent,
    WhatsAppBusinessAccount,
    WabaHistoryInbox,
    WabaHistoryBatch,
    WabaHistoryItem,
    WabaHistoryThread,
    WabaHistoryMessage,
    WabaHistoryAssetMessage,
)


class Command(BaseCommand):
    help = "Process pending WABA history inbox items into normalized tables"

    def add_arguments(self, parser):
        parser.add_argument("--batch-size", type=int, default=200)

    def handle(self, *args, **options):
        batch_size = options["batch_size"]
        pending = (
            WabaHistoryInbox.objects.select_for_update(skip_locked=True)
            .filter(status=WabaHistoryInbox.STATUS_PENDING)
            .order_by("created_at")[:batch_size]
        )
        processed = 0
        failed = 0
        with transaction.atomic():
            for inbox in pending:
                inbox.status = WabaHistoryInbox.STATUS_PROCESSING
                inbox.attempts += 1
                inbox.save(update_fields=["status", "attempts", "updated_at"])

        # Process outside of atomic batch update to reduce lock time
        for inbox in pending:
            try:
                self._process_inbox_item(inbox)
                inbox.status = WabaHistoryInbox.STATUS_DONE
                inbox.last_error = None
                inbox.save(update_fields=["status", "last_error", "updated_at"])
                processed += 1
            except Exception as exc:  # noqa: BLE001
                inbox.status = WabaHistoryInbox.STATUS_FAILED
                inbox.last_error = str(exc)
                inbox.save(update_fields=["status", "last_error", "updated_at"])
                failed += 1
        self.stdout.write(self.style.SUCCESS(f"Processed: {processed}, Failed: {failed}"))

    def _process_inbox_item(self, inbox: WabaHistoryInbox) -> None:
        value = inbox.payload or {}
        waba = inbox.waba
        if waba is None:
            # ensure waba by entry id
            waba, _ = WhatsAppBusinessAccount.objects.get_or_create(waba_id=inbox.entry_id)
            inbox.waba = waba
            inbox.save(update_fields=["waba"]) 

        # Create a WebhookEvent for this history batch
        event, _ = WebhookEvent.objects.update_or_create(
            event_kind=WebhookEvent.KIND_WABA,
            subtype="history",
            entry_id=inbox.entry_id,
            waba=waba,
            event_timestamp=inbox.event_timestamp,
            defaults={
                "object": "whatsapp_business_account",
                "field": "history",
                "raw_payload": value,
                "display_phone_number": inbox.display_phone_number,
                "phone_number_id": inbox.phone_number_id,
            },
        )

        # Process asset messages (media contents revealed separately)
        for msg in value.get("messages", []) or []:
            msg_type = msg.get("type")
            blob = None
            for kind in ("image", "audio", "video", "document", "sticker"):
                if kind in msg:
                    blob = msg.get(kind)
                    break
            WabaHistoryAssetMessage.objects.update_or_create(
                event=event,
                wamid=msg.get("id"),
                defaults={
                    "from_number": msg.get("from"),
                    "device_timestamp": self._to_dt(msg.get("timestamp")),
                    "msg_type": msg_type or "unknown",
                    "content": blob or {},
                },
            )

        # Process history batches (threads and messages)
        history_list = value.get("history") or []
        if not history_list:
            return

        batch, _ = WabaHistoryBatch.objects.update_or_create(
            event=event,
            defaults={
                "display_phone_number": inbox.display_phone_number,
                "phone_number_id": inbox.phone_number_id,
            },
        )

        for item in history_list:
            meta = item.get("metadata") or {}
            errors = item.get("errors")
            history_item = WabaHistoryItem.objects.create(
                batch=batch,
                phase=meta.get("phase"),
                chunk_order=meta.get("chunk_order"),
                progress=meta.get("progress"),
                errors=errors,
            )
            for thread in item.get("threads", []) or []:
                th = WabaHistoryThread.objects.create(
                    item=history_item,
                    whatsapp_user_phone=thread.get("id", ""),
                )
                for m in thread.get("messages", []) or []:
                    m_type = m.get("type")
                    content = m.get(m_type) if m_type and m_type != "media_placeholder" else None
                    status = (m.get("history_context") or {}).get("status")
                    WabaHistoryMessage.objects.create(
                        thread=th,
                        from_number=m.get("from"),
                        to_number=m.get("to"),
                        wamid=m.get("id"),
                        device_timestamp=self._to_dt(m.get("timestamp")),
                        msg_type=m_type or "unknown",
                        content=content,
                        status=status,
                    )

    def _to_dt(self, ts):
        if not ts:
            return None
        try:
            return timezone.datetime.fromtimestamp(int(ts), tz=timezone.utc)
        except Exception:  # noqa: BLE001
            return None

