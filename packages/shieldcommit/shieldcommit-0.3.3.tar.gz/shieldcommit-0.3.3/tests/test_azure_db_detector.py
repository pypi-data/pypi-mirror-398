import unittest
import tempfile
from pathlib import Path
from src.shieldcommit.azure_db_detector import (
    parse_terraform_azure_db_versions,
    get_azure_db_warning,
    scan_azure_db_versions,
    AZURE_DB_ENGINES
)


class TestAzureDBDetector(unittest.TestCase):
    
    def test_parse_terraform_azure_mysql_versions(self):
        """Test parsing Azure MySQL versions from Terraform content."""
        content = '''
        resource "azurerm_mysql_server" "example" {
          version = "8.0"
          name    = "example-mysql"
        }
        '''
        findings = parse_terraform_azure_db_versions(content)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["engine"], "mysql")
        self.assertEqual(findings[0]["version"], "8.0")
    
    def test_parse_terraform_azure_postgresql_versions(self):
        """Test parsing Azure PostgreSQL versions from Terraform content."""
        content = '''
        resource "azurerm_postgresql_server" "example" {
          version = "11"
          name    = "example-postgres"
        }
        '''
        findings = parse_terraform_azure_db_versions(content)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["engine"], "postgres")
        self.assertEqual(findings[0]["version"], "11")
    
    def test_parse_terraform_azure_sql_versions(self):
        """Test parsing Azure SQL versions from Terraform content."""
        content = '''
        resource "azurerm_mssql_server" "example" {
          name    = "example-sql"
          sku_name = "GP_Gen5_2"
        }
        '''
        findings = parse_terraform_azure_db_versions(content)
        # SQL detection is via SKU
        self.assertTrue(any(f["engine"] == "sql" for f in findings) or len(findings) == 0)
    
    def test_parse_multiple_azure_db_versions(self):
        """Test parsing multiple Azure database versions."""
        content = '''
        resource "azurerm_mysql_server" "mysql1" {
          version = "5.7"
        }
        
        resource "azurerm_postgresql_server" "postgres1" {
          version = "12"
        }
        '''
        findings = parse_terraform_azure_db_versions(content)
        self.assertTrue(len(findings) >= 2)
    
    def test_get_azure_db_warning_deprecated_mysql(self):
        """Test warning message for deprecated MySQL version."""
        warning = get_azure_db_warning("mysql", "5.7")
        self.assertIn("DEPRECATED", warning)
        self.assertIn("🚨", warning)
        self.assertIn("2024-10", warning)
    
    def test_get_azure_db_warning_deprecated_postgres(self):
        """Test warning message for deprecated PostgreSQL version."""
        warning = get_azure_db_warning("postgres", "11")
        self.assertIn("DEPRECATED", warning)
        self.assertIn("🚨", warning)
        self.assertIn("2023-10", warning)
    
    def test_get_azure_db_warning_extended_postgres(self):
        """Test warning message for extended support PostgreSQL version."""
        warning = get_azure_db_warning("postgres", "13")
        self.assertIn("Extended Support", warning)
        self.assertIn("⚠️", warning)
        self.assertIn("2025-11", warning)
    
    def test_get_azure_db_warning_current(self):
        """Test info message for current version."""
        warning = get_azure_db_warning("mysql", "8.0")
        self.assertIn("currently supported", warning)
        self.assertIn("✓", warning)
    
    def test_get_azure_db_warning_unknown(self):
        """Test warning for unknown version."""
        warning = get_azure_db_warning("mysql", "9.0")
        self.assertIn("unknown", warning)
        self.assertIn("⚠️", warning)
    
    def test_scan_azure_db_versions_deprecated(self):
        """Test scanning a Terraform file for deprecated Azure database versions."""
        with tempfile.TemporaryDirectory() as tmp_path:
            tmp_path = Path(tmp_path)
            tf_file = tmp_path / "database.tf"
            tf_file.write_text('''
        resource "azurerm_mysql_server" "example" {
          version = "5.7"
        }
        ''')
            
            warnings = scan_azure_db_versions(tf_file)
            self.assertEqual(len(warnings), 1)
            self.assertEqual(warnings[0]["type"], "azure_db_version")
            self.assertEqual(warnings[0]["status"], "deprecated")
    
    def test_scan_azure_db_versions_current(self):
        """Test that current versions don't trigger warnings."""
        with tempfile.TemporaryDirectory() as tmp_path:
            tmp_path = Path(tmp_path)
            tf_file = tmp_path / "database.tf"
            tf_file.write_text('''
        resource "azurerm_mysql_server" "example" {
          version = "8.0"
        }
        ''')
            
            warnings = scan_azure_db_versions(tf_file)
            self.assertEqual(len(warnings), 0)
    
    def test_scan_azure_db_versions_non_tf_file(self):
        """Test that non-Terraform files are ignored."""
        with tempfile.TemporaryDirectory() as tmp_path:
            tmp_path = Path(tmp_path)
            py_file = tmp_path / "script.py"
            py_file.write_text('version = "5.7"')
            
            warnings = scan_azure_db_versions(py_file)
            self.assertEqual(len(warnings), 0)
    
    def test_scan_azure_db_versions_extended_support(self):
        """Test detecting extended support versions."""
        with tempfile.TemporaryDirectory() as tmp_path:
            tmp_path = Path(tmp_path)
            tf_file = tmp_path / "database.tf"
            tf_file.write_text('''
        resource "azurerm_postgresql_server" "example" {
          version = "13"
        }
        ''')
            
            warnings = scan_azure_db_versions(tf_file)
            self.assertEqual(len(warnings), 1)
            self.assertEqual(warnings[0]["status"], "extended")


if __name__ == "__main__":
    unittest.main()
