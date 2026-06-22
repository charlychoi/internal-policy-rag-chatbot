from __future__ import annotations

from pathlib import Path
import csv
import io
import zipfile
import xml.etree.ElementTree as ET
from typing import Iterable

SUPPORTED_SOURCE_EXTENSIONS = [
    "md",
    "txt",
    "pdf",
    "docx",
    "xlsx",
    "pptx",
    "png",
    "jpg",
    "jpeg",
    "webp",
    "tif",
    "tiff",
]

_TEXT_EXTENSIONS = {".md", ".txt"}
_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff"}


def load_policy_documents(paths: Iterable[Path]) -> list[dict]:
    docs: list[dict] = []
    for path in paths:
        text, note = extract_text(path)
        if not text.strip():
            text = note or f"{path.name}: 이 파일 형식은 업로드는 가능하지만 로컬 fallback 미리보기 텍스트를 추출하지 못했습니다."
        docs.append({"title": path.name, "content": text, "source": str(path), "extraction_note": note})
    return docs


def extract_text(path: Path) -> tuple[str, str]:
    suffix = path.suffix.lower()
    try:
        if suffix in _TEXT_EXTENSIONS:
            return path.read_text(encoding="utf-8"), "plain text"
        if suffix == ".pdf":
            return _extract_pdf(path)
        if suffix == ".docx":
            return _extract_docx(path), "docx OOXML text"
        if suffix == ".xlsx":
            return _extract_xlsx(path), "xlsx shared strings + sheet text"
        if suffix == ".pptx":
            return _extract_pptx(path), "pptx slide text"
        if suffix in _IMAGE_EXTENSIONS:
            return "", "이미지는 Open Notebook/LiteParse OCR 대상입니다. 현재 로컬 fallback에는 OCR 엔진이 없어 원문 등록만 지원합니다."
        return "", f"지원 목록 밖의 확장자입니다: {suffix}"
    except Exception as exc:  # keep UI alive for bad documents
        return "", f"텍스트 추출 실패({type(exc).__name__}): {exc}"


def _extract_pdf(path: Path) -> tuple[str, str]:
    try:
        import fitz  # PyMuPDF
    except Exception:
        return "", "PDF는 업로드 가능하지만 로컬 fallback 추출에는 PyMuPDF가 필요합니다. Open Notebook/LiteParse 연결 시 원문 처리 대상입니다."
    doc = fitz.open(path)
    pages = [page.get_text("text") for page in doc]
    return "\n\n".join(pages), f"pdf text, pages={doc.page_count}"


def _xml_text(xml_bytes: bytes) -> str:
    root = ET.fromstring(xml_bytes)
    parts: list[str] = []
    for elem in root.iter():
        if elem.text and elem.tag.endswith('}t'):
            parts.append(elem.text)
        elif elem.text and elem.tag.endswith('}instrText'):
            continue
    return " ".join(parts)


def _extract_docx(path: Path) -> str:
    with zipfile.ZipFile(path) as zf:
        chunks = []
        for name in sorted(zf.namelist()):
            if name.startswith("word/") and name.endswith(".xml") and ("document" in name or "header" in name or "footer" in name):
                chunks.append(_xml_text(zf.read(name)))
    return "\n\n".join(c for c in chunks if c.strip())


def _extract_pptx(path: Path) -> str:
    with zipfile.ZipFile(path) as zf:
        chunks = []
        for name in sorted(zf.namelist()):
            if name.startswith("ppt/slides/slide") and name.endswith(".xml"):
                text = _xml_text(zf.read(name))
                if text.strip():
                    chunks.append(f"## {Path(name).stem}\n{text}")
    return "\n\n".join(chunks)


def _extract_xlsx(path: Path) -> str:
    try:
        import openpyxl
    except Exception:
        return _extract_xlsx_ooxml(path)
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    output = io.StringIO()
    writer = csv.writer(output)
    for ws in wb.worksheets:
        output.write(f"\n## Sheet: {ws.title}\n")
        for row in ws.iter_rows(values_only=True):
            values = ["" if v is None else str(v) for v in row]
            if any(v.strip() for v in values):
                writer.writerow(values)
    return output.getvalue()


def _extract_xlsx_ooxml(path: Path) -> str:
    with zipfile.ZipFile(path) as zf:
        shared: list[str] = []
        if "xl/sharedStrings.xml" in zf.namelist():
            root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
            for si in root:
                texts = [el.text or "" for el in si.iter() if el.tag.endswith('}t')]
                shared.append("".join(texts))
        chunks = []
        for name in sorted(n for n in zf.namelist() if n.startswith("xl/worksheets/sheet") and n.endswith(".xml")):
            root = ET.fromstring(zf.read(name))
            vals = []
            for c in root.iter():
                if c.tag.endswith('}c'):
                    cell_type = c.attrib.get('t')
                    v = next((child.text for child in c if child.tag.endswith('}v')), None)
                    if v is None:
                        continue
                    if cell_type == 's' and v.isdigit() and int(v) < len(shared):
                        vals.append(shared[int(v)])
                    else:
                        vals.append(v)
            if vals:
                chunks.append(f"## {Path(name).stem}\n" + "\n".join(vals))
    return "\n\n".join(chunks)
