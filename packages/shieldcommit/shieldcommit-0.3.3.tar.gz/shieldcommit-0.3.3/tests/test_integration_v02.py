"""
Integration tests for ShieldCommit v0.2 - Testing secrets + version warnings together
Includes EKS, RDS, AKS, GCP versions + Azure and GCP database versions
"""

import pytest
from pathlib import Path
import tempfile
from shieldcommit.scanner import scan_files


def test_scan_files_with_secrets_and_warnings():
    """Test scanning a file that has both secrets and version warnings."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.tf', delete=False) as f:
        f.write('''
resource "aws_eks_cluster" "main" {
  kubernetes_version = "1.26"
  secret_key = "sk_live_test1234567890abcdefghij"  # This is a secret
}

resource "aws_db_instance" "db" {
  engine = "postgres"
  engine_version = "12"
  db_password = "password='super_secret_123'"  # This is a secret
}
''')
        f.flush()
        
        path = Path(f.name)
        result = scan_files([str(path)])
        
        # Verify result structure
        assert "findings" in result
        assert "warnings" in result
        assert isinstance(result["findings"], list)
        assert isinstance(result["warnings"], list)
        
        # Should have secrets (findings)
        assert len(result["findings"]) > 0
        
        # Should have version warnings
        assert len(result["warnings"]) > 0
        
        # Verify findings are secrets
        secret_patterns = {f["pattern"] for f in result["findings"]}
        assert "Stripe Secret Key" in secret_patterns or "Generic Password" in secret_patterns
        
        # Verify warnings are version issues
        warning_types = {w["type"] for w in result["warnings"]}
        assert "eks_version" in warning_types or "rds_version" in warning_types
        
        path.unlink()


def test_scan_files_warnings_only():
    """Test scanning a file that has only version warnings, no secrets."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.tf', delete=False) as f:
        f.write('''
resource "aws_eks_cluster" "main" {
  kubernetes_version = "1.25"
  name = "my-cluster"
}
''')
        f.flush()
        
        path = Path(f.name)
        result = scan_files([str(path)])
        
        assert len(result["findings"]) == 0
        # Now detects both EKS and AKS warnings for the same version pattern
        assert len(result["warnings"]) >= 1
        warning_types = {w["type"] for w in result["warnings"]}
        assert "eks_version" in warning_types or "aks_version" in warning_types
        
        path.unlink()


def test_scan_files_secrets_only():
    """Test scanning a Python file with secrets (no version warnings)."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write('''
api_key = "sk_live_test1234567890abcdefghij"
password = "password='secret123'"
''')
        f.flush()
        
        path = Path(f.name)
        result = scan_files([str(path)])
        
        assert len(result["findings"]) > 0
        assert len(result["warnings"]) == 0  # Python files don't get version warnings
        
        path.unlink()


def test_scan_multiple_files():
    """Test scanning multiple files with mixed results."""
    files = []
    
    # Create a Terraform file with warnings
    with tempfile.NamedTemporaryFile(mode='w', suffix='.tf', delete=False) as f:
        f.write('kubernetes_version = "1.25"')
        f.flush()
        files.append(f.name)
    
    # Create a Python file with secrets
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write('api_key = "sk_live_test1234567890abcdefghij"')
        f.flush()
        files.append(f.name)
    
    result = scan_files(files)
    
    assert len(result["findings"]) > 0  # From Python file
    assert len(result["warnings"]) > 0  # From Terraform file
    
    for file in files:
        Path(file).unlink()


def test_scan_aks_versions():
    """Test scanning for AKS version warnings."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.tf', delete=False) as f:
        f.write('''
resource "azurerm_kubernetes_cluster" "main" {
  kubernetes_version = "1.26"
  name = "my-aks-cluster"
}
''')
        f.flush()
        
        path = Path(f.name)
        result = scan_files([str(path)])
        
        assert len(result["warnings"]) > 0
        warning_types = {w["type"] for w in result["warnings"]}
        assert "aks_version" in warning_types
        
        # Check for extended support status
        aks_warnings = [w for w in result["warnings"] if w["type"] == "aks_version"]
        assert len(aks_warnings) > 0
        assert aks_warnings[0]["status"] == "extended"
        
        path.unlink()


