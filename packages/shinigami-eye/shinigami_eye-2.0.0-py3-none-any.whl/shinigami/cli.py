#!/usr/bin/env python3
"""
SHINIGAMI-EYE CLI - Main command-line interface
All-Seeing Cybersecurity Framework
"""

import argparse
import sys
from datetime import datetime
from typing import Dict

from shinigami import __version__
from shinigami.utils.ascii_art import print_banner, print_status, print_module_header, Colors
from shinigami.utils.logger import get_logger
from shinigami.utils.report import generate_report
from shinigami.modules.port_scanner import PortScanner
from shinigami.modules.web_recon import WebRecon
from shinigami.modules.ssl_analyzer import SSLAnalyzer
from shinigami.modules.dns_enum import DNSEnumerator

# v2.0 Enhancements
from shinigami.modules.cve_scanner import CVEScanner
from shinigami.modules.osint import OSINTCollector
from shinigami.modules.web_screenshot import WebScreenshot

import yaml
from pathlib import Path

logger = get_logger("CLI")


def print_disclaimer():
    """Print legal disclaimer"""
    disclaimer = f"""
{Colors.BOLD}{Colors.YELLOW}⚠️  LEGAL DISCLAIMER ⚠️{Colors.END}

SHINIGAMI-EYE is designed for {Colors.BOLD}EDUCATIONAL PURPOSES{Colors.END} and {Colors.BOLD}AUTHORIZED{Colors.END}
security testing only.

{Colors.RED}By using this tool, you agree to:{Colors.END}
  • Only scan systems you own or have explicit permission to test
  • Comply with all applicable local, state, and federal laws
  • Not use this tool for illegal or malicious purposes

{Colors.BOLD}Unauthorized access to computer systems is ILLEGAL.{Colors.END}

Type 'yes' to accept and continue, or 'no' to exit: """
    
    response = input(disclaimer).strip().lower()
    if response != 'yes':
        print(f"\n{Colors.RED}Disclaimer not accepted. Exiting.{Colors.END}\n")
        sys.exit(0)
    print(f"\n{Colors.GREEN}✓ Disclaimer accepted{Colors.END}\n")


def cmd_portscan(args):
    """Execute port scan"""
    print_module_header("PORT SCANNER")
    
    scanner = PortScanner(args.target, timeout=args.timeout, threads=args.threads)
    
    if args.port:
        # Single port
        results = scanner.scan_single_port(args.port)
    elif args.common:
        # Common ports only
        results = scanner.scan_common_ports(grab_banners=not args.no_banner)
    else:
        # Range scan
        start_port = args.start_port or 1
        end_port = args.end_port or 1000
        results = scanner.scan_tcp_range(start_port, end_port, grab_banners=not args.no_banner)
    
    # Save report if requested
    if args.output:
        report_data = {
            'target': args.target,
            'timestamp': datetime.now().isoformat(),
            'report_type': 'Port Scan',
            'port_scan': results
        }
        generate_report(report_data, args.format, args.output)
    
    return results


def cmd_webrecon(args):
    """Execute web reconnaissance"""
    print_module_header("WEB RECONNAISSANCE")
    
    recon = WebRecon(args.domain, timeout=args.timeout, threads=args.threads)
    
    results = {
        'domain': args.domain,
        'timestamp': datetime.now().isoformat(),
        'report_type': 'Web Reconnaissance'
    }
    
    if not args.skip_subdomains:
        logger.info("Starting subdomain enumeration...")
        results['subdomains'] = recon.enumerate_subdomains()
    
    if not args.skip_tech:
        logger.info("Detecting technologies...")
        results['technologies'] = recon.detect_technologies(f"https://{args.domain}")
    
    if not args.skip_security:
        logger.info("Checking security headers...")
        results['security_headers'] = recon.check_security_headers(f"https://{args.domain}")
    
    if args.discover_dirs:
        logger.info("Discovering directories...")
        results['directories'] = recon.discover_directories(f"https://{args.domain}")
    
    # Save report if requested
    if args.output:
        generate_report({'target': args.domain, **results}, args.format, args.output)
    
    return results


def cmd_ssl(args):
    """Execute SSL/TLS analysis"""
    print_module_header("SSL/TLS ANALYZER")
    
    analyzer = SSLAnalyzer(timeout=args.timeout)
    results = analyzer.full_analysis(args.hostname, args.port)
    
    # Save report if requested
    if args.output:
        report_data = {
            'target': args.hostname,
            'timestamp': datetime.now().isoformat(),
            'report_type': 'SSL/TLS Analysis',
            'ssl_analysis': results
        }
        generate_report(report_data, args.format, args.output)
    
    return results


