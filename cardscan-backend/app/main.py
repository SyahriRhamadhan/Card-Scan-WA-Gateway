import logging

from fastapi import FastAPI, File, Form, HTTPException, UploadFile

from app.core.config import get_settings
from app.schemas import ScanBusinessCardResponse, WhatsAppSendResult
from app.services.ocr import OcrSpaceService
from app.services.parser import parse_business_card
from app.services.wa_gateway import WAGatewayClient


settings = get_settings()
logger = logging.getLogger(settings.app_name)

app = FastAPI(title=settings.app_name, version="0.1.0")

ocr_service = OcrSpaceService(settings)
wa_client = WAGatewayClient(settings)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/v1/scan/business-card", response_model=ScanBusinessCardResponse)
async def scan_business_card(
    file: UploadFile = File(...),
    send_to_whatsapp: bool = Form(False),
    whatsapp_to: str | None = Form(None),
) -> ScanBusinessCardResponse:
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File harus berupa gambar.")

    content = await file.read()

    raw_text = await ocr_service.extract_text(file.filename or "upload.png", content)
    parsed = parse_business_card(raw_text)

    whatsapp_result = WhatsAppSendResult(sent=False)
    if send_to_whatsapp:
        recipient = whatsapp_to or settings.default_whatsapp_to
        if not recipient:
            raise HTTPException(
                status_code=400,
                detail="whatsapp_to atau DEFAULT_WHATSAPP_TO harus diisi jika send_to_whatsapp=true.",
            )
        wa_result = await wa_client.send_text_message(recipient=recipient, message=parsed.message)
        whatsapp_result = WhatsAppSendResult(
            sent=wa_result.sent,
            recipient=wa_result.recipient,
            provider_message_id=wa_result.provider_message_id,
            raw_response=wa_result.raw_response,
        )

    return ScanBusinessCardResponse(
        raw_text=raw_text,
        contact=parsed.contact,
        whatsapp=whatsapp_result,
    )
