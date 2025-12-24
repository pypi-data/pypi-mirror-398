import pytest
from pathlib import Path
from openaudit.core.domain import Rule, Finding, Severity
from openaudit.core.rules_engine import RulesEngine

def test_severity_comparison():
    assert Severity.CRITICAL > Severity.HIGH
    assert Severity.HIGH > Severity.MEDIUM
    assert Severity.MEDIUM > Severity.LOW
    assert Severity.HIGH >= Severity.HIGH
    assert Severity.LOW < Severity.CRITICAL
    assert Severity.LOW <= Severity.LOW
    assert not (Severity.LOW > Severity.HIGH)
    # Test NotImplemented path
    try:
        _ = Severity.LOW < 5
    except TypeError:
        pass
    
    try:
        Severity.LOW < "invalid"
    except TypeError:
        pass

def test_rule_model_defaults():
    r = Rule(id="TEST", description="desc", regex=".*")
    assert r.category == "general"
    assert r.remediation == "No remediation provided."
    assert r.severity == Severity.HIGH

def test_finding_creation():
    f = Finding(
        rule_id="TEST",
        description="desc",
        file_path="foo.py",
        line_number=1,
        secret_hash="masked",
        severity=Severity.MEDIUM,
        category="secret"
    )
    assert f.rule_id == "TEST"
    assert f.severity == Severity.MEDIUM

def test_rules_engine_load(tmp_path):
    # Create a dummy rules.yaml
    rules_dir = tmp_path / "rules"
    rules_dir.mkdir()
    rule_file = rules_dir / "test.yaml"
    rule_content = """
rules:
  - id: "TEST_RULE"
    description: "Testing rule loading"
    regex: "test"
    severity: "low"
    category: "test_cat"
    """
    rule_file.write_text(rule_content, encoding="utf-8")

    engine = RulesEngine(rules_dir)
    loaded_rules = engine.load_rules()
    
    assert len(loaded_rules) == 1
    assert loaded_rules[0].id == "TEST_RULE"
    assert loaded_rules[0].category == "test_cat"

def test_rules_engine_load_empty(tmp_path):
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    engine = RulesEngine(empty_dir)
    rules = engine.load_rules()
    assert len(rules) == 0

def test_rules_engine_malformed(tmp_path):
    rules_dir = tmp_path / "rules_bad"
    rules_dir.mkdir()
    bad_file = rules_dir / "bad.yaml"
    bad_file.write_text("rules: [", encoding="utf-8") # Invalid YAML

    engine = RulesEngine(rules_dir)
    rules = engine.load_rules()
    # Should catch exception and continue/return empty (for that file)
    assert len(rules) == 0
