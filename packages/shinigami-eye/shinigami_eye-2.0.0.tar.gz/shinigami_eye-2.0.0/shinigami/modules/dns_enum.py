"""
DNS Enumeration Module - Comprehensive DNS intelligence
"""

import dns.resolver
import dns.zone
import dns.query
import socket
from typing import List, Dict, Optional
from datetime import datetime

from shinigami.utils.logger import get_logger

logger = get_logger("DNSEnum")


class DNSEnumerator:
    """DNS enumeration and intelligence gathering"""
    
    RECORD_TYPES = ['A', 'AAAA', 'CNAME', 'MX', 'NS', 'TXT', 'SOA', 'PTR', 'SRV']
    
    def __init__(self, domain: str, timeout: int = 5):
        """
        Initialize DNS enumerator
        
        Args:
            domain: Target domain
            timeout: Query timeout in seconds
        """
        self.domain = domain
        self.timeout = timeout
        self.resolver = dns.resolver.Resolver()
        self.resolver.timeout = timeout
        self.resolver.lifetime = timeout
    
    def query_record(self, record_type: str, domain: Optional[str] = None) -> List[str]:
        """
        Query specific DNS record type
        
        Args:
            record_type: Type of DNS record (A, MX, etc.)
            domain: Domain to query (default: self.domain)
            
        Returns:
            List of record values
        """
        target = domain or self.domain
        
        try:
            answers = self.resolver.resolve(target, record_type)
            results = [str(rdata) for rdata in answers]
            logger.scan(f"{record_type} records for {target}: {results}")
            return results
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.Timeout, Exception) as e:
            logger.debug(f"No {record_type} records for {target}: {str(e)}")
            return []
    
    def enumerate_all_records(self) -> Dict:
        """
        Enumerate all common DNS records
        
        Returns:
            Dictionary of all DNS records
        """
        logger.info(f"Enumerating DNS records for {self.domain}")
        
        records = {}
        for record_type in self.RECORD_TYPES:
            records[record_type] = self.query_record(record_type)
        
        logger.success(f"DNS enumeration completed for {self.domain}")
        return records
    
    def attempt_zone_transfer(self) -> Optional[Dict]:
        """
        Attempt DNS zone transfer (AXFR)
        
        Returns:
            Zone transfer data or None if not allowed
        """
        logger.info(f"Attempting zone transfer for {self.domain}")
        
        try:
            # Get name servers
            ns_records = self.query_record('NS')
            
            if not ns_records:
                logger.warning("No name servers found")
                return None
            
            for ns in ns_records:
                ns_clean = ns.rstrip('.')
                logger.info(f"Attempting zone transfer from {ns_clean}")
                
                try:
                    # Resolve NS to IP
                    ns_ip = socket.gethostbyname(ns_clean)
                    
                    # Attempt zone transfer
                    zone = dns.zone.from_xfr(dns.query.xfr(ns_ip, self.domain))
                    
                    if zone:
                        logger.success(f"Zone transfer successful from {ns_clean}!")
                        
                        records = []
                        for name, node in zone.nodes.items():
                            for rdataset in node.rdatasets:
                                records.append({
                                    'name': str(name),
                                    'type': dns.rdatatype.to_text(rdataset.rdtype),
                                    'value': str(rdataset)
                                })
                        
                        return {
                            'nameserver': ns_clean,
                            'records': records,
                            'total': len(records)
                        }
                        
                except Exception as e:
                    logger.debug(f"Zone transfer failed for {ns_clean}: {str(e)}")
                    continue
            
            logger.info("Zone transfer not allowed on any nameserver")
            return None
            
        except Exception as e:
            logger.error(f"Error during zone transfer attempt: {str(e)}")
            return None
    
    def reverse_dns(self, ip: str) -> Optional[str]:
        """
        Perform reverse DNS lookup
        
        Args:
            ip: IP address
            
        Returns:
            Hostname or None
        """
        try:
            hostname = socket.gethostbyaddr(ip)[0]
            logger.scan(f"Reverse DNS for {ip}: {hostname}")
            return hostname
        except socket.herror:
            logger.debug(f"No reverse DNS for {ip}")
            return None
    
    def check_dnssec(self) -> Dict:
        """
        Check DNSSEC configuration
        
        Returns:
            DNSSEC status information
        """
        logger.info(f"Checking DNSSEC for {self.domain}")
        
        try:
            # Query for DNSKEY records
            dnskey_records = self.query_record('DNSKEY')
            
            # Query for DS records from parent
            ds_records = self.query_record('DS')
            
            # Query for RRSIG records
            rrsig_records = self.query_record('RRSIG')
            
            has_dnssec = bool(dnskey_records or ds_records or rrsig_records)
            
            result = {
                'enabled': has_dnssec,
                'dnskey_count': len(dnskey_records),
                'ds_count': len(ds_records),
                'rrsig_count': len(rrsig_records)
            }
            
            if has_dnssec:
                logger.success("DNSSEC is enabled")
            else:
                logger.warning("DNSSEC is not enabled")
            
            return result
            
        except Exception as e:
            logger.error(f"Error checking DNSSEC: {str(e)}")
            return {'enabled': False, 'error': str(e)}
    
    def find_wildcard(self) -> bool:
        """
        Check if domain uses wildcard DNS
        
        Returns:
            True if wildcard is configured
        """
        import random
        import string
        
        # Generate random subdomain
        random_sub = ''.join(random.choices(string.ascii_lowercase, k=20))
        test_domain = f"{random_sub}.{self.domain}"
        
        try:
            answers = self.resolver.resolve(test_domain, 'A')
            if answers:
                logger.warning(f"Wildcard DNS detected - {test_domain} resolves")
                return True
        except:
            pass
        
        logger.info("No wildcard DNS detected")
        return False
    
    def full_enumeration(self) -> Dict:
        """
        Perform comprehensive DNS enumeration
        
        Returns:
            Complete DNS intelligence
        """
        logger.info(f"Starting full DNS enumeration for {self.domain}")
        
        results = {
            'domain': self.domain,
            'timestamp': datetime.now().isoformat(),
            'records': self.enumerate_all_records(),
            'zone_transfer': self.attempt_zone_transfer(),
            'dnssec': self.check_dnssec(),
            'wildcard': self.find_wildcard()
        }
        
        # Reverse DNS for A records
        if 'A' in results['records']:
            results['reverse_dns'] = {}
            for ip in results['records']['A']:
                hostname = self.reverse_dns(ip)
                if hostname:
                    results['reverse_dns'][ip] = hostname
        
        logger.success(f"DNS enumeration completed for {self.domain}")
        return results


def enumerate_dns(domain: str) -> Dict:
    """
    Quick DNS enumeration
    
    Args:
        domain: Target domain
        
    Returns:
        DNS enumeration results
    """
    enumerator = DNSEnumerator(domain)
    return enumerator.full_enumeration()
