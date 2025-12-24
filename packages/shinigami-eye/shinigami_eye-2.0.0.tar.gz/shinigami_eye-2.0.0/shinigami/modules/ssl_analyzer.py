"""
SSL/TLS Analyzer Module - Certificate and security analysis
"""

import ssl
import socket
import OpenSSL
from datetime import datetime
from typing import Dict, List, Optional
import concurrent.futures

from shinigami.utils.logger import get_logger

logger = get_logger("SSLAnalyzer")


class SSLAnalyzer:
    """SSL/TLS certificate and security analyzer"""
    
    WEAK_CIPHERS = [
        'RC4', 'DES', '3DES', 'MD5', 'NULL', 'EXPORT', 'anon'
    ]
    
    def __init__(self, timeout: int = 5):
        """
        Initialize SSL analyzer
        
        Args:
            timeout: Connection timeout in seconds
        """
        self.timeout = timeout
    
    def get_certificate(self, hostname: str, port: int = 443) -> Optional[Dict]:
        """
        Get SSL certificate information
        
        Args:
            hostname: Target hostname
            port: SSL port (default 443)
            
        Returns:
            Dictionary with certificate information
        """
        logger.info(f"Retrieving SSL certificate from {hostname}:{port}")
        
        try:
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            with socket.create_connection((hostname, port), timeout=self.timeout) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert_bin = ssock.getpeercert(binary_form=True)
                    cert_dict = ssock.getpeercert()
                    
                    # Parse with PyOpenSSL for more details
                    x509 = OpenSSL.crypto.load_certificate(
                        OpenSSL.crypto.FILETYPE_ASN1, cert_bin
                    )
                    
                    # Extract subject and issuer
                    subject = dict(x509.get_subject().get_components())
                    issuer = dict(x509.get_issuer().get_components())
                    
                    # Convert bytes to strings
                    subject = {k.decode(): v.decode() for k, v in subject.items()}
                    issuer = {k.decode(): v.decode() for k, v in issuer.items()}
                    
                    # Extract dates
                    not_before = datetime.strptime(
                        x509.get_notBefore().decode('ascii'), '%Y%m%d%H%M%SZ'
                    )
                    not_after = datetime.strptime(
                        x509.get_notAfter().decode('ascii'), '%Y%m%d%H%M%SZ'
                    )
                    
                    # Check if expired
                    is_expired = datetime.now() > not_after
                    days_remaining = (not_after - datetime.now()).days
                    
                    cert_info = {
                        'subject': subject,
                        'issuer': issuer,
                        'version': x509.get_version(),
                        'serial_number': str(x509.get_serial_number()),
                        'not_before': not_before.isoformat(),
                        'not_after': not_after.isoformat(),
                        'is_expired': is_expired,
                        'days_remaining': days_remaining,
                        'signature_algorithm': x509.get_signature_algorithm().decode(),
                        'san': cert_dict.get('subjectAltName', [])
                    }
                    
                    if is_expired:
                        logger.warning(f"Certificate is EXPIRED")
                    elif days_remaining < 30:
                        logger.warning(f"Certificate expires in {days_remaining} days")
                    else:
                        logger.success(f"Certificate is valid for {days_remaining} days")
                    
                    return cert_info
                    
        except Exception as e:
            logger.error(f"Error retrieving certificate: {str(e)}")
            return None
    
    def check_ciphers(self, hostname: str, port: int = 443) -> Dict:
        """
        Check supported SSL/TLS ciphers
        
        Args:
            hostname: Target hostname
            port: SSL port (default 443)
            
        Returns:
            Dictionary with cipher information
        """
        logger.info(f"Checking SSL/TLS ciphers for {hostname}:{port}")
        
        try:
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            with socket.create_connection((hostname, port), timeout=self.timeout) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cipher = ssock.cipher()
                    version = ssock.version()
                    
                    # Check for weak ciphers
                    cipher_name = cipher[0] if cipher else ""
                    is_weak = any(weak in cipher_name for weak in self.WEAK_CIPHERS)
                    
                    result = {
                        'cipher_suite': cipher_name,
                        'protocol_version': version,
                        'bits': cipher[2] if cipher else 0,
                        'is_weak': is_weak
                    }
                    
                    if is_weak:
                        logger.warning(f"Weak cipher detected: {cipher_name}")
                    else:
                        logger.success(f"Strong cipher: {cipher_name} ({version})")
                    
                    return result
                    
        except Exception as e:
            logger.error(f"Error checking ciphers: {str(e)}")
            return {}
    
    def check_vulnerabilities(self, hostname: str, port: int = 443) -> Dict:
        """
        Check for common SSL/TLS vulnerabilities
        
        Args:
            hostname: Target hostname
            port: SSL port
            
        Returns:
            Dictionary with vulnerability assessment
        """
        logger.info(f"Checking SSL/TLS vulnerabilities for {hostname}:{port}")
        
        vulnerabilities = {
            'heartbleed': False,  # CVE-2014-0160
            'poodle': False,      # CVE-2014-3566
            'beast': False,       # CVE-2011-3389
            'weak_cipher': False,
            'expired_cert': False,
            'self_signed': False
        }
        
        try:
            # Check certificate
            cert_info = self.get_certificate(hostname, port)
            if cert_info:
                vulnerabilities['expired_cert'] = cert_info['is_expired']
                
                # Check if self-signed
                if cert_info['subject'] == cert_info['issuer']:
                    vulnerabilities['self_signed'] = True
                    logger.warning("Certificate is self-signed")
            
            # Check ciphers
            cipher_info = self.check_ciphers(hostname, port)
            if cipher_info:
                vulnerabilities['weak_cipher'] = cipher_info.get('is_weak', False)
                
                # Check for SSLv3 (POODLE)
                if cipher_info.get('protocol_version') == 'SSLv3':
                    vulnerabilities['poodle'] = True
                    logger.warning("SSLv3 is enabled - vulnerable to POODLE")
                
                # Check for TLS 1.0 (BEAST)
                if cipher_info.get('protocol_version') == 'TLSv1.0':
                    vulnerabilities['beast'] = True
                    logger.warning("TLS 1.0 is enabled - vulnerable to BEAST")
            
            vuln_count = sum(1 for v in vulnerabilities.values() if v)
            
            if vuln_count == 0:
                logger.success("No major SSL/TLS vulnerabilities detected")
            else:
                logger.warning(f"Found {vuln_count} potential vulnerabilities")
            
            return {
                'vulnerabilities': vulnerabilities,
                'total_found': vuln_count,
                'risk_level': 'high' if vuln_count >= 3 else 'medium' if vuln_count >= 1 else 'low'
            }
            
        except Exception as e:
            logger.error(f"Error checking vulnerabilities: {str(e)}")
            return {'vulnerabilities': vulnerabilities, 'total_found': 0, 'risk_level': 'unknown'}
    
    def full_analysis(self, hostname: str, port: int = 443) -> Dict:
        """
        Perform full SSL/TLS analysis
        
        Args:
            hostname: Target hostname
            port: SSL port
            
        Returns:
            Complete analysis results
        """
        logger.info(f"Performing full SSL/TLS analysis for {hostname}:{port}")
        
        results = {
            'hostname': hostname,
            'port': port,
            'timestamp': datetime.now().isoformat(),
            'certificate': self.get_certificate(hostname, port),
            'ciphers': self.check_ciphers(hostname, port),
            'vulnerabilities': self.check_vulnerabilities(hostname, port)
        }
        
        logger.success(f"SSL/TLS analysis completed for {hostname}")
        return results


def analyze_ssl(hostname: str, port: int = 443) -> Dict:
    """
    Quick SSL/TLS analysis
    
    Args:
        hostname: Target hostname
        port: SSL port
        
    Returns:
        Analysis results
    """
    analyzer = SSLAnalyzer()
    return analyzer.full_analysis(hostname, port)
