"""
GCP GKE version detector for Terraform files.
Warns on deprecated and extended support versions.
"""

import re
from pathlib import Path
from typing import List, Dict, Any

# GCP GKE version support timeline (as of 2024)
# https://cloud.google.com/kubernetes-engine/docs/release-notes-regular
GCP_VERSIONS = {
    "1.30": {"status": "current", "eol": "2025-12"},
    "1.29": {"status": "current", "eol": "2025-10"},
    "1.28": {"status": "current", "eol": "2025-05"},
    "1.27": {"status": "extended", "eol": "2025-04"},  # Extended support
    "1.26": {"status": "extended", "eol": "2024-10"},  # Extended support
    "1.25": {"status": "deprecated", "eol": "2024-07"},
    "1.24": {"status": "deprecated", "eol": "2024-02"},
    "1.23": {"status": "deprecated", "eol": "2023-12"},
}

def parse_terraform_gcp_versions(content: str) -> List[Dict[str, Any]]:
    """
    Parse Terraform file content for GCP GKE cluster versions.
    Detects versions in:
    - Resource blocks: min_master_version = "1.27"
    - Variable defaults: variable "cluster_version" { default = "1.27" }
    Returns list of version findings with line numbers.
    """
    findings = []
    lines = content.splitlines()
    
    # Pattern 1: Explicit version in resources: min_master_version = "1.27"
    version_pattern = r'min_master_version\s*=\s*["\']([0-9]+\.[0-9]+)["\']'
    channel_pattern = r'channel\s*=\s*["\']([A-Z]+)["\']'
    
    # Pattern 2: Variable default values
    var_version_pattern = r'default\s*=\s*["\']([0-9]+\.[0-9]+)["\']'
    
    in_cluster_version_var = False
    
    for line_no, line in enumerate(lines, 1):
        # Track if we're in a cluster_version variable block
        if 'variable' in line and 'cluster_version' in line:
            in_cluster_version_var = True
        elif in_cluster_version_var and '}' in line:
            in_cluster_version_var = False
        
        # Check for explicit version in resources
        version_matches = re.finditer(version_pattern, line)
        for match in version_matches:
            version = match.group(1)
            findings.append({
                "line": line_no,
                "version": version,
                "snippet": line.strip(),
                "match": match.group(0),
                "type": "explicit"
            })
        
        # Check for version in variable defaults
        if in_cluster_version_var:
            version_matches = re.finditer(var_version_pattern, line)
            for match in version_matches:
                version = match.group(1)
                findings.append({
                    "line": line_no,
                    "version": version,
                    "snippet": line.strip(),
                    "match": match.group(0),
                    "type": "variable"
                })
        
        # Check for release channel
        channel_matches = re.finditer(channel_pattern, line)
        for match in channel_matches:
            channel = match.group(1)
            findings.append({
                "line": line_no,
                "channel": channel,
                "snippet": line.strip(),
                "match": match.group(0),
                "type": "channel"
            })
    
    return findings

def get_version_warning(version: str) -> str:
    """Get warning message for a given GCP GKE version."""
    if version not in GCP_VERSIONS:
        return f"⚠️  GCP GKE version {version} is unknown. Check Google Cloud documentation."
    
    info = GCP_VERSIONS[version]
    status = info["status"]
    eol = info["eol"]
    
    if status == "deprecated":
        return f"🚨 GCP GKE {version} is DEPRECATED (EOL: {eol}). Upgrade immediately."
    elif status == "extended":
        return f"⚠️  GCP GKE {version} on Extended Support (EOL: {eol}). Higher costs. Consider upgrading."
    else:  # current
        return f"✓ GCP GKE {version} is currently supported (EOL: {eol})."

def get_channel_info(channel: str) -> str:
    """Get info message for GCP release channel."""
    channels = {
        "RAPID": "GCP GKE RAPID channel - receives latest versions quickly.",
        "REGULAR": "GCP GKE REGULAR channel - recommended for production.",
        "STABLE": "GCP GKE STABLE channel - receives latest versions after extended validation."
    }
    return channels.get(channel, f"⚠️  Unknown GCP release channel: {channel}")

def scan_gcp_versions(file_path: Path) -> List[Dict[str, Any]]:
    """
    Scan a Terraform file for GCP GKE version warnings.
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
    
    findings = parse_terraform_gcp_versions(content)
    
    for finding in findings:
        if finding["type"] == "explicit":
            version = finding["version"]
            warning_msg = get_version_warning(version)
            
            # Only warn on non-current versions
            if version in GCP_VERSIONS and GCP_VERSIONS[version]["status"] != "current":
                warnings.append({
                    "file": str(file_path),
                    "line": finding["line"],
                    "type": "gcp_version",
                    "version": version,
                    "status": GCP_VERSIONS[version]["status"],
                    "message": warning_msg,
                    "snippet": finding["snippet"]
                })
        elif finding["type"] == "channel":
            channel = finding["channel"]
            info_msg = get_channel_info(channel)
            warnings.append({
                "file": str(file_path),
                "line": finding["line"],
                "type": "gcp_channel",
                "channel": channel,
                "message": info_msg,
                "snippet": finding["snippet"]
            })
    
    return warnings