def cmd_dns(args):
    """Execute DNS enumeration"""
    print_module_header("DNS ENUMERATOR")
    
    enumerator = DNSEnumerator(args.domain, timeout=args.timeout)
    results = enumerator.full_enumeration()
    
    # Save report if requested
    if args.output:
        report_data = {
            'target': args.domain,
            'timestamp': datetime.now().isoformat(),
            'report_type': 'DNS Enumeration',
            'dns_enum': results
        }
        generate_report(report_data, args.format, args.output)
    
    return results


def cmd_full(args):
    """Execute full scan (all modules)"""
    print_module_header("FULL SCAN - ALL MODULES")
    
    target = args.target
    results = {
        'target': target,
        'timestamp': datetime.now().isoformat(),
        'report_type': 'Full Scan'
    }
    
    # Port Scan
    print_status("Starting port scan...", "info")
    scanner = PortScanner(target, timeout=args.timeout, threads=args.threads)
    results['port_scan'] = scanner.scan_common_ports()
    
    # DNS Enumeration
    print_status("Starting DNS enumeration...", "info")
    dns_enum = DNSEnumerator(target, timeout=args.timeout)
    results['dns_enum'] = dns_enum.full_enumeration()
    
    # Web Reconnaissance
    print_status("Starting web reconnaissance...", "info")
    web_recon = WebRecon(target, timeout=args.timeout, threads=args.threads)
    results['web_recon'] = {
        'subdomains': web_recon.enumerate_subdomains(),
        'technologies': web_recon.detect_technologies(f"https://{target}"),
        'security_headers': web_recon.check_security_headers(f"https://{target}")
    }
    
    # SSL Analysis
    print_status("Starting SSL/TLS analysis...", "info")
    ssl_analyzer = SSLAnalyzer(timeout=args.timeout)
    results['ssl_analysis'] = ssl_analyzer.full_analysis(target, 443)
    
    print_status("Full scan completed!", "success")
    
    # Save report
    if args.output:
        generate_report(results, args.format, args.output)
    else:
        # Auto-generate report
        generate_report(results, args.format or 'html')
    
    return results


def cmd_cve(args):
    """Execute CVE vulnerability scan"""
    print_module_header("CVE SCANNER")
    
    scanner = CVEScanner()
    
    results = {
        'target': args.service,
        'version': args.version,
        'timestamp': datetime.now().isoformat(),
        'report_type': 'CVE Scan'
    }
    
    logger.info(f"Scanning {args.service} {args.version} for CVEs...")
    cves = scanner.scan_service(args.service, args.version)
    
    if cves:
        print(f"\n{Colors.RED}Found {len(cves)} CVEs:{Colors.END}\n")
        for cve in cves:
            severity_color = {
                'CRITICAL': Colors.RED,
                'HIGH': Colors.BOLD + Colors.RED,
                'MEDIUM': Colors.YELLOW,
                'LOW': Colors.CYAN,
                'UNKNOWN': Colors.GRAY
            }.get(cve.severity, Colors.END)
            
            print(f"{severity_color}{cve.cve_id}{Colors.END} ({cve.severity} - {cve.cvss_score}/10.0)")
            print(f"  {cve.description[:150]}...")
            print()
    else:
        print(f"\n{Colors.GREEN}✓ No CVEs found{Colors.END}\n")
    
    results['cves'] = [cve.to_dict() for cve in cves]
    
    # Save report if requested
    if args.output:
        generate_report(results, args.format, args.output)
    
    return results


