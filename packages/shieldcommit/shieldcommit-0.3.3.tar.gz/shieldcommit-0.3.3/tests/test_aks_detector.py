import unittest
import tempfile
from pathlib import Path
from src.shieldcommit.aks_detector import (
    parse_terraform_aks_versions,
    get_version_warning,
    scan_aks_versions,
    AKS_VERSIONS
)


class TestAKSDetector(unittest.TestCase):
    
    def test_parse_terraform_aks_versions(self):
        """Test parsing AKS versions from Terraform content."""
        content = '''
        resource "azurerm_kubernetes_cluster" "example" {
          kubernetes_version = "1.27"
          name               = "example-aks"
        }
        '''
        findings = parse_terraform_aks_versions(content)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["version"], "1.27")
        self.assertEqual(findings[0]["line"], 3)
    
    def test_parse_multiple_versions(self):
        """Test parsing multiple AKS versions."""
        content = '''
        resource "azurerm_kubernetes_cluster" "cluster1" {
          kubernetes_version = "1.27"
        }
        
        resource "azurerm_kubernetes_cluster" "cluster2" {
          kubernetes_version = "1.30"
        }
        '''
        findings = parse_terraform_aks_versions(content)
        self.assertEqual(len(findings), 2)
        versions = [f["version"] for f in findings]
        self.assertIn("1.27", versions)
        self.assertIn("1.30", versions)
    
    def test_get_version_warning_deprecated(self):
        """Test warning message for deprecated version."""
        warning = get_version_warning("1.25")
        self.assertIn("DEPRECATED", warning)
        self.assertIn("🚨", warning)
        self.assertIn("2024-11", warning)
    
    def test_get_version_warning_extended(self):
        """Test warning message for extended support version."""
        warning = get_version_warning("1.27")
        self.assertIn("Extended Support", warning)
        self.assertIn("⚠️", warning)
        self.assertIn("2025-07", warning)
    
    def test_get_version_warning_current(self):
        """Test info message for current version."""
        warning = get_version_warning("1.30")
        self.assertIn("currently supported", warning)
        self.assertIn("✓", warning)
    
    def test_get_version_warning_unknown(self):
        """Test warning for unknown version."""
        warning = get_version_warning("1.99")
        self.assertIn("unknown", warning)
        self.assertIn("⚠️", warning)
    
    def test_scan_aks_versions_tf_file(self):
        """Test scanning a Terraform file for AKS warnings."""
        with tempfile.TemporaryDirectory() as tmp_path:
            tmp_path = Path(tmp_path)
            tf_file = tmp_path / "cluster.tf"
            tf_file.write_text('''
        resource "azurerm_kubernetes_cluster" "example" {
          kubernetes_version = "1.25"
        }
        ''')
            
            warnings = scan_aks_versions(tf_file)
            self.assertEqual(len(warnings), 1)
            self.assertEqual(warnings[0]["type"], "aks_version")
            self.assertEqual(warnings[0]["status"], "deprecated")
    
    def test_scan_aks_versions_current_version(self):
        """Test that current versions don't trigger warnings."""
        with tempfile.TemporaryDirectory() as tmp_path:
            tmp_path = Path(tmp_path)
            tf_file = tmp_path / "cluster.tf"
            tf_file.write_text('''
        resource "azurerm_kubernetes_cluster" "example" {
          kubernetes_version = "1.30"
        }
        ''')
            
            warnings = scan_aks_versions(tf_file)
            self.assertEqual(len(warnings), 0)
    
    def test_scan_aks_versions_non_tf_file(self):
        """Test that non-Terraform files are ignored."""
        with tempfile.TemporaryDirectory() as tmp_path:
            tmp_path = Path(tmp_path)
            py_file = tmp_path / "script.py"
            py_file.write_text('kubernetes_version = "1.25"')
            
            warnings = scan_aks_versions(py_file)
            self.assertEqual(len(warnings), 0)


if __name__ == "__main__":
    unittest.main()
