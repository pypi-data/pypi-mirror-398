"""
CVE Scanner Module - Vulnerability Detection
Matches service versions against CVE database
"""

import requests
import json
import re
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import sqlite3
from pathlib import Path


class CVE:
    """Represents a CVE vulnerability"""
    
    def __init__(self, cve_id: str, description: str, cvss_score: float, 
                 severity: str, published_date: str, references: List[str] = None):
        self.cve_id = cve_id
        self.description = description
        self.cvss_score = cvss_score
        self.severity = severity
        self.published_date = published_date
        self.references = references or []
    
    def __repr__(self):
        return f"CVE({self.cve_id}, {self.severity}, {self.cvss_score})"
    
    def to_dict(self):
        return {
            'cve_id': self.cve_id,
            'description': self.description,
            'cvss_score': self.cvss_score,
            'severity': self.severity,
            'published_date': self.published_date,
            'references': self.references
        }


class CVEDatabase:
    """Manages local CVE database cache"""
    
    def __init__(self, db_path: str = "data/cve_database.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cves (
                id TEXT PRIMARY KEY,
                description TEXT,
                cvss_score REAL,
                severity TEXT,
                published_date TEXT,
                modified_date TEXT,
                product TEXT,
                version TEXT,
                vendor TEXT,
                ref_urls TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_product 
            ON cves(product, version)
        ''')
        
        conn.commit()
        conn.close()
    
    def cache_cve(self, cve: CVE, product: str, version: str, vendor: str = ""):
        """Cache CVE in local database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO cves 
            (id, description, cvss_score, severity, published_date, 
             product, version, vendor, ref_urls)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            cve.cve_id,
            cve.description,
            cve.cvss_score,
            cve.severity,
            cve.published_date,
            product.lower(),
            version,
            vendor.lower(),
            json.dumps(cve.references)
        ))
        
        conn.commit()
        conn.close()
    
    def get_cached_cves(self, product: str, version: str) -> List[CVE]:
        """Retrieve cached CVEs for product/version"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, description, cvss_score, severity, published_date, ref_urls
            FROM cves
            WHERE product = ? AND version = ?
        ''', (product.lower(), version))
        
        results = []
        for row in cursor.fetchall():
            cve = CVE(
                cve_id=row[0],
                description=row[1],
                cvss_score=row[2],
                severity=row[3],
                published_date=row[4],
                references=json.loads(row[5]) if row[5] else []
            )
            results.append(cve)
        
        conn.close()
        return results


