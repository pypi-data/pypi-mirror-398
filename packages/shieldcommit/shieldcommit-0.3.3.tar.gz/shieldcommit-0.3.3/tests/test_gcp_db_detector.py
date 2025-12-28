import unittest
import tempfile
from pathlib import Path
from src.shieldcommit.gcp_db_detector import (
    parse_terraform_gcp_cloudsql_versions,
    parse_gcp_version_string,
    get_gcp_cloudsql_warning,
    scan_gcp_cloudsql_versions,
    GCP_CLOUDSQL_ENGINES
)


class TestGCPDatabaseDetector(unittest.TestCase):
    
    def test_parse_gcp_version_string_mysql(self):
        """Test parsing GCP MySQL version strings."""
        engine, version = parse_gcp_version_string("MYSQL_8_0")
        self.assertEqual(engine, "mysql")
        self.assertEqual(version, "8.0")
        
        engine, version = parse_gcp_version_string("MYSQL_5_7")
        self.assertEqual(engine, "mysql")
        self.assertEqual(version, "5.7")
    
    def test_parse_gcp_version_string_postgres(self):
        """Test parsing GCP PostgreSQL version strings."""
        engine, version = parse_gcp_version_string("POSTGRES_14")
        self.assertEqual(engine, "postgres")
        self.assertEqual(version, "14")
        
        engine, version = parse_gcp_version_string("POSTGRES_11")
        self.assertEqual(engine, "postgres")
        self.assertEqual(version, "11")
    
    def test_parse_gcp_version_string_sqlserver(self):
        """Test parsing GCP SQL Server version strings."""
        engine, version = parse_gcp_version_string("SQLSERVER_2019")
        self.assertEqual(engine, "sqlserver")
        self.assertEqual(version, "2019")
        
        engine, version = parse_gcp_version_string("SQLSERVER_2017")
        self.assertEqual(engine, "sqlserver")
        self.assertEqual(version, "2017")
    
    def test_parse_terraform_gcp_cloudsql_mysql(self):
        """Test parsing GCP Cloud SQL MySQL versions from Terraform content."""
        content = '''
        resource "google_sql_database_instance" "example" {
          database_version = "MYSQL_8_0"
          name             = "example-mysql"
        }
        '''
        findings = parse_terraform_gcp_cloudsql_versions(content)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["engine"], "mysql")
        self.assertEqual(findings[0]["version"], "8.0")
    
    def test_parse_terraform_gcp_cloudsql_postgres(self):
        """Test parsing GCP Cloud SQL PostgreSQL versions from Terraform content."""
        content = '''
        resource "google_sql_database_instance" "example" {
          database_version = "POSTGRES_15"
          name             = "example-postgres"
        }
        '''
        findings = parse_terraform_gcp_cloudsql_versions(content)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["engine"], "postgres")
        self.assertEqual(findings[0]["version"], "15")
    
    def test_parse_terraform_gcp_cloudsql_sqlserver(self):
        """Test parsing GCP Cloud SQL SQL Server versions from Terraform content."""
        content = '''
        resource "google_sql_database_instance" "example" {
          database_version = "SQLSERVER_2019"
          name             = "example-sql"
        }
        '''
        findings = parse_terraform_gcp_cloudsql_versions(content)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["engine"], "sqlserver")
        self.assertEqual(findings[0]["version"], "2019")
    
    def test_parse_multiple_gcp_cloudsql_versions(self):
        """Test parsing multiple GCP Cloud SQL versions."""
        content = '''
        resource "google_sql_database_instance" "mysql" {
          database_version = "MYSQL_5_7"
        }
        
        resource "google_sql_database_instance" "postgres" {
          database_version = "POSTGRES_12"
        }
        '''
        findings = parse_terraform_gcp_cloudsql_versions(content)
        self.assertEqual(len(findings), 2)
    
    def test_get_gcp_cloudsql_warning_deprecated_mysql(self):
        """Test warning message for deprecated MySQL version."""
        warning = get_gcp_cloudsql_warning("mysql", "5.7")
        self.assertIn("DEPRECATED", warning)
        self.assertIn("🚨", warning)
        self.assertIn("2024-10", warning)
    
    def test_get_gcp_cloudsql_warning_deprecated_postgres(self):
        """Test warning message for deprecated PostgreSQL version."""
        warning = get_gcp_cloudsql_warning("postgres", "11")
        self.assertIn("DEPRECATED", warning)
        self.assertIn("🚨", warning)
        self.assertIn("2023-10", warning)
    
    def test_get_gcp_cloudsql_warning_extended_postgres(self):
        """Test warning message for extended support PostgreSQL version."""
        warning = get_gcp_cloudsql_warning("postgres", "13")
        self.assertIn("Extended Support", warning)
        self.assertIn("⚠️", warning)
        self.assertIn("2025-11", warning)
    
    def test_get_gcp_cloudsql_warning_current(self):
        """Test info message for current version."""
        warning = get_gcp_cloudsql_warning("mysql", "8.0")
        self.assertIn("currently supported", warning)
        self.assertIn("✓", warning)
    
    def test_get_gcp_cloudsql_warning_unknown_version(self):
        """Test warning for unknown version."""
        warning = get_gcp_cloudsql_warning("mysql", "9.0")
        self.assertIn("unknown", warning)
        self.assertIn("⚠️", warning)
    
    def test_scan_gcp_cloudsql_versions_deprecated(self):
        """Test scanning a Terraform file for deprecated GCP Cloud SQL versions."""
        with tempfile.TemporaryDirectory() as tmp_path:
            tmp_path = Path(tmp_path)
            tf_file = tmp_path / "cloudsql.tf"
            tf_file.write_text('''
        resource "google_sql_database_instance" "example" {
          database_version = "MYSQL_5_7"
        }
        ''')
            
            warnings = scan_gcp_cloudsql_versions(tf_file)
            self.assertEqual(len(warnings), 1)
            self.assertEqual(warnings[0]["type"], "gcp_cloudsql_version")
            self.assertEqual(warnings[0]["status"], "deprecated")
    
    def test_scan_gcp_cloudsql_versions_current(self):
        """Test that current versions don't trigger warnings."""
        with tempfile.TemporaryDirectory() as tmp_path:
            tmp_path = Path(tmp_path)
            tf_file = tmp_path / "cloudsql.tf"
            tf_file.write_text('''
        resource "google_sql_database_instance" "example" {
          database_version = "POSTGRES_16"
        }
        ''')
            
            warnings = scan_gcp_cloudsql_versions(tf_file)
            self.assertEqual(len(warnings), 0)
    
    def test_scan_gcp_cloudsql_versions_extended(self):
        """Test detecting extended support versions."""
        with tempfile.TemporaryDirectory() as tmp_path:
            tmp_path = Path(tmp_path)
            tf_file = tmp_path / "cloudsql.tf"
            tf_file.write_text('''
        resource "google_sql_database_instance" "example" {
          database_version = "POSTGRES_13"
        }
        ''')
            
            warnings = scan_gcp_cloudsql_versions(tf_file)
            self.assertEqual(len(warnings), 1)
            self.assertEqual(warnings[0]["status"], "extended")
    
    def test_scan_gcp_cloudsql_versions_non_tf_file(self):
        """Test that non-Terraform files are ignored."""
        with tempfile.TemporaryDirectory() as tmp_path:
            tmp_path = Path(tmp_path)
            py_file = tmp_path / "script.py"
            py_file.write_text('database_version = "MYSQL_5_7"')
            
            warnings = scan_gcp_cloudsql_versions(py_file)
            self.assertEqual(len(warnings), 0)


if __name__ == "__main__":
    unittest.main()
