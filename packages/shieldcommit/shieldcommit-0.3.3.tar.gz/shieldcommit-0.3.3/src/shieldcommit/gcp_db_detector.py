"""
GCP Cloud SQL database version detector for Terraform files.
Warns on deprecated and extended support database versions.
Supports MySQL, PostgreSQL, and SQL Server.
"""

import re
from pathlib import Path
from typing import List, Dict, Any

# GCP Cloud SQL version support timeline
# https://cloud.google.com/sql/docs/mysql/release-notes
# https://cloud.google.com/sql/docs/postgres/release-notes
# https://cloud.google.com/sql/docs/sqlserver/release-notes

GCP_CLOUDSQL_ENGINES = {
    # MySQL versions
    "mysql": {
        "status": "current",
        "versions": {
            "8.0": {"status": "current", "eol": "2026-04"},
            "5.7": {"status": "deprecated", "eol": "2024-10"},
            "5.6": {"status": "deprecated", "eol": "2021-02"},
        }
    },
    # PostgreSQL versions
    "postgres": {
        "status": "current",
        "versions": {
            "16": {"status": "current", "eol": "2028-11"},
            "15": {"status": "current", "eol": "2027-10"},
            "14": {"status": "extended", "eol": "2026-10"},
            "13": {"status": "extended", "eol": "2025-11"},
            "12": {"status": "deprecated", "eol": "2024-11"},
            "11": {"status": "deprecated", "eol": "2023-10"},
        }
    },
    # SQL Server versions
    "sqlserver": {
        "status": "current",
        "versions": {
            "2019": {"status": "extended", "eol": "2025-01"},
            "2017": {"status": "deprecated", "eol": "2024-10"},
            "2016": {"status": "deprecated", "eol": "2024-07"},
        }
    },
}

def parse_terraform_gcp_cloudsql_versions(content: str) -> List[Dict[str, Any]]:
    """
    Parse Terraform file content for GCP Cloud SQL database versions.
    Looks for:
    - database_version in google_sql_database_instance
    """
    findings = []
    lines = content.splitlines()
    
    # Pattern to match: database_version = "MYSQL_8_0" or "POSTGRES_14" or "SQLSERVER_2019"
    db_version_pattern = r'database_version\s*=\s*["\']([A-Z_0-9]+)["\']'
    
    current_resource = None
    
    for line_no, line in enumerate(lines, 1):
        # Detect resource type
        if 'google_sql_database_instance' in line:
            current_resource = 'sql_instance'
        
        # Match database versions
        if current_resource:
            db_matches = re.finditer(db_version_pattern, line)
            for match in db_matches:
                version_str = match.group(1)
                # Parse version string like MYSQL_8_0, POSTGRES_14, SQLSERVER_2019
                engine, version = parse_gcp_version_string(version_str)
                
                findings.append({
                    "line": line_no,
                    "engine": engine,
                    "version": version,
                    "version_str": version_str,
                    "snippet": line.strip(),
                    "match": match.group(0),
                    "type": "version"
                })
    
    return findings

def parse_gcp_version_string(version_str: str) -> tuple:
    """
    Parse GCP database version strings.
    Examples: MYSQL_8_0 -> ('mysql', '8.0')
              POSTGRES_14 -> ('postgres', '14')
              SQLSERVER_2019 -> ('sqlserver', '2019')
    """
    if version_str.startswith('MYSQL'):
        # MYSQL_5_7 or MYSQL_8_0
        version = version_str.replace('MYSQL_', '').replace('_', '.')
        return ('mysql', version)
    elif version_str.startswith('POSTGRES'):
        # POSTGRES_11 or POSTGRES_15
        version = version_str.replace('POSTGRES_', '')
        return ('postgres', version)
    elif version_str.startswith('SQLSERVER'):
        # SQLSERVER_2016 or SQLSERVER_2019
        version = version_str.replace('SQLSERVER_', '')
        return ('sqlserver', version)
    else:
        # Unknown format
        return ('unknown', version_str)

def get_gcp_cloudsql_warning(engine: str, version: str) -> str:
    """Get warning message for a given GCP Cloud SQL database version."""
    if engine not in GCP_CLOUDSQL_ENGINES:
        return f"⚠️  GCP Cloud SQL engine '{engine}' is not recognized. Check GCP documentation."
    
    engine_info = GCP_CLOUDSQL_ENGINES[engine]
    versions = engine_info.get("versions", {})
    
    if version not in versions:
        return f"⚠️  {engine.upper()} version {version} is unknown. Check GCP Cloud SQL documentation."
    
    info = versions[version]
    status = info["status"]
    eol = info["eol"]
    
    if status == "deprecated":
        return f"🚨 GCP Cloud SQL {engine.upper()} {version} is DEPRECATED (EOL: {eol}). Upgrade immediately."
    elif status == "extended":
        return f"⚠️  GCP Cloud SQL {engine.upper()} {version} on Extended Support (EOL: {eol}). Higher costs. Consider upgrading."
    else:  # current
        return f"✓ GCP Cloud SQL {engine.upper()} {version} is currently supported (EOL: {eol})."

def scan_gcp_cloudsql_versions(file_path: Path) -> List[Dict[str, Any]]:
    """
    Scan a Terraform file for GCP Cloud SQL database version warnings.
    Returns list of warnings.
    """
    warnings = []
    
    # Only scan Terraform files
    if file_path.suffix not in {'.tf', '.json'}:
        return warnings
    
    try:
        content = file_path.read_text(errors="ignore")
    except Exception:
        return warnings
    
    findings = parse_terraform_gcp_cloudsql_versions(content)
    
    for finding in findings:
        engine = finding["engine"]
        version = finding["version"]
        
        if engine in GCP_CLOUDSQL_ENGINES:
            versions = GCP_CLOUDSQL_ENGINES[engine].get("versions", {})
            if version in versions:
                info = versions[version]
                # Only warn on non-current versions
                if info["status"] != "current":
                    warning_msg = get_gcp_cloudsql_warning(engine, version)
                    warnings.append({
                        "file": str(file_path),
                        "line": finding["line"],
                        "type": "gcp_cloudsql_version",
                        "engine": engine,
                        "version": version,
                        "status": info["status"],
                        "message": warning_msg,
                        "snippet": finding["snippet"]
                    })
    
    return warnings
