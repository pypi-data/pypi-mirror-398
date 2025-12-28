"""
PayloadForge Disclaimer Module

⚠️  ETHICAL USE ONLY ⚠️

This module handles the ethical use disclaimer and first-run banner.
All users must acknowledge the disclaimer before using the tool.
"""

import os
from pathlib import Path
from typing import Optional

# ANSI color codes
COLORS = {
    "RED": "\033[91m",
    "YELLOW": "\033[93m",
    "GREEN": "\033[92m",
    "CYAN": "\033[96m",
    "BOLD": "\033[1m",
    "RESET": "\033[0m",
}

DISCLAIMER_BANNER = f"""
{COLORS['RED']}╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║  {COLORS['BOLD']}██████╗  █████╗ ██╗   ██╗██╗      ██████╗  █████╗ ██████╗ ███████╗ ██████╗ ██████╗ ███████╗{COLORS['RED']}  ║
║  {COLORS['BOLD']}██╔══██╗██╔══██╗╚██╗ ██╔╝██║     ██╔═══██╗██╔══██╗██╔══██╗██╔════╝██╔═══██╗██╔══██╗██╔════╝{COLORS['RED']}  ║
║  {COLORS['BOLD']}██████╔╝███████║ ╚████╔╝ ██║     ██║   ██║███████║██║  ██║█████╗  ██║   ██║██████╔╝██║  ███╗{COLORS['RED']} ║
║  {COLORS['BOLD']}██╔═══╝ ██╔══██║  ╚██╔╝  ██║     ██║   ██║██╔══██║██║  ██║██╔══╝  ██║   ██║██╔══██╗██║   ██║{COLORS['RED']} ║
║  {COLORS['BOLD']}██║     ██║  ██║   ██║   ███████╗╚██████╔╝██║  ██║██████╔╝██║     ╚██████╔╝██║  ██║╚██████╔╝{COLORS['RED']} ║
║  {COLORS['BOLD']}╚═╝     ╚═╝  ╚═╝   ╚═╝   ╚══════╝ ╚═════╝ ╚═╝  ╚═╝╚═════╝ ╚═╝      ╚═════╝ ╚═╝  ╚═╝ ╚═════╝{COLORS['RED']}  ║
║                                                                              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  {COLORS['YELLOW']}⚠️  ETHICAL USE DISCLAIMER ⚠️{COLORS['RED']}                                             ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  {COLORS['CYAN']}This toolkit is designed EXCLUSIVELY for:{COLORS['RED']}                                ║
║  {COLORS['GREEN']}✓{COLORS['RED']} Authorized penetration testing with written permission               ║
║  {COLORS['GREEN']}✓{COLORS['RED']} Educational purposes and security research                           ║
║  {COLORS['GREEN']}✓{COLORS['RED']} Capture The Flag (CTF) competitions                                  ║
║  {COLORS['GREEN']}✓{COLORS['RED']} Testing your own systems and applications                            ║
║                                                                              ║
║  {COLORS['YELLOW']}⛔ PROHIBITED USES:{COLORS['RED']}                                                       ║
║  {COLORS['RED']}✗ Unauthorized access or testing of systems you don't own              ║
║  {COLORS['RED']}✗ Malicious exploitation or attacks                                    ║
║  {COLORS['RED']}✗ Any illegal activities                                               ║
║                                                                              ║
║  {COLORS['CYAN']}By continuing, you confirm that you:{COLORS['RED']}                                     ║
║  • Have authorization for any testing activities                             ║
║  • Accept full responsibility for your actions                               ║
║  • Will use this tool ethically and legally                                  ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝{COLORS['RESET']}
"""

COMPACT_DISCLAIMER = f"""
{COLORS['YELLOW']}⚠️  PayloadForge - For Ethical Use Only{COLORS['RESET']}
{COLORS['CYAN']}Ensure you have authorization before testing any systems.{COLORS['RESET']}
"""


def get_config_dir() -> Path:
    """Get the configuration directory path."""
    if os.name == "nt":  # Windows
        config_dir = Path(os.environ.get("APPDATA", Path.home())) / ".payloadforge"
    else:  # Linux/macOS
        config_dir = Path.home() / ".payloadforge"
    return config_dir


def get_disclaimer_file() -> Path:
    """Get the path to the disclaimer acknowledgment file."""
    return get_config_dir() / ".disclaimer_accepted"


def is_disclaimer_accepted() -> bool:
    """Check if the user has previously accepted the disclaimer."""
    return get_disclaimer_file().exists()


def accept_disclaimer() -> None:
    """Mark the disclaimer as accepted."""
    config_dir = get_config_dir()
    config_dir.mkdir(parents=True, exist_ok=True)
    disclaimer_file = get_disclaimer_file()
    disclaimer_file.write_text("ACCEPTED\n")


def show_disclaimer(compact: bool = False) -> None:
    """
    Display the ethical use disclaimer.
    
    Args:
        compact: If True, show a compact version of the disclaimer.
    """
    if compact:
        print(COMPACT_DISCLAIMER)
    else:
        print(DISCLAIMER_BANNER)


def check_first_run(force: bool = False) -> bool:
    """
    Check if this is the first run and show disclaimer if needed.
    
    Args:
        force: If True, always show the disclaimer.
        
    Returns:
        True if disclaimer was shown and accepted, False otherwise.
    """
    if force or not is_disclaimer_accepted():
        show_disclaimer()
        
        # In non-interactive mode, just show the banner
        try:
            response = input(f"\n{COLORS['YELLOW']}Do you accept these terms? (yes/no): {COLORS['RESET']}")
            if response.lower() in ("yes", "y"):
                accept_disclaimer()
                print(f"\n{COLORS['GREEN']}✓ Terms accepted. Welcome to PayloadForge!{COLORS['RESET']}\n")
                return True
            else:
                print(f"\n{COLORS['RED']}✗ You must accept the terms to use PayloadForge.{COLORS['RESET']}\n")
                return False
        except (EOFError, KeyboardInterrupt):
            # Non-interactive mode - show banner only
            return True
    
    return True


def require_disclaimer() -> None:
    """Decorator helper to ensure disclaimer is accepted before proceeding."""
    if not is_disclaimer_accepted():
        if not check_first_run():
            raise SystemExit(1)
