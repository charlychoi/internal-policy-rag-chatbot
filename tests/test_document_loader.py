from __future__ import annotations

import zipfile
from pathlib import Path

import sys
sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from document_loader import SUPPORTED_SOURCE_EXTENSIONS, load_policy_documents


def _write_docx(path: Path, text: str) -> None:
    xml = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>{text}</w:t></w:r></w:p></w:body></w:document>'''
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("word/document.xml", xml)


def test_upload_extensions_include_open_notebook_liteparse_formats() -> None:
    for ext in ["pdf", "docx", "xlsx", "pptx", "png", "jpg", "jpeg", "webp", "md", "txt"]:
        assert ext in SUPPORTED_SOURCE_EXTENSIONS


def test_docx_text_is_extracted_for_local_fallback(tmp_path: Path) -> None:
    docx = tmp_path / "leave-policy.docx"
    _write_docx(docx, "연차휴가 규정 입사 1년 미만 직원")

    docs = load_policy_documents([docx])

    assert docs[0]["title"] == "leave-policy.docx"
    assert "연차휴가 규정" in docs[0]["content"]
    assert "docx" in docs[0]["extraction_note"]


def test_image_upload_is_accepted_but_ocr_limitation_is_explicit(tmp_path: Path) -> None:
    image = tmp_path / "notice.png"
    image.write_bytes(b"not a real image; extension acceptance test")

    docs = load_policy_documents([image])

    assert "OCR" in docs[0]["content"]
    assert "Open Notebook" in docs[0]["content"]
