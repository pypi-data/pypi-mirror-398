"""
Display utilities for CLI output
"""
from typing import Optional


class Colors:
    """ANSI color codes"""
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    RESET = '\033[0m'


def print_error(message: str):
    """Print error message in red"""
    print(f"{Colors.RED}✗ {message}{Colors.RESET}")


def print_success(message: str):
    """Print success message in green"""
    print(f"{Colors.GREEN}✓ {message}{Colors.RESET}")


def print_warning(message: str):
    """Print warning message in yellow"""
    print(f"{Colors.YELLOW}⚠ {message}{Colors.RESET}")


def print_info(message: str):
    """Print info message in blue"""
    print(f"{Colors.BLUE}ℹ {message}{Colors.RESET}")


def print_header(message: str):
    """Print header message"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{message}{Colors.RESET}\n")


def print_auth_error(reason: str, message: str, credits_remaining: Optional[int] = None, tier: Optional[str] = None):
    """Print formatted authorization error"""
    print_header("❌ Authorization Failed")
    
    if reason == "invalid_api_key":
        print_error("Invalid or expired API key")
        print_info("Get your API key at: https://rohkun.com/dashboard")
        print_info("Set it with: rohkun config --api-key YOUR_KEY")
        
    elif reason == "insufficient_credits":
        print_error(f"Insufficient credits (0 remaining)")
        print_info(f"Current plan: {tier or 'free'}")
        print_info("Upgrade at: https://rohkun.com/pricing")
        
    elif reason == "account_suspended":
        print_error("Your account has been suspended")
        print_info("Contact support: support@rohkun.com")
        
    else:
        print_error(message)


def print_scan_summary(
    endpoints_found: int,
    api_calls_found: int,
    connections_found: int,
    files_scanned: int,
    duration_seconds: float
):
    """Print scan summary"""
    print_header("📊 Scan Complete")
    print(f"  Files scanned:     {files_scanned}")
    print(f"  Endpoints found:   {endpoints_found}")
    print(f"  API calls found:   {api_calls_found}")
    print(f"  Connections found: {connections_found}")
    print(f"  Duration:          {duration_seconds:.2f}s")
    print()
