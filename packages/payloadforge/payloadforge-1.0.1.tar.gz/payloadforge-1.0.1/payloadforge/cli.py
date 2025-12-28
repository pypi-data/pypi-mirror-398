"""
PayloadForge CLI - Command Line Interface

⚠️  ETHICAL USE ONLY ⚠️

This module provides the command-line interface for PayloadForge.
All commands generate payload strings for authorized testing only.

Usage:
    payloadforge --xss basic
    payloadforge --sqli error mysql
    payloadforge --ssti jinja2
    payloadforge --cmd linux --encode=unicode
    payloadforge encode --url "<script>alert()</script>"
"""

import sys
import click
from typing import Optional

from payloadforge import __version__
from payloadforge.disclaimer import (
    require_disclaimer,
    show_disclaimer,
    is_disclaimer_accepted,
    COLORS,
)
from payloadforge.logger import enable_logging, is_logging_enabled


def print_banner():
    """Print the PayloadForge banner."""
    banner = f"""
{COLORS['CYAN']}╔═══════════════════════════════════════════════════════════════╗
║     {COLORS['BOLD']}PayloadForge v{__version__}{COLORS['CYAN']}                                      ║
║     {COLORS['YELLOW']}Ethical Cybersecurity Payload Generator{COLORS['CYAN']}                      ║
╚═══════════════════════════════════════════════════════════════╝{COLORS['RESET']}
"""
    click.echo(banner)


def print_payloads(payloads: list, title: str):
    """Print payloads in a formatted way."""
    click.echo(f"\n{COLORS['GREEN']}═══ {title} ═══{COLORS['RESET']}\n")
    for i, payload in enumerate(payloads, 1):
        click.echo(f"{COLORS['YELLOW']}[{i:02d}]{COLORS['RESET']} {payload}")
    click.echo(f"\n{COLORS['CYAN']}Total: {len(payloads)} payloads{COLORS['RESET']}")


@click.group(invoke_without_command=True)
@click.option("--version", "-v", is_flag=True, help="Show version")
@click.option("--xss", type=click.Choice(["basic", "dom", "event", "polyglot", "all"]),
              help="Generate XSS payloads")
@click.option("--sqli", nargs=2, type=str, metavar="TYPE DB",
              help="Generate SQLi payloads (error|time|union|boolean) (mysql|mssql|postgres)")
@click.option("--ssti", type=click.Choice(["jinja2", "twig", "smarty", "velocity", "all"]),
              help="Generate SSTI payloads")
@click.option("--cmd", type=click.Choice(["linux", "windows"]),
              help="Generate command injection payloads")
@click.option("--encode", "-e", type=click.Choice(["url", "html", "unicode", "base64"]),
              help="Apply encoding to output")
@click.option("--count", "-n", type=int, default=None,
              help="Limit number of payloads")
