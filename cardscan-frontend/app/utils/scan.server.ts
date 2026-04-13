import { getBackendApiUrl } from "./env.server";

export async function scanBusinessCardOnBackend(formData: FormData) {
  const backendUrl = getBackendApiUrl().replace(/\/$/, "");
  const file = formData.get("file");

  if (!(file instanceof File)) {
    throw new Error("File gambar tidak ditemukan.");
  }

  const payload = new FormData();
  payload.append("file", file, file.name);

  const sendToWhatsapp = String(formData.get("send_to_whatsapp") ?? "false");
  payload.append("send_to_whatsapp", sendToWhatsapp);

  const whatsappTo = String(formData.get("whatsapp_to") ?? "").trim();
  if (whatsappTo) {
    payload.append("whatsapp_to", whatsappTo);
  }

  const response = await fetch(`${backendUrl}/v1/scan/business-card`, {
    method: "POST",
    body: payload,
  });

  const text = await response.text();
  let data: unknown = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = { raw: text };
  }

  if (!response.ok) {
    const message =
      typeof data === "object" && data && "detail" in data
        ? String((data as { detail: unknown }).detail)
        : "Backend gagal memproses gambar.";
    throw new Error(message);
  }

  return data;
}
