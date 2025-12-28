"""
Intelligent entropy-based secret detection with exclusions
Filters out legitimate identifiers (ARNs, UUIDs, etc.) that look random but aren't secrets
"""

import re
from typing import List, Tuple

class EntropyFilter:
    """Filter high-entropy strings to avoid false positives"""
    
    # Known non-secret patterns that look like entropy
    NON_SECRET_PATTERNS = {
        # AWS ARNs: arn:aws:service:region:account-id:resource
        'aws_arn': r'^arn:aws:[a-z0-9\-]+:[a-z0-9\-]*:[0-9]*:[a-z0-9\-/:]*$',
        
        # Google resource names: projects/ID/resources/ID
        'google_resource': r'^projects/[a-z0-9\-]+/.*',
        
        # UUIDs: 550e8400-e29b-41d4-a716-446655440000
        'uuid': r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
        
        # Hashes (SHA, MD5, etc): 64 hex chars or 32 hex chars
        'hash': r'^[a-f0-9]{32}$|^[a-f0-9]{64}$',
        
        # Kubernetes IDs: numbers and hyphens
        'k8s_resource': r'^[a-z0-9\-]{20,}$',
        
        # Docker image SHA: sha256:hexstring
        'docker_sha': r'^sha256:[a-f0-9]{64}$',
        
        # Git commit hash
        'git_hash': r'^[a-f0-9]{40}$|^[a-f0-9]{7}$',
        
        # AWS account ID (12 digits)
        'aws_account': r'^\d{12}$',
        
        # Role/Policy names (common pattern)
        'role_name': r'^[a-zA-Z][a-zA-Z0-9\-_]*-?[a-zA-Z0-9]*$',
    }
    
    # Context that indicates NOT a secret
    NON_SECRET_CONTEXTS = [
        'arn:',
        'policy_arn',
        'role_arn',
        'resource_id',
        'resource_name',
        'account_id',
        'account-id',
        'image_id',
        'instance_id',
        'hash',
        'checksum',
        'sha256',
        'sha512',
        'md5',
        'uuid',
        'request_id',
        'trace_id',
        'correlation_id',
        'session_id',  # session IDs are not secrets
        'user_id',
        'org_id',
        'project_id',
        'bucket_id',
    ]
    
    @staticmethod
    def is_likely_arn(value: str) -> bool:
        """Check if value is an AWS ARN"""
        return bool(re.match(
            r'^arn:aws:[a-z0-9\-]+:[a-z0-9\-]*:[0-9]*:[a-z0-9\-/:]*$',
            value.lower()
        ))
    
    @staticmethod
    def is_likely_uuid(value: str) -> bool:
        """Check if value is a UUID"""
        return bool(re.match(
            r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
            value.lower()
        ))
    
    @staticmethod
    def is_likely_hash(value: str) -> bool:
        """Check if value is a hash (MD5, SHA1, SHA256, etc)"""
        # MD5: 32 hex, SHA1: 40 hex, SHA256: 64 hex
        return bool(re.match(r'^[a-f0-9]{32}$|^[a-f0-9]{40}$|^[a-f0-9]{64}$', value.lower()))
    
    @staticmethod
    def is_likely_git_hash(value: str) -> bool:
        """Check if value is a git commit hash"""
        return bool(re.match(r'^[a-f0-9]{7}$|^[a-f0-9]{40}$', value.lower()))
    
    @staticmethod
    def is_likely_docker_sha(value: str) -> bool:
        """Check if value is a Docker image SHA"""
        return bool(re.match(r'^sha256:[a-f0-9]{64}$', value.lower()))
    
    @staticmethod
    def is_likely_google_resource(value: str) -> bool:
        """Check if value is a Google resource name (projects/xxx/resources/yyy)"""
        return bool(re.match(r'^projects/[a-z0-9\-]+/.*', value.lower()))
    
    @staticmethod
    def has_non_secret_context(line: str) -> bool:
        """Check if line context indicates this is NOT a secret"""
        line_lower = line.lower()
        
        for context in EntropyFilter.NON_SECRET_CONTEXTS:
            if context in line_lower:
                return True
        
        return False
    
    @staticmethod
    def should_flag_as_secret(value: str, line: str = None) -> bool:
        """
        Determine if a high-entropy string should be flagged as a secret
        
        Args:
            value: The string value to check
            line: The full line of code (for context)
        
        Returns:
            True if should be flagged, False if should be excluded
        """
        
        if not value or len(value) < 12:
            return False
        
        # Check for known non-secret patterns
        if EntropyFilter.is_likely_arn(value):
            return False
        
        if EntropyFilter.is_likely_uuid(value):
            return False
        
        if EntropyFilter.is_likely_hash(value):
            return False
        
        if EntropyFilter.is_likely_git_hash(value):
            return False
        
        if EntropyFilter.is_likely_docker_sha(value):
            return False
        
        if EntropyFilter.is_likely_google_resource(value):
            return False
        
        # Check context
        if line and EntropyFilter.has_non_secret_context(line):
            return False
        
        # If it has a colon (like arn:, protocol://, etc), likely not a secret
        if ':' in value:
            return False
        
        # If it's mostly numbers (like AWS account ID), likely not a secret
        if len([c for c in value if c.isdigit()]) / len(value) > 0.8:
            return False
        
        # Check if it looks like a common naming pattern (role names, resource names)
        # These have capital letters and hyphens/underscores, not random
        if re.match(r'^[a-zA-Z][a-zA-Z0-9\-_]*$', value) and len(value) < 40:
            return False
        
        # If we got here, it might be a real secret
        return True


def filter_entropy_findings(findings: List[dict]) -> List[dict]:
    """
    Filter out high-entropy findings that are actually legitimate identifiers
    
    Args:
        findings: List of finding dicts from pattern matching
    
    Returns:
        Filtered list of findings
    """
    filtered = []
    
    for finding in findings:
        # Only filter "High Entropy String" pattern
        if finding.get('pattern') != 'High Entropy String':
            filtered.append(finding)
            continue
        
        # Extract the matched value
        match_value = finding.get('match', '')
        full_line = finding.get('snippet', '')
        
        # Check if it should be excluded
        if not EntropyFilter.should_flag_as_secret(match_value, full_line):
            # Skip this finding (it's a false positive)
            continue
        
        # Keep the finding
        filtered.append(finding)
    
    return filtered
