import argparse
from rich.console import Console
from ..scanner.system_scanner import SystemScanner
from ..core.config import config

console = Console()

def main():
    parser = argparse.ArgumentParser(description="PyEnvDoctor - Gestionnaire d'environnements Python")
    subparsers = parser.add_subparsers(dest='command')

    # Commande scan
    scan_parser = subparsers.add_parser('scan', help='Scanner les installations Python')
    scan_parser.set_defaults(func=handle_scan)

    args = parser.parse_args()
    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()

def handle_scan(args):
    console.print("[bold green]Démarrage du scan...[/bold green]")
    scanner = SystemScanner()
    scanner.scan()
    
    installations = scanner.get_installations()
    console.print(f"\n[bold]Installations trouvées:[/bold] {len(installations)}")
    for install in installations:
        console.print(f"• [cyan]{install.path}[/cyan] ({install.provider})")

if __name__ == "__main__":
    main()
