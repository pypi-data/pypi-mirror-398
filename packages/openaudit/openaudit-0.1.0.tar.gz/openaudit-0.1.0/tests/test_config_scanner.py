import pytest
from openaudit.core.domain import ScanContext, Finding
from openaudit.features.config.scanner import ConfigScanner

def test_dotenv_detection(sample_config_rules, temp_scan_dir):
    # .env exists
    env_file = temp_scan_dir / ".env"
    env_file.write_text("DEBUG=True\nDATABASE_URL=postgres://user:pass@localhost:5432/db", encoding="utf-8")
    
    ctx = ScanContext(target_path=str(temp_scan_dir))
    scanner = ConfigScanner(sample_config_rules)
    findings = scanner.scan(ctx)

    # Expect: 
    # 1. Dotenv exposed rule (hardcoded in scanner)
    # 2. DEBUG rule (from rules fixture)
    
    rule_ids = [f.rule_id for f in findings]
    assert "CONF_DOTENV_EXPOSED" in rule_ids
    assert "CONF_DEBUG" in rule_ids
    
    # Check category
    for f in findings:
        assert f.category == "config"

def test_dockerfile_scanning(sample_config_rules, temp_scan_dir):
    docker_file = temp_scan_dir / "Dockerfile"
    docker_file.write_text("FROM ubuntu\nUSER root\nEXPOSE 80", encoding="utf-8")
    
    ctx = ScanContext(target_path=str(temp_scan_dir))
    scanner = ConfigScanner(sample_config_rules)
    findings = scanner.scan(ctx)
    
    # Expect DOCKER_ROOT finding
    found = False
    for f in findings:
        if f.rule_id == "DOCKER_ROOT":
            found = True
            assert f.category == "infrastructure"
    assert found

def test_ignored_files(sample_config_rules, temp_scan_dir):
    # Create a random file that shouldn't match config logic
    readme = temp_scan_dir / "README.md"
    readme.write_text("USER root", encoding="utf-8") # Has the pattern but implies a Dockerfile rule

    ctx = ScanContext(target_path=str(temp_scan_dir))
    scanner = ConfigScanner(sample_config_rules)
    findings = scanner.scan(ctx)
    
    # ConfigScanner checks filename specific rules/types
    # README.md is not .env, Dockerfile, or docker-compose
    # So finding count should be 0
    assert len(findings) == 0
