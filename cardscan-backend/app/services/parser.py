import re
from dataclasses import dataclass

from app.schemas import ContactDetails

EMAIL_RE = re.compile(r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b")
WEB_RE = re.compile(r"\b((?:https?://)?(?:www\.)?[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})(?:/[^\s]*)?\b")
PHONE_RE = re.compile(r"(?:(?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{2,4}\)?[\s.-]?)?\d{3,4}[\s.-]?\d{3,4}(?:[\s.-]?\d{2,4})?)")
COMPANY_MARKERS = (
    "pt",
    "cv",
    "ltd",
    "inc",
    "corp",
    "company",
    "co",
    "co.",
    "group",
    "solutions",
    "studio",
    "technologies",
    "technology",
    "digital",
)
COMPANY_MARKER_SET = set(COMPANY_MARKERS)
SERVICE_KEYWORDS = (
    "company profile",
    "web/mobile",
    "mobile app",
    "e-commerce",
    "custom erp",
    "odoo erp",
    "asset & inventory",
    "rfid",
    "development",
)


@dataclass
class ParsedContact:
    contact: ContactDetails
    message: str


def _clean_lines(text: str) -> list[str]:
    lines = []
    for line in text.splitlines():
        value = re.sub(r"\b0\b", " ", line)
        value = re.sub(r"\s+", " ", value).strip(" -\t\r\n")
        if value:
            lines.append(value)
    return lines


def _looks_like_name(line: str) -> bool:
    if len(line) < 4 or len(line) > 40:
        return False
    if any(ch.isdigit() for ch in line):
        return False
    if "@" in line or "www" in line.lower():
        return False
    words = line.split()
    if len(words) > 4:
        return False
    return sum(word[:1].isalpha() for word in words) >= 1


def _looks_like_company(line: str) -> bool:
    lowered = line.lower()
    words = [token.strip(".,()[]") for token in lowered.split()]
    has_marker_word = any(word in COMPANY_MARKER_SET for word in words)
    return has_marker_word or any(marker in lowered for marker in COMPANY_MARKERS if len(marker) > 3) or line.isupper()


def _is_contact_line(line: str) -> bool:
    lowered = line.lower()
    return bool(
        EMAIL_RE.search(line)
        or WEB_RE.search(line)
        or PHONE_RE.search(line)
        or any(token in lowered for token in ("www.", "http://", "https://", "@"))
    )


def _is_service_line(line: str) -> bool:
    lowered = line.lower()
    return any(keyword in lowered for keyword in SERVICE_KEYWORDS)


def _name_score(line: str) -> int:
    if not _looks_like_name(line):
        return -999
    words = line.split()
    score = 0
    if 2 <= len(words) <= 3:
        score += 3
    if all(word[:1].isupper() for word in words if word):
        score += 2
    if _looks_like_company(line):
        score -= 3
    return score


def _company_score(line: str) -> int:
    if len(line) < 3:
        return -999
    lowered = line.lower()
    score = 0
    if _looks_like_company(line):
        score += 4
    if len(line.split()) >= 2:
        score += 1
    if any(ch.isdigit() for ch in line):
        score -= 2
    if _is_service_line(line):
        score -= 5
    if any(term in lowered for term in ("manager", "director", "sales", "marketing", "founder", "ceo", "cto", "owner", "real estate", "agent", "agen")):
        score -= 2
    return score


def _normalize_phone(value: str) -> str:
    digits = re.sub(r"\D", "", value)
    if not digits:
        return value.strip()
    if digits.startswith("0"):
        digits = "62" + digits[1:]
    if digits.startswith("62"):
        return f"+{digits}"
    if value.strip().startswith("+"):
        return "+" + digits
    return digits


def _normalize_website(value: str) -> str:
    cleaned = value.lower().strip().rstrip(".,")
    cleaned = re.sub(r"^https?://", "", cleaned)
    cleaned = re.sub(r"^www\.", "", cleaned)
    return cleaned


def _company_from_website(websites: list[str]) -> str | None:
    if not websites:
        return None
    root = websites[0].split("/")[0]
    head = root.split(".")[0]
    if not head:
        return None
    words = re.split(r"[-_]", head)
    return " ".join(word.capitalize() for word in words if word)


def _split_identity_line(line: str) -> tuple[str | None, str | None, str | None]:
    words = line.split()
    lowered_words = [word.lower().strip(".,()[]") for word in words]
    marker_index = None

    for idx, word in enumerate(lowered_words[:4]):
        if word in COMPANY_MARKER_SET:
            marker_index = idx
            break

    if marker_index is None:
        return None, None, None

    if marker_index + 2 >= len(words):
        return None, None, None

    company = " ".join(words[: marker_index + 1]).strip()
    name = " ".join(words[marker_index + 1 : marker_index + 3]).strip()
    remainder = " ".join(words[marker_index + 3 :]).strip()
    if not company or not name:
        return None, None, None
    return company, name, remainder or None


def parse_business_card(text: str) -> ParsedContact:
    lines = _clean_lines(text)
    emails = sorted(set(EMAIL_RE.findall(text)))
    websites = sorted(set(_normalize_website(match.group(1)) for match in WEB_RE.finditer(text)))
    phones = sorted(set(_normalize_phone(match.group(0).strip()) for match in PHONE_RE.finditer(text) if len(re.sub(r"\D", "", match.group(0))) >= 8))

    content_lines = [line for line in lines if not _is_contact_line(line)]

    name = None
    company = None
    title = None
    address = None
    notes: list[str] = []

    for line in content_lines:
        split_company, split_name, split_title = _split_identity_line(line)
        if split_company and company is None:
            company = split_company
        if split_name and name is None:
            name = split_name
        if split_title and title is None and ("real estate" in split_title.lower() or "agent" in split_title.lower() or "agen" in split_title.lower()):
            title = split_title

    company_candidates = sorted(content_lines, key=_company_score, reverse=True)
    name_candidates = sorted(content_lines, key=_name_score, reverse=True)

    if company_candidates and _company_score(company_candidates[0]) > 0:
        company = company_candidates[0]

    for candidate in name_candidates:
        if _name_score(candidate) > 0 and candidate != company:
            name = candidate
            break

    for line in content_lines:
        lowered = line.lower()
        if title is None and (
            any(keyword in lowered for keyword in ("director", "manager", "sales", "marketing", "founder", "ceo", "cto", "owner", "real estate", "agent", "agen"))
            or ("chief" in lowered and "officer" in lowered)
        ):
            title = line
            continue
        if address is None and any(keyword in lowered for keyword in ("street", "st.", "road", "rd.", "avenue", "ave", "city", "kota", "jalan", "jln", "rt", "rw")):
            address = line

    if company is None:
        company = _company_from_website(websites)

    if not name:
        notes.append("Nama tidak terdeteksi otomatis, perlu review manual.")
    if not company:
        notes.append("Perusahaan tidak terdeteksi otomatis.")
    if not phones:
        notes.append("Nomor telepon tidak terdeteksi.")

    contact = ContactDetails(
        name=name,
        company=company,
        title=title,
        phones=phones,
        emails=emails,
        websites=websites,
        address=address,
        raw_lines=lines,
        confidence_notes=notes,
    )

    message_parts = []
    if contact.name:
        message_parts.append(f"Nama: {contact.name}")
    if contact.company:
        message_parts.append(f"Perusahaan: {contact.company}")
    if contact.title:
        message_parts.append(f"Jabatan: {contact.title}")
    if contact.phones:
        message_parts.append(f"Telepon: {', '.join(contact.phones)}")
    if contact.emails:
        message_parts.append(f"Email: {', '.join(contact.emails)}")
    if contact.websites:
        message_parts.append(f"Website: {', '.join(contact.websites)}")
    if contact.address:
        message_parts.append(f"Alamat: {contact.address}")
    if not message_parts:
        message_parts.append("Hasil OCR belum bisa diparse otomatis.")

    return ParsedContact(contact=contact, message="\n".join(message_parts))
