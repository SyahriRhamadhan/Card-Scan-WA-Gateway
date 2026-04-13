import type { ActionFunctionArgs, MetaFunction } from "@remix-run/node";
import { json } from "@remix-run/node";
import { useFetcher } from "@remix-run/react";
import { useEffect, useMemo, useRef, useState } from "react";

import { scanBusinessCardOnBackend } from "../utils/scan.server";

type ScanResponse = {
  raw_text: string;
  contact: {
    name?: string | null;
    company?: string | null;
    title?: string | null;
    phones: string[];
    emails: string[];
    websites: string[];
    address?: string | null;
    raw_lines: string[];
    confidence_notes: string[];
  };
  whatsapp: {
    sent: boolean;
    recipient?: string | null;
    provider_message_id?: string | null;
    raw_response?: Record<string, unknown>;
  };
};

type ActionData =
  | { ok: true; data: ScanResponse }
  | { ok: false; error: string };

export const meta: MetaFunction = () => [
  { title: "Cardscan | OCR ke WhatsApp" },
  {
    name: "description",
    content: "Frontend Remix untuk scan kartu nama, review hasil OCR, lalu kirim ke WhatsApp gateway v2.",
  },
];

export async function action({ request }: ActionFunctionArgs) {
  try {
    const formData = await request.formData();
    const data = (await scanBusinessCardOnBackend(formData)) as ScanResponse;
    return json<ActionData>({ ok: true, data });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Gagal memproses gambar.";
    return json<ActionData>({ ok: false, error: message }, { status: 400 });
  }
}

