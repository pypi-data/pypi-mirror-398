import dataclasses
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union


def asdict_omit_none(obj):
    """Recursively convert a dataclass to a dict, omitting fields with None values."""
    if dataclasses.is_dataclass(obj):
        result = {}
        for f in dataclasses.fields(obj):
            value = getattr(obj, f.name)
            if value is not None:
                result[f.name] = asdict_omit_none(value)
        return result
    if isinstance(obj, list):
        return [asdict_omit_none(v) for v in obj]
    if isinstance(obj, dict):
        return {k: asdict_omit_none(v) for k, v in obj.items() if v is not None}
    return obj


class Serializable:
    @property
    def object(self) -> Dict[str, Any]:  # convenient alias: obj.object -> dict
        return asdict_omit_none(self)

    def to_dict(self) -> Dict[str, Any]:
        return asdict_omit_none(self)


# Simple objects
@dataclass
class Text(Serializable):
    body: str
    preview_url: bool = False


@dataclass
class Reaction(Serializable):
    message_id: str
    emoji: str


@dataclass
class Location(Serializable):
    latitude: float
    longitude: float
    name: Optional[str] = None
    address: Optional[str] = None


# Media base + specializations
@dataclass
class Media(Serializable):
    id: Optional[str] = None
    link: Optional[str] = None

    def __post_init__(self):
        if self.id is None and self.link is None:
            raise ValueError("Either 'id' or 'link' is required for media.")


@dataclass
class Image(Media):
    caption: Optional[str] = None


@dataclass
class Audio(Media):
    pass


@dataclass
class Document(Media):
    caption: Optional[str] = None
    filename: Optional[str] = None


@dataclass
class Video(Media):
    caption: Optional[str] = None


@dataclass
class Sticker(Media):
    pass


# Template
@dataclass
class Language(Serializable):
    code: str
    policy: str = "deterministic"


@dataclass
class Template(Serializable):
    name: str
    language: Union[Language, Dict]
    components: Optional[List[Dict[str, Any]]] = None

    def __post_init__(self):
        if isinstance(self.language, dict):
            self.language = Language(**self.language)


# Contacts
@dataclass
class Name(Serializable):
    formatted_name: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_name: Optional[str] = None
    prefix: Optional[str] = None
    suffix: Optional[str] = None


@dataclass
class Phone(Serializable):
    phone: Optional[str] = None
    type: Optional[str] = None
    wa_id: Optional[str] = None


@dataclass
class Email(Serializable):
    email: Optional[str] = None
    type: Optional[str] = None


@dataclass
class Address(Serializable):
    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip: Optional[str] = None
    country: Optional[str] = None
    country_code: Optional[str] = None
    type: Optional[str] = None


@dataclass
class Org(Serializable):
    company: Optional[str] = None
    department: Optional[str] = None
    title: Optional[str] = None


@dataclass
class Url(Serializable):
    url: Optional[str] = None
    type: Optional[str] = None


@dataclass
class Contact(Serializable):
    name: Union[Name, Dict]
    addresses: Optional[List[Union[Address, Dict]]] = None
    birthday: Optional[str] = None  # YYYY-MM-DD
    emails: Optional[List[Union[Email, Dict]]] = None
    org: Optional[Union[Org, Dict]] = None
    phones: Optional[List[Union[Phone, Dict]]] = None
    urls: Optional[List[Union[Url, Dict]]] = None

    def __post_init__(self):
        if isinstance(self.name, dict):
            self.name = Name(**self.name)
        if self.addresses:
            self.addresses = [Address(**a) if isinstance(a, dict) else a for a in self.addresses]
        if self.emails:
            self.emails = [Email(**e) if isinstance(e, dict) else e for e in self.emails]
        if isinstance(self.org, dict):
            self.org = Org(**self.org)
        if self.phones:
            self.phones = [Phone(**p) if isinstance(p, dict) else p for p in self.phones]
        if self.urls:
            self.urls = [Url(**u) if isinstance(u, dict) else u for u in self.urls]


# Interactive
@dataclass
class InteractiveHeader(Serializable):
    type: str  # text, video, image, document
    text: Optional[str] = None
    video: Optional[Union[Video, Dict]] = None
    image: Optional[Union[Image, Dict]] = None
    document: Optional[Union[Document, Dict]] = None

    def __post_init__(self):
        if isinstance(self.video, dict):
            self.video = Video(**self.video)
        if isinstance(self.image, dict):
            self.image = Image(**self.image)
        if isinstance(self.document, dict):
            self.document = Document(**self.document)


@dataclass
class InteractiveBody(Serializable):
    text: str


@dataclass
class InteractiveFooter(Serializable):
    text: str


@dataclass
class ReplyButton(Serializable):
    type: str = "reply"
    title: str = ""
    id: str = ""


@dataclass
class SectionRow(Serializable):
    id: str
    title: str
    description: Optional[str] = None


@dataclass
class Product(Serializable):
    product_retailer_id: str


@dataclass
class Section(Serializable):
    title: Optional[str] = None
    rows: Optional[List[Union[SectionRow, Dict]]] = None
    product_items: Optional[List[Union[Product, Dict]]] = None

    def __post_init__(self):
        if self.rows:
            self.rows = [SectionRow(**r) if isinstance(r, dict) else r for r in self.rows]
        if self.product_items:
            self.product_items = [Product(**p) if isinstance(p, dict) else p for p in self.product_items]


@dataclass
class Action(Serializable):
    button: Optional[str] = None
    buttons: Optional[List[Union[ReplyButton, Dict]]] = None
    catalog_id: Optional[str] = None
    product_retailer_id: Optional[str] = None
    sections: Optional[List[Union[Section, Dict]]] = None

    def __post_init__(self):
        if self.buttons:
            self.buttons = [ReplyButton(**b) if isinstance(b, dict) else b for b in self.buttons]
        if self.sections:
            self.sections = [Section(**s) if isinstance(s, dict) else s for s in self.sections]


@dataclass
class Interactive(Serializable):
    type: str  # list, button, product, product_list
    action: Union[Action, Dict]
    header: Optional[Union[InteractiveHeader, Dict]] = None
    body: Optional[Union[InteractiveBody, Dict]] = None
    footer: Optional[Union[InteractiveFooter, Dict]] = None

    def __post_init__(self):
        if isinstance(self.action, dict):
            self.action = Action(**self.action)
        if isinstance(self.header, dict):
            self.header = InteractiveHeader(**self.header)
        if isinstance(self.body, dict):
            self.body = InteractiveBody(**self.body)
        if isinstance(self.footer, dict):
            self.footer = InteractiveFooter(**self.footer)
