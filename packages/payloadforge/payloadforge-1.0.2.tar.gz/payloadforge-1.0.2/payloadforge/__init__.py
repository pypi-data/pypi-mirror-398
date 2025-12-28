"""
PayloadForge - Ethical Cybersecurity Payload Generation Toolkit

⚠️  ETHICAL USE ONLY ⚠️

This toolkit is designed for:
- Security professionals conducting authorized penetration testing
- Students learning about web application security
- Researchers studying vulnerability patterns

DO NOT use this tool for:
- Unauthorized testing of systems you don't own
- Malicious attacks or exploitation
- Any illegal activities

By using this software, you agree to use it responsibly and ethically.
Always obtain proper authorization before testing any systems.
"""

__version__ = "1.0.2"
__author__ = "Bala Kavi"
__license__ = "MIT"

from payloadforge.disclaimer import show_disclaimer, check_first_run

# Show disclaimer on first import if running interactively
import sys
if hasattr(sys, 'ps1') or 'pytest' not in sys.modules:
    check_first_run()

__all__ = [
    "__version__",
    "__author__",
    "__license__",
    "show_disclaimer",
]
