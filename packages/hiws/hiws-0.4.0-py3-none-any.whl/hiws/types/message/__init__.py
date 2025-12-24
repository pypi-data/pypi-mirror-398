from pydantic import BaseModel, Field
from typing import List, Optional, Union, Literal
from hiws.types.message.contact import Contact


class BaseMessage(BaseModel):
    from_phone_number: str = Field(alias="from")
    id: str
    timestamp: str

class Text(BaseModel):
    body: str

class TextMessage(BaseMessage):
    text: Text
    type: Literal["text"] = "text"
    
class Reaction(BaseModel):
    message_id: str
    emoji: str
    
class ReactionMessage(BaseMessage):
    reaction: Reaction
    type: Literal["reaction"] = "reaction"
    
class Media(BaseModel):
    id: str
    mime_type: str
    caption: str
    sha256: str
    
class ImageMessage(BaseMessage):
    image: Media
    type: Literal["image"] = "image"

class Audio(BaseModel):
    id: str
    mime_type: str
    sha256: Optional[str] = None
    voice: Optional[bool] = None

class AudioMessage(BaseMessage):
    audio: Audio
    type: Literal["audio"] = "audio"

class Document(BaseModel):
    id: str
    mime_type: str
    sha256: Optional[str] = None
    filename: Optional[str] = None
    caption: Optional[str] = None

class DocumentMessage(BaseMessage):
    document: Document
    type: Literal["document"] = "document"
    
class StickerMessage(BaseMessage):
    sticker: Media
    type: Literal["sticker"] = "sticker"
    
class MessageError(BaseModel):
    code: int
    details: str
    title: str

class UnknownMessage(BaseModel):
    errors: List[MessageError]
    type: Literal["unknown"] = "unknown"
    
class Location(BaseModel):
    latitude: float
    longitude: float
    name: Optional[str]
    address: Optional[str]
    
class LocationMessage(BaseMessage):
    location: Location
    type: Literal["location"] = "location"
    
class ContactMessage(BaseMessage):
    contacts: List[Contact]
    type: Literal["contacts"] = "contacts"
    
class Button(BaseModel):
    text: str
    payload: Optional[str]
    
class QuickReplyButtonMessage(BaseMessage):
    button: Button
    type: Literal["button"] = "button"
    
class SystemUpdate(BaseModel):
    body: str
    type: Literal["system"] = "system"
    new_wa_id: Optional[str]
    
class SystemMessage(BaseMessage):
    system: SystemUpdate
    type: Literal["system"] = "system"
    

Message = Union[
    TextMessage,
    ReactionMessage,
    ImageMessage,
    AudioMessage,
    DocumentMessage,
    StickerMessage,
    LocationMessage,
    QuickReplyButtonMessage,
    SystemMessage,
    UnknownMessage,
]
    