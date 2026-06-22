from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
import json
import re

DEFAULT_ONTOLOGY_PATH = Path(__file__).resolve().parents[1] / "data" / "samples" / "policy_ontology.json"


@dataclass(frozen=True)
class PolicyClassification:
    domain: str
    intent: str
    route: str
    risk: str = ""
    reason: str = ""
    confidence: float = 0.5

    def to_dict(self) -> dict:
        return asdict(self)


def load_ontology(path: Path = DEFAULT_ONTOLOGY_PATH) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def classify_policy_query(query: str, ontology: dict | None = None) -> PolicyClassification:
    ontology = ontology or load_ontology()
    normalized = query.lower()

    # 1) Safety/risk rules have priority over normal retrieval.
    for risk in ontology.get("classification_rules", {}).get("risk_detection", []):
        if _matches_any(normalized, risk.get("patterns", [])):
            domain = _infer_domain_from_query(normalized, ontology) or "ethics_compliance"
            return PolicyClassification(
                domain=domain,
                intent="위험/컴플라이언스",
                route=risk.get("action", "refuse"),
                risk=risk.get("risk_id", "unknown_risk"),
                reason=risk.get("label", "위험 질문"),
                confidence=0.92,
            )

    # 2) Domain classification from ontology domain keywords.
    best_domain = "general_policy"
    best_domain_obj = None
    best_score = 0
    for domain in ontology.get("domains", []):
        score = sum(1 for kw in domain.get("keywords", []) if kw.lower() in normalized)
        if score > best_score:
            best_score = score
            best_domain = domain["id"]
            best_domain_obj = domain

    # 3) Lightweight intent classification. The ontology file may or may not
    # define explicit intents, so keep robust defaults.
    intent = "일반 문의"
    for item in ontology.get("intents", []):
        if _matches_any(normalized, item.get("keywords", [])):
            intent = item.get("label", intent)
            break
    if intent == "일반 문의":
        if _matches_any(normalized, ["언제", "기한", "며칠", "몇 일", "까지"]):
            intent = "기한 문의"
        elif _matches_any(normalized, ["누구", "승인", "담당", "권한"]):
            intent = "승인권자 문의"
        elif _matches_any(normalized, ["어떻게", "절차", "신청", "방법"]):
            intent = "절차 문의"
        elif _matches_any(normalized, ["가능", "되나요", "쓸 수", "사용"]):
            intent = "자격/가능 여부 문의"

    route = (best_domain_obj or {}).get("default_action") if best_score else "needs_hr_review"
    route = route or "answerable"
    reason = "관련 규정 출처 기반 답변 가능" if best_score else "규정 영역이 모호하여 담당부서 확인 필요"
    return PolicyClassification(best_domain, intent, route, reason=reason, confidence=0.75 if best_score else 0.35)


def build_safe_response(classification: PolicyClassification) -> str | None:
    if classification.route == "refuse":
        return (
            f"이 질문은 `{classification.risk}` 위험 유형으로 분류됩니다. "
            "규정 회피, 개인정보 유출, 보안 통제 우회, 불법/비윤리 행위에 대한 방법은 안내할 수 없습니다. "
            "정상적인 절차와 담당부서 문의 방법을 안내해 주세요."
        )
    if classification.route == "needs_hr_review":
        return (
            "이 질문은 개별 사안 판단 또는 담당부서 확인이 필요한 영역입니다. "
            "관련 규정의 일반 원칙은 안내할 수 있지만, 최종 판단은 인사/총무/보안/개인정보 담당부서에 확인해 주세요."
        )
    return None


def _matches_any(text: str, keywords: list[str]) -> bool:
    return any(re.search(re.escape(k.lower()), text) for k in keywords)


def _infer_domain_from_query(text: str, ontology: dict) -> str | None:
    best_domain = None
    best_score = 0
    for domain in ontology.get("domains", []):
        score = sum(1 for kw in domain.get("keywords", []) if kw.lower() in text)
        if score > best_score:
            best_domain = domain.get("id")
            best_score = score
    return best_domain
