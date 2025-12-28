"""
Tests for EKS detector module.
"""

import pytest
from pathlib import Path
import tempfile
from shieldcommit.eks_detector import (
    parse_terraform_eks_versions,
    get_version_warning,
    scan_eks_versions
)


def test_parse_terraform_eks_versions():
    """Test parsing of EKS versions from Terraform content."""
    content = """
resource "aws_eks_cluster" "main" {
  name             = "my-cluster"
  kubernetes_version = "1.27"
  role_arn         = aws_iam_role.eks_cluster.arn
}

resource "aws_eks_cluster" "secondary" {
  kubernetes_version = "1.30"
}
"""
    findings = parse_terraform_eks_versions(content)
    assert len(findings) == 2
    assert findings[0]["version"] == "1.27"
    assert findings[0]["line"] == 4
    assert findings[1]["version"] == "1.30"
    assert findings[1]["line"] == 9


def test_parse_terraform_eks_versions_no_match():
    """Test parsing when no EKS versions found."""
    content = "resource 'aws_s3_bucket' 'bucket' { }"
    findings = parse_terraform_eks_versions(content)
    assert len(findings) == 0


def test_get_version_warning_current():
    """Test warning message for current EKS version."""
    msg = get_version_warning("1.30")
    assert "currently supported" in msg
    assert "1.30" in msg


def test_get_version_warning_extended():
    """Test warning message for extended support version."""
    msg = get_version_warning("1.27")
    assert "Extended Support" in msg
    assert "1.27" in msg


def test_get_version_warning_deprecated():
    """Test warning message for deprecated version."""
    msg = get_version_warning("1.25")
    assert "DEPRECATED" in msg
    assert "1.25" in msg


def test_get_version_warning_unknown():
    """Test warning for unknown version."""
    msg = get_version_warning("1.99")
    assert "unknown" in msg


def test_scan_eks_versions_terraform_file():
    """Test scanning a Terraform file for EKS versions."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.tf', delete=False) as f:
        f.write('kubernetes_version = "1.26"\n')
        f.flush()
        
        path = Path(f.name)
        warnings = scan_eks_versions(path)
        
        assert len(warnings) == 1
        assert warnings[0]["type"] == "eks_version"
        assert warnings[0]["version"] == "1.26"
        assert warnings[0]["status"] == "extended"
        assert "Extended Support" in warnings[0]["message"]
        
        path.unlink()


def test_scan_eks_versions_non_terraform_file():
    """Test that non-Terraform files are skipped."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write('kubernetes_version = "1.26"\n')
        f.flush()
        
        path = Path(f.name)
        warnings = scan_eks_versions(path)
        
        assert len(warnings) == 0
        path.unlink()


def test_scan_eks_versions_current_version_no_warning():
    """Test that current versions don't generate warnings."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.tf', delete=False) as f:
        f.write('kubernetes_version = "1.30"\n')
        f.flush()
        
        path = Path(f.name)
        warnings = scan_eks_versions(path)
        
        assert len(warnings) == 0
        path.unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
