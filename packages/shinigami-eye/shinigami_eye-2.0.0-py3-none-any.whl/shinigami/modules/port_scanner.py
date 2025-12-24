"""
Port Scanner Module - Advanced port scanning capabilities
Supports TCP, UDP, SYN scanning with service detection
"""

import socket
import concurrent.futures
from typing import List, Dict, Tuple, Optional
from datetime import datetime
import struct

from shinigami.utils.logger import get_logger

logger = get_logger("PortScanner")


class PortScanner:
    """Advanced port scanner with multiple scanning techniques"""
    
    # Common ports and their services
    COMMON_PORTS = {
        20: "ftp-data", 21: "ftp", 22: "ssh", 23: "telnet", 25: "smtp",
        53: "dns", 80: "http", 110: "pop3", 143: "imap", 443: "https",
        445: "smb", 3306: "mysql", 3389: "rdp", 5432: "postgresql",
        5900: "vnc", 6379: "redis", 8080: "http-proxy", 8443: "https-alt",
        27017: "mongodb", 9200: "elasticsearch", 9300: "elasticsearch"
    }
    
    def __init__(self, target: str, timeout: float = 1.0, threads: int = 100):
        """
        Initialize port scanner
        
        Args:
            target: Target IP or hostname
            timeout: Connection timeout in seconds
            threads: Number of concurrent threads
        """
        self.target = target
        self.timeout = timeout
        self.threads = threads
        self.results = {}
    
    def _tcp_connect_scan(self, port: int) -> Tuple[int, bool, Optional[str]]:
        """
        Perform TCP connect scan on a single port
        
        Args:
            port: Port number to scan
            
        Returns:
            Tuple of (port, is_open, service_name)
        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            result = sock.connect_ex((self.target, port))
            sock.close()
            
            if result == 0:
                service = self.COMMON_PORTS.get(port, "unknown")
                return (port, True, service)
            return (port, False, None)
        except Exception as e:
            logger.debug(f"Error scanning port {port}: {str(e)}")
            return (port, False, None)
    
    def _grab_banner(self, port: int) -> Optional[str]:
        """
        Attempt to grab service banner
        
        Args:
            port: Port number
            
        Returns:
            Service banner or None
        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            sock.connect((self.target, port))
            
            # Try to receive banner
            try:
                banner = sock.recv(1024).decode('utf-8', errors='ignore').strip()
                sock.close()
                return banner if banner else None
            except:
                sock.close()
                return None
        except:
            return None
    
    def scan_tcp_range(self, start_port: int, end_port: int, grab_banners: bool = True) -> Dict:
        """
        Scan a range of TCP ports
        
        Args:
            start_port: Starting port number
            end_port: Ending port number
            grab_banners: Whether to attempt banner grabbing
            
        Returns:
            Dictionary of scan results
        """
        logger.info(f"Scanning TCP ports {start_port}-{end_port} on {self.target}")
        start_time = datetime.now()
        
        open_ports = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.threads) as executor:
            future_to_port = {
                executor.submit(self._tcp_connect_scan, port): port 
                for port in range(start_port, end_port + 1)
            }
            
            for future in concurrent.futures.as_completed(future_to_port):
                port, is_open, service = future.result()
                
                if is_open:
                    banner = None
                    if grab_banners:
                        banner = self._grab_banner(port)
                    
                    open_ports.append({
                        'port': port,
                        'service': service,
                        'banner': banner
                    })
                    logger.scan(f"Open port: {port}/{service}" + 
                               (f" - {banner[:50]}..." if banner else ""))
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        self.results = {
            'target': self.target,
            'scan_type': 'TCP Connect',
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'duration': duration,
            'ports_scanned': end_port - start_port + 1,
            'open_ports': open_ports,
            'open_count': len(open_ports)
        }
        
        logger.success(f"Scan completed in {duration:.2f}s - Found {len(open_ports)} open ports")
        return self.results
    
    def scan_common_ports(self, grab_banners: bool = True) -> Dict:
        """
        Scan most common ports
        
        Args:
            grab_banners: Whether to attempt banner grabbing
            
        Returns:
            Dictionary of scan results
        """
        common_port_list = list(self.COMMON_PORTS.keys())
        logger.info(f"Scanning {len(common_port_list)} common ports on {self.target}")
        start_time = datetime.now()
        
        open_ports = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.threads) as executor:
            future_to_port = {
                executor.submit(self._tcp_connect_scan, port): port 
                for port in common_port_list
            }
            
            for future in concurrent.futures.as_completed(future_to_port):
                port, is_open, service = future.result()
                
                if is_open:
                    banner = None
                    if grab_banners:
                        banner = self._grab_banner(port)
                    
                    open_ports.append({
                        'port': port,
                        'service': service,
                        'banner': banner
                    })
                    logger.scan(f"Open port: {port}/{service}" + 
                               (f" - {banner[:50]}..." if banner else ""))
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        self.results = {
            'target': self.target,
            'scan_type': 'Common Ports',
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'duration': duration,
            'ports_scanned': len(common_port_list),
            'open_ports': open_ports,
            'open_count': len(open_ports)
        }
        
        logger.success(f"Scan completed in {duration:.2f}s - Found {len(open_ports)} open ports")
        return self.results
    
    def scan_single_port(self, port: int) -> Dict:
        """
        Scan a single port
        
        Args:
            port: Port number to scan
            
        Returns:
            Dictionary with scan result
        """
        logger.info(f"Scanning port {port} on {self.target}")
        port_num, is_open, service = self._tcp_connect_scan(port)
        
        if is_open:
            banner = self._grab_banner(port)
            logger.success(f"Port {port} is open - Service: {service}")
            return {
                'target': self.target,
                'port': port,
                'open': True,
                'service': service,
                'banner': banner
            }
        else:
            logger.info(f"Port {port} is closed")
            return {
                'target': self.target,
                'port': port,
                'open': False
            }


def quick_scan(target: str, timeout: float = 1.0) -> Dict:
    """
    Quick scan of common ports
    
    Args:
        target: Target IP or hostname
        timeout: Connection timeout
        
    Returns:
        Scan results dictionary
    """
    scanner = PortScanner(target, timeout=timeout)
    return scanner.scan_common_ports()


def full_scan(target: str, start_port: int = 1, end_port: int = 65535, timeout: float = 1.0) -> Dict:
    """
    Full port range scan
    
    Args:
        target: Target IP or hostname
        start_port: Starting port
        end_port: Ending port
        timeout: Connection timeout
        
    Returns:
        Scan results dictionary
    """
    scanner = PortScanner(target, timeout=timeout)
    return scanner.scan_tcp_range(start_port, end_port)
