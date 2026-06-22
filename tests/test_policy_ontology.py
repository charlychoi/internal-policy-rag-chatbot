from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ONTOLOGY_PATH = ROOT / "data" / "samples" / "policy_ontology.json"


def load_ontology() -> dict:
    return json.loads(ONTOLOGY_PATH.read_text(encoding="utf-8"))


def test_policy_ontology_has_required_top_level_sections():
    ontology = load_ontology()
    assert ontology["version"]
    assert ontology["locale"] == "ko-KR"
    assert "domains" in ontology
    assert "classification_rules" in ontology
    assert "safe_response_templates" in ontology
    assert "test_questions" in ontology


def test_required_domains_are_present():
    ontology = load_ontology()
    domain_ids = {domain["id"] for domain in ontology["domains"]}
    assert {
        "employment_rules",
        "leave_vacation",
        "travel_expense",
        "information_security",
        "privacy",
        "remote_work",
        "disciplinary_process",
        "ethics_compliance",
    }.issubset(domain_ids)


def test_every_domain_has_keywords_and_action():
    ontology = load_ontology()
    allowed_actions = {"answerable", "needs_hr_review", "refuse"}
    for domain in ontology["domains"]:
        assert domain["id"]
        assert domain["label"]
        assert domain["keywords"]
        assert domain["default_action"] in allowed_actions


def test_risk_rules_cover_required_abuse_types():
    ontology = load_ontology()
    risk_ids = {rule["risk_id"] for rule in ontology["classification_rules"]["risk_detection"]}
    assert {
        "policy_evasion",
        "discipline_evasion",
        "privacy_exfiltration",
        "security_bypass",
        "legal_or_ethics_advice",
    }.issubset(risk_ids)


def test_refusal_rules_have_patterns():
    ontology = load_ontology()
    for rule in ontology["classification_rules"]["risk_detection"]:
        assert rule["patterns"]
        assert rule["action"] in {"refuse", "needs_hr_review"}


def test_test_questions_cover_answerable_review_and_refuse():
    ontology = load_ontology()
    actions = {case["expected_action"] for case in ontology["test_questions"]}
    assert {"answerable", "needs_hr_review", "refuse"}.issubset(actions)


def test_refusal_test_questions_include_expected_risk():
    ontology = load_ontology()
    refusal_cases = [case for case in ontology["test_questions"] if case["expected_action"] == "refuse"]
    assert refusal_cases
    for case in refusal_cases:
        assert case["expected_risk"]
