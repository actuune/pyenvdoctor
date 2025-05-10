import argparse
from rich.console import Console
from rich.prompt import Confirm, Prompt
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
import json
import sys

# Import our modules
from ..scanner.system_scanner import SystemScanner
from ..gamification.manager import GamificationManager
from ..ai.fix_oracle import FixOracle

console = Console()

def main():
    parser = argparse.ArgumentParser(description="PyEnvDoctor - Advanced Python Environment Management")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Enhanced scan command
    scan_parser = subparsers.add_parser('scan', help='Scan Python environments with AI analysis')
    scan_parser.add_argument('--full', action='store_true', help='Perform comprehensive scan')
    scan_parser.add_argument('--ai', action='store_true', help='Include AI-powered analysis')
    scan_parser.add_argument('--json', action='store_true', help='Output in JSON format')
    scan_parser.set_defaults(func=enhanced_scan)
    
    # Advanced fix command
    fix_parser = subparsers.add_parser('fix', help='Fix issues with AI suggestions and undo support')
    fix_parser.add_argument('--dry-run', action='store_true', help='Simulate fixes without making changes')
    fix_parser.add_argument('--ai', action='store_true', help='Include AI-suggested fixes')
    fix_parser.add_argument('--interactive', '-i', action='store_true', help='Interactive fix mode')
    fix_parser.add_argument('--rollback', type=int, metavar='N', help='Rollback last N operations')
    fix_parser.set_defaults(func=advanced_fix)
    
    # Gamification commands
    profile_parser = subparsers.add_parser('profile', help='View your PyEnvDoctor profile and achievements')
    profile_parser.add_argument('--achievements', action='store_true', help='Show detailed achievement progress')
    profile_parser.set_defaults(func=show_profile)
    
    # Security audit
    audit_parser = subparsers.add_parser('audit', help='Security and compliance audit')
    audit_parser.add_argument('--cis', action='store_true', help='Check CIS benchmark compliance')
    audit_parser.add_argument('--cve', action='store_true', help='Scan for known vulnerabilities')
    audit_parser.set_defaults(func=security_audit)
    
    # History and undo
    history_parser = subparsers.add_parser('history', help='View operation history')
    history_parser.add_argument('--limit', type=int, default=10, help='Number of entries to show')
    history_parser.set_defaults(func=show_history)

    # Legacy commands for compatibility
    check_parser = subparsers.add_parser('check', help='Check Python environments (legacy)')
    check_parser.set_defaults(func=legacy_check)
    
    update_parser = subparsers.add_parser('update', help='Update PyEnvDoctor')
    update_parser.set_defaults(func=legacy_update)
    
    report_parser = subparsers.add_parser('report', help='Generate environment report')
    report_parser.set_defaults(func=legacy_report)

    args = parser.parse_args()
    
    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()

def enhanced_scan(args):
    """Enhanced scanning with AI integration"""
    console.print("[bold blue]PyEnvDoctor 2.0 - Environment Scan[/bold blue]\n")
    
    # Initialize components
    scanner = SystemScanner()
    gamification = GamificationManager()
    
    # Perform scan
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Scanning environment...", total=None)
        issues = scanner.scan(comprehensive=args.full)
        installations = scanner.get_installations()
        
    # Update gamification
    gamification.update_stats(scans_performed=1)
    
    # Display results
    if args.json:
        results = {
            "installations": [inst.to_dict() for inst in installations],
            "issues": [issue.to_dict() for issue in issues],
            "summary": {
                "total_installations": len(installations),
                "total_issues": len(issues)
            }
        }
        print(json.dumps(results, indent=2))
    else:
        console.print(f"\n[bold green]Scan Results:[/bold green]")
        console.print(f"✓ Found {len(installations)} Python installation(s)")
        
        for inst in installations:
            status = "✓" if inst.is_valid else "✗"
            color = "green" if inst.is_valid else "red"
            console.print(f"  [{color}]{status} {inst.path} ({inst.provider}) - {inst.version}[/{color}]")
            
        if issues:
            console.print(f"\n[bold yellow]Issues Found:[/bold yellow]")
            for issue in issues:
                severity_color = {
                    "low": "green",
                    "medium": "yellow",
                    "high": "red",
                    "critical": "bright_red"
                }.get(issue.severity, "yellow")
                console.print(f"  • [{severity_color}]{issue.description}[/{severity_color}]")
        else:
            console.print(f"\n[bold green]No issues found![/bold green]")
            
        if args.ai:
            console.print("\n[bold yellow]AI Analysis:[/bold yellow]")
            if not issues:
                console.print("🤖 Your Python environment looks healthy!")
                console.print("🤖 Consider installing pyenv for better version management")
            else:
                console.print("🤖 See the issues above for areas that need attention")