def cmd_osint(args):
    """Execute OSINT intelligence gathering"""
    print_module_header("OSINT INTELLIGENCE GATHERING")
    
    # Load API keys from config
    api_keys = _load_api_keys()
    
    collector = OSINTCollector(
        shodan_key=api_keys.get('shodan_api_key'),
        vt_key=api_keys.get('virustotal_api_key')
    )
    
    logger.info(f"Gathering intelligence for {args.target}...")
    
    results = collector.gather_intelligence(
        args.target,
        enable_shodan=args.osint_all or args.shodan,
        enable_vt=args.osint_all or args.virustotal,
        enable_geo=not args.skip_geo
    )
    
    # Print results
    print(f"\n{Colors.BOLD}IP Address:{Colors.END} {results.get('ip_address', 'N/A')}\n")
    
    if 'geolocation' in results and results['geolocation']:
        geo = results['geolocation']
        if not geo.get('error'):
            print(f"{Colors.BOLD}Geolocation:{Colors.END}")
            print(f"  Location: {geo.get('city')}, {geo.get('country')}")
            print(f"  Coordinates: {geo.get('latitude')}, {geo.get('longitude')}")
            print(f"  ISP: {geo.get('isp')}")
            print()
    
    if 'shodan' in results and results['shodan']:
        shodan = results['shodan']
        if not shodan.get('error'):
            print(f"{Colors.BOLD}Shodan Data:{Colors.END}")
            print(f"  Organization: {shodan.get('organization')}")
            print(f"  ASN: {shodan.get('asn')}")
            print(f"  Open Ports: {', '.join(map(str, shodan.get('ports', [])))}")
            print()
        else:
            print(f"{Colors.YELLOW}Shodan: {shodan['error']}{Colors.END}\n")
    
    if 'virustotal' in results and results['virustotal']:
        vt = results['virustotal']
        if not vt.get('error'):
            print(f"{Colors.BOLD}VirusTotal:{Colors.END}")
            print(f"  Malicious: {vt.get('malicious', 0)}")
            print(f"  Suspicious: {vt.get('suspicious', 0)}")
            print(f"  Clean: {vt.get('clean', 0)}")
            print()
        else:
            print(f"{Colors.YELLOW}VirusTotal: {vt['error']}{Colors.END}\n")
    
    # Save report if requested
    if args.output:
        generate_report(results, args.format, args.output)
    
    return results


def _load_api_keys():
    """Load API keys from config file"""
    config_path = Path('config/api_keys.yaml')
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f) or {}
        except:
            return {}
    return {}


