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
    
    # Commande check
    check_parser = subparsers.add_parser('check', help='Vérifier les environnements Python')
    check_parser.add_argument('--full', action='store_true', help='Effectuer une vérification complète')
    check_parser.add_argument('--quick', action='store_true', help='Effectuer une vérification rapide')
    check_parser.add_argument('--report', action='store_true', help='Générer un rapport')
    check_parser.set_defaults(func=check_command)
    
    # Commande update
    update_parser = subparsers.add_parser('update', help='Mettre à jour PyEnvDoctor')
    update_parser.add_argument('--silent', action='store_true', help='Mise à jour silencieuse')
    update_parser.set_defaults(func=update_command)
    
    # Commande report
    report_parser = subparsers.add_parser('report', help='Générer un rapport')
    report_parser.add_argument('--format', choices=['text', 'json', 'html'], default='text', help='Format de sortie')
    report_parser.add_argument('--output', help='Fichier de sortie')
    report_parser.set_defaults(func=report_command)

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

def check_command(args):
    """Run diagnostic checks on Python environments"""
    console.print("[bold green]Exécution des vérifications...[/bold green]")
    if args.full:
        console.print("Mode complet activé")
    elif args.quick:
        console.print("Mode rapide activé")
    else:
        console.print("Vérification standard")
    
    if args.report:
        console.print("Génération du rapport...")

def update_command(args):
    """Update PyEnvDoctor"""
    if args.silent:
        print("Mise à jour silencieuse en cours...")
    else:
        console.print("[bold green]Mise à jour de PyEnvDoctor...[/bold green]")
        console.print("Vérification des mises à jour...")

def report_command(args):
    """Generate a report of Python installations"""
    console.print("[bold green]Génération du rapport...[/bold green]")
    console.print(f"Format: {args.format}")
    if args.output:
        console.print(f"Sortie: {args.output}")

if __name__ == "__main__":
    main()