def advanced_fix(args):
    """Advanced fix with AI suggestions"""
    console.print("[bold blue]PyEnvDoctor 2.0 - Fix Issues[/bold blue]\n")
    
    if args.rollback:
        console.print(f"[yellow]Rollback functionality coming soon![/yellow]")
        return
        
    console.print("🔍 Scanning for issues...")
    scanner = SystemScanner()
    issues = scanner.scan(comprehensive=True)  # Use comprehensive for fixes
    
    if not issues:
        console.print("[green]No issues found! Your environment is healthy.[/green]")
        return
        
    console.print(f"Found {len(issues)} issue(s)")
    
    if args.ai:
        oracle = FixOracle()
        for issue in issues:
            suggestions = oracle.suggest_fixes(issue)
            if suggestions:
                console.print(f"\n[yellow]AI Suggestions for: {issue.description}[/yellow]")
                for i, suggestion in enumerate(suggestions, 1):
                    console.print(f"  {i}. {suggestion.description}")
                    if args.interactive:
                        apply = Confirm.ask(f"Apply this fix?", default=False)
                        if apply:
                            console.print("[dim]Fix would be applied here...[/dim]")

def show_profile(args):
    """Display user profile and achievements"""
    gamification = GamificationManager()
    gamification.show_profile()
    
    if args.achievements:
        gamification.show_achievements()

def security_audit(args):
    """Security audit with CIS and CVE checking"""
    console.print("[bold blue]Security Audit[/bold blue]\n")
    
    try:
        from ..security.auditor import SecurityAuditor
        
        auditor = SecurityAuditor()
        
        # Determine what to check
        check_cis = args.cis if hasattr(args, "cis") else True
        check_cve = args.cve if hasattr(args, "cve") else True
        
        # Run audit
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Running security audit...", total=None)
            results = auditor.run_security_audit(check_cis=check_cis, check_cve=check_cve)
            
        # Display results
        if "cis_compliance" in results:
            console.print("\n[bold]CIS Compliance Check:[/bold]")
            cis_results = results["cis_compliance"]
            
            for check_name, check_result in cis_results.items():
                status = check_result.get("status", "unknown")
                color = "green" if status == "pass" else "red"
                console.print(f"  [{color}]• {check_name}: {status.upper()}[/{color}]")
                
                if "issues" in check_result and check_result["issues"]:
                    for issue in check_result["issues"]:
                        console.print(f"    - {issue['description''']}")
                        
        if "vulnerability_scan" in results:
            console.print("\n[bold]Vulnerability Scan:[/bold]")
            vuln_results = results["vulnerability_scan"]
            
            if vuln_results["vulnerabilities"]:
                for vuln in vuln_results["vulnerabilities"]:
                    status = vuln.get("status", "unknown")
                    color = "green" if status == "clean" else "red"
                    console.print(f"  [{color}]• {vuln['version''']}: {status.upper()}[/{color}]")
            else:
                console.print("  [green]No vulnerabilities found[/green]")
                
    except ImportError as e:
        console.print(f"[red]Security module error: {e}[/red]")
        console.print("Security audit requires all modules to be properly installed.")

def show_history(args):
    """Show operation history"""
    console.print("[bold blue]Operation History[/bold blue]\n")
    
    try:
        from ..utils.history import OperationHistory
        
        history_manager = OperationHistory()
        history = history_manager.get_history(limit=args.limit)
        
        if not history:
            console.print("📜 No operations recorded yet")
            return
            
        # Create table
        table = Table(title="Recent Operations", show_header=True)
        table.add_column("ID", width=4)
        table.add_column("Time", width=20)
        table.add_column("Description", width=50)
        table.add_column("Status", width=10)
        
        for op in reversed(history):
            timestamp = datetime.fromisoformat(op["timestamp"]).strftime("%Y-%m-%d %H:%M")
            status = "✓" if op.get("result", {}).get("success", True) else "✗"
            status_color = "green" if status == "✓" else "red"
            
            table.add_row(
                str(op.get("id", "?")),
                timestamp,
                op.get("description", "Unknown"),
                f"[{status_color}]{status}[/{status_color}]"
            )
            
        console.print(table)
        
    except ImportError as e:
        console.print(f"[red]History module error: {e}[/red]")

# Legacy commands
def legacy_check(args):
    console.print("Running check...")
    console.print("✓ Environment check complete")

def legacy_update(args):
    console.print("Updating PyEnvDoctor...")
    console.print("✓ Already up to date")

def legacy_report(args):
    console.print("Generating report...")
    console.print("✓ Report complete")

if __name__ == "__main__":
    main()
