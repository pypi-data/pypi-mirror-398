"""
RDS engine version detector for Terraform files.
Warns on end-of-life and extended support engines.
"""

import re
from pathlib import Path
from typing import List, Dict, Any

# RDS engine version support timeline
# https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_MariaDB.html
RDS_ENGINES = {
    # PostgreSQL versions
    "postgres": {
        "16": {"status": "current", "eol": "2028-11"},
        "15": {"status": "current", "eol": "2027-10"},
        "14": {"status": "extended", "eol": "2026-10"},  # Extended support
        "13": {"status": "extended", "eol": "2025-11"},  # Extended support
        "12": {"status": "deprecated", "eol": "2024-11"},
        "11": {"status": "deprecated", "eol": "2023-10"},
    },
    # MySQL versions
    "mysql": {
        "8.0": {"status": "current", "eol": "2026-04"},
        "5.7": {"status": "deprecated", "eol": "2023-10"},
        "5.6": {"status": "deprecated", "eol": "2021-02"},
    },
    # MariaDB versions
    "mariadb": {
        "10.6": {"status": "current", "eol": "2026-07"},
        "10.5": {"status": "extended", "eol": "2025-06"},  # Extended support
        "10.4": {"status": "extended", "eol": "2024-06"},  # Extended support
        "10.3": {"status": "deprecated", "eol": "2023-05"},
    },
}

def parse_terraform_rds_versions(content: str) -> List[Dict[str, Any]]:
    """
    Parse Terraform file content for RDS engine versions.
    Detects versions in:
    - Resource blocks: engine = "postgres", engine_version = "15"
    - Variable defaults: variable "db_engine_version" { default = "14" }
    Returns list of version findings with line numbers and engine type.
    """
    findings = []
    lines = content.splitlines()
    
    # Pattern to match engine and engine_version in resources
    engine_pattern = r'engine\s*=\s*["\']([a-z]+)["\']'
    version_pattern = r'engine_version\s*=\s*["\']([0-9.]+)["\']'
    
    # Pattern for variable defaults
    var_version_pattern = r'default\s*=\s*["\']([0-9.]+)["\']'
    
    current_engine = None
    in_db_version_var = False
    
    for line_no, line in enumerate(lines, 1):
        # Track if we're in a db version variable block
        if 'variable' in line and ('db_engine_version' in line or 'engine_version' in line or 'db_version' in line):
            in_db_version_var = True
        elif in_db_version_var and '}' in line:
            in_db_version_var = False
        
        # Check for engine in resources
        engine_match = re.search(engine_pattern, line)
        if engine_match:
            current_engine = engine_match.group(1)
        
        # Check for version in resources
        version_match = re.search(version_pattern, line)
        if version_match and current_engine:
            version = version_match.group(1)
            findings.append({
                "line": line_no,
                "engine": current_engine,
                "version": version,
                "snippet": line.strip(),
                "match": version_match.group(0)
            })
        
        # Check for version in variable defaults
        if in_db_version_var:
            version_match = re.search(var_version_pattern, line)
            if version_match:
                # Use postgres as default engine if not found
                engine = current_engine or 'postgres'
                version = version_match.group(1)
                findings.append({
                    "line": line_no,
                    "engine": engine,
                    "version": version,
                    "snippet": line.strip(),
                    "match": version_match.group(0)
                })
    
    return findings

def get_rds_warning(engine: str, version: str) -> str:
    """Get warning message for a given RDS engine version."""
    if engine not in RDS_ENGINES:
        return f"⚠️  RDS engine '{engine}' is not recognized. Check AWS documentation."
    
    if version not in RDS_ENGINES[engine]:
        return f"⚠️  {engine.upper()} version {version} is unknown. Check AWS documentation."
    
    info = RDS_ENGINES[engine][version]
    status = info["status"]
    eol = info["eol"]
    
    if status == "deprecated":
        return f"🚨 {engine.upper()} {version} is DEPRECATED (EOL: {eol}). Upgrade immediately."
    elif status == "extended":
        return f"⚠️  {engine.upper()} {version} on Extended Support (EOL: {eol}). Higher costs. Consider upgrading."
    else:  # current
        return f"✓ {engine.upper()} {version} is currently supported (EOL: {eol})."

def scan_rds_versions(file_path: Path) -> List[Dict[str, Any]]:
    """
    Scan a Terraform file for RDS version warnings.
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
    
    findings = parse_terraform_rds_versions(content)
    
    for finding in findings:
        engine = finding["engine"]
        version = finding["version"]
        
        if engine in RDS_ENGINES and version in RDS_ENGINES[engine]:
            info = RDS_ENGINES[engine][version]
            # Only warn on non-current versions
            if info["status"] != "current":
                warning_msg = get_rds_warning(engine, version)
                warnings.append({
                    "file": str(file_path),
                    "line": finding["line"],
                    "type": "rds_version",
                    "engine": engine,
                    "version": version,
                    "status": info["status"],
                    "message": warning_msg,
                    "snippet": finding["snippet"]
                })
    
    return warnings
