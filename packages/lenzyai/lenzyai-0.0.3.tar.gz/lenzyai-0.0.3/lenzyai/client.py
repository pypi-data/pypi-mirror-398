"""LenzyAI SDK client implementation."""

import os
import logging
import hmac
import hashlib
import json
import time
from typing import Optional, Dict, Any, List

import requests

from .types import Message, WebhookPayload


# Configure logging
logger = logging.getLogger("lenzyai")

# Webhook configuration
WEBHOOK_SIGNATURE_TOLERANCE_SECONDS = 300


class LenzyAI:
    """
    LenzyAI SDK client for recording conversation messages.

    Example:
        >>> client = LenzyAI(api_key="your-api-key")
        >>> client.record_messages(
        ...     project_id="proj_123",
        ...     external_conversation_id="conv_456",
        ...     messages=[
        ...         {"role": "USER", "content": "Hello"},
        ...         {"role": "ASSISTANT", "content": "Hi there!", "sent_at": "2025-11-27T10:30:00.000Z"},
        ...     ],
        ...     external_user_id="user_789",  # optional
        ... )
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        enabled: Optional[bool] = None,
    ) -> None:
        """
        Initialize the LenzyAI client.

        Args:
            api_key: API key for authentication. If not provided, reads from
                    LENZYAI_API_KEY environment variable.
            base_url: Base URL for the API. If not provided, reads from
                     LENZYAI_API_BASE_URL environment variable or defaults
                     to 'https://app.lenzy.ai'.
            enabled: Whether the SDK is enabled. If not provided, reads from
                    LENZYAI_ENABLED environment variable. If the value is
                    "false" or "0", the SDK is disabled. Defaults to True.

        Raises:
            ValueError: If API key is not provided and SDK is enabled.
        """
        # Determine if SDK is enabled
        enabled_env = self._get_env("LENZYAI_ENABLED")
        if enabled is not None:
            self._enabled = enabled
        elif enabled_env is not None:
            self._enabled = enabled_env not in ("false", "0")
        else:
            self._enabled = True

        # Get API key
        self._api_key = api_key or self._get_env("LENZYAI_API_KEY") or ""

        # Validate API key requirement
        if not self._api_key and self._enabled:
            raise ValueError(
                "API key is required. Please provide it in the constructor or "
                "set the LENZYAI_API_KEY environment variable."
            )

        # Get base URL
        self._base_url = (
            base_url
            or self._get_env("LENZYAI_API_BASE_URL")
            or "https://app.lenzy.ai"
        )

        # Create session for connection pooling
        self._session = requests.Session()
        self._session.headers.update({
            "Content-Type": "application/json",
        })

    def record_messages(
        self,
        project_id: str,
        external_conversation_id: str,
        messages: List[Message],
        external_user_id: Optional[str] = None,
    ) -> None:
        """
        Record messages for a conversation.

        Args:
            project_id: The project identifier
            external_conversation_id: The external conversation identifier
            messages: List of messages to record (at least 1 required).
                     Each message should be a dict with:
                     - role: "USER" or "ASSISTANT" (required)
                     - content: Message content (required)
                     - external_id: Optional unique identifier for the message
                     - sent_at: Optional ISO 8601 timestamp when the message was sent
            external_user_id: Optional external user identifier

        Returns:
            None

        Notes:
            - If the SDK is disabled, this method returns immediately without
              making any API calls.
            - All exceptions are caught and logged. The method never raises
              exceptions (except during initialization).
            - Errors are logged with the prefix "LenzyAI Error:".

        Example:
            >>> client.record_messages(
            ...     project_id="proj_123",
            ...     external_conversation_id="conv_456",
            ...     messages=[
            ...         {"role": "USER", "content": "Hello!"},
            ...         {"role": "ASSISTANT", "content": "Hi there!", "sent_at": "2025-11-27T10:30:00.000Z"},
            ...     ],
            ...     external_user_id="user_789",  # optional
            ... )
        """
        if not self._enabled:
            return

        try:
            # Validate inputs
            if not project_id:
                raise ValueError("project_id is required")
            if not external_conversation_id:
                raise ValueError("external_conversation_id is required")
            if not messages or len(messages) == 0:
                raise ValueError("At least 1 message is required")
            if external_user_id is not None and len(external_user_id) == 0:
                raise ValueError("external_user_id must not be empty if provided")

            # Transform messages to API format
            messages_payload: List[Dict[str, Any]] = []
            for message in messages:
                # Validate message structure
                if not isinstance(message, dict):
                    raise ValueError("Each message must be a dictionary")
                if "role" not in message:
                    raise ValueError("Each message must have a 'role' field")
                if "content" not in message:
                    raise ValueError("Each message must have a 'content' field")
                if message["role"] not in ("USER", "ASSISTANT"):
                    raise ValueError("Message role must be 'USER' or 'ASSISTANT'")

                # Build message payload
                message_dict: Dict[str, Any] = {
                    "role": message["role"],
                    "content": message["content"],
                    "externalConversationId": external_conversation_id,
                }

                # Add optional fields
                if "external_id" in message:
                    message_dict["externalId"] = message["external_id"]
                if "sent_at" in message:
                    message_dict["sentAt"] = message["sent_at"]

                if external_user_id:
                    message_dict["externalUserId"] = external_user_id

                messages_payload.append(message_dict)

            # Build URL
            url = f"{self._base_url}/api/projects/{project_id}/messages"

            # Make request
            response = self._session.post(
                url,
                json=messages_payload,
                headers={"x-api-key": self._api_key},
                timeout=30,
            )

            # Check for errors
            if not response.ok:
                error_data = {}
                try:
                    error_data = response.json()
                except Exception:
                    pass

                logger.error(
                    f"LenzyAI Error: Error recording messages. "
                    f"Status: {response.status_code}, "
                    f"Response: {error_data}"
                )
                return

        except requests.exceptions.RequestException as e:
            logger.error(f"LenzyAI Error: Error recording messages. {e}")
        except Exception as e:
            logger.error(f"LenzyAI Error: Error recording messages. {e}")

    @staticmethod
    def _get_env(key: str) -> Optional[str]:
        """
        Get environment variable value.

        Args:
            key: Environment variable name.

        Returns:
            Environment variable value or None if not set.
        """
        return os.environ.get(key)

    def __enter__(self) -> "LenzyAI":
        """Context manager entry."""
        return self

    def __exit__(self, *args: Any) -> None:
        """Context manager exit - closes the session."""
        self._session.close()

    def close(self) -> None:
        """Close the underlying HTTP session."""
        self._session.close()

    @staticmethod
    def validate_webhook_payload(
        payload: str,
        signature: str,
        secret: str,
    ) -> WebhookPayload:
        """
        Validate a webhook signature from Lenzy AI and return the parsed payload.

        Args:
            payload: The raw webhook payload (JSON string)
            signature: The X-Lenzy-Signature header value (format: "t=<timestamp>,v1=<signature>")
            secret: Your webhook signing secret

        Returns:
            The parsed webhook payload as a WebhookPayload dict

        Raises:
            ValueError: If signature format is invalid
            ValueError: If signature is expired (older than 5 minutes)
            ValueError: If signature validation fails

        Example:
            >>> payload = request.body  # Raw JSON string
            >>> signature = request.headers.get('X-Lenzy-Signature')
            >>> secret = os.environ.get('LENZY_WEBHOOK_SECRET')
            >>>
            >>> try:
            ...     data = LenzyAI.validate_webhook_payload(payload, signature, secret)
            ...     # Process validated webhook
            ...     for event in data['events']:
            ...         print(f"Event: {event['description']}")
            ... except ValueError as e:
            ...     print(f"Invalid webhook: {e}")
        """
        # Parse signature header format: "t=<timestamp>,v1=<signature>"
        parts = signature.split(',')
        if len(parts) != 2:
            raise ValueError('Invalid signature format')

        timestamp_part = parts[0]
        signature_part = parts[1]

        if not timestamp_part.startswith('t=') or not signature_part.startswith('v1='):
            raise ValueError('Invalid signature format')

        try:
            timestamp = int(timestamp_part[2:])
        except ValueError:
            raise ValueError('Invalid signature format')

        provided_signature = signature_part[3:]

        # Check timestamp tolerance (prevent replay attacks)
        current_time = int(time.time())
        if abs(current_time - timestamp) > WEBHOOK_SIGNATURE_TOLERANCE_SECONDS:
            raise ValueError('Signature expired')

        # Reconstruct the signed payload: "timestamp.payload"
        signed_payload = f"{timestamp}.{payload}"

        # Compute expected signature using HMAC-SHA256
        expected_signature = hmac.new(
            secret.encode('utf-8'),
            signed_payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        # Timing-safe comparison to prevent timing attacks
        if len(expected_signature) != len(provided_signature):
            raise ValueError('Invalid signature')

        is_signature_valid = hmac.compare_digest(
            expected_signature,
            provided_signature
        )

        if not is_signature_valid:
            raise ValueError('Invalid signature')

        # Parse the JSON payload
        raw_payload = json.loads(payload)

        # Convert to Python snake_case convention with explicit field mapping
        return {
            'alert': {
                'id': raw_payload['alert']['id'],
                'name': raw_payload['alert']['name'],
                'description': raw_payload['alert']['description'],
            },
            'events': [
                {
                    'id': event['id'],
                    'description': event['description'],
                    'reason': event['reason'],
                    'user_quote': event['userQuote'],
                    'user_message_id': event['userMessageId'],
                    'external_user_message_id': event.get('externalUserMessageId'),
                    'assistant_quote': event['assistantQuote'],
                    'assistant_message_id': event['assistantMessageId'],
                    'external_assistant_message_id': event.get('externalAssistantMessageId'),
                    'user_id': event.get('userId'),
                    'external_user_id': event.get('externalUserId'),
                    'happened_at': event['happenedAt'],
                }
                for event in raw_payload['events']
            ]
        }