@click.option("--log", is_flag=True, help="Enable action logging")
@click.option("--disclaimer", is_flag=True, help="Show disclaimer")
@click.pass_context
def main(ctx, version, xss, sqli, ssti, cmd, encode, count, log, disclaimer):
    """
    PayloadForge - Ethical Cybersecurity Payload Generator
    
    Generate safe proof-of-concept payloads for authorized security testing.
    
    \b
    Examples:
        payloadforge --xss basic
        payloadforge --sqli error mysql
        payloadforge --ssti jinja2
        payloadforge --cmd linux --encode=unicode
        payloadforge encode --url "<script>alert()</script>"
    """
    # Show disclaimer on first run
    require_disclaimer()
    
    if version:
        click.echo(f"PayloadForge v{__version__}")
        return
    
    if disclaimer:
        show_disclaimer()
        return
    
    if log:
        enable_logging()
        click.echo(f"{COLORS['GREEN']}✓ Logging enabled{COLORS['RESET']}")
    
    # Print banner for main commands
    if xss or sqli or ssti or cmd:
        print_banner()
    
    # Handle XSS payloads
    if xss:
        from payloadforge.generators.xss import XSSGenerator
        
        if xss == "basic":
            payloads = XSSGenerator.generate_basic(count)
            title = "Basic XSS Payloads"
        elif xss == "dom":
            payloads = XSSGenerator.generate_dom(count)
            title = "DOM-based XSS Payloads"
        elif xss == "event":
            payloads = XSSGenerator.generate_event_handlers(count)
            title = "Event Handler XSS Payloads"
        elif xss == "polyglot":
            payloads = XSSGenerator.generate_polyglot(count)
            title = "Polyglot XSS Payloads"
        else:  # all
            all_payloads = XSSGenerator.generate_all()
            for category, plist in all_payloads.items():
                print_payloads(plist[:count] if count else plist, f"{category.upper()} XSS")
            return
        
        if encode:
            payloads = XSSGenerator.with_encoding(payloads, encode)
            title += f" ({encode.upper()} encoded)"
        
        print_payloads(payloads, title)
        return
    
    # Handle SQLi payloads
    if sqli:
        attack_type, db_type = sqli
        from payloadforge.generators.sqli import SQLiGenerator
        
        if attack_type == "error":
            payloads = SQLiGenerator.generate_error_based(db_type, count)
            title = f"Error-based SQLi ({db_type.upper()})"
        elif attack_type == "time":
            payloads = SQLiGenerator.generate_time_based(db_type, count)
            title = f"Time-based Blind SQLi ({db_type.upper()})"
        elif attack_type == "union":
            payloads = SQLiGenerator.generate_union_based(db_type, count)
            title = f"Union-based SQLi ({db_type.upper()})"
        elif attack_type == "boolean":
            payloads = SQLiGenerator.generate_boolean_based(db_type, count)
            title = f"Boolean-based Blind SQLi ({db_type.upper()})"
        else:
            click.echo(f"{COLORS['RED']}Invalid attack type: {attack_type}{COLORS['RESET']}")
            click.echo("Valid types: error, time, union, boolean")
            return
        
        print_payloads(payloads, title)
        return
    
    # Handle SSTI payloads
    if ssti:
        from payloadforge.generators.ssti import SSTIGenerator
        
        if ssti == "jinja2":
            payloads = SSTIGenerator.generate_jinja2(count)
            title = "Jinja2 SSTI Payloads"
        elif ssti == "twig":
            payloads = SSTIGenerator.generate_twig(count)
            title = "Twig SSTI Payloads"
        elif ssti == "smarty":
            payloads = SSTIGenerator.generate_smarty(count)
            title = "Smarty SSTI Payloads"
        elif ssti == "velocity":
            payloads = SSTIGenerator.generate_velocity(count)
            title = "Velocity SSTI Payloads"
        else:  # all
            all_payloads = SSTIGenerator.generate_all()
            for engine, plist in all_payloads.items():
                print_payloads(plist[:count] if count else plist, f"{engine.upper()} SSTI")
            return
        
        print_payloads(payloads, title)
        return
    
    # Handle Command Injection payloads
    if cmd:
        from payloadforge.generators.cmdi import CMDiGenerator
        
        if cmd == "linux":
            payloads = CMDiGenerator.generate_linux(count)
            title = "Linux Command Injection Payloads"
        else:  # windows
            payloads = CMDiGenerator.generate_windows(count)
            title = "Windows Command Injection Payloads"
        
        if encode:
            payloads = CMDiGenerator.with_encoding(payloads, encode)
            title += f" ({encode.upper()} encoded)"
        
        print_payloads(payloads, title)
        return
    
    # If no command specified, show help
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@main.command()
@click.option("--url", "-u", is_flag=True, help="URL encode")
@click.option("--html", "-h", is_flag=True, help="HTML entity encode")
@click.option("--unicode", "-U", is_flag=True, help="Unicode escape encode")
@click.option("--base64", "-b", is_flag=True, help="Base64 encode")
@click.option("--decode", "-d", is_flag=True, help="Decode instead of encode")
@click.argument("text")
def encode(url, html, unicode, base64, decode, text):
    """
    Encode or decode text.
    
    \b
    Examples:
        payloadforge encode --url "<script>alert()</script>"
        payloadforge encode --html "<img src=x>"
        payloadforge encode --base64 "whoami"
        payloadforge encode --url --decode "%3Cscript%3E"
    """
    require_disclaimer()
    
    from payloadforge.encoders import url as url_enc, html as html_enc
    from payloadforge.encoders import unicode as unicode_enc, base64_enc
    
    result = text
    
    if url:
        if decode:
            result = url_enc.decode(result)
        else:
            result = url_enc.encode(result)
    
    if html:
        if decode:
            result = html_enc.decode(result)
        else:
            result = html_enc.encode(result)
    
    if unicode:
        if decode:
            result = unicode_enc.decode_escape(result)
        else:
            result = unicode_enc.encode_escape(result)
    
    if base64:
        if decode:
            result = base64_enc.decode(result)
        else:
            result = base64_enc.encode(result)
    
    click.echo(f"\n{COLORS['GREEN']}Result:{COLORS['RESET']}\n{result}\n")