class CVEScanner:
    """Main CVE Scanner class"""
    
    def __init__(self, use_cache: bool = True):
        self.use_cache = use_cache
        self.db = CVEDatabase()
        self.nvd_api_base = "https://services.nvd.nist.gov/rest/json/cves/2.0"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'SHINIGAMI-EYE-CVE-Scanner/2.0'
        })
    
    def scan_service(self, service_name: str, version: str) -> List[CVE]:
        """
        Scan service for CVEs
        
        Args:
            service_name: Service name (e.g., "Apache", "OpenSSH")
            version: Version string (e.g., "2.4.29", "8.2p1")
        
        Returns:
            List of CVE objects
        """
        # Normalize service name
        product = self._normalize_product_name(service_name)
        clean_version = self._extract_version(version)
        
        if not product or not clean_version:
            return []
        
        # Check cache first
        if self.use_cache:
            cached = self.db.get_cached_cves(product, clean_version)
            if cached:
                return cached
        
        # Query NVD API
        cves = self._query_nvd(product, clean_version)
        
        # Cache results
        if self.use_cache and cves:
            for cve in cves:
                self.db.cache_cve(cve, product, clean_version)
        
        return cves
    
    def _normalize_product_name(self, service_name: str) -> str:
        """Normalize service name to product name"""
        # Map common service names to CVE product names
        mapping = {
            'apache': 'apache_http_server',
            'nginx': 'nginx',
            'openssh': 'openssh',
            'mysql': 'mysql',
            'postgresql': 'postgresql',
            'mongodb': 'mongodb',
            'redis': 'redis',
            'elasticsearch': 'elasticsearch',
            'tomcat': 'tomcat',
            'iis': 'internet_information_services',
            'ssh': 'openssh',
            'ftp': 'vsftpd',
            'smtp': 'postfix',
            'pop3': 'dovecot',
            'imap': 'dovecot'
        }
        
        service_lower = service_name.lower()
        for key, value in mapping.items():
            if key in service_lower:
                return value
        
        return service_lower
    
    def _extract_version(self, version_string: str) -> str:
        """Extract clean version number from banner"""
        if not version_string:
            return ""
        
        # Extract version pattern like 2.4.29, 8.2p1, etc.
        match = re.search(r'(\d+\.[\d\.]+[a-z]?\d*)', version_string)
        if match:
            return match.group(1)
        
        return ""
    
    def _query_nvd(self, product: str, version: str) -> List[CVE]:
        """Query NVD API for CVEs - no restrictive filtering"""
        try:
            # Try multiple query approaches for best coverage
            all_cves = []
            
            # Query 1: Product + version
            queries = [
                f"{product} {version}",
                f"{product.replace('_', ' ')} {version}",
            ]
            
            for search_terms in queries:
                params = {
                    'keywordSearch': search_terms,
                    'resultsPerPage': 50
                }
                
                response = self.session.get(
                    self.nvd_api_base,
                    params=params,
                    timeout=15
                )
                
                if response.status_code != 200:
                    continue
                
                data = response.json()
                
                for vuln in data.get('vulnerabilities', []):
                    cve_data = vuln.get('cve', {})
                    cve_id = cve_data.get('id', '')
                    
                    # Skip if already added
                    if any(c.cve_id == cve_id for c in all_cves):
                        continue
                    
                    # Get description (prefer English)
                    descriptions = cve_data.get('descriptions', [])
                    description = ''
                    for desc in descriptions:
                        if desc.get('lang') == 'en':
                            description = desc.get('value', '')
                            break
                    if not description and descriptions:
                        description = descriptions[0].get('value', '')
                    
                    # Get CVSS score from any available version
                    metrics = cve_data.get('metrics', {})
                    cvss_score = 0.0
                    severity = "UNKNOWN"
                    
                    # Try CVSS v3.1
                    if 'cvssMetricV31' in metrics and metrics['cvssMetricV31']:
                        cvss_data = metrics['cvssMetricV31'][0]['cvssData']
                        cvss_score = cvss_data.get('baseScore', 0.0)
                        severity = cvss_data.get('baseSeverity', 'UNKNOWN')
                    # Try CVSS v3.0
                    elif 'cvssMetricV30' in metrics and metrics['cvssMetricV30']:
                        cvss_data = metrics['cvssMetricV30'][0]['cvssData']
                        cvss_score = cvss_data.get('baseScore', 0.0)
                        severity = cvss_data.get('baseSeverity', 'UNKNOWN')
                    # Fall back to CVSS v2
                    elif 'cvssMetricV2' in metrics and metrics['cvssMetricV2']:
                        cvss_score = metrics['cvssMetricV2'][0]['cvssData'].get('baseScore', 0.0)
                        severity = self._cvss_to_severity(cvss_score)
                    
                    # Include CVEs with any score (don't filter by score=0)
                    # Some valid CVEs might not have scores yet
                    
                    # Get references
                    references = []
                    for ref in cve_data.get('references', []):
                        references.append(ref.get('url', ''))
                    
                    # Published date
                    published = cve_data.get('published', '')
                    
                    cve = CVE(
                        cve_id=cve_id,
                        description=description[:250],
                        cvss_score=cvss_score,
                        severity=severity if cvss_score > 0 else "UNKNOWN",
                        published_date=published,
                        references=references[:5]
                    )
                    
                    all_cves.append(cve)
                
                # If we found CVEs with first query, don't need second
                if all_cves:
                    break
            
            # Sort by CVSS score (highest first), then by CVE ID (newest first)
            all_cves.sort(key=lambda x: (x.cvss_score, x.cve_id), reverse=True)
            
            return all_cves[:20]  # Return top 20
            
        except Exception as e:
            print(f"NVD API error: {e}")
            return []
    
    def _cvss_to_severity(self, score: float) -> str:
        """Convert CVSS score to severity"""
        if score >= 9.0:
            return "CRITICAL"
        elif score >= 7.0:
            return "HIGH"
        elif score >= 4.0:
            return "MEDIUM"
        elif score > 0.0:
            return "LOW"
        return "UNKNOWN"
    
    def get_exploit_availability(self, cve_id: str) -> bool:
        """Check if public exploits are available (placeholder)"""
        # In future: integrate with Exploit-DB API
        # For now, check if references contain "exploit"
        try:
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                'SELECT ref_urls FROM cves WHERE id = ?',
                (cve_id,)
            )
            
            result = cursor.fetchone()
            conn.close()
            
            if result and result[0]:
                refs = json.loads(result[0])
                return any('exploit' in ref.lower() for ref in refs)
            
            return False
            
        except Exception:
            return False


# Quick test
if __name__ == "__main__":
    scanner = CVEScanner()
    
    # Test with Apache 2.4.29 (known vulnerable)
    print("Testing CVE Scanner...")
    print(f"Scanning: Apache 2.4.29")
    
    cves = scanner.scan_service("Apache", "2.4.29")
    
    if cves:
        print(f"\nFound {len(cves)} CVEs:")
        for cve in cves[:5]:  # Show first 5
            print(f"\n{cve.cve_id} ({cve.severity} - {cve.cvss_score}/10.0)")
            print(f"  {cve.description[:100]}...")
    else:
        print("No CVEs found")
