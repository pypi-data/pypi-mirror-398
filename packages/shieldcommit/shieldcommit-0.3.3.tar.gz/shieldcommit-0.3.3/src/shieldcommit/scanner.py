import re
from pathlib import Path
from .patterns import PATTERNS
from .entropy_filter import filter_entropy_findings
from .eks_detector import scan_eks_versions
from .rds_detector import scan_rds_versions
from .aks_detector import scan_aks_versions
from .gcp_detector import scan_gcp_versions
from .azure_db_detector import scan_azure_db_versions
from .gcp_db_detector import scan_gcp_cloudsql_versions

def scan_text(text):
    """
    Return list of (pattern_name, match_obj) for given text.
    """
    findings = []
    for name, pattern in PATTERNS.items():
        try:
            for m in re.finditer(pattern, text):
                findings.append((name, m))
        except re.error:
            # skip bad regex to avoid crash
            continue
    return findings

def scan_file(path: Path):
    """
    Scan a file and return findings with line numbers and snippets.
    """
    findings = []
    try:
        text = path.read_text(errors="ignore")
    except Exception:
        return findings

    for name, m in scan_text(text):
        start = m.start()
        line_no = text.count("\n", 0, start) + 1
        lines = text.splitlines()
        snippet = lines[line_no - 1][:200] if line_no - 1 < len(lines) else ""
        findings.append({
            "file": str(path),
            "pattern": name,
            "line": line_no,
            "snippet": snippet,
            "match": m.group(0)[:200]
        })

    return findings

def scan_files(paths):
    """
    Scan files for secrets and warnings (EKS/RDS/AKS/GCP versions + Azure/GCP databases).
    Returns dict with 'findings' (secrets) and 'warnings' (version issues).
    """
    findings = []
    warnings = []
    
    for p in paths:
        p = Path(p)
        if p.is_file():
            findings.extend(scan_file(p))
            # Scan for Kubernetes versions
            warnings.extend(scan_eks_versions(p))
            warnings.extend(scan_aks_versions(p))
            warnings.extend(scan_gcp_versions(p))
            # Scan for database versions
            warnings.extend(scan_rds_versions(p))
            warnings.extend(scan_azure_db_versions(p))
            warnings.extend(scan_gcp_cloudsql_versions(p))
    
    # Filter out false positives (ARNs, UUIDs, hashes, etc)
    findings = filter_entropy_findings(findings)
    
    return {
        "findings": findings,
        "warnings": warnings
    }