@main.command()
@click.option("--type", "-t", "payload_type", 
              type=click.Choice(["xss", "sqli", "ssti", "cmdi"]),
              help="Payload type for wizard")
def wizard(payload_type):
    """
    Interactive payload building wizard.
    
    Step-by-step guided payload generation.
    """
    require_disclaimer()
    print_banner()
    
    click.echo(f"{COLORS['CYAN']}═══ PayloadForge Wizard ═══{COLORS['RESET']}\n")
    
    if not payload_type:
        click.echo("Select payload type:")
        click.echo("  1. XSS (Cross-Site Scripting)")
        click.echo("  2. SQLi (SQL Injection)")
        click.echo("  3. SSTI (Server-Side Template Injection)")
        click.echo("  4. CMDi (Command Injection)")
        
        choice = click.prompt("Enter choice", type=int, default=1)
        payload_type = ["xss", "sqli", "ssti", "cmdi"][choice - 1]
    
    if payload_type == "xss":
        _xss_wizard()
    elif payload_type == "sqli":
        _sqli_wizard()
    elif payload_type == "ssti":
        _ssti_wizard()
    elif payload_type == "cmdi":
        _cmdi_wizard()


def _xss_wizard():
    """XSS payload wizard."""
    from payloadforge.generators.xss import XSSGenerator
    
    click.echo("\nSelect XSS type:")
    click.echo("  1. Basic Reflection")
    click.echo("  2. DOM-based")
    click.echo("  3. Event Handlers")
    click.echo("  4. Polyglot")
    
    choice = click.prompt("Enter choice", type=int, default=1)
    
    if choice == 1:
        payloads = XSSGenerator.generate_basic()
    elif choice == 2:
        payloads = XSSGenerator.generate_dom()
    elif choice == 3:
        payloads = XSSGenerator.generate_event_handlers()
    else:
        payloads = XSSGenerator.generate_polyglot()
    
    # Ask about encoding
    if click.confirm("Apply encoding?"):
        click.echo("\nSelect encoding:")
        click.echo("  1. URL")
        click.echo("  2. HTML entities")
        click.echo("  3. Unicode")
        
        enc_choice = click.prompt("Enter choice", type=int, default=1)
        encoding = ["url", "html", "unicode"][enc_choice - 1]
        payloads = XSSGenerator.with_encoding(payloads, encoding)
    
    print_payloads(payloads, "Generated XSS Payloads")


def _sqli_wizard():
    """SQLi payload wizard."""
    from payloadforge.generators.sqli import SQLiGenerator
    
    click.echo("\nSelect database type:")
    click.echo("  1. MySQL")
    click.echo("  2. MSSQL")
    click.echo("  3. PostgreSQL")
    
    db_choice = click.prompt("Enter choice", type=int, default=1)
    db_type = ["mysql", "mssql", "postgres"][db_choice - 1]
    
    click.echo("\nSelect attack type:")
    click.echo("  1. Error-based")
    click.echo("  2. Time-based Blind")
    click.echo("  3. Union-based")
    click.echo("  4. Boolean-based Blind")
    
    attack_choice = click.prompt("Enter choice", type=int, default=1)
    
    if attack_choice == 1:
        payloads = SQLiGenerator.generate_error_based(db_type)
        title = "Error-based SQLi"
    elif attack_choice == 2:
        payloads = SQLiGenerator.generate_time_based(db_type)
        title = "Time-based Blind SQLi"
    elif attack_choice == 3:
        payloads = SQLiGenerator.generate_union_based(db_type)
        title = "Union-based SQLi"
    else:
        payloads = SQLiGenerator.generate_boolean_based(db_type)
        title = "Boolean-based Blind SQLi"
    
    # Ask about obfuscation
    if click.confirm("Apply obfuscation?"):
        click.echo("\nSelect obfuscation method:")
        click.echo("  1. Case flipping")
        click.echo("  2. Whitespace bypass")
        click.echo("  3. Inline comments")
        
        obf_choice = click.prompt("Enter choice", type=int, default=1)
        method = ["case", "whitespace", "comment"][obf_choice - 1]
        payloads = SQLiGenerator.obfuscate(payloads, method)
    
    print_payloads(payloads, f"{title} ({db_type.upper()})")


