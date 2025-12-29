"""CVE Parser - Fetch and parse CVE information"""

import requests
import json
from dataclasses import dataclass
from typing import Optional
from pathlib import Path
import time

from core.config import NVD_API_URL, NVD_RATE_LIMIT, NVD_TIMEOUT, PROJECT_ROOT


@dataclass
class CVEData:
    """Structured CVE information"""
    cve_id: str
    description: str
    cvss_score: Optional[float]
    cvss_severity: Optional[str]
    affected_software: list[str]
    references: list[str]
    published_date: Optional[str]


class CVEParser:
    """Parse CVE data from NVD API or local cache"""
    
    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = cache_dir or PROJECT_ROOT / "data/raw/cves"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.last_request_time = 0
    
    def _rate_limit(self):
        """Respect NVD API rate limit"""
        elapsed = time.time() - self.last_request_time
        if elapsed < (30 / NVD_RATE_LIMIT):
            time.sleep((30 / NVD_RATE_LIMIT) - elapsed)
        self.last_request_time = time.time()
    
    def fetch_cve(self, cve_id: str, use_cache: bool = True) -> Optional[CVEData]:
        """
        Fetch CVE from NVD API or cache
        
        Args:
            cve_id: CVE identifier (e.g., CVE-2024-1234)
            use_cache: Try local cache first
            
        Returns:
            CVEData object or None if not found
        """
        # Validate CVE ID format
        if not cve_id.startswith("CVE-"):
            raise ValueError(f"Invalid CVE ID format: {cve_id}")
        
        # Try cache first
        if use_cache:
            cached = self._load_from_cache(cve_id)
            if cached:
                return cached
        
        # Fetch from NVD
        try:
            self._rate_limit()
            params = {"cveId": cve_id}
            response = requests.get(NVD_API_URL, params=params, timeout=NVD_TIMEOUT)
            response.raise_for_status()
            
            data = response.json()
            if data.get("totalResults", 0) == 0:
                return None
            
            cve_item = data["vulnerabilities"][0]["cve"]
            parsed = self._parse_cve_data(cve_item)
            
            # Cache for future use
            self._save_to_cache(cve_id, cve_item)
            
            return parsed
            
        except requests.RequestException as e:
            print(f"Error fetching CVE: {e}")
            return None
    
    def _parse_cve_data(self, cve_item: dict) -> CVEData:
        """Parse raw NVD JSON into CVEData"""
        
        # Description
        descriptions = cve_item.get("descriptions", [])
        description = next(
            (d["value"] for d in descriptions if d["lang"] == "en"),
            "No description available"
        )
        
        # CVSS Score
        metrics = cve_item.get("metrics", {})
        cvss_score = None
        cvss_severity = None
        
        # Try CVSS v3 first, then v2
        for version in ["cvssMetricV31", "cvssMetricV30", "cvssMetricV2"]:
            if version in metrics and metrics[version]:
                metric = metrics[version][0]
                cvss_data = metric.get("cvssData", {})
                cvss_score = cvss_data.get("baseScore")
                cvss_severity = cvss_data.get("baseSeverity") or metric.get("severity")
                break
        
        # Affected software (from CPE)
        affected = []
        configurations = cve_item.get("configurations", [])
        for config in configurations:
            for node in config.get("nodes", []):
                for cpe_match in node.get("cpeMatch", []):
                    cpe = cpe_match.get("criteria", "")
                    if cpe.startswith("cpe:2.3:"):
                        parts = cpe.split(":")
                        if len(parts) >= 5:
                            vendor = parts[3]
                            product = parts[4]
                            affected.append(f"{vendor}:{product}")
        
        # Remove duplicates
        affected = list(set(affected))[:5]  # Limit to 5
        
        # References
        references = [
            ref["url"] for ref in cve_item.get("references", [])[:3]
        ]
        
        # Published date
        published = cve_item.get("published")
        
        return CVEData(
            cve_id=cve_item["id"],
            description=description,
            cvss_score=cvss_score,
            cvss_severity=cvss_severity,
            affected_software=affected,
            references=references,
            published_date=published
        )
    
    def _load_from_cache(self, cve_id: str) -> Optional[CVEData]:
        """Load CVE from local cache"""
        cache_file = self.cache_dir / f"{cve_id}.json"
        if cache_file.exists():
            try:
                with open(cache_file) as f:
                    data = json.load(f)
                return self._parse_cve_data(data)
            except Exception:
                return None
        return None
    
    def _save_to_cache(self, cve_id: str, cve_data: dict):
        """Save CVE to local cache"""
        cache_file = self.cache_dir / f"{cve_id}.json"
        try:
            with open(cache_file, 'w') as f:
                json.dump(cve_data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not cache CVE: {e}")
    
    def format_for_model(self, cve_data: CVEData) -> str:
        """Format CVE data into model-friendly prompt"""
        
        prompt = f"""CVE ID: {cve_data.cve_id}
Description: {cve_data.description}"""
        
        if cve_data.cvss_score:
            prompt += f"\nCVSS Score: {cve_data.cvss_score} ({cve_data.cvss_severity})"
        
        if cve_data.affected_software:
            prompt += f"\nAffected Software: {', '.join(cve_data.affected_software)}"
        
        return prompt
