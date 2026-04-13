# Cardscan Frontend

Frontend Remix untuk upload kartu nama, lihat hasil OCR, lalu kirim ke backend Python.

## Setup

```bash
cd cardscan/cardscan-frontend
npm install
copy .env.example .env
```

Isi `.env`:

- `BACKEND_API_URL=http://127.0.0.1:8000`

## Run

```bash
npm run dev
```

## Alur

- Upload gambar di halaman utama
- Remix action mem-forward file ke backend Python
- Backend mengembalikan hasil OCR dan status kirim WhatsApp

