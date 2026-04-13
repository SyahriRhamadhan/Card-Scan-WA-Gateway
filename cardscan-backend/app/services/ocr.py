import os
import re
from io import BytesIO

import httpx
from PIL import Image, ImageOps
from app.core.config import Settings


class OcrSpaceService:
    def __init__(self, settings: Settings):
        self.settings = settings

    async def _extract_once(self, file_name: str, file_bytes: bytes) -> str:
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

    def _build_rotation_variants(self, file_name: str, file_bytes: bytes) -> list[tuple[int, str, bytes]]:
        try:
            image = Image.open(BytesIO(file_bytes))
            image = ImageOps.exif_transpose(image)
        except Exception:
            return [(0, file_name, file_bytes)]

        base_name, _ = os.path.splitext(file_name)
        safe_base = base_name or "upload"
        variants: list[tuple[int, str, bytes]] = []
        for angle in (0, 90, 180, 270):
            rotated = image.rotate(angle, expand=True) if angle else image
            buffer = BytesIO()
            # Always send PNG bytes with PNG file name to avoid MIME/extension mismatch.
            rotated.save(buffer, format="PNG")
            variant_name = f"{safe_base}-rot{angle}.png"
            variants.append((angle, variant_name, buffer.getvalue()))
        return variants

    def _score_text(self, text: str) -> int:
        words = [token for token in re.split(r"\s+", text.strip()) if token]
        email_hits = len(re.findall(r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b", text))
        web_hits = len(re.findall(r"\b(?:https?://)?(?:www\.)?[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b", text))
        phone_hits = len(re.findall(r"(?:\+?\d[\d\s().-]{7,}\d)", text))
        return (len(words) * 2) + (email_hits * 14) + (web_hits * 10) + (phone_hits * 8)

    async def extract_text(self, file_name: str, file_bytes: bytes) -> str:
        variants = self._build_rotation_variants(file_name=file_name, file_bytes=file_bytes)

        best_text = ""
        best_score = -1
        last_error: Exception | None = None

        for angle, variant_name, variant_bytes in variants:
            try:
                text = await self._extract_once(file_name=variant_name, file_bytes=variant_bytes)
                score = self._score_text(text)
                # Prefer orientation that yields richer structured content.
                if score > best_score:
                    best_score = score
                    best_text = text
            except Exception as exc:
                last_error = exc
                continue

        if best_text:
            return best_text
        if last_error:
            raise last_error
        raise RuntimeError("OCR.space tidak mengembalikan hasil dari semua orientasi.")
