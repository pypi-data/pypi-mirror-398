"""
AKS Kubernetes version detector for Terraform files.
Warns on deprecated and extended support versions.
"""

import re
from pathlib import Path
from typing import List, Dict, Any

# AKS version support timeline (as of 2024)
# https://learn.microsoft.com/en-us/azure/aks/supported-kubernetes-versions
AKS_VERSIONS = {
    "1.30": {"status": "current", "eol": "2025-11"},
    "1.29": {"status": "current", "eol": "2025-08"},
    "1.28": {"status": "current", "eol": "2025-04"},
    "1.27": {"status": "extended", "eol": "2025-07"},  # Extended support
    "1.26": {"status": "extended", "eol": "2025-02"},  # Extended support
    "1.25": {"status": "deprecated", "eol": "2024-11"},
    "1.24": {"status": "deprecated", "eol": "2024-08"},
    "1.23": {"status": "deprecated", "eol": "2024-02"},
    "1.22": {"status": "deprecated", "eol": "2023-11"},
}

def parse_terraform_aks_versions(content: str) -> List[Dict[str, Any]]:
    """
    Parse Terraform file content for AKS cluster versions.
    Detects versions in:
    - Resource blocks: kubernetes_version = "1.27"
    - Variable defaults: variable "cluster_version" { default = "1.27" }
    Returns list of version findings with line numbers.
    """
    findings = []
    lines = content.splitlines()
    
    # Pattern 1: Direct resource usage: kubernetes_version = "1.27"
    pattern1 = r'kubernetes_version\s*=\s*["\']([0-9]+\.[0-9]+)["\']'
    
    # Pattern 2: Variable default values: default = "1.27" (for cluster_version or similar)
    pattern2 = r'default\s*=\s*["\']([0-9]+\.[0-9]+)["\']'
    
    in_cluster_version_var = False
    
    for line_no, line in enumerate(lines, 1):
        # Track if we're in a cluster_version variable block
        if 'variable' in line and 'cluster_version' in line:
            in_cluster_version_var = True
        elif in_cluster_version_var and '}' in line:
            in_cluster_version_var = False
        
        # Check pattern 1: Direct kubernetes_version
        matches = re.finditer(pattern1, line)
        for match in matches:
            version = match.group(1)
            findings.append({
                "line": line_no,
                "version": version,
                "snippet": line.strip(),
                "match": match.group(0)
            })
        
        # Check pattern 2: Variable default (when in cluster_version variable block)
        if in_cluster_version_var:
            matches = re.finditer(pattern2, line)
            for match in matches:
                version = match.group(1)
                findings.append({
                    "line": line_no,
                    "version": version,
                    "snippet": line.strip(),
                    "match": match.group(0)
                })
    
    return findings

def get_version_warning(version: str) -> str:
    """Get warning message for a given AKS version."""
    if version not in AKS_VERSIONS:
        return f"⚠️  AKS version {version} is unknown. Check Azure documentation."
    
    info = AKS_VERSIONS[version]
    status = info["status"]
    eol = info["eol"]
    
    if status == "deprecated":
        return f"🚨 AKS {version} is DEPRECATED (EOL: {eol}). Upgrade immediately."
    elif status == "extended":
        return f"⚠️  AKS {version} on Extended Support (EOL: {eol}). Higher costs. Consider upgrading."
    else:  # current
        return f"✓ AKS {version} is currently supported (EOL: {eol})."

def scan_aks_versions(file_path: Path) -> List[Dict[str, Any]]:
    """
    Scan a Terraform file for AKS version warnings.
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
    
    findings = parse_terraform_aks_versions(content)
    
    for finding in findings:
        version = finding["version"]
        warning_msg = get_version_warning(version)
        
        # Only warn on non-current versions
        if version in AKS_VERSIONS and AKS_VERSIONS[version]["status"] != "current":
            warnings.append({
                "file": str(file_path),
                "line": finding["line"],
                "type": "aks_version",
                "version": version,
                "status": AKS_VERSIONS[version]["status"],
                "message": warning_msg,
                "snippet": finding["snippet"]
            })
    
    return warnings
