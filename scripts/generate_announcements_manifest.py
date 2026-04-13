from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import quote


ROOT_DIR = Path(__file__).resolve().parents[1]
PDF_DIR = ROOT_DIR / "pdfs"
OUTPUT_FILE = PDF_DIR / "announcements.js"

CATEGORY_LABELS = {
    "nclt-orders": "NCLT Orders",
    "list-of-creditors": "List of Creditors",
    "e-auction-notices": "E-auction Notices",
    "process-memorandum": "Process Memorandum",
}

CATEGORY_ORDER = {
    "NCLT Orders": 0,
    "List of Creditors": 1,
    "E-auction Notices": 2,
    "Process Memorandum": 3,
}
SPECIAL_WORDS = {
    "ca": "CA",
    "cirp": "CIRP",
    "eoi": "EOI",
    "ibc": "IBC",
    "nclt": "NCLT",
    "pdf": "PDF",
    "vhm": "VHM",
}


def normalize_text(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def format_category_name(folder_name: str) -> str:
    normalized = folder_name.strip().replace("_", "-").lower()

    if normalized in CATEGORY_LABELS:
        return CATEGORY_LABELS[normalized]

    return format_title(folder_name)


def detect_category(relative_path: Path) -> str:
    pdf_relative_path = relative_path.relative_to(PDF_DIR)

    if len(pdf_relative_path.parts) > 1:
        return format_category_name(pdf_relative_path.parts[0])

    return "General Notices"


def format_title(stem: str) -> str:
    cleaned = re.sub(r"[_\-]+", " ", stem).strip()
    cleaned = re.sub(r"\s+", " ", cleaned)

    words = []
    for raw_word in cleaned.split(" "):
        lower_word = raw_word.lower()
        if lower_word in SPECIAL_WORDS:
            words.append(SPECIAL_WORDS[lower_word])
        elif raw_word.isupper():
            words.append(raw_word)
        else:
            words.append(raw_word[:1].upper() + raw_word[1:])

    return " ".join(words)


def encode_relative_path(relative_path: Path) -> str:
    return "/".join(quote(part) for part in relative_path.parts)


def build_documents() -> list[dict[str, str]]:
    documents: list[dict[str, str]] = []

    for file_path in PDF_DIR.rglob("*.pdf"):
        relative_path = file_path.relative_to(ROOT_DIR)
        category = detect_category(file_path)
        documents.append(
            {
                "category": category,
                "title": format_title(file_path.stem),
                "file": encode_relative_path(relative_path),
            }
        )

    documents.sort(key=lambda item: item["title"].lower(), reverse=True)
    documents.sort(key=lambda item: (CATEGORY_ORDER.get(item["category"], 999), item["category"].lower()))
    return documents


def write_manifest(documents: list[dict[str, str]]) -> None:
    payload = "window.__VHM_ANNOUNCEMENTS__ = " + json.dumps(documents, indent=2, ensure_ascii=True) + ";\n"
    OUTPUT_FILE.write_text(payload, encoding="utf-8")


if __name__ == "__main__":
    write_manifest(build_documents())