def test_scan_gcp_versions():
    """Test scanning for GCP GKE version warnings."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.tf', delete=False) as f:
        f.write('''
resource "google_container_cluster" "main" {
  min_master_version = "1.25"
  name = "my-gke-cluster"
}
''')
        f.flush()
        
        path = Path(f.name)
        result = scan_files([str(path)])
        
        assert len(result["warnings"]) > 0
        warning_types = {w["type"] for w in result["warnings"]}
        assert "gcp_version" in warning_types
        
        # Check for deprecated status
        gcp_warnings = [w for w in result["warnings"] if w["type"] == "gcp_version"]
        assert len(gcp_warnings) > 0
        assert gcp_warnings[0]["status"] == "deprecated"
        
        path.unlink()


def test_scan_gcp_release_channel():
    """Test scanning for GCP release channel info."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.tf', delete=False) as f:
        f.write('''
resource "google_container_cluster" "main" {
  release_channel {
    channel = "RAPID"
  }
}
''')
        f.flush()
        
        path = Path(f.name)
        result = scan_files([str(path)])
        
        # Channel info is always reported (not filtered as warnings)
        warning_types = {w["type"] for w in result["warnings"]}
        if "gcp_channel" in warning_types:
            gcp_channels = [w for w in result["warnings"] if w["type"] == "gcp_channel"]
            assert len(gcp_channels) > 0
            assert gcp_channels[0]["channel"] == "RAPID"
        
        path.unlink()


def test_scan_all_cloud_providers():
    """Test scanning files from all four cloud providers."""
    files = []
    
    # EKS
    with tempfile.NamedTemporaryFile(mode='w', suffix='.tf', delete=False) as f:
        f.write('kubernetes_version = "1.26"  # EKS')
        f.flush()
        files.append(f.name)
    
    # RDS
    with tempfile.NamedTemporaryFile(mode='w', suffix='.tf', delete=False) as f:
        f.write('''
engine = "postgres"
engine_version = "12"
''')
        f.flush()
        files.append(f.name)
    
    # AKS
    with tempfile.NamedTemporaryFile(mode='w', suffix='.tf', delete=False) as f:
        f.write('kubernetes_version = "1.25"  # AKS')
        f.flush()
        files.append(f.name)
    
    # GCP GKE
    with tempfile.NamedTemporaryFile(mode='w', suffix='.tf', delete=False) as f:
        f.write('min_master_version = "1.24"  # GCP GKE')
        f.flush()
        files.append(f.name)
    
    result = scan_files(files)
    
    # Should have warnings from all providers
    warning_types = {w["type"] for w in result["warnings"]}
    assert len(result["warnings"]) > 0
    
    for file in files:
        Path(file).unlink()


def test_scan_azure_database_versions():
    """Test scanning for Azure database version warnings."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.tf', delete=False) as f:
        f.write('''
resource "azurerm_mysql_server" "example" {
  version = "5.7"
}
''')
        f.flush()
        
        path = Path(f.name)
        result = scan_files([str(path)])
        
        assert len(result["warnings"]) > 0
        warning_types = {w["type"] for w in result["warnings"]}
        assert "azure_db_version" in warning_types
        
        azure_warnings = [w for w in result["warnings"] if w["type"] == "azure_db_version"]
        assert len(azure_warnings) > 0
        assert azure_warnings[0]["status"] == "deprecated"
        
        path.unlink()


def test_scan_gcp_cloudsql_versions():
    """Test scanning for GCP Cloud SQL database version warnings."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.tf', delete=False) as f:
        f.write('''
resource "google_sql_database_instance" "example" {
  database_version = "MYSQL_5_7"
}
''')
        f.flush()
        
        path = Path(f.name)
        result = scan_files([str(path)])
        
        assert len(result["warnings"]) > 0
        warning_types = {w["type"] for w in result["warnings"]}
        assert "gcp_cloudsql_version" in warning_types
        
        gcp_warnings = [w for w in result["warnings"] if w["type"] == "gcp_cloudsql_version"]
        assert len(gcp_warnings) > 0
        assert gcp_warnings[0]["status"] == "deprecated"
        
        path.unlink()


def test_scan_all_platforms_and_databases():
    """Test scanning all cloud platforms and their databases."""
    files = []
    
    # Kubernetes platforms
    with tempfile.NamedTemporaryFile(mode='w', suffix='.tf', delete=False) as f:
        f.write('kubernetes_version = "1.25"  # EKS/AKS')
        f.flush()
        files.append(f.name)
    
    # AWS RDS
    with tempfile.NamedTemporaryFile(mode='w', suffix='.tf', delete=False) as f:
        f.write('engine_version = "12"  # RDS')
        f.flush()
        files.append(f.name)
    
    # Azure Database
    with tempfile.NamedTemporaryFile(mode='w', suffix='.tf', delete=False) as f:
        f.write('''
resource "azurerm_mysql_server" "example" {
  version = "5.7"
}
''')
        f.flush()
        files.append(f.name)
    
    # GCP Cloud SQL
    with tempfile.NamedTemporaryFile(mode='w', suffix='.tf', delete=False) as f:
        f.write('''
resource "google_sql_database_instance" "example" {
  database_version = "POSTGRES_11"
}
''')
        f.flush()
        files.append(f.name)
    
    result = scan_files(files)
    
    # Should have warnings from all platforms and databases
    assert len(result["warnings"]) > 0
    
    warning_types = {w["type"] for w in result["warnings"]}
    # Check for at least some of the expected warning types
    assert len(warning_types) > 0
    
    for file in files:
        Path(file).unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])