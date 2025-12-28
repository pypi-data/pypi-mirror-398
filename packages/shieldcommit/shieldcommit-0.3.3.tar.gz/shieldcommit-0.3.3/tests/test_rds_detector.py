"""
Tests for RDS detector module.
"""

import pytest
from pathlib import Path
import tempfile
from shieldcommit.rds_detector import (
    parse_terraform_rds_versions,
    get_rds_warning,
    scan_rds_versions
)


def test_parse_terraform_rds_versions():
    """Test parsing of RDS versions from Terraform content."""
    content = """
resource "aws_db_instance" "postgres" {
  identifier = "my-db"
  engine = "postgres"
  engine_version = "13"
}

resource "aws_db_instance" "mysql" {
  engine = "mysql"
  engine_version = "8.0"
}
"""
    findings = parse_terraform_rds_versions(content)
    assert len(findings) == 2
    assert findings[0]["engine"] == "postgres"
    assert findings[0]["version"] == "13"
    assert findings[1]["engine"] == "mysql"
    assert findings[1]["version"] == "8.0"


def test_parse_terraform_rds_versions_mariadb():
    """Test parsing MariaDB versions."""
    content = """
resource "aws_db_instance" "mariadb" {
  engine = "mariadb"
  engine_version = "10.5"
}
"""
    findings = parse_terraform_rds_versions(content)
    assert len(findings) == 1
    assert findings[0]["engine"] == "mariadb"
    assert findings[0]["version"] == "10.5"


def test_parse_terraform_rds_versions_no_match():
    """Test parsing when no RDS versions found."""
    content = "resource 'aws_s3_bucket' 'bucket' { }"
    findings = parse_terraform_rds_versions(content)
    assert len(findings) == 0


def test_get_rds_warning_current():
    """Test warning message for current RDS version."""
    msg = get_rds_warning("postgres", "15")
    assert "currently supported" in msg
    assert "15" in msg


def test_get_rds_warning_extended():
    """Test warning message for extended support version."""
    msg = get_rds_warning("postgres", "13")
    assert "Extended Support" in msg
    assert "13" in msg


def test_get_rds_warning_deprecated():
    """Test warning message for deprecated version."""
    msg = get_rds_warning("postgres", "12")
    assert "DEPRECATED" in msg
    assert "12" in msg


def test_get_rds_warning_unknown_engine():
    """Test warning for unknown engine."""
    msg = get_rds_warning("oracle", "19c")
    assert "not recognized" in msg


def test_get_rds_warning_unknown_version():
    """Test warning for unknown version of known engine."""
    msg = get_rds_warning("postgres", "99.99")
    assert "unknown" in msg


def test_scan_rds_versions_terraform_file():
    """Test scanning a Terraform file for RDS versions."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.tf', delete=False) as f:
        f.write('engine = "mariadb"\nengine_version = "10.4"\n')
        f.flush()
        
        path = Path(f.name)
        warnings = scan_rds_versions(path)
        
        assert len(warnings) == 1
        assert warnings[0]["type"] == "rds_version"
        assert warnings[0]["engine"] == "mariadb"
        assert warnings[0]["version"] == "10.4"
        assert warnings[0]["status"] == "extended"
        assert "Extended Support" in warnings[0]["message"]
        
        path.unlink()


def test_scan_rds_versions_non_terraform_file():
    """Test that non-Terraform files are skipped."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write('engine = "postgres"\nengine_version = "13"\n')
        f.flush()
        
        path = Path(f.name)
        warnings = scan_rds_versions(path)
        
        assert len(warnings) == 0
        path.unlink()


def test_scan_rds_versions_current_version_no_warning():
    """Test that current versions don't generate warnings."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.tf', delete=False) as f:
        f.write('engine = "mysql"\nengine_version = "8.0"\n')
        f.flush()
        
        path = Path(f.name)
        warnings = scan_rds_versions(path)
        
        assert len(warnings) == 0
        path.unlink()


def test_scan_rds_versions_multiple_deprecations():
    """Test scanning multiple deprecated versions."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.tf', delete=False) as f:
        f.write('''
resource "aws_db_instance" "old_postgres" {
  engine = "postgres"
  engine_version = "12"
}

resource "aws_db_instance" "old_mysql" {
  engine = "mysql"
  engine_version = "5.7"
}
''')
        f.flush()
        
        path = Path(f.name)
        warnings = scan_rds_versions(path)
        
        assert len(warnings) == 2
        assert all(w["status"] == "deprecated" for w in warnings)
        
        path.unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