export default function Index() {
  const fetcher = useFetcher<ActionData>();
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  useEffect(() => {
    if (!selectedFile) {
      setPreviewUrl(null);
      return;
    }

    const url = URL.createObjectURL(selectedFile);
    setPreviewUrl(url);

    return () => URL.revokeObjectURL(url);
  }, [selectedFile]);

  const isSubmitting = fetcher.state !== "idle";
  const result = fetcher.data && fetcher.data.ok ? fetcher.data.data : null;
  const error = fetcher.data && !fetcher.data.ok ? fetcher.data.error : null;

  const confidenceNotes = useMemo(
    () => result?.contact.confidence_notes ?? [],
    [result?.contact.confidence_notes],
  );

  return (
    <main className="mx-auto max-w-5xl px-4 pb-12 pt-8 sm:px-6">
      <section className="mb-8 flex justify-center gap-8">
        <button
          type="button"
          className="rounded-xl border border-black bg-[#87d4df] px-8 py-3 text-3xl leading-none shadow-saweria transition-transform hover:-translate-y-0.5"
        >
          Login
        </button>
        <button
          type="button"
          className="rounded-xl border border-black bg-[#ffbd2e] px-8 py-3 text-3xl leading-none shadow-saweria transition-transform hover:-translate-y-0.5"
        >
          Daftar
        </button>
      </section>

      <section className="rounded-xl border border-black bg-paper p-6 shadow-saweria sm:p-8">
        <p className="mb-5 text-2xl leading-relaxed text-[#0f2140] sm:text-[2rem]">
          Scan kartu nama kamu dan kirim otomatis ke WhatsApp gateway. Alur backend: OCR.space,
          parsing data kontak, lalu trigger API WA v2.
        </p>

        <fetcher.Form method="post" encType="multipart/form-data" className="space-y-5">
          <div className="rounded-xl border border-black bg-[#f6f8f8] p-4">
            <h3 className="text-2xl text-[#0f2140]">Saran posisi foto</h3>
            <ul className="mt-2 list-disc space-y-1 pl-6 text-lg text-[#0f2140]">
              <li>Posisikan kartu lurus dan penuh di frame, sisakan margin tipis di sekeliling.</li>
              <li>Hindari blur, usahakan kamera stabil dan fokus ke teks.</li>
              <li>Gunakan cahaya merata, hindari bayangan tangan atau pantulan lampu.</li>
              <li>Jika terbalik, tetap upload saja. Backend akan coba rotasi otomatis.</li>
            </ul>
          </div>

          <label className="block cursor-pointer rounded-xl border border-black bg-[#dfe4e4] p-4 shadow-saweria/70">
            <input
              ref={fileInputRef}
              type="file"
              name="file"
              accept="image/*"
              className="hidden"
              onChange={(event) => {
                const file = event.currentTarget.files?.[0] ?? null;
                setSelectedFile(file);
              }}
              required
            />
            <div className="flex min-h-52 items-center justify-center text-center">
              {previewUrl ? (
                <img
                  className="max-h-72 w-full rounded-lg border border-black object-contain"
                  src={previewUrl}
                  alt="Preview kartu nama"
                />
              ) : (
                <div className="space-y-2">
                  <h3 className="text-3xl text-[#0f2140]">Upload kartu nama</h3>
                  <p className="text-xl text-[#0f2140]">Format JPG, PNG, WEBP. Klik area ini untuk pilih file.</p>
                </div>
              )}
            </div>
          </label>

          <div className="grid gap-4">
            <div className="flex flex-wrap items-center justify-between gap-4 rounded-xl border border-black bg-[#dfe4e4] p-4">
              <div className="space-y-1">
                <strong className="block text-xl text-[#0f2140]">Kirim ke WhatsApp</strong>
                <span className="text-lg text-[#0f2140]">
                  Aktifkan kalau hasil OCR langsung mau dikirim ke gateway v2.
                </span>
              </div>
              <label className="relative inline-flex h-9 w-16 items-center">
                <input type="checkbox" name="send_to_whatsapp" value="true" className="peer sr-only" />
                <span className="pointer-events-none absolute inset-0 rounded-full border border-black bg-white peer-checked:bg-[#b8efd4]" />
                <span className="pointer-events-none absolute left-1 top-1 h-7 w-7 rounded-full border border-black bg-[#ffbd2e] transition-transform peer-checked:translate-x-7" />
              </label>
            </div>

            <div className="space-y-2">
              <label htmlFor="whatsapp_to" className="text-xl text-[#0f2140]">
                Nomor tujuan WhatsApp
              </label>
              <input
                id="whatsapp_to"
                type="text"
                name="whatsapp_to"
                placeholder="62812xxxxxxx"
                className="w-full rounded-xl border border-black bg-white px-4 py-3 text-xl outline-none focus:ring-2 focus:ring-[#8cc9d4]"
              />
            </div>
          </div>

          <div className="flex flex-wrap gap-3">
            <button
              className="rounded-xl border border-black bg-[#8cc9d4] px-6 py-2 text-2xl shadow-saweria disabled:opacity-60"
              type="submit"
              disabled={isSubmitting}
            >
              {isSubmitting ? "Memproses..." : "Scan Sekarang"}
            </button>
            <button
              className="rounded-xl border border-black bg-[#f8a6af] px-6 py-2 text-2xl shadow-saweria"
              type="button"
              onClick={() => {
                setSelectedFile(null);
                setPreviewUrl(null);
                if (fileInputRef.current) {
                  fileInputRef.current.value = "";
                }
              }}
            >
              Reset
            </button>
          </div>

          {error ? (
            <div className="rounded-xl border border-black bg-[#ffd0d0] px-4 py-3 text-lg text-[#7d1111]">
              {error}
            </div>
          ) : null}
          {isSubmitting ? (
            <div className="rounded-xl border border-black bg-[#fff3c1] px-4 py-3 text-lg text-[#1f2937]">
              Mengirim gambar dan memproses OCR...
            </div>
          ) : null}
        </fetcher.Form>
      </section>

      <section className="relative mt-12">
        <span className="absolute right-0 top-0 -translate-y-full rounded-t-xl border border-black bg-[#f8a6af] px-4 py-2 text-2xl text-black">
          hasil scan
        </span>
      </section>

      <section className="rounded-xl border border-black bg-paper p-6 shadow-saweria sm:p-8">
        <ol className="list-decimal space-y-2 pl-7 text-2xl leading-relaxed text-[#0f2140]">
          <li>Nama: {result?.contact.name ?? "-"}</li>
          <li>Perusahaan: {result?.contact.company ?? "-"}</li>
          <li>Jabatan: {result?.contact.title ?? "-"}</li>
          <li>Telepon: {result?.contact.phones.length ? result.contact.phones.join(", ") : "-"}</li>
          <li>Email: {result?.contact.emails.length ? result.contact.emails.join(", ") : "-"}</li>
          <li>Website: {result?.contact.websites.length ? result.contact.websites.join(", ") : "-"}</li>
          <li>Status WA: {result ? (result.whatsapp.sent ? "Terkirim" : "Belum dikirim") : "-"}</li>
          <li>Message ID: {result?.whatsapp.provider_message_id ?? "-"}</li>
        </ol>

        <div className="mt-6 rounded-xl border border-black bg-[#f6f8f8] p-4 text-lg leading-relaxed text-[#0f2140]">
          {result?.raw_text || "Belum ada hasil OCR."}
        </div>

        <div className="mt-6 space-y-2 rounded-xl border border-black bg-[#f6f8f8] p-4 text-[#0f2140]">
          <strong className="text-2xl">Catatan OCR</strong>
          {confidenceNotes.length ? (
            <ul className="list-disc space-y-1 pl-6 text-xl">
              {confidenceNotes.map((note) => (
                <li key={note}>{note}</li>
              ))}
            </ul>
          ) : (
            <p className="text-xl">Tidak ada catatan tambahan.</p>
          )}
        </div>
      </section>
    </main>
  );
}
