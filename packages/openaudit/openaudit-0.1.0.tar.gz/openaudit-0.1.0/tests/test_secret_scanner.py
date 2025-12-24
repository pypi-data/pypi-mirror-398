import pytest
import math
from unittest.mock import patch, MagicMock
from openaudit.core.domain import ScanContext, Finding, Rule, Severity
from openaudit.features.secrets.scanner import SecretScanner

def test_secret_scanner_detection(sample_secret_rules, temp_scan_dir):
    # key like AKIA...
    secret_content = "aws_key = 'AKIA1234567890123456'"
    file = temp_scan_dir / "secrets.py"
    file.write_text(secret_content, encoding="utf-8")

    ctx = ScanContext(target_path=str(temp_scan_dir))
    scanner = SecretScanner(sample_secret_rules)
    findings = scanner.scan(ctx)

    assert len(findings) >= 1
    f = findings[0]
    assert f.rule_id == "AWS_TEST_KEY"
    assert f.secret_hash.startswith("AK")  # Masking preserves first 2 chars
    assert "*" in f.secret_hash  # check masking
    assert f.category == "secret"

def test_secret_scanner_entropy(sample_secret_rules, temp_scan_dir):
    # Rule HIGH_ENTROPY_TEST checks for 32 chars
    # Low entropy string (repeated chars)
    low_ent = "A" * 32
    # High entropy string
    high_ent = "aB3dE9gH1jK2lM4nP5qR6sT7uV8wX0yZ"
    
    content = f"""
    api_key = "{low_ent}"
    api_key = "{high_ent}"
    """
    file = temp_scan_dir / "config.py"
    file.write_text(content, encoding="utf-8")

    ctx = ScanContext(target_path=str(temp_scan_dir))
    scanner = SecretScanner(sample_secret_rules)
    findings = scanner.scan(ctx)

    # Should detect the high entropy one, but verify behavior regarding the low entropy one
    # The current logic filters out low entropy matches if check is enabled.
    
    found_hashes = [f.secret_hash for f in findings]
    # We expect high entropy to be found and masked
    # low entropy might be filtered out depending on implementation threshold (typically 4.5)
    
    # So we expect only 1 finding
    assert len(findings) == 1
    assert "aB" in findings[0].secret_hash and "*" in findings[0].secret_hash

def test_shannon_entropy_calculation(sample_secret_rules):
    # Direct access to _calculate_entropy
    scanner = SecretScanner(sample_secret_rules)
    e1 = scanner._calculate_entropy("aaaaa")
    assert e1 < 1.0
    e2 = scanner._calculate_entropy("abcdefg")
    assert e2 > 2.0

def test_secret_scanner_bad_regex():
    bad_rule = Rule(
        id="BAD_REGEX",
        description="Bad Regex",
        regex="[", # Invalid regex
        severity=Severity.HIGH,
        category="secret"
    )
    scanner = SecretScanner([bad_rule])
    # Should handle error and continue (have 0 rules compiled)
    assert len(scanner.compiled_rules) == 0

def test_scan_error(sample_secret_rules, temp_scan_dir):
    # Mock read_text to raise exception
    file = temp_scan_dir / "unreadable.py"
    file.touch()
    
    with patch('pathlib.Path.read_text', side_effect=PermissionError("Boom")):
        ctx = ScanContext(target_path=str(temp_scan_dir))
        scanner = SecretScanner(sample_secret_rules)
        # Should catch exception and return empty findings (or continue)
        findings = scanner.scan(ctx)
        # Verify it didn't crash
        assert isinstance(findings, list)
