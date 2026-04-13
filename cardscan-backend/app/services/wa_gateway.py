from dataclasses import dataclass

import httpx

from app.core.config import Settings


@dataclass
class SendResult:
    sent: bool
    recipient: str | None
    provider_message_id: str | None
    raw_response: dict


class WAGatewayClient:
    def __init__(self, settings: Settings):
        self.settings = settings

    async def send_text_message(self, recipient: str, message: str) -> SendResult:
        if not self.settings.wa_gateway_base_url:
            raise RuntimeError("WA_GATEWAY_BASE_URL belum diisi.")

        url = self.settings.wa_gateway_base_url.rstrip("/") + "/" + self.settings.wa_gateway_send_path.lstrip("/")
        headers = {"Content-Type": "application/json"}
        if self.settings.wa_gateway_token:
            headers["Authorization"] = f"Bearer {self.settings.wa_gateway_token}"

        payload = {"to": recipient, "message": message}

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()

        body = response.json() if response.content else {}
        provider_message_id = None
        if isinstance(body, dict):
            provider_message_id = body.get("message_id") or body.get("id") or body.get("data", {}).get("message_id")

        return SendResult(
            sent=True,
            recipient=recipient,
            provider_message_id=provider_message_id,
            raw_response=body if isinstance(body, dict) else {"response": body},
        )

