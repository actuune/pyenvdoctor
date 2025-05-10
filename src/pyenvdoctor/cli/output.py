from rich.table import Table
from rich.console import Console

console = Console()

def print_installations_table(installations):
    table = Table(title="Python Installations")
    table.add_column("Path", style="cyan")
    table.add_column("Version", style="green")
    table.add_column("Provider", style="yellow")
    
    for install in installations:
        table.add_row(install.path, install.version, install.provider)
    
    console.print(table)
