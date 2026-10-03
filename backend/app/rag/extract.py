"""Safe text extraction for uploaded learning material.

Only plain text, Markdown and PDF are accepted. File type is checked by
extension *and* content (magic bytes / UTF-8 decoding) - the client-supplied
content type is never trusted on its own.
"""

from __future__ import annotations

import io
import re
from dataclasses import dataclass

from pypdf import PdfReader

ALLOWED_EXTENSIONS = {".txt": "text/plain", ".md": "text/markdown", ".markdown": "text/markdown", ".pdf": "application/pdf"}
MAX_PDF_PAGES = 60


class ExtractionError(ValueError):
    pass


@dataclass
class ExtractedText:
    text: str
    content_type: str


def _ext(filename: str) -> str:
    m = re.search(r"(\.[A-Za-z0-9]+)$", filename or "")
    return m.group(1).lower() if m else ""


def sanitize_filename(filename: str) -> str:
    name = re.sub(r"[^A-Za-z0-9._ -]", "_", (filename or "document").split("/")[-1].split("\\")[-1])
    return name[:120] or "document"


def extract_text(filename: str, data: bytes) -> ExtractedText:
    ext = _ext(filename)
    if ext not in ALLOWED_EXTENSIONS:
        raise ExtractionError("Please upload a .txt, .md or .pdf file.")
    if not data:
        raise ExtractionError("The file is empty.")

    if ext == ".pdf":
        if not data.startswith(b"%PDF-"):
            raise ExtractionError("This file does not look like a real PDF.")
        try:
            reader = PdfReader(io.BytesIO(data))
            if reader.is_encrypted:
                raise ExtractionError("Password-protected PDFs are not supported.")
            if len(reader.pages) > MAX_PDF_PAGES:
                raise ExtractionError(f"PDFs are limited to {MAX_PDF_PAGES} pages.")
            text = "\n\n".join((page.extract_text() or "") for page in reader.pages)
        except ExtractionError:
            raise
        except Exception as exc:  # malformed PDFs raise many different errors
            raise ExtractionError("We couldn't read this PDF.") from exc
    else:
        if b"\x00" in data[:4096]:
            raise ExtractionError("This file looks like binary data, not text.")
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            try:
                text = data.decode("latin-1")
            except UnicodeDecodeError as exc:  # pragma: no cover
                raise ExtractionError("Text files must be UTF-8 encoded.") from exc

    text = normalize_text(text)
    if len(text) < 40:
        raise ExtractionError("We couldn't find enough readable text in this file.")
    return ExtractedText(text=text, content_type=ALLOWED_EXTENSIONS[ext])


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
