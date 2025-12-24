from typing import List, Optional
from pydantic import BaseModel
from hiws.types.message import Message
from hiws.types.status import Status


class Profile(BaseModel):
    name: str


class RequestContact(BaseModel):
    profile: Profile
    wa_id: str


class Metadata(BaseModel):
    display_phone_number: str
    phone_number_id: str


class Value(BaseModel):
    messaging_product: str
    metadata: Metadata
    contacts: List[RequestContact]
    messages: Optional[List[Message]] = None
    statuses: Optional[List[Status]] = None


class Change(BaseModel):
    value: Value
    field: str


class Entry(BaseModel):
    id: str
    changes: List[Change]


class Update(BaseModel):
    object: str
    entry: List[Entry]
    
    # helper properties to access nested data easily
    @property
    def message(self) -> Optional[Message]:
        for entry in self.entry:
            for change in entry.changes:
                if change.value.messages:
                    return change.value.messages[0]
        return None
    @property
    def changed_field(self) -> Optional[str]:
        for entry in self.entry:
            for change in entry.changes:
                return change.field
        return None
    @property
    def status(self) -> Optional[Status]:
        for entry in self.entry:
            for change in entry.changes:
                if change.value.statuses:
                    return change.value.statuses[0]
        return None
    @property
    def contact(self) -> Optional[RequestContact]:
        for entry in self.entry:
            for change in entry.changes:
                if change.value.contacts:
                    return change.value.contacts[0]
        return None
