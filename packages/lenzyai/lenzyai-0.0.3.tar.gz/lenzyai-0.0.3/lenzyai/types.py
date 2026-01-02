"""Type definitions for LenzyAI SDK."""

from typing import List, Optional, TypedDict
from typing_extensions import Literal
from datetime import datetime


class MessageRole:
    """Message role constants."""
    USER = "USER"
    ASSISTANT = "ASSISTANT"


MessageRoleType = Literal["USER", "ASSISTANT"]


class Message(TypedDict, total=False):
    """
    A single message in a conversation.

    Attributes:
        role: The role of the message sender ("USER" or "ASSISTANT")
        content: The content of the message
        external_id: Optional unique identifier for the message
        sent_at: Optional ISO 8601 timestamp when the message was sent
    """
    role: MessageRoleType
    content: str
    external_id: str
    sent_at: str


class WebhookAlert(TypedDict):
    """Alert information in webhook payload."""
    id: str
    name: str
    description: str


class WebhookEvent(TypedDict, total=False):
    """Event information in webhook payload."""
    id: str
    description: str
    reason: str
    user_quote: str
    user_message_id: str
    external_user_message_id: str
    assistant_quote: str
    assistant_message_id: str
    external_assistant_message_id: str
    user_id: str
    external_user_id: str
    happened_at: str


class WebhookPayload(TypedDict):
    """
    Webhook payload structure sent by Lenzy AI alerts.

    Attributes:
        alert: Information about the alert that triggered
        events: List of events that were detected
    """
    alert: WebhookAlert
    events: List[WebhookEvent]