def _ssti_wizard():
    """SSTI payload wizard."""
    from payloadforge.generators.ssti import SSTIGenerator
    
    click.echo("\nSelect template engine:")
    click.echo("  1. Jinja2 (Python)")
    click.echo("  2. Twig (PHP)")
    click.echo("  3. Smarty (PHP)")
    click.echo("  4. Velocity (Java)")
    
    choice = click.prompt("Enter choice", type=int, default=1)
    
    safe_only = click.confirm("Detection payloads only (safer)?")
    
    if choice == 1:
        payloads = SSTIGenerator.generate_jinja2(safe_only=safe_only)
        title = "Jinja2 SSTI"
    elif choice == 2:
        payloads = SSTIGenerator.generate_twig(safe_only=safe_only)
        title = "Twig SSTI"
    elif choice == 3:
        payloads = SSTIGenerator.generate_smarty(safe_only=safe_only)
        title = "Smarty SSTI"
    else:
        payloads = SSTIGenerator.generate_velocity(safe_only=safe_only)
        title = "Velocity SSTI"
    
    print_payloads(payloads, title)


def _cmdi_wizard():
    """Command injection payload wizard."""
    from payloadforge.generators.cmdi import CMDiGenerator
    
    click.echo("\nSelect target OS:")
    click.echo("  1. Linux")
    click.echo("  2. Windows")
    
    os_choice = click.prompt("Enter choice", type=int, default=1)
    os_type = "linux" if os_choice == 1 else "windows"
    
    click.echo("\nSelect payload type:")
    click.echo("  1. Basic injection")
    click.echo("  2. Blind (time-based)")
    click.echo("  3. Out-of-band")
    
    type_choice = click.prompt("Enter choice", type=int, default=1)
    
    if type_choice == 1:
        if os_type == "linux":
            payloads = CMDiGenerator.generate_linux()
        else:
            payloads = CMDiGenerator.generate_windows()
        title = f"Basic {os_type.capitalize()} CMDi"
    elif type_choice == 2:
        payloads = CMDiGenerator.generate_blind(os_type)
        title = f"Blind {os_type.capitalize()} CMDi"
    else:
        collaborator = click.prompt("Enter collaborator URL", default="your-collaborator.com")
        payloads = CMDiGenerator.generate_oob(os_type, collaborator)
        title = f"OOB {os_type.capitalize()} CMDi"
    
    # Ask about encoding
    if click.confirm("Apply encoding?"):
        click.echo("\nSelect encoding:")
        click.echo("  1. URL")
        click.echo("  2. Base64")
        click.echo("  3. Unicode")
        
        enc_choice = click.prompt("Enter choice", type=int, default=1)
        encoding = ["url", "base64", "unicode"][enc_choice - 1]
        payloads = CMDiGenerator.with_encoding(payloads, encoding)
    
    print_payloads(payloads, title)


@main.command()
def list_all():
    """List all available payload categories."""
    require_disclaimer()
    print_banner()
    
    click.echo(f"{COLORS['GREEN']}═══ Available Payload Categories ═══{COLORS['RESET']}\n")
    
    categories = {
        "XSS (Cross-Site Scripting)": [
            "basic - Basic reflection XSS",
            "dom - DOM-based XSS",
            "event - Event handler XSS",
            "polyglot - Works in multiple contexts",
        ],
        "SQLi (SQL Injection)": [
            "error - Error-based injection",
            "time - Time-based blind",
            "union - Union-based extraction",
            "boolean - Boolean-based blind",
        ],
        "SSTI (Server-Side Template Injection)": [
            "jinja2 - Python Jinja2",
            "twig - PHP Twig",
            "smarty - PHP Smarty",
            "velocity - Java Velocity",
        ],
        "CMDi (Command Injection)": [
            "linux - Linux/Unix commands",
            "windows - Windows commands",
            "blind - Time-based blind",
            "oob - Out-of-band detection",
        ],
        "Encoding Options": [
            "url - URL encoding",
            "html - HTML entities",
            "unicode - Unicode escapes",
            "base64 - Base64 encoding",
        ],
    }
    
    for category, items in categories.items():
        click.echo(f"{COLORS['CYAN']}{category}:{COLORS['RESET']}")
        for item in items:
            click.echo(f"  • {item}")
        click.echo()


if __name__ == "__main__":
    main()
