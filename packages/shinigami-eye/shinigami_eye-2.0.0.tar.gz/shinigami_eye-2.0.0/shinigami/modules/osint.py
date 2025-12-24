"""
OSINT Module - Open Source Intelligence Gathering
Integrates with Shodan, VirusTotal, and other OSINT sources
"""

import requests
import json
from typing import Dict, Optional, List
from datetime import datetime
import socket


class OSINTCollector:
    """Collects intelligence from multiple OSINT sources"""
    
    def __init__(self, shodan_key: str = None, vt_key: str = None):
        """
        Initialize OSINT collector
        
        Args:
            shodan_key: Shodan API key
            vt_key: VirusTotal API key
        """
        self.shodan_key = shodan_key
        self.vt_key = vt_key
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'SHINIGAMI-EYE-OSINT/2.0'
        })
    
    def gather_intelligence(self, target: str, enable_shodan: bool = True,
                          enable_vt: bool = True, enable_geo: bool = True) -> Dict:
        """
        Gather comprehensive OSINT
        
        Args:
            target: Domain or IP address
            enable_shodan: Query Shodan
            enable_vt: Query VirusTotal
            enable_geo: Get geolocation
        
        Returns:
            Dictionary with all gathered intelligence
        """
        results = {
            'target': target,
            'timestamp': datetime.now().isoformat(),
            'ip_address': self._resolve_ip(target)
        }
        
        ip = results['ip_address']
        
        if enable_geo and ip:
            results['geolocation'] = self.geolocate(ip)
        
        if enable_shodan and self.shodan_key and ip:
            results['shodan'] = self.query_shodan(ip)
        elif enable_shodan:
            results['shodan'] = {'error': 'Shodan API key not configured'}
        
        if enable_vt and self.vt_key:
            results['virustotal'] = self.query_virustotal(target)
        elif enable_vt:
            results['virustotal'] = {'error': 'VirusTotal API key not configured'}
        
        results['whois'] = self.basic_whois(target)
        
        return results
    
    def _resolve_ip(self, target: str) -> Optional[str]:
        """Resolve domain to IP address"""
        try:
            return socket.gethostbyname(target)
        except:
            # If already an IP, return it
            if self._is_ip(target):
                return target
            return None
    
    def _is_ip(self, target: str) -> bool:
        """Check if target is an IP address"""
        parts = target.split('.')
        if len(parts) != 4:
            return False
        try:
            return all(0 <= int(part) <= 255 for part in parts)
        except:
            return False
    
    def query_shodan(self, ip: str) -> Dict:
        """
        Query Shodan for host information
        
        Args:
            ip: IP address to query
        
        Returns:
            Shodan data or error
        """
        if not self.shodan_key:
            return {'error': 'API key not configured'}
        
        try:
            url = f"https://api.shodan.io/shodan/host/{ip}"
            params = {'key': self.shodan_key}
            
            response = self.session.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'ip': data.get('ip_str', ''),
                    'organization': data.get('org', ''),
                    'asn': data.get('asn', ''),
                    'isp': data.get('isp', ''),
                    'hostnames': data.get('hostnames', []),
                    'ports': data.get('ports', []),
                    'tags': data.get('tags', []),
                    'vulns': data.get('vulns', []),
                    'last_update': data.get('last_update', ''),
                    'country': data.get('country_name', ''),
                    'city': data.get('city', '')
                }
            elif response.status_code == 401:
                return {'error': 'Invalid API key'}
            elif response.status_code == 404:
                return {'error': 'No information available'}
            else:
                return {'error': f'HTTP {response.status_code}'}
                
        except Exception as e:
            return {'error': str(e)}
    
    def query_virustotal(self, domain: str) -> Dict:
        """
        Query VirusTotal for domain reputation
        
        Args:
            domain: Domain to query
        
        Returns:
            VirusTotal data or error
        """
        if not self.vt_key:
            return {'error': 'API key not configured'}
        
        try:
            url = f"https://www.virustotal.com/api/v3/domains/{domain}"
            headers = {'x-apikey': self.vt_key}
            
            response = self.session.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                attributes = data.get('data', {}).get('attributes', {})
                stats = attributes.get('last_analysis_stats', {})
                
                return {
                    'reputation': attributes.get('reputation', 0),
                    'malicious': stats.get('malicious', 0),
                    'suspicious': stats.get('suspicious', 0),
                    'clean': stats.get('harmless', 0),
                    'undetected': stats.get('undetected', 0),
                    'categories': attributes.get('categories', {}),
                    'last_analysis_date': attributes.get('last_analysis_date', '')
                }
            elif response.status_code == 401:
                return {'error': 'Invalid API key'}
            elif response.status_code == 404:
                return {'error': 'Domain not found'}
            else:
                return {'error': f'HTTP {response.status_code}'}
                
        except Exception as e:
            return {'error': str(e)}
    
    def geolocate(self, ip: str) -> Dict:
        """
        Get geographic location of IP
        
        Args:
            ip: IP address
        
        Returns:
            Geolocation data (using free ipapi.co)
        """
        try:
            url = f"https://ipapi.co/{ip}/json/"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'country': data.get('country_name', ''),
                    'country_code': data.get('country_code', ''),
                    'region': data.get('region', ''),
                    'city': data.get('city', ''),
                    'latitude': data.get('latitude', 0),
                    'longitude': data.get('longitude', 0),
                    'timezone': data.get('timezone', ''),
                    'isp': data.get('org', ''),
                    'asn': data.get('asn', '')
                }
            else:
                return {'error': 'Geolocation unavailable'}
                
        except Exception as e:
            return {'error': str(e)}
    
    def basic_whois(self, domain: str) -> Dict:
        """
        Basic WHOIS information
        
        Args:
            domain: Domain to query
        
        Returns:
            Basic WHOIS data
        """
        try:
            import whois
            w = whois.whois(domain)
            return {
                'registrar': w.registrar if hasattr(w, 'registrar') else None,
                'creation_date': str(w.creation_date) if hasattr(w, 'creation_date') else None,
                'expiration_date': str(w.expiration_date) if hasattr(w, 'expiration_date') else None,
                'name_servers': w.name_servers if hasattr(w, 'name_servers') else []
            }
        except:
            # WHOIS might fail, return basic info
            return {'error': 'WHOIS query failed'}


# Quick test
if __name__ == "__main__":
    print("Testing OSINT Collector...")
    
    # Test with free geolocation only (no API key needed)
    collector = OSINTCollector()
    
    target = "example.com"
    print(f"\nGathering OSINT for: {target}")
    print("(Using free geolocation only - Shodan/VT require API keys)")
    
    results = collector.gather_intelligence(
        target,
        enable_shodan=False,  # Requires API key
        enable_vt=False,      # Requires API key
        enable_geo=True       # Free service
    )
    
    print(f"\nResults:")
    print(f"IP: {results.get('ip_address')}")
    print(f"Geolocation: {results.get('geolocation')}")
    print(f"WHOIS: {results.get('whois')}")
