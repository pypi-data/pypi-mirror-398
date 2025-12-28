"""
Azure database version detector for Terraform files.
Warns on deprecated and extended support database versions.
Supports Azure SQL Database, MySQL, and PostgreSQL.
"""

import re
from pathlib import Path
from typing import List, Dict, Any

# Azure database version support timeline
# https://learn.microsoft.com/en-us/azure/mysql/
# https://learn.microsoft.com/en-us/azure/postgresql/
# https://learn.microsoft.com/en-us/sql/sql-server/

AZURE_DB_ENGINES = {
    # Azure SQL Database
    "sql": {
        "status": "current",
        "versions": {
            "2019": {"status": "extended", "eol": "2025-01"},
            "2017": {"status": "deprecated", "eol": "2024-10"},
            "2016": {"status": "deprecated", "eol": "2024-07"},
            "2014": {"status": "deprecated", "eol": "2024-07"},
        }
    },
    # Azure MySQL versions
    "mysql": {
        "status": "current",
        "versions": {
            "8.0": {"status": "current", "eol": "2026-04"},
            "5.7": {"status": "deprecated", "eol": "2024-10"},
            "5.6": {"status": "deprecated", "eol": "2021-02"},
        }
    },
    # Azure PostgreSQL versions
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
}

def parse_terraform_azure_db_versions(content: str) -> List[Dict[str, Any]]:
    """
    Parse Terraform file content for Azure database versions.
    Looks for:
    - azurerm_mssql_server with version tag
    - azurerm_mysql_server with version
    - azurerm_postgresql_server with version
    """
    findings = []
    lines = content.splitlines()
    
    # Pattern for SQL Server
    sql_pattern = r'sku_name\s*=\s*["\']([A-Z0-9]+)["\']'
    # Pattern for MySQL server version
    mysql_pattern = r'version\s*=\s*["\']([0-9.]+)["\']'
    # Pattern for PostgreSQL server version
    postgres_pattern = r'version\s*=\s*["\']([0-9.]+)["\']'
    
    current_resource = None
    
    for line_no, line in enumerate(lines, 1):
        # Detect resource type
        if 'azurerm_mssql_server' in line:
            current_resource = 'sql'
        elif 'azurerm_mysql_server' in line or 'azurerm_mysql_flexible_server' in line:
            current_resource = 'mysql'
        elif 'azurerm_postgresql_server' in line or 'azurerm_postgresql_flexible_server' in line:
            current_resource = 'postgres'
        
        # Match SQL versions
        if current_resource == 'sql':
            sql_matches = re.finditer(sql_pattern, line)
            for match in sql_matches:
                sku = match.group(1)
                # Extract SQL Server version from SKU (e.g., GP_Gen5_2 -> infer from context)
                # For simplicity, we'll note the SKU
                findings.append({
                    "line": line_no,
                    "engine": "sql",
                    "version": sku,
                    "snippet": line.strip(),
                    "match": match.group(0),
                    "type": "sku"
                })
        
        # Match MySQL versions
        elif current_resource == 'mysql':
            mysql_matches = re.finditer(mysql_pattern, line)
            for match in mysql_matches:
                version = match.group(1)
                findings.append({
                    "line": line_no,
                    "engine": "mysql",
                    "version": version,
                    "snippet": line.strip(),
                    "match": match.group(0),
                    "type": "version"
                })
        
        # Match PostgreSQL versions
        elif current_resource == 'postgres':
            postgres_matches = re.finditer(postgres_pattern, line)
            for match in postgres_matches:
                version = match.group(1)
                findings.append({
                    "line": line_no,
                    "engine": "postgres",
                    "version": version,
                    "snippet": line.strip(),
                    "match": match.group(0),
                    "type": "version"
                })
    
    return findings

def get_azure_db_warning(engine: str, version: str) -> str:
    """Get warning message for a given Azure database version."""
    if engine not in AZURE_DB_ENGINES:
        return f"⚠️  Azure database engine '{engine}' is not recognized. Check Azure documentation."
    
    engine_info = AZURE_DB_ENGINES[engine]
    versions = engine_info.get("versions", {})
    
    if version not in versions:
        return f"⚠️  {engine.upper()} version {version} is unknown. Check Azure documentation."
    
    info = versions[version]
    status = info["status"]
    eol = info["eol"]
    
    if status == "deprecated":
        return f"🚨 Azure {engine.upper()} {version} is DEPRECATED (EOL: {eol}). Upgrade immediately."
    elif status == "extended":
        return f"⚠️  Azure {engine.upper()} {version} on Extended Support (EOL: {eol}). Higher costs. Consider upgrading."
    else:  # current
        return f"✓ Azure {engine.upper()} {version} is currently supported (EOL: {eol})."

def scan_azure_db_versions(file_path: Path) -> List[Dict[str, Any]]:
    """
    Scan a Terraform file for Azure database version warnings.
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
    
    findings = parse_terraform_azure_db_versions(content)
    
    for finding in findings:
        engine = finding["engine"]
        version = finding["version"]
        
        if engine in AZURE_DB_ENGINES:
            versions = AZURE_DB_ENGINES[engine].get("versions", {})
            if version in versions:
                info = versions[version]
                # Only warn on non-current versions
                if info["status"] != "current":
                    warning_msg = get_azure_db_warning(engine, version)
                    warnings.append({
                        "file": str(file_path),
                        "line": finding["line"],
                        "type": "azure_db_version",
                        "engine": engine,
                        "version": version,
                        "status": info["status"],
                        "message": warning_msg,
                        "snippet": finding["snippet"]
                    })
    
    return warnings
