"""Enrich log records with IOC extraction."""

import re

from ioc_finder import find_iocs


# Base64 pattern: 50+ chars of base64 alphabet, optionally ending with =
BASE64_PATTERN = re.compile(r'[A-Za-z0-9+/]{50,}={0,2}')

# Suspicious PowerShell patterns (no LLM needed)
SUSPICIOUS_PATTERNS = {
    'encoded_powershell': re.compile(r'-e(nc|ncodedcommand)?\s+[A-Za-z0-9+/=]{20,}', re.I),
    'download_cradle': re.compile(r'(Invoke-WebRequest|IWR|wget|curl|DownloadString|DownloadFile)', re.I),
    'execution': re.compile(r'(IEX|Invoke-Expression|\.Invoke\()', re.I),
    'amsi_bypass': re.compile(r'(amsi|AmsiUtils|amsiInitFailed)', re.I),
    'hidden_window': re.compile(r'-w(indowstyle)?\s*(hidden|1)', re.I),
}


def detect_base64(text: str) -> list[str]:
    """Detect base64-encoded strings in text."""
    return BASE64_PATTERN.findall(text)


def detect_suspicious_patterns(text: str) -> list[str]:
    """Detect suspicious patterns without LLM calls."""
    found = []
    for name, pattern in SUSPICIOUS_PATTERNS.items():
        if pattern.search(text):
            found.append(name)
    return found


def extract_iocs(text: str) -> dict:
    """Extract IOCs from text using ioc-finder + custom patterns.

    Returns a dict with keys like:
    - ipv4s, ipv6s
    - domains, urls
    - md5s, sha1s, sha256s, sha512s
    - email_addresses
    - registry_key_paths
    - file_paths
    - base64_strings (custom)
    - suspicious_patterns (custom)
    """
    # find_iocs returns a dict with all IOC types
    iocs = find_iocs(text, parse_domain_from_url=True)

    # Add custom detections (no LLM needed)
    base64_strings = detect_base64(text)
    if base64_strings:
        iocs['base64_strings'] = base64_strings

    suspicious = detect_suspicious_patterns(text)
    if suspicious:
        iocs['suspicious_patterns'] = suspicious

    # Filter out empty lists to keep storage compact
    return {k: v for k, v in iocs.items() if v}


def enrich_record(raw_text: str) -> dict:
    """Enrich a log record's text with IOC extraction.

    Returns enrichment metadata as a dict.
    """
    return {
        "iocs": extract_iocs(raw_text)
    }
