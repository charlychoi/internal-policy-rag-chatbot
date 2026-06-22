from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from collections import Counter

from policy_ontology import PolicyClassification, classify_policy_query, build_safe_response
from open_notebook_client import OpenNotebookClient
from document_loader import load_policy_documents

_WORD_RE = re.compile(r"[가-힣A-Za-z0-9]+")


@dataclass
class PolicyAnswer:
    answer: str
    route: str
    domain: str
    intent: str
    sources: list[str]
    used_open_notebook: bool


def load_local_policy_docs(paths: list[Path]) -> list[dict]:
    return load_policy_documents(paths)


def answer_policy_question(
    question: str,
    local_docs: list[dict],
    open_notebook: OpenNotebookClient | None = None,
    prefer_open_notebook: bool = True,
) -> PolicyAnswer:
    classification = classify_policy_query(question)
    safe = build_safe_response(classification)
    if safe and classification.route == "refuse":
        return _from_safe(safe, classification)

    if prefer_open_notebook and open_notebook and open_notebook.health():
        try:
            result = open_notebook.ask_simple(question)
            answer = result.get("answer") or result.get("final_answer") or str(result)
            if safe:
                answer = f"{safe}\n\n참고로 검색된 일반 규정 정보:\n{answer}"
            return PolicyAnswer(answer, classification.route, classification.domain, classification.intent, ["Open Notebook RAG"], True)
        except Exception as exc:
            # Fall back locally but expose the fallback in answer for PoC transparency.
            fallback = _local_answer(question, local_docs)
            answer = f"Open Notebook 호출이 준비되지 않아 로컬 fallback으로 답변합니다. ({type(exc).__name__})\n\n{fallback.answer}"
            if safe:
                answer = f"{safe}\n\n{answer}"
            return PolicyAnswer(answer, classification.route, classification.domain, classification.intent, fallback.sources, False)

    fallback = _local_answer(question, local_docs)
    answer = fallback.answer
    if safe:
        answer = f"{safe}\n\n참고용 관련 규정:\n{answer}"
    return PolicyAnswer(answer, classification.route, classification.domain, classification.intent, fallback.sources, False)


def _from_safe(message: str, c: PolicyClassification) -> PolicyAnswer:
    return PolicyAnswer(message, c.route, c.domain, c.intent, [], False)


def _local_answer(question: str, docs: list[dict]) -> PolicyAnswer:
    ranked = sorted(((score(question, d["content"]), d) for d in docs), key=lambda x: x[0], reverse=True)
    hits = [(s, d) for s, d in ranked if s > 0][:1]
    if not hits:
        return PolicyAnswer("관련 규정 문서를 찾지 못했습니다. 문서를 추가 업로드하거나 담당부서에 확인해 주세요.", "needs_hr_review", "unknown", "검색 실패", [], False)
    snippets = []
    sources = []
    for _, doc in hits:
        snippets.append(_best_snippet(question, doc["content"]))
        sources.append(doc["title"])
    answer = "\n\n".join(snippets)
    answer += "\n\n※ 이 답변은 PoC용 규정 검색 결과입니다. 최종 판단은 최신 원문과 담당부서 확인이 필요합니다."
    c = classify_policy_query(question)
    return PolicyAnswer(answer, c.route, c.domain, c.intent, sources, False)


def tokenize(text: str) -> list[str]:
    tokens = []
    for token in _WORD_RE.findall(text):
        t = token.lower()
        tokens.append(t)
        # Lightweight Korean particle trimming for PoC keyword fallback.
        for suffix in ["은", "는", "이", "가", "을", "를", "에", "의", "도", "로", "으로", "까지", "인가요", "하나요"]:
            if len(t) > len(suffix) + 1 and t.endswith(suffix):
                tokens.append(t[: -len(suffix)])
    return tokens


def score(query: str, content: str) -> float:
    q_tokens = tokenize(query)
    d_tokens = tokenize(content)
    q = Counter(q_tokens)
    d = Counter(d_tokens)
    if not q or not d:
        return 0.0
    exact = sum(min(q[t], d[t]) for t in q)
    substring = 0
    content_text = content.lower()
    for t in set(q_tokens):
        if len(t) >= 2 and t in content_text:
            substring += 1
    return exact + substring


def _best_snippet(query: str, content: str) -> str:
    blocks = [b.strip() for b in re.split(r"\n\s*\n", content) if b.strip()]
    if not blocks:
        return content[:500]
    return max(blocks, key=lambda b: score(query, b))[:800]
