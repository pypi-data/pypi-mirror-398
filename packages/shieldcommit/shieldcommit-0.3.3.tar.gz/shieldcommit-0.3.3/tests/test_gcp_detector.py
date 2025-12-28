import unittest
import tempfile
from pathlib import Path
from src.shieldcommit.gcp_detector import (
    parse_terraform_gcp_versions,
    get_version_warning,
    get_channel_info,
    scan_gcp_versions,
    GCP_VERSIONS
)


class TestGCPDetector(unittest.TestCase):
    
    def test_parse_terraform_gcp_versions_explicit(self):
        """Test parsing GCP versions from Terraform content."""
        content = '''
        resource "google_container_cluster" "example" {
          min_master_version = "1.27"
          name               = "example-gke"
        }
        '''
        findings = parse_terraform_gcp_versions(content)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["version"], "1.27")
        self.assertEqual(findings[0]["line"], 3)
        self.assertEqual(findings[0]["type"], "explicit")
    
    def test_parse_terraform_gcp_versions_channel(self):
        """Test parsing GCP release channel from Terraform content."""
        content = '''
        resource "google_container_cluster" "example" {
          release_channel {
            channel = "REGULAR"
          }
        }
        '''
        findings = parse_terraform_gcp_versions(content)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["channel"], "REGULAR")
        self.assertEqual(findings[0]["type"], "channel")
    
    def test_parse_multiple_gcp_versions(self):
        """Test parsing multiple GCP versions."""
        content = '''
        resource "google_container_cluster" "cluster1" {
          min_master_version = "1.27"
        }
        
        resource "google_container_cluster" "cluster2" {
          min_master_version = "1.30"
        }
        '''
        findings = parse_terraform_gcp_versions(content)
        self.assertEqual(len(findings), 2)
        versions = [f["version"] for f in findings if f["type"] == "explicit"]
        self.assertIn("1.27", versions)
        self.assertIn("1.30", versions)
    
    def test_get_version_warning_deprecated(self):
        """Test warning message for deprecated version."""
        warning = get_version_warning("1.25")
        self.assertIn("DEPRECATED", warning)
        self.assertIn("🚨", warning)
        self.assertIn("2024-07", warning)
    
    def test_get_version_warning_extended(self):
        """Test warning message for extended support version."""
        warning = get_version_warning("1.27")
        self.assertIn("Extended Support", warning)
        self.assertIn("⚠️", warning)
        self.assertIn("2025-04", warning)
    
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
    
    def test_get_channel_info_regular(self):
        """Test channel info for REGULAR channel."""
        info = get_channel_info("REGULAR")
        self.assertIn("REGULAR", info)
        self.assertIn("production", info)
    
    def test_get_channel_info_rapid(self):
        """Test channel info for RAPID channel."""
        info = get_channel_info("RAPID")
        self.assertIn("RAPID", info)
    
    def test_get_channel_info_stable(self):
        """Test channel info for STABLE channel."""
        info = get_channel_info("STABLE")
        self.assertIn("STABLE", info)
    
    def test_scan_gcp_versions_deprecated(self):
        """Test scanning a Terraform file for deprecated GCP versions."""
        with tempfile.TemporaryDirectory() as tmp_path:
            tmp_path = Path(tmp_path)
            tf_file = tmp_path / "gke.tf"
            tf_file.write_text('''
        resource "google_container_cluster" "example" {
          min_master_version = "1.25"
        }
        ''')
            
            warnings = scan_gcp_versions(tf_file)
            self.assertEqual(len(warnings), 1)
            self.assertEqual(warnings[0]["type"], "gcp_version")
            self.assertEqual(warnings[0]["status"], "deprecated")
    
    def test_scan_gcp_versions_current(self):
        """Test that current versions don't trigger version warnings."""
        with tempfile.TemporaryDirectory() as tmp_path:
            tmp_path = Path(tmp_path)
            tf_file = tmp_path / "gke.tf"
            tf_file.write_text('''
        resource "google_container_cluster" "example" {
          min_master_version = "1.30"
        }
        ''')
            
            warnings = scan_gcp_versions(tf_file)
            self.assertEqual(len(warnings), 0)
    
    def test_scan_gcp_channel_warning(self):
        """Test scanning for GCP release channel."""
        with tempfile.TemporaryDirectory() as tmp_path:
            tmp_path = Path(tmp_path)
            tf_file = tmp_path / "gke.tf"
            tf_file.write_text('''
        resource "google_container_cluster" "example" {
          release_channel {
            channel = "REGULAR"
          }
        }
        ''')
            
            warnings = scan_gcp_versions(tf_file)
            self.assertEqual(len(warnings), 1)
            self.assertEqual(warnings[0]["type"], "gcp_channel")
            self.assertEqual(warnings[0]["channel"], "REGULAR")
    
    def test_scan_gcp_versions_non_tf_file(self):
        """Test that non-Terraform files are ignored."""
        with tempfile.TemporaryDirectory() as tmp_path:
            tmp_path = Path(tmp_path)
            py_file = tmp_path / "script.py"
            py_file.write_text('min_master_version = "1.25"')
            
            warnings = scan_gcp_versions(py_file)
            self.assertEqual(len(warnings), 0)


if __name__ == "__main__":
    unittest.main()
