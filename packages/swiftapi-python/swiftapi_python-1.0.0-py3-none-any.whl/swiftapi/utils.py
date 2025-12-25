"""
SwiftAPI SDK Utilities - UX and Display
"""

import sys

try:
    from colorama import Fore, Style, init
    init(autoreset=True)
    COLORS_AVAILABLE = True
except ImportError:
    COLORS_AVAILABLE = False


# Color constants
class Colors:
    """Terminal color codes for SwiftAPI output."""

    if COLORS_AVAILABLE:
        RED = Fore.RED
        GREEN = Fore.GREEN
        YELLOW = Fore.YELLOW
        BLUE = Fore.BLUE
        MAGENTA = Fore.MAGENTA
        CYAN = Fore.CYAN
        WHITE = Fore.WHITE
        RESET = Style.RESET_ALL
        BOLD = Style.BRIGHT
    else:
        RED = GREEN = YELLOW = BLUE = MAGENTA = CYAN = WHITE = RESET = BOLD = ""


# Unicode symbols
class Symbols:
    """Unicode symbols for SwiftAPI output."""

    LOCK = "\U0001F512"        # Locked
    UNLOCK = "\U0001F513"      # Unlocked
    CHECK = "\u2713"           # Checkmark
    CROSS = "\u2717"           # X mark
    SHIELD = "\U0001F6E1"      # Shield
    KEY = "\U0001F511"         # Key
    WARNING = "\u26A0"         # Warning
    LIGHTNING = "\u26A1"       # Lightning bolt


def print_approved(action_type: str, intent: str):
    """Print approval message with green styling."""
    print(f"{Colors.GREEN}{Symbols.CHECK} APPROVED{Colors.RESET} [{action_type}] {intent}")


def print_denied(action_type: str, intent: str, reason: str = None):
    """Print denial message with red styling."""
    msg = f"{Colors.RED}{Symbols.LOCK} DENIED{Colors.RESET} [{action_type}] {intent}"
    if reason:
        msg += f"\n  {Colors.YELLOW}Reason: {reason}{Colors.RESET}"
    print(msg, file=sys.stderr)


def print_verified(jti: str):
    """Print verification success message."""
    print(f"{Colors.CYAN}{Symbols.SHIELD} VERIFIED{Colors.RESET} Attestation {jti[:16]}...")


def print_revoked(jti: str):
    """Print revocation message."""
    print(f"{Colors.RED}{Symbols.CROSS} REVOKED{Colors.RESET} Attestation {jti[:16]}...")


def print_error(message: str):
    """Print error message."""
    print(f"{Colors.RED}{Symbols.WARNING} ERROR{Colors.RESET} {message}", file=sys.stderr)


def print_info(message: str):
    """Print info message."""
    print(f"{Colors.BLUE}{Symbols.LIGHTNING} INFO{Colors.RESET} {message}")


def format_attestation(attestation: dict) -> str:
    """Format attestation for display."""
    lines = [
        f"{Colors.CYAN}Execution Attestation{Colors.RESET}",
        f"  JTI: {attestation.get('jti', 'N/A')}",
        f"  Expires: {attestation.get('expires_at', 'N/A')}",
        f"  Fingerprint: {attestation.get('action_fingerprint', 'N/A')[:32]}...",
        f"  Signed: {attestation.get('signing_mode', 'N/A')}",
    ]
    return "\n".join(lines)
