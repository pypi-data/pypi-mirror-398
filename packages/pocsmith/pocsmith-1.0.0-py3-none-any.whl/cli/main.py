#!/usr/bin/env python3
"""
PoCSmith CLI - Command-line interface for AI-powered exploit generation
"""

import click
import sys
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from parsers.cve_parser import CVEParser
from generators.poc_generator import PoCGenerator
from generators.shellcode_generator import ShellcodeGenerator
from formatters.output_formatter import OutputFormatter
from core.config import ETHICAL_WARNING, OUTPUT_DIR


@click.group()
@click.version_option(version='1.0.0')
def cli():
    """PoCSmith - AI-Powered Security Research Tool"""
    click.echo(click.style("PoCSmith v1.0", fg='cyan', bold=True))
    click.echo()


@cli.command()
@click.argument('cve_id')
@click.option('--output', '-o', help='Save to file')
@click.option('--no-cache', is_flag=True, help='Skip local cache')
def cve(cve_id, output, no_cache):
    """Generate PoC exploit from CVE ID"""
    
    click.echo(f"[*] Fetching {cve_id}...")
    
    # Parse CVE
    parser = CVEParser()
    cve_data = parser.fetch_cve(cve_id, use_cache=not no_cache)
    
    if not cve_data:
        click.echo(click.style(f"[!] CVE not found: {cve_id}", fg='red'))
        return
    
    # Display CVE info
    click.echo(f"[+] {cve_data.description[:100]}...")
    if cve_data.cvss_score:
        click.echo(f"[+] CVSS: {cve_data.cvss_score} ({cve_data.cvss_severity})")
    
    click.echo("[*] Generating exploit...")
    
    # Generate exploit
    generator = PoCGenerator()
    exploit = generator.generate_from_cve(
        cve_id=cve_data.cve_id,
        cve_description=cve_data.description,
        cvss_score=cve_data.cvss_score,
        affected_software=cve_data.affected_software
    )
    
    # Format output
    formatter = OutputFormatter()
    cleaned = formatter.clean(exploit)
    final = formatter.add_header(cleaned, f"Exploit for {cve_id}", tool_name="PoCSmith")
    
    # Output
    if output:
        filepath = formatter.to_file(final, output)
        click.echo(click.style(f"[+] Saved to: {filepath}", fg='green'))
    else:
        click.echo("\n" + "="*60)
        click.echo(final)
        click.echo("="*60)


@cli.command()
@click.option('--vuln', required=True, help='Vulnerability type')
@click.option('--target', help='Target software/version')
@click.option('--details', help='Additional details')
@click.option('--output', '-o', help='Save to file')
def generate(vuln, target, details, output):
    """Generate PoC from vulnerability description"""
    
    click.echo(f"[*] Generating exploit for: {vuln}")
    if target:
        click.echo(f"[*] Target: {target}")
    
    # Generate
    generator = PoCGenerator()
    exploit = generator.generate_from_description(vuln, target, details)
    
    # Format
    formatter = OutputFormatter()
    cleaned = formatter.clean(exploit)
    final = formatter.add_header(cleaned, f"Exploit for {vuln}", tool_name="PoCSmith")
    
    # Output
    if output:
        filepath = formatter.to_file(final, output)
        click.echo(click.style(f"[+] Saved to: {filepath}", fg='green'))
    else:
        click.echo("\n" + "="*60)
        click.echo(final)
        click.echo("="*60)


@cli.command()
@click.option('--platform', required=True, 
              type=click.Choice(['linux_x86', 'linux_x64', 'windows_x86', 'windows_x64', 'arm']))
@click.option('--type', 'payload_type', required=True,
              type=click.Choice(['reverse_shell', 'bind_shell', 'exec', 'download_exec']))
@click.option('--lhost', help='Listener host (for shells)')
@click.option('--lport', type=int, help='Listener port')
@click.option('--command', help='Command to execute')
@click.option('--output', '-o', help='Save to file')
def shellcode(platform, payload_type, lhost, lport, command, output):
    """Generate shellcode for specified platform"""
    
    click.echo(f"[*] Generating {payload_type} for {platform}...")
    
    # Generate
    generator = ShellcodeGenerator()
    try:
        code = generator.generate(
            platform=platform,
            payload_type=payload_type,
            lhost=lhost,
            lport=lport,
            command=command
        )
    except ValueError as e:
        click.echo(click.style(f"[!] Error: {e}", fg='red'))
        return
    
    # Format
    formatter = OutputFormatter()
    cleaned = formatter.clean(code)
    
    # Output
    if output:
        filepath = formatter.to_file(cleaned, output, add_shebang=False)
        click.echo(click.style(f"[+] Saved to: {filepath}", fg='green'))
    else:
        click.echo("\n" + "="*60)
        click.echo(cleaned)
        click.echo("="*60)


@cli.command()
def list_platforms():
    """List supported platforms for shellcode"""
    click.echo("Supported Platforms:")
    for key, desc in ShellcodeGenerator.list_platforms().items():
        click.echo(f"  {key:15} - {desc}")


@cli.command()
def list_payloads():
    """List supported payload types"""
    click.echo("Supported Payload Types:")
    for key, desc in ShellcodeGenerator.list_payload_types().items():
        click.echo(f"  {key:20} - {desc}")


@cli.command()
def disclaimer():
    """Show ethical use disclaimer"""
    click.echo(click.style(ETHICAL_WARNING, fg='yellow', bold=True))


if __name__ == '__main__':
    cli()
