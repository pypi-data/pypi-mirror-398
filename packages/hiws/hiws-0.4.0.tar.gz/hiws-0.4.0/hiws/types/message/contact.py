from pydantic import BaseModel, Field
from typing import List, Literal, Optional


class Address(BaseModel):
    city: Optional[str]
    country: Optional[str]
    country_code: Optional[str]
    state: Optional[str]
    street: Optional[str]
    type: Literal["HOME", "WORK"] = "HOME"
    zip: Optional[str]


class Email(BaseModel):
    email: str
    type: Literal["HOME", "WORK"] = "HOME"


class Name(BaseModel):
    formatted_name: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    middle_name: Optional[str]
    prefix: Optional[str]
    suffix: Optional[str]


class Org(BaseModel):
    company: Optional[str]
    department: Optional[str]
    title: Optional[str]


class Phone(BaseModel):
    phone: str
    wa_id: Optional[str]
    type: Literal["HOME", "WORK", "MOBILE"] = "HOME"


class Url(BaseModel):
    url: str
    type: Literal["HOME", "WORK"] = "HOME"


class Contact(BaseModel):
    addresses: Optional[List[Address]]
    birthday: Optional[str]
    emails: Optional[List[Email]]
    name: Optional[Name]
    org: Optional[Org]
    phones: List[Phone]
    urls: Optional[List[Url]]
