"""
Web Reconnaissance Module - Web intelligence gathering
Subdomain enumeration, directory discovery, technology detection
"""

import requests
import dns.resolver
import socket
import concurrent.futures
from typing import List, Dict, Set, Optional
from urllib.parse import urljoin, urlparse
import re
from datetime import datetime

from shinigami.utils.logger import get_logger

logger = get_logger("WebRecon")


class WebRecon:
    """Web reconnaissance and intelligence gathering"""
    
    def __init__(self, domain: str, timeout: int = 5, threads: int = 20):
        """
        Initialize web reconnaissance
        
        Args:
            domain: Target domain
            timeout: Request timeout in seconds
            threads: Number of concurrent threads
        """
        self.domain = domain
        self.timeout = timeout
        self.threads = threads
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.subdomains = set()
        self.results = {}
    
    def _check_subdomain(self, subdomain: str) -> Optional[Dict]:
        """
        Check if subdomain exists
        
        Args:
            subdomain: Subdomain to check
            
        Returns:
            Dictionary with subdomain info or None
        """
        full_domain = f"{subdomain}.{self.domain}"
        try:
            # Try DNS resolution
            answers = dns.resolver.resolve(full_domain, 'A')
            ips = [str(rdata) for rdata in answers]
            
            # Try HTTP/HTTPS
            for protocol in ['https', 'http']:
                try:
                    url = f"{protocol}://{full_domain}"
                    response = self.session.get(url, timeout=self.timeout, allow_redirects=True)
                    
                    return {
                        'subdomain': full_domain,
                        'ips': ips,
                        'url': url,
                        'status_code': response.status_code,
                        'title': self._extract_title(response.text),
                        'server': response.headers.get('Server', 'Unknown'),
                        'protocol': protocol
                    }
                except requests.exceptions.RequestException:
                    continue
            
            # DNS resolved but no HTTP
            return {
                'subdomain': full_domain,
                'ips': ips,
                'url': None,
                'status_code': None,
                'title': None,
                'server': None,
                'protocol': None
            }
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.Timeout, Exception):
            return None
    
    def _extract_title(self, html: str) -> Optional[str]:
        """Extract title from HTML"""
        match = re.search(r'<title>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip()
        return None
    
    def enumerate_subdomains(self, wordlist: Optional[List[str]] = None) -> List[Dict]:
        """
        Enumerate subdomains using wordlist
        
        Args:
            wordlist: List of subdomain names to try
            
        Returns:
            List of discovered subdomains
        """
        if wordlist is None:
            # Default common subdomains
            wordlist = [
                'www', 'mail', 'ftp', 'localhost', 'webmail', 'smtp', 'pop', 'ns1', 'ns2',
                'webdisk', 'admin', 'blog', 'dev', 'staging', 'test', 'portal', 'api',
                'vpn', 'remote', 'cdn', 'shop', 'store', 'support', 'cloud', 'secure',
                'app', 'mobile', 'static', 'assets', 'images', 'img', 'email', 'direct',
                'old', 'new', 'beta', 'alpha', 'prod', 'production', 'demo', 'sandbox'
            ]
        
        logger.info(f"Enumerating subdomains for {self.domain} using {len(wordlist)} patterns")
        discovered = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.threads) as executor:
            future_to_sub = {
                executor.submit(self._check_subdomain, sub): sub 
                for sub in wordlist
            }
            
            for future in concurrent.futures.as_completed(future_to_sub):
                result = future.result()
                if result:
                    discovered.append(result)
                    logger.scan(f"Found subdomain: {result['subdomain']} - {result.get('ips', [])}")
        
        logger.success(f"Discovered {len(discovered)} subdomains")
        return discovered
    
    def detect_technologies(self, url: str) -> Dict:
        """
        Detect web technologies used
        
        Args:
            url: URL to analyze
            
        Returns:
            Dictionary of detected technologies
        """
        logger.info(f"Detecting technologies for {url}")
        
        try:
            response = self.session.get(url, timeout=self.timeout)
            
            technologies = {
                'server': response.headers.get('Server', 'Unknown'),
                'powered_by': response.headers.get('X-Powered-By', 'Unknown'),
                'frameworks': [],
                'cms': None,
                'javascript_libraries': [],
                'analytics': []
            }
            
            html = response.text.lower()
            
            # Detect CMS
            cms_patterns = {
                'WordPress': ['wp-content', 'wp-includes'],
                'Joomla': ['joomla', 'com_content'],
                'Drupal': ['drupal', 'sites/all/'],
                'Magento': ['mage', 'magento'],
                'Shopify': ['shopify', 'cdn.shopify'],
                'Wix': ['wix.com', 'wixstatic']
            }
            
            for cms, patterns in cms_patterns.items():
                if any(pattern in html for pattern in patterns):
                    technologies['cms'] = cms
                    break
            
            # Detect frameworks
            framework_patterns = {
                'React': ['react', 'react-dom'],
                'Vue.js': ['vue.js', 'vue.min.js'],
                'Angular': ['angular', 'ng-app'],
                'jQuery': ['jquery'],
                'Bootstrap': ['bootstrap'],
                'Laravel': ['laravel'],
                'Django': ['django'],
                'Flask': ['flask']
            }
            
            for framework, patterns in framework_patterns.items():
                if any(pattern in html for pattern in patterns):
                    technologies['frameworks'].append(framework)
            
            # Detect analytics
            analytics_patterns = {
                'Google Analytics': ['google-analytics.com', 'gtag'],
                'Google Tag Manager': ['googletagmanager.com'],
                'Facebook Pixel': ['facebook.net/en_us/fbevents.js'],
                'Hotjar': ['hotjar.com']
            }
            
            for analytics, patterns in analytics_patterns.items():
                if any(pattern in html for pattern in patterns):
                    technologies['analytics'].append(analytics)
            
            logger.success(f"Technology detection completed")
            return technologies
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error detecting technologies: {str(e)}")
            return {}
    
    def discover_directories(self, url: str, wordlist: Optional[List[str]] = None) -> List[Dict]:
        """
        Discover directories and files
        
        Args:
            url: Base URL
            wordlist: List of paths to try
            
        Returns:
            List of discovered paths
        """
        if wordlist is None:
            wordlist = [
                'admin', 'login', 'dashboard', 'wp-admin', 'adminpanel', 'cpanel',
                'api', 'v1', 'v2', 'backup', 'config', 'uploads', 'images', 'assets',
                'css', 'js', 'static', 'media', 'files', 'download', 'downloads',
                'robots.txt', 'sitemap.xml', '.git', '.env', 'phpinfo.php',
                'test', 'dev', 'staging', 'old', 'new', 'tmp', 'temp'
            ]
        
        logger.info(f"Discovering directories for {url}")
        discovered = []
        
        def check_path(path):
            test_url = urljoin(url, path)
            try:
                response = self.session.get(test_url, timeout=self.timeout, allow_redirects=False)
                if response.status_code in [200, 301, 302, 403]:
                    return {
                        'url': test_url,
                        'status_code': response.status_code,
                        'size': len(response.content),
                        'type': 'file' if '.' in path else 'directory'
                    }
            except:
                pass
            return None
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.threads) as executor:
            future_to_path = {executor.submit(check_path, path): path for path in wordlist}
            
            for future in concurrent.futures.as_completed(future_to_path):
                result = future.result()
                if result:
                    discovered.append(result)
                    logger.scan(f"Found: {result['url']} [{result['status_code']}]")
        
        logger.success(f"Discovered {len(discovered)} paths")
        return discovered
    
    def check_security_headers(self, url: str) -> Dict:
        """
        Check security headers
        
        Args:
            url: URL to check
            
        Returns:
            Dictionary of security headers status
        """
        logger.info(f"Checking security headers for {url}")
        
        try:
            response = self.session.get(url, timeout=self.timeout)
            headers = response.headers
            
            security_headers = {
                'Strict-Transport-Security': headers.get('Strict-Transport-Security'),
                'X-Content-Type-Options': headers.get('X-Content-Type-Options'),
                'X-Frame-Options': headers.get('X-Frame-Options'),
                'X-XSS-Protection': headers.get('X-XSS-Protection'),
                'Content-Security-Policy': headers.get('Content-Security-Policy'),
                'Referrer-Policy': headers.get('Referrer-Policy'),
                'Permissions-Policy': headers.get('Permissions-Policy')
            }
            
            missing = [k for k, v in security_headers.items() if v is None]
            
            if missing:
                logger.warning(f"Missing security headers: {', '.join(missing)}")
            else:
                logger.success("All recommended security headers present")
            
            return {
                'headers': security_headers,
                'missing': missing,
                'score': ((7 - len(missing)) / 7) * 100
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error checking security headers: {str(e)}")
            return {}


def quick_recon(domain: str) -> Dict:
    """
    Quick reconnaissance of a domain
    
    Args:
        domain: Target domain
        
    Returns:
        Reconnaissance results
    """
    recon = WebRecon(domain)
    
    results = {
        'domain': domain,
        'timestamp': datetime.now().isoformat(),
        'subdomains': recon.enumerate_subdomains(),
        'technologies': recon.detect_technologies(f"https://{domain}"),
        'security_headers': recon.check_security_headers(f"https://{domain}")
    }
    
    return results
