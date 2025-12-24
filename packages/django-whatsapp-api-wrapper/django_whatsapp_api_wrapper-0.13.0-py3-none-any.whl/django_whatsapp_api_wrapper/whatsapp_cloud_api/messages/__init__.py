import logging
import requests
import dataclasses
from . import types
from .types import asdict_omit_none

MESSAGE_TYPE_MAP = {
    "text": types.Text,
    "image": types.Image,
    "audio": types.Audio,
    "document": types.Document,
    "video": types.Video,
    "sticker": types.Sticker,
    "location": types.Location,
    "contacts": types.Contact,
    "reaction": types.Reaction,
    "template": types.Template,
    "interactive": types.Interactive,
}

class Message:
    # type: ignore
    def __init__(
        self,
        messaging_product: str = "whatsapp",
        to: str = "",
        type: str = "",
        data: dict = {},
        instance: "WhatsApp" = None,
        recipient_type: str = "individual",
    ):
        if instance is not None:
            from ...client import WhatsApp
            assert isinstance(instance, WhatsApp)
        self.instance = instance
        self.type = type
        self.data = data
        self.messaging_product = messaging_product
        self.recipient_type = recipient_type
        self.to = to

    def send(self) -> dict:
        try:
            sender = self.instance.phone_number_id
        except AttributeError:
            logging.error("Phone number id not found on WhatsApp instance.")
            return {"error": "WhatsApp instance not configured with phone_number_id"}

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": self.recipient_type,
            "to": self.to,
            "type": self.type,
        }

        dataclass_to_instantiate = MESSAGE_TYPE_MAP.get(self.type)

        if dataclass_to_instantiate:
            try:
                if self.type == "contacts":
                    if not isinstance(self.data, list):
                        raise ValueError("data for contacts message must be a list of contact objects or dicts")
                    contacts_serialized = []
                    for item in self.data:
                        if dataclasses.is_dataclass(item) or isinstance(item, types.Serializable):
                            contacts_serialized.append(asdict_omit_none(item))
                        elif isinstance(item, dict):
                            contacts_serialized.append(asdict_omit_none(types.Contact(**item)))
                        else:
                            raise ValueError("Each contact must be a dataclass instance or dict")
                    payload[self.type] = contacts_serialized
                else:
                    if dataclasses.is_dataclass(self.data) or isinstance(self.data, types.Serializable):
                        payload[self.type] = asdict_omit_none(self.data)
                    elif isinstance(self.data, dict):
                        dataclass_obj = dataclass_to_instantiate(**self.data)
                        payload[self.type] = asdict_omit_none(dataclass_obj)
                    else:
                        raise ValueError("data must be a dataclass instance or dict for message type '%s'" % self.type)
            except (TypeError, ValueError) as e:
                error_msg = f"Invalid data for message type '{self.type}': {e}"
                logging.error(f"{error_msg} | Data: {self.data}")
                return {"error": error_msg}
        else:
            logging.warning(f"Message type '{self.type}' not in defined types map, sending raw data.")
            payload[self.type] = self.data

        logging.info(f"Sending message to {self.to}")
        r = requests.post(self.instance.url, headers=self.instance.headers, json=payload)
        if r.status_code == 200:
            logging.info(f"Message sent to {self.to}")
            return r.json()

        logging.info(f"Message not sent to {self.to}")
        logging.info(f"Status code: {r.status_code}")
        try:
            error_response = r.json()
            logging.error(f"Response: {error_response}")
            return error_response
        except requests.exceptions.JSONDecodeError:
            logging.error(f"Response: {r.text}")
            return {"error": "Failed to decode JSON response", "status_code": r.status_code, "text": r.text}
    
    
