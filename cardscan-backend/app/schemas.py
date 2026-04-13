from typing import Optional

from pydantic import BaseModel, Field


class ContactDetails(BaseModel):
    name: Optional[str] = None
    company: Optional[str] = None
    title: Optional[str] = None
    phones: list[str] = Field(default_factory=list)
    emails: list[str] = Field(default_factory=list)
    websites: list[str] = Field(default_factory=list)
    address: Optional[str] = None
    raw_lines: list[str] = Field(default_factory=list)
    confidence_notes: list[str] = Field(default_factory=list)


class WhatsAppSendResult(BaseModel):
    sent: bool = False
    recipient: Optional[str] = None
    provider_message_id: Optional[str] = None
    raw_response: dict = Field(default_factory=dict)


class ScanBusinessCardResponse(BaseModel):
    raw_text: str
    contact: ContactDetails
    whatsapp: WhatsAppSendResult = Field(default_factory=WhatsAppSendResult)