def main():
    """Main CLI entry point"""
    
    parser = argparse.ArgumentParser(
        description=f'{Colors.BOLD}{Colors.CYAN}SHINIGAMI-EYE (神死眼){Colors.END} - All-Seeing Cybersecurity Framework',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
{Colors.BOLD}Examples:{Colors.END}
  {Colors.CYAN}Port Scan:{Colors.END}
    shinigami-eye portscan -t 192.168.1.1 -s 1 -e 1000
    shinigami-eye portscan -t example.com --common
    
  {Colors.CYAN}Web Reconnaissance:{Colors.END}
    shinigami-eye webrecon -d example.com
    shinigami-eye webrecon -d example.com --discover-dirs
    
  {Colors.CYAN}SSL/TLS Analysis:{Colors.END}
    shinigami-eye ssl -H example.com
    shinigami-eye ssl -H example.com -p 8443
    
  {Colors.CYAN}DNS Enumeration:{Colors.END}
    shinigami-eye dns -d example.com
    
  {Colors.CYAN}Full Scan:{Colors.END}
    shinigami-eye full -t example.com -o report.html

{Colors.YELLOW}⚠️  Educational use only. Unauthorized scanning is illegal.{Colors.END}
"""
    )
    
    parser.add_argument('-v', '--version', action='version', version=f'SHINIGAMI-EYE {__version__}')
    parser.add_argument('--no-banner', action='store_true', help='Suppress banner')
    parser.add_argument('--no-disclaimer', action='store_true', help='Skip disclaimer (use with caution)')
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Port Scan Command
    port_parser = subparsers.add_parser('portscan', help='Port scanner')
    port_parser.add_argument('-t', '--target', required=True, help='Target IP or hostname')
    port_parser.add_argument('-p', '--port', type=int, help='Single port to scan')
    port_parser.add_argument('-s', '--start-port', type=int, help='Start port for range scan')
    port_parser.add_argument('-e', '--end-port', type=int, help='End port for range scan')
    port_parser.add_argument('--common', action='store_true', help='Scan common ports only')
    port_parser.add_argument('--no-banner', dest='no_banner', action='store_true', help='Skip banner grabbing')
    port_parser.add_argument('--timeout', type=float, default=1.0, help='Connection timeout (default: 1.0)')
    port_parser.add_argument('--threads', type=int, default=100, help='Number of threads (default: 100)')
    port_parser.add_argument('-o', '--output', help='Output file')
    port_parser.add_argument('-f', '--format', choices=['json', 'html', 'md'], default='json', help='Output format')
    
    # Web Recon Command
    web_parser = subparsers.add_parser('webrecon', help='Web reconnaissance')
    web_parser.add_argument('-d', '--domain', required=True, help='Target domain')
    web_parser.add_argument('--skip-subdomains', action='store_true', help='Skip subdomain enumeration')
    web_parser.add_argument('--skip-tech', action='store_true', help='Skip technology detection')
    web_parser.add_argument('--skip-security', action='store_true', help='Skip security headers check')
    web_parser.add_argument('--discover-dirs', action='store_true', help='Discover directories')
    web_parser.add_argument('--timeout', type=int, default=5, help='Request timeout (default: 5)')
    web_parser.add_argument('--threads', type=int, default=20, help='Number of threads (default: 20)')
    web_parser.add_argument('-o', '--output', help='Output file')
    web_parser.add_argument('-f', '--format', choices=['json', 'html', 'md'], default='json', help='Output format')
    
    # SSL Analyzer Command
    ssl_parser = subparsers.add_parser('ssl', help='SSL/TLS analysis')
    ssl_parser.add_argument('-H', '--hostname', required=True, help='Target hostname')
    ssl_parser.add_argument('-p', '--port', type=int, default=443, help='SSL port (default: 443)')
    ssl_parser.add_argument('--timeout', type=int, default=5, help='Connection timeout (default: 5)')
    ssl_parser.add_argument('-o', '--output', help='Output file')
    ssl_parser.add_argument('-f', '--format', choices=['json', 'html', 'md'], default='json', help='Output format')
    
    # DNS Enumerator Command
    dns_parser = subparsers.add_parser('dns', help='DNS enumeration')
    dns_parser.add_argument('-d', '--domain', required=True, help='Target domain')
    dns_parser.add_argument('--timeout', type=int, default=5, help='Query timeout (default: 5)')
    dns_parser.add_argument('-o', '--output', help='Output file')
    dns_parser.add_argument('-f', '--format', choices=['json', 'html', 'md'], default='json', help='Output format')
    
    # CVE Scanner Command (v2.0)
    cve_parser = subparsers.add_parser('cve', help='CVE vulnerability scanner')
    cve_parser.add_argument('-s', '--service', required=True, help='Service name (e.g., Apache, OpenSSH)')
    cve_parser.add_argument('-v', '--version', required=True, help='Service version (e.g., 2.4.29)')
    cve_parser.add_argument('-o', '--output', help='Output file')
    cve_parser.add_argument('-f', '--format', choices=['json', 'html', 'md'], default='json', help='Output format')
    
    # OSINT Command (v2.0)
    osint_parser = subparsers.add_parser('osint', help='OSINT intelligence gathering')
    osint_parser.add_argument('-t', '--target', required=True, help='Target domain or IP')
    osint_parser.add_argument('--shodan', action='store_true', help='Query Shodan')
    osint_parser.add_argument('--virustotal', action='store_true', help='Query VirusTotal')
    osint_parser.add_argument('--osint-all', action='store_true', help='Query all OSINT sources')
    osint_parser.add_argument('--skip-geo', action='store_true', help='Skip geolocation lookup')
    osint_parser.add_argument('-o', '--output', help='Output file')
    osint_parser.add_argument('-f', '--format', choices=['json', 'html', 'md'], default='json', help='Output format')
    
    # Full Scan Command
    full_parser = subparsers.add_parser('full', help='Full scan (all modules)')
    full_parser.add_argument('-t', '--target', required=True, help='Target domain or IP')
    full_parser.add_argument('--timeout', type=int, default=5, help='Connection timeout (default: 5)')
    full_parser.add_argument('--threads', type=int, default=50, help='Number of threads (default: 50)')
    full_parser.add_argument('-o', '--output', help='Output file')
    full_parser.add_argument('-f', '--format', choices=['json', 'html', 'md'], default='html', help='Output format (default: html)')
    
    args = parser.parse_args()
    
    # Print banner
    if not args.no_banner:
        print_banner()
    
    # Show disclaimer
    if not args.no_disclaimer:
        print_disclaimer()
    
    # Execute command
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    try:
        if args.command == 'portscan':
            cmd_portscan(args)
        elif args.command == 'webrecon':
            cmd_webrecon(args)
        elif args.command == 'ssl':
            cmd_ssl(args)
        elif args.command == 'dns':
            cmd_dns(args)
        elif args.command == 'cve':  # v2.0
            cmd_cve(args)
        elif args.command == 'osint':  # v2.0
            cmd_osint(args)
        elif args.command == 'full':
            cmd_full(args)
        
        print(f"\n{Colors.BOLD}{Colors.GREEN}✓ Scan completed successfully!{Colors.END}\n")
        
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}⚠️  Scan interrupted by user{Colors.END}\n")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error during scan: {str(e)}")
        print(f"\n{Colors.RED}✗ Scan failed: {str(e)}{Colors.END}\n")
        sys.exit(1)


if __name__ == '__main__':
    main()
