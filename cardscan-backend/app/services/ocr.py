import httpx
from app.core.config import Settings


class OcrSpaceService:
    def __init__(self, settings: Settings):
        self.settings = settings

    async def extract_text(self, file_name: str, file_bytes: bytes) -> str:
        headers = {"apikey": self.settings.ocrspace_api_key}
        data = {
            "language": self.settings.ocr_lang,
            "isOverlayRequired": "false",
        }
        files = {
            "file": (file_name, file_bytes),
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(self.settings.ocrspace_endpoint, headers=headers, data=data, files=files)
            response.raise_for_status()

        payload = response.json()
        if not isinstance(payload, dict):
            raise RuntimeError("Response OCR.space tidak valid.")

        parsed_results = payload.get("ParsedResults") or []
        if not parsed_results:
            error_message = payload.get("ErrorMessage") or payload.get("ErrorDetails") or "OCR.space tidak mengembalikan teks."
            if isinstance(error_message, list):
                error_message = "; ".join(str(item) for item in error_message)
            raise RuntimeError(str(error_message))

        texts = []
        for item in parsed_results:
            if isinstance(item, dict) and item.get("ParsedText"):
                texts.append(str(item["ParsedText"]).strip())

        return "\n".join(texts).strip()
