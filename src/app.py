from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import streamlit as st

sys.path.append(str(Path(__file__).parent))
from open_notebook_client import OpenNotebookClient
from document_loader import SUPPORTED_SOURCE_EXTENSIONS, load_policy_documents
from policy_rag_chain import answer_policy_question
from policy_ontology import classify_policy_query

ROOT = Path(__file__).resolve().parents[1]
SAMPLE_DIR = ROOT / "data" / "samples"
SAMPLE_DOCS = [p for p in SAMPLE_DIR.glob("*.md")]

st.set_page_config(page_title="사내 규정집 RAG 챗봇 PoC", page_icon="📚", layout="wide")
st.title("📚 사내 규정집 자연어 검색 챗봇 PoC")
st.caption("Open Notebook RAG 연동 준비 · 파일 업로드 · 규정 온톨로지 · 안전 가드레일")

client = OpenNotebookClient()
on_ready = client.health()
st.sidebar.write("Open Notebook API")
if on_ready:
    st.sidebar.success("연결됨")
else:
    st.sidebar.warning("미연결: 로컬 fallback 사용")
st.sidebar.code(client.api_base)

uploaded_files = st.file_uploader(
    "규정집 문서 업로드",
    type=SUPPORTED_SOURCE_EXTENSIONS,
    accept_multiple_files=True,
    help="Open Notebook/LiteParse 기준: PDF, DOCX, XLSX, PPTX, 이미지와 Markdown/TXT를 받습니다. 로컬 fallback은 텍스트 추출 가능한 형식부터 검색합니다.",
)
paths = []
if uploaded_files:
    tmpdir = Path(tempfile.mkdtemp(prefix="policy-docs-"))
    for f in uploaded_files:
        out = tmpdir / f.name
        out.write_bytes(f.read())
        paths.append(out)
        if on_ready and st.sidebar.checkbox("업로드 파일을 Open Notebook Source로 등록", value=False):
            try:
                result = client.upload_source(out)
                st.sidebar.json(result)
            except Exception as exc:
                st.sidebar.error(f"Open Notebook 업로드 실패: {exc}")
else:
    paths = SAMPLE_DOCS

local_docs = load_policy_documents(paths)
st.sidebar.metric("로드된 문서", len(local_docs))
with st.sidebar.expander("지원 업로드 형식"):
    st.write(", ".join(f".{ext}" for ext in SUPPORTED_SOURCE_EXTENSIONS))

question = st.text_input("질문", "입사 1년 미만 직원도 연차를 쓸 수 있나요?")
if st.button("규정 검색하기", type="primary") and question.strip():
    c = classify_policy_query(question)
    st.write("**분류:**", c.domain, "/", c.intent, "/", c.route)
    answer = answer_policy_question(question, local_docs, open_notebook=client, prefer_open_notebook=True)
    if answer.route == "refuse":
        st.error(answer.answer)
    elif answer.route == "needs_hr_review":
        st.warning(answer.answer)
    else:
        st.success(answer.answer)
    st.write("**Open Notebook 사용:**", "예" if answer.used_open_notebook else "아니오 / fallback")
    if answer.sources:
        st.write("**출처 후보:**")
        for source in answer.sources:
            st.code(source)

with st.expander("로드된 문서 미리보기"):
    for doc in local_docs:
        st.markdown(f"### {doc['title']}")
        st.write(doc["content"][:1200])
