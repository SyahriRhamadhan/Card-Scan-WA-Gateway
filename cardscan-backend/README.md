# Cardscan Backend

Backend Python untuk upload foto kartu nama, OCR lewat OCR.space free API, lalu kirim hasilnya ke WhatsApp gateway v2.

## Stack

- FastAPI
- OCR.space free API
- Client HTTP untuk WhatsApp gateway v2

## Prasyarat

- Python 3.10+
- OCR.space API key free. Default demo key `helloworld` sudah diset untuk testing, tapi sebaiknya ganti ke key sendiri

## Setup

```bash
cd cardscan-backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Isi `.env` terutama:

- `OCRSPACE_API_KEY`
- `WA_GATEWAY_BASE_URL`
- `WA_GATEWAY_SEND_PATH`
- `WA_GATEWAY_TOKEN`
- `OCR_LANG` jika perlu bahasa selain `eng`

## Run

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Endpoint

### `GET /health`

Health check.

### `POST /v1/scan/business-card`

Form-data:

- `file`: gambar kartu nama
- `send_to_whatsapp`: `true` / `false`
- `whatsapp_to`: nomor tujuan, opsional jika sudah ada `DEFAULT_WHATSAPP_TO`

Response berisi:

- teks OCR mentah dari OCR.space
- hasil parsing kontak
- status kirim WA jika diaktifkan

## Catatan integrasi WA gateway v2

OCR.space mengirim file sebagai multipart ke endpoint `https://api.ocr.space/parse/image`.

Struktur request ke gateway dibuat generik supaya gampang disesuaikan dengan provider kamu.
Kalau payload gateway kamu berbeda, ubah `app/services/wa_gateway.py`.
