"""
ASCII Art Module - Death Note Inspired
Monochrome visual effects for SHINIGAMI-EYE framework
"""
import time
import sys
from typing import Optional

class Colors:
    """ANSI color codes for terminal output"""
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    MAGENTA = '\033[95m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'
    PURPLE = '\033[35m'
    DARK_RED = '\033[31m'
    BLACK = '\033[30m'
    GRAY = '\033[90m'

DEATH_NOTE_BANNER = """
        ██████╗ ██╗  ██╗██╗███╗   ██╗██╗ ██████╗  █████╗ ███╗   ███╗██╗    ███████╗██╗   ██╗███████╗
       ██╔════╝ ██║  ██║██║████╗  ██║██║██╔════╝ ██╔══██╗████╗ ████║██║    ██╔════╝╚██╗ ██╔╝██╔════╝
       ███████╗ ███████║██║██╔██╗ ██║██║██║  ███╗███████║██╔████╔██║██║    █████╗   ╚████╔╝ █████╗  
       ╚════██║ ██╔══██║██║██║╚██╗██║██║██║   ██║██╔══██║██║╚██╔╝██║██║    ██╔══╝    ╚██╔╝  ██╔══╝  
       ███████║ ██║  ██║██║██║ ╚████║██║╚██████╔╝██║  ██║██║ ╚═╝ ██║██║    ███████╗   ██║   ███████╗
       ╚══════╝ ╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝╚═╝ ╚═════╝ ╚═╝  ╚═╝╚═╝     ╚═╝╚═╝    ╚══════╝   ╚═╝   ╚══════╝

                                       神 死 眼 - The All-Seeing Eye
                                            
                    
                              ╔════════════════════════════════════════════╗
                              ║                                            ║
                              ║  ██████╗ ███████╗ █████╗ ████████╗██╗  ██╗  ║
                              ║  ██╔══██╗██╔════╝██╔══██╗╚══██╔══╝██║  ██║  ║
                              ║  ██║  ██║█████╗  ███████║   ██║   ███████║  ║
                              ║  ██║  ██║██╔══╝  ██╔══██║   ██║   ██╔══██║  ║
                              ║  ██████╔╝███████╗██║  ██║   ██║   ██║  ██║  ║
                              ║  ╚═════╝ ╚══════╝╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝  ║
                              ║                                            ║
                              ║  ███╗   ██╗ ██████╗ ████████╗███████╗      ║
                              ║  ████╗  ██║██╔═══██╗╚══██╔══╝██╔════╝      ║
                              ║  ██╔██╗ ██║██║   ██║   ██║   █████╗        ║
                              ║  ██║╚██╗██║██║   ██║   ██║   ██╔══╝        ║
                              ║  ██║ ╚████║╚██████╔╝   ██║   ███████╗      ║
                              ║  ╚═╝  ╚═══╝ ╚═════╝    ╚═╝   ╚══════╝      ║
                              ║                                            ║
                              ║  ────────────────────────────────────────  ║
                              ║                                            ║
                              ║  How to use:                             ║
                              ║                                            ║
                              ║  • Write target's IP/domain in this book ║
                              ║  • Their network secrets will be revealed║
                              ║  • All ports, services, and vulns exposed║
                              ║                                            ║
                              ║  ────────────────────────────────────────  ║
                              ║                                            ║
                              ║  Target: ____________________________      ║
                              ║                                            ║
                              ║  Method: [ ] Port Scan  [ ] Web Recon   ║
                              ║          [ ] SSL Check  [ ] DNS Enum    ║
                              ║                                            ║
                              ╚════════════════════════════════════════════╝
                              
                        [ Network Reconnaissance & Security Intelligence Framework ]
                                    Version 1.0.0 - "Death Note Edition"
                                          Educational Use Only
"""

def print_banner():
    """Print the main SHINIGAMI-EYE banner"""
    print(DEATH_NOTE_BANNER)

def animate_text(text: str, delay: float = 0.03):
    """Animate text character by character"""
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    print()

def print_status(message: str, status: str = "info"):
    """Print formatted status message"""
    symbols = {
        "success": "[✓]",
        "error": "[✗]",
        "warning": "[!]",
        "info": "[i]",
        "scan": "[◉]"
    }
    symbol = symbols.get(status, symbols["info"])
    print(f"{symbol} {message}")

def print_module_header(module_name: str):
    """Print module header"""
    print(f"\n{'='*70}")
    print(f"  {module_name}")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    print_banner()
    time.sleep(1)
    animate_text("Opening the Death Note...", 0.04)
    time.sleep(0.5)
    print_status("Network scanner loaded", "success")
    print_status("Vulnerability database ready", "success")
    print_status("Intelligence modules active", "success")
    print_status("All systems operational", "success")
    print()
    print("Remember: Those who use this tool must follow the rules...")
    print("Rule I: Only scan systems you own or have permission to test")
    print("Rule II: Unauthorized access is illegal and punishable by law")
